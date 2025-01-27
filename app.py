import os
import io
import json
import base64
import zipfile
import tempfile

from pathlib import Path
from flask import Flask, request
from flask_cors import CORS

# Se servono: PyPDF2, docx, openpyxl, langdetect, gliner, ecc.
# pip install gliner langdetect
from gliner import GLiNER
from langdetect import detect

app = Flask(__name__)
CORS(app)  # Consenti richieste da frontend (HTML/jQuery ecc.)

################################
# 1. CARICAMENTO MODELLI GLiNER
################################
# Supponiamo di gestire solo 2 lingue: inglese e italiano
gliner_models = {
    "en": GLiNER.from_pretrained("gliner-community/gliner_medium-v2.5"),
    "it": GLiNER.from_pretrained("DeepMount00/GLiNER_ITA_LARGE")
}

# Eventuali label. Puoi caricarle da un file, se preferisci.
LABELS = ["PERSON", "ORG", "LOC"]

############################
# 2. FUNZIONI UTILI
############################

def extract_text(path: Path) -> str:
    """
    Estrai il testo dal file locale. 
    Esempio minimizzato: se hai bisogno di PDF, DOCX o XLSX, integra le librerie
    (PyPDF2, python-docx, openpyxl) e la logica di estrazione.
    Per brevità, qui ipotizziamo si tratti di .txt.
    """
    # Esempio banale: leggi .txt
    # Se vuoi veramente gestire PDF, DOCX, XLSX, sostituisci con la logica appropriata.
    return path.read_text(encoding="utf-8", errors="replace")

def detect_language_of_text(text: str) -> str:
    try:
        code = detect(text)
        if code not in gliner_models:
            return "en"  # fallback se non supportato
        return code
    except:
        return "en"  # fallback

def anonymize_text(text: str, lang_code: str):
    """
    Usa GLiNER per riconoscere entità e sostituirle con placeholder.
    Restituisce (testo_anonimizzato, lista_mapping).
    lista_mapping = [(placeholder, original), ...].
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
    Sostituisce i placeholder con gli originali.
    mapping_list è una lista di tuple (placeholder, original).
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
    Riceve un file ("file"), estrae testo, anonimizza, ritorna:
    {
      "anonymized_text": "...",
      "zip_base64": "..."
    }
    Lo zip_base64 contiene "anonymized.txt" + "mapping.json".
    """
    if "file" not in request.files:
        return {"error": "File not provided"}, 400

    uploaded_file = request.files["file"]
    if uploaded_file.filename == "":
        return {"error": "Empty filename"}, 400

    # Salva in un file temporaneo
    with tempfile.NamedTemporaryFile(delete=False, suffix=uploaded_file.filename) as tf:
        uploaded_file.save(tf.name)
        raw_text = extract_text(Path(tf.name))

    lang_code = detect_language_of_text(raw_text)
    anonymized_text, mapping_list = anonymize_text(raw_text, lang_code)

    # Creiamo uno ZIP in memoria con anonymized.txt e mapping.json
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("anonymized.txt", anonymized_text)
        # Qui il mapping è in chiaro; se vuoi cifrarlo, puoi farlo
        zf.writestr("mapping.json", json.dumps({
            "mapping": mapping_list,
            "language": lang_code
        }, ensure_ascii=False, indent=2))

    # Convertiamo lo ZIP in base64
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
    Riceve due file:
      - "textFile" (il testo anonimizzato, ex anonymized.txt)
      - "mappingFile" (il mapping.json)
    Restituisce:
      {
        "deanonymized_base64": "..."
      }
    con la stringa de-anonimizzata in base64.
    """
    if "textFile" not in request.files or "mappingFile" not in request.files:
        return {"error": "Missing textFile or mappingFile"}, 400

    # Leggiamo il testo anonimizzato
    anonymized_data = request.files["textFile"].read().decode("utf-8", errors="replace")

    # Leggiamo il file di mapping
    mapping_content = request.files["mappingFile"].read().decode("utf-8", errors="replace")
    try:
        mapping_json = json.loads(mapping_content)
    except:
        return {"error": "Invalid JSON in mappingFile"}, 400

    # Recuperiamo la lista di tuple (placeholder, original)
    mapping_list = mapping_json.get("mapping", [])

    # Eseguiamo la de-anonimizzazione
    deanonymized = deanonymize_text(anonymized_data, mapping_list)

    # Convertiamo in base64 per restituirlo
    result_b64 = base64.b64encode(deanonymized.encode("utf-8")).decode("utf-8")

    return {
        "deanonymized_base64": result_b64
    }

###################
# AVVIO DELL'APP
###################
if __name__ == "__main__":
    app.run(debug=True, port=5000)
