import os
import io
import json
import base64
import zipfile
import tempfile

from pathlib import Path
from flask import Flask, request
from flask_cors import CORS

from gliner import GLiNER
from langdetect import detect

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests (e.g., from HTML/JS frontends)

################################
# 1. LOAD GLiNER MODELS
################################
gliner_models = {
    "en": GLiNER.from_pretrained("gliner-community/gliner_medium-v2.5"),
    "it": GLiNER.from_pretrained("DeepMount00/GLiNER_ITA_LARGE")
}

LABELS = ["PERSON", "ORG", "LOC"]  # Example entity labels

############################
# 2. UTILITY FUNCTIONS
############################

def extract_text(path: Path) -> str:
    """
    Extract text from a local file, handling PDF, DOCX, XLSX, and TXT.
    If you need more formats, extend accordingly.
    """
    suffix = path.suffix.lower()
    text = ""

    if suffix == ".pdf":
        # PDF extraction
        from PyPDF2 import PdfReader
        try:
            reader = PdfReader(str(path))
            for page in reader.pages:
                page_text = page.extract_text() or ""
                text += page_text + "\n"
        except Exception as e:
            print(f"Error reading PDF {path}: {e}")
            return ""
        return text.strip()

    elif suffix == ".docx":
        # DOCX extraction
        import docx
        try:
            doc = docx.Document(str(path))
            for para in doc.paragraphs:
                text += para.text + "\n"
        except Exception as e:
            print(f"Error reading DOCX {path}: {e}")
            return ""
        return text.strip()

    elif suffix == ".xlsx":
        # XLSX extraction
        import openpyxl
        try:
            wb = openpyxl.load_workbook(str(path), data_only=True)
            for sheet in wb.worksheets:
                for row in sheet.iter_rows(values_only=True):
                    row_text = [str(cell) for cell in row if cell is not None]
                    if row_text:
                        text += " ".join(row_text) + "\n"
        except Exception as e:
            print(f"Error reading XLSX {path}: {e}")
            return ""
        return text.strip()

    elif suffix == ".txt":
        # TXT read
        try:
            return path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            print(f"Error reading TXT {path}: {e}")
            return ""

    else:
        print(f"Unsupported file format: {suffix}")
        return ""

def detect_language_of_text(text: str) -> str:
    try:
        code = detect(text)
        if code not in gliner_models:
            return "en"  # fallback if not supported
        return code
    except:
        return "en"  # fallback

def anonymize_text(text: str, lang_code: str):
    """
    Use GLiNER to detect entities and replace them with placeholders.
    Returns (anonymized_text, mapping_list) where
    mapping_list = [(placeholder, original_text), ...].
    """
    model = gliner_models[lang_code]
    entities = model.predict_entities(text, LABELS, threshold=0.5)

    anonymized = text
    mapping_list = []
    for i, ent in enumerate(entities):
        placeholder = f"{{{{{ent['label']}_{i}}}}}"
        anonymized = anonymized.replace(ent["text"], placeholder)
        mapping_list.append((placeholder, ent["text"]))
    return anonymized, mapping_list

def deanonymize_text(anonymized_text: str, mapping_list: list) -> str:
    """
    Replace placeholders with their original strings.
    mapping_list is [(placeholder, original), ...].
    """
    deanonymized = anonymized_text
    for placeholder, original in mapping_list:
        deanonymized = deanonymized.replace(placeholder, original)
    return deanonymized

############################
# 3. ENDPOINT /api/anonymize
############################
@app.route("/api/anonymize", methods=["POST"])
def api_anonymize():
    """
    Receives a single file ("file"), extracts text, anonymizes, and returns:
    {
      "anonymized_text": "...",
      "zip_base64": "..."
    }
    The zip_base64 contains anonymized.txt + mapping.json.
    """
    if "file" not in request.files:
        return {"error": "File not provided"}, 400

    uploaded_file = request.files["file"]
    if uploaded_file.filename == "":
        return {"error": "Empty filename"}, 400

    # Save to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=uploaded_file.filename) as tf:
        uploaded_file.save(tf.name)
        raw_text = extract_text(Path(tf.name))

    lang_code = detect_language_of_text(raw_text)
    anonymized_text, mapping_list = anonymize_text(raw_text, lang_code)

    # Create a ZIP in memory with anonymized.txt + mapping.json
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("anonymized.txt", anonymized_text)
        zf.writestr("mapping.json", json.dumps({
            "mapping": mapping_list,
            "language": lang_code
        }, ensure_ascii=False, indent=2))

    # Convert ZIP to Base64
    zip_buffer.seek(0)
    zip_data = zip_buffer.read()
    zip_base64 = base64.b64encode(zip_data).decode("utf-8")

    return {
        "anonymized_text": anonymized_text,
        "zip_base64": zip_base64
    }

##############################
# 4. ENDPOINT /api/deanonymize
##############################
@app.route("/api/deanonymize", methods=["POST"])
def api_deanonymize():
    """
    Receives two files:
      - textFile (the anonymized text, e.g. anonymized.txt)
      - mappingFile (the mapping.json)
    Returns:
    {
      "deanonymized_base64": "..."
    } with the de-anonymized text in Base64.
    """
    if "textFile" not in request.files or "mappingFile" not in request.files:
        return {"error": "Missing textFile or mappingFile"}, 400

    # Read the anonymized text
    anonymized_data = request.files["textFile"].read().decode("utf-8", errors="replace")

    # Read the mapping file
    mapping_content = request.files["mappingFile"].read().decode("utf-8", errors="replace")
    try:
        mapping_json = json.loads(mapping_content)
    except:
        return {"error": "Invalid JSON in mappingFile"}, 400

    # Extract the list of (placeholder, original)
    mapping_list = mapping_json.get("mapping", [])

    # Perform de-anonymization
    deanonymized = deanonymize_text(anonymized_data, mapping_list)

    # Encode result in Base64
    result_b64 = base64.b64encode(deanonymized.encode("utf-8")).decode("utf-8")

    return {
        "deanonymized_base64": result_b64
    }

###################
# APP ENTRY POINT
###################
if __name__ == "__main__":
    app.run(debug=True, port=5000)
