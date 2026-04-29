# Text OCR

Text OCR is a full-stack image-to-text application with a React + Vite frontend and a Flask backend. It lets you upload an image, extract text with Tesseract OCR, and optionally improve the output with preprocessing, spell checking, punctuation correction, and spaCy-based entity detection.

## Features

- Upload PNG or JPG images for OCR
- Preprocess images before OCR for better accuracy
- Choose OCR language or enable auto-detection across multiple languages
- Optional spell check and punctuation correction
- Named entity highlighting using spaCy
- Displays detected language and script information
- Copy extracted text to the clipboard

## Project Structure

- `frontend/` – React UI built with Vite
- `backend/` – Flask API that handles image upload and OCR processing

## Requirements

### Frontend
- Node.js 18+ recommended

### Backend
- Python 3.12+
- Tesseract OCR installed on your system
- The backend Python packages listed in `backend/requirements.txt`
- Additional backend packages used by the app:
  - `spacy`
  - `langdetect`
  - `pyspellchecker`
- spaCy English model:
  - `en_core_web_sm`

## Setup

### 1) Clone the repository

```bash
git clone <repo-url>
cd text_ocr
```

### 2) Set up the backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install spacy langdetect pyspellchecker
python -m spacy download en_core_web_sm
```

If Tesseract is not already installed, install it through your system package manager. On Ubuntu/Debian, for example:

```bash
sudo apt update
sudo apt install tesseract-ocr
```

### 3) Set up the frontend

```bash
cd ../frontend
npm install
```

## Running the App

### Start the backend

From the `backend/` directory:

```bash
python main.py
```

The Flask API runs on `http://localhost:5000`.

### Start the frontend

From the `frontend/` directory:

```bash
npm run dev
```

The Vite app runs on `http://localhost:5173` by default.

## How It Works

1. Open the frontend in your browser.
2. Upload an image.
3. Choose OCR options such as language, preprocessing, spell check, and punctuation correction.
4. The frontend sends the file to `POST /api/upload` on the backend.
5. The backend performs OCR, post-processing, and entity extraction.
6. The UI displays the extracted text, corrected text, detected entities, detected language, and scripts.

## API

### `POST /api/upload`

#### Form fields

- `file` – image file (`png`, `jpg`, or `jpeg`)
- `spell_check` – `true` or `false`
- `punctuation` – `true` or `false`
- `preprocessing` – `true` or `false`
- `segmentation` – `true` or `false`
- `language` – OCR language code or `auto`

#### Example response

```json
{
  "entities": [],
  "corrected_text": "Extracted text here",
  "language": "en",
  "detected_language": "en",
  "detected_scripts": ["LATIN"]
}
```

## Notes

- Uploaded files are saved temporarily in `backend/uploads/` and removed after processing.
- The backend accepts images up to 16 MB.
- For best OCR results, use clear, high-resolution images.
- If you use a different Tesseract installation path, you may need to update the backend configuration accordingly.

## License

No license has been specified for this project.
