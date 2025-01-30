# Overview

Questa applicazione fornisce un sistema multilingua per **anonimizzare** e **de-anonimizzare** documenti di testo, sfruttando [GLiNER](https://github.com/gliner/GliNER) per il Named Entity Recognition (NER). Supporta vari formati di file (TXT, PDF, DOCX, XLSX, ecc.) e riconosce in modo automatico l’inglese e l’italiano (estensibile ad altre lingue).

## Funzionalità Principali

- **Anonimizzazione**:  
  - Caricamento di un documento (PDF, DOCX, XLSX, TXT, ecc.).  
  - Riconoscimento delle entità nominate (ad es. PERSON, ORG, LOC).  
  - Sostituzione con placeholder.  
  - Download di un archivio ZIP contenente:
    - `anonymized.txt` (testo anonimizzato)
    - `mapping.json` (mappatura dei placeholder → testo originale)  

- **De-anonimizzazione**:  
  - Caricamento del testo anonimizzato e del relativo file di mappatura.  
  - Ricostruzione del testo originale.  
  - Download del file de-anonimizzato (opzionalmente in un archivio ZIP).

## Struttura del Progetto

- **Backend** (Flask, `app.py`):
  - Espone due endpoint REST:
    - `POST /api/anonymize`
    - `POST /api/deanonymize`
  - Utilizza GLiNER per l’estrazione e l’anonimizzazione delle entità.
  - Gestisce il caricamento dei file, l’estrazione del testo e l’identificazione della lingua.
  - Restituisce i risultati in formati JSON + file in Base64.

- **Frontend** (HTML, CSS, jQuery/Bootstrap):
  - **`index.html`**: interfaccia per l’anonimizzazione (drag & drop, upload file, anteprima del testo anonimizzato, download ZIP).
  - **`deanonymize.html`**: interfaccia per la de-anonimizzazione (caricamento del file anonimizzato e del file di mapping, download del file de-anonimizzato).

## Requisiti

- Python 3.8+  
- [Flask](https://pypi.org/project/Flask/) e [Flask-CORS](https://pypi.org/project/Flask-Cors/)  
- [GLiNER](https://github.com/gliner/GliNER) e [langdetect](https://pypi.org/project/langdetect/)  
- Librerie opzionali per l’estrazione del testo dai documenti (es. `PyPDF2`, `python-docx`, `openpyxl`).

## Installazione

1. **Clona** o **scarica** il repository.
2. (Opzionale) Crea un ambiente virtuale:
   ```bash
   python -m venv venv
   source venv/bin/activate   # Linux/Mac
   # oppure su Windows:
   venv\Scripts\activate
   ```
3. Installa le dipendenze Python:
   ```bash
   pip install -r requirements.txt
   ```
4. Assicurati che i file `index.html` e `deanonymize.html` siano nella posizione desiderata (stessa directory o cartella `static/`, a seconda di come vuoi servire i file).

## Esecuzione del Backend

All’interno della cartella del progetto (dove risiede `app.py`):

```bash
python app.py
```

Per impostazione predefinita, il server sarà disponibile su `http://localhost:5000`. Nel terminale vedrai i log delle richieste e dello stato del server.

## Utilizzo

### Anonimizzazione

1. Apri `index.html` nel browser (o servila da un web server locale).
2. Nella pagina:
   - Seleziona o trascina un file (PDF, DOCX, XLSX, TXT, ecc.).  
   - Clicca sul pulsante **“Anonimizza”**.  
3. Il backend:
   - Estrae il testo.
   - Rileva la lingua.
   - Anonimizza le entità e genera il mapping.
4. L’applicazione mostra il **testo anonimizzato** e **scarica** un archivio ZIP con `anonymized.txt` e `mapping.json`.

### De-anonimizzazione

1. Apri `deanonymize.html`.
2. Carica:
   - Il file di testo anonimizzato (`anonymized.txt`).
   - Il file di mapping (`mapping.json`).
3. Clicca **“De-anonimizza”**.  
4. Il backend sostituisce i placeholder con le entità originali.  
5. Viene mostrato il testo de-anonimizzato e (opzionalmente) scaricato in un file.

## Personalizzazione

- **Estrazione del Testo**: puoi estendere la funzione di parsing per altri formati.  
- **Labels**: personalizza la lista di entità nel file `gliner_entities.txt` o nel codice.  
- **Librerie**: installa solo quelle necessarie (PDF, DOCX, XLSX, ecc.) se vuoi supportare quei formati.  
- **CORS**: assicurati di configurare `flask_cors.CORS(app)` se usi domini diversi per frontend/backend.

## Esempio di Struttura

```
project/
├── app.py
├── requirements.txt
├── index.html         (Pagina Anonimizzazione)
├── deanonymize.html   (Pagina De-anonimizzazione)
├── styles.css         (Stili comuni)
└── ...
```

## Licenza
