## Overview

This project provides a **multilingual anonymizer** and **de-anonymizer** for text files, using [GLiNER](https://github.com/Babelscape/GLiNER) for Named Entity Recognition. It supports different file formats (TXT, PDF, DOCX, XLSX, etc.) and can detect English and Italian by default (you can extend it to other languages).

It consists of:

1. A **Flask-based backend** (`app.py`) exposing two main REST endpoints:
   - `POST /api/anonymize` – Receives a single file, extracts text, anonymizes named entities, returns:
     - The anonymized text in plain form.
     - A Base64-encoded ZIP that contains:
       1. `anonymized.txt`
       2. `mapping.json` (placeholder → original text pairs).
   - `POST /api/deanonymize` – Receives two files (`anonymized text` and `mapping.json`), restores the original text, and returns a Base64-encoded file.

2. Two **HTML/CSS + jQuery** frontends:
   - **`index.html`**: The **anonymization** page. Users can drag & drop or select a file to upload, click “Anonymize,” see the anonymized text, and automatically download a ZIP with the anonymized data and mapping.
   - **`deanonymize.html`**: The **de-anonymization** page. Users can drag & drop or select the anonymized text file and the mapping file, then click “De-anonymize” to get the restored original text as a Base64 download.

---

## Requirements

- **Python** 3.8+  
- **pip** (to install dependencies)  
- **Flask** and **Flask-CORS** (for the backend server)  
- **GLiNER** and **langdetect** (for Named Entity Recognition and language detection)  
- (Optional) **PyPDF2**, **python-docx**, **openpyxl**, etc., if you want to fully extract text from PDF, DOCX, XLSX.  
- A simple local or remote web server to serve the **HTML** pages, or open them directly from the filesystem (for testing).

---

## Installation

1. **Clone or download** this repository.
2. Create a **virtual environment** (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate     # Windows
   ```
3. **Install required Python packages**:
   ```bash
   pip install flask flask-cors gliner langdetect
   # If needed for PDF/DOCX/XLSX:
   pip install PyPDF2 python-docx openpyxl
   ```
4. **Check** that the files `index.html` and `deanonymize.html` are in the same directory or a convenient static folder.

---

## Running the Backend

Inside the project folder (where `app.py` is located), run:

```bash
python app.py
```

By default, it starts on `http://localhost:5000`. You will see log messages in the terminal indicating the server status.

---

## Anonymization

1. **Open** `index.html` in your browser (e.g., double-click the file or serve it from a local static server).  
2. A simple **navbar** appears with two links:
   - “Anonymize” → This page.
   - “De-anonymize” → `deanonymize.html`.
3. On the **left**, you will see a **drag & drop** area and a button to select the file:
   - Supported file formats for text extraction depend on your backend logic. In the simplest case, it handles `.txt`.
   - Once the file is selected, its name is displayed.
4. Click the **“Anonymize”** button. The page will:
   - Send an AJAX request (`POST /api/anonymize`) with the file.
   - The server replies with a JSON containing:
     - `anonymized_text`: The text containing placeholders, displayed on the **right**.
     - `zip_base64`: A base64 string for a ZIP containing `anonymized.txt` + `mapping.json`.
   - The frontend automatically triggers a download for the ZIP file (“anonymized_package.zip”).

---

## De-anonymization

1. **Open** `deanonymize.html` in your browser.  
2. The **navbar** links:
   - “Anonymize” → `index.html`.
   - “De-anonymize” → This page.
3. You see two **drag & drop** zones (and buttons to select files):
   - One for the **anonymized text** (e.g., `anonymized.txt`).
   - One for the **mapping** file (e.g., `mapping.json`).
4. After you have selected both files, click **“De-anonymize.”**  
5. The page sends a `POST /api/deanonymize` request with these two files. The backend:
   - Reads the anonymized text.
   - Reads `mapping.json` with placeholder → original mappings.
   - Replaces placeholders with original text.
   - Returns a JSON with `deanonymized_base64`.
6. The frontend automatically **downloads** the restored file as `deanonymized.txt`.

---

## Customization

- **File extraction**: Currently, the sample code in `extract_text` only reads `.txt`. If you want PDF, DOCX, XLSX support, integrate the relevant libraries (`PyPDF2`, `python-docx`, `openpyxl`) within `extract_text` accordingly.
- **CORS**: If you’re opening the HTML files on a different origin than the Flask server, ensure `flask_cors.CORS(app)` is used or manage CORS headers manually.
- **Labels**: By default, it recognizes `["PERSON", "ORG", "LOC"]`. You can customize labels or load them from a file.
- **Language detection**: We use `langdetect`; if the detected language code is not one of the loaded GLiNER models, we default to `"en"`.
- **Encryption**: This example does not encrypt `mapping.json`. If you want a hybrid RSA+AES approach, adapt the code to encrypt/decrypt the mapping.

---

## Example Folder Structure

```
project/
├── app.py
├── requirements.txt  (optional)
├── index.html        (Anonymization frontend)
├── deanonymize.html  (De-anonymization frontend)
└── ...
```

---

## Usage Summary

1. **Start the Flask backend**:
   ```bash
   python app.py
   # runs on http://localhost:5000
   ```
2. **Open `index.html`** to anonymize:
   - Drag or select a file.  
   - Click “Anonymize.”  
   - View anonymized text and auto-download a ZIP with `anonymized.txt` + `mapping.json`.
3. **Open `deanonymize.html`** to de-anonymize:
   - Upload both the anonymized text (`anonymized.txt`) and the `mapping.json`.  
   - Click “De-anonymize.”  
   - Auto-download `deanonymized.txt`.

---

## License
