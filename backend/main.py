from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
import cv2
import numpy as np
import pytesseract
from PIL import Image
import spacy
import json
import logging
import traceback
from spellchecker import SpellChecker
import re
from langdetect import detect, DetectorFactory
import unicodedata

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Load spaCy model
try:
    logger.info("Loading spaCy model...")
    nlp = spacy.load("en_core_web_sm")
    logger.info("spaCy model loaded successfully")
except OSError as e:
    logger.error(f"Error loading spaCy model: {str(e)}")
    try:
        # If model not found, download it
        logger.info("Downloading spaCy model...")
        import subprocess
        subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
        nlp = spacy.load("en_core_web_sm")
        logger.info("spaCy model downloaded and loaded successfully")
    except Exception as e:
        logger.error(f"Failed to download spaCy model: {str(e)}")
        raise

# Supported languages for PySpellChecker
SPELLCHECKER_LANGS = {'en', 'es', 'de', 'fr', 'pt', 'it', 'ru'}

# Helper to get spell checker for a language
def get_spellchecker(language):
    if language in SPELLCHECKER_LANGS:
        return SpellChecker(language=language)
    return None

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def deskew(image):
    try:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        coords = np.column_stack(np.where(binary > 0))
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle += 90
        elif angle > 45:
            angle -= 90
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        return rotated
    except Exception as e:
        logger.error(f"Error in deskew: {str(e)}")
        return image

def preprocess_image(image):
    try:
        blurred = cv2.GaussianBlur(image, (1, 1), 0)
        kernel = np.array([[0, -1, 0],
                          [-1, 5, -1],
                          [0, -1, 0]])
        sharpened = cv2.filter2D(blurred, -1, kernel)
        return sharpened
    except Exception as e:
        logger.error(f"Error in preprocess_image: {str(e)}")
        return image

def thin_text(image):
    try:
        kernel = np.ones((1, 1), np.uint8)
        thinned = cv2.erode(image, kernel, iterations=2)
        return thinned
    except Exception as e:
        logger.error(f"Error in thin_text: {str(e)}")
        return image

def correct_spelling(text, doc, spell_check=True, punctuation=True, language='en'):
    import re
    # Split by newlines and preserve empty lines
    lines = text.split('\n')
    processed_lines = []
    # Get all proper nouns from spaCy with their original case
    proper_nouns = {ent.text for ent in doc.ents}
    # Get spell checker for the language
    spell = get_spellchecker(language) if spell_check else None
    
    # Common technical terms and acronyms to preserve
    technical_terms = {
        'API', 'CLI', 'GUI', 'UI', 'UX', 'CPU', 'GPU', 'RAM', 'ROM', 'HTTP', 'HTTPS',
        'URL', 'URI', 'JSON', 'XML', 'HTML', 'CSS', 'JS', 'SQL', 'NoSQL', 'REST',
        'SOAP', 'API/CLI', 'API/UI', 'CLI/GUI'
    }
    
    for line in lines:
        # Preserve empty lines exactly as they are
        if not line.strip():
            processed_lines.append(line)
            continue
            
        # Process non-empty lines
        tokens = re.findall(r'\b\w+\b|[^\w\s]', line)
        corrected_tokens = []
        for token in tokens:
            if not token.isalnum():
                corrected_tokens.append(token)
                continue
            # Preserve technical terms and acronyms
            if token in technical_terms or (token.isupper() and len(token) >= 2):
                corrected_tokens.append(token)
                continue
            # Check if token is a proper noun before spell checking
            if token in proper_nouns:
                corrected_tokens.append(token)
                continue
            # Check if token is part of a multi-word proper noun
            if any(token in proper_noun.split() for proper_noun in proper_nouns):
                corrected_tokens.append(token)
                continue
            if spell_check and spell and not any(c.isdigit() for c in token):
                if spell.unknown([token]):
                    correction = spell.correction(token)
                    corrected_tokens.append(correction if correction else token)
                else:
                    corrected_tokens.append(token)
            else:
                corrected_tokens.append(token)
        
        # Reconstruct the line with proper spacing
        result = ''
        for i, token in enumerate(corrected_tokens):
            is_special_number = False
            if i > 0 and i < len(corrected_tokens) - 1:
                if (token == '.' and corrected_tokens[i-1].isdigit() and corrected_tokens[i+1].isdigit()):
                    is_special_number = True
                elif (token == '.' and all(t.isdigit() for t in corrected_tokens[max(0, i-3):i]) and all(t.isdigit() for t in corrected_tokens[i+1:min(len(corrected_tokens), i+4)])):
                    is_special_number = True
                elif (token == ':' and all(t.isalnum() for t in corrected_tokens[max(0, i-2):i]) and all(t.isalnum() for t in corrected_tokens[i+1:min(len(corrected_tokens), i+3)])):
                    is_special_number = True
            
            # Add space before token if needed
            if i > 0:
                if token.isalnum() and corrected_tokens[i-1].isalnum():
                    result += ' '
                elif punctuation and token == '(' and corrected_tokens[i-1].isalnum():
                    result += ' '
            
            result += token
            
            # Add space after token if needed
            if i < len(corrected_tokens) - 1:
                if punctuation and token in ['.', ',', ':', ';'] and not is_special_number:
                    result += ' '
                elif punctuation and token == ')' and corrected_tokens[i+1].isalnum():
                    result += ' '
        
        # Preserve any trailing whitespace from the original line
        if line.endswith(' '):
            result += ' '
            
        processed_lines.append(result)
    
    # Join lines with newlines, preserving the original line break style
    return '\n'.join(processed_lines)

def process_text_with_spacy(text, spell_check=True, punctuation=True):
    try:
        if not text or not text.strip():
            logger.warning("Empty text received for spaCy processing")
            return {
                'entities': [],
                'corrected_text': text
            }
        # Detect language
        try:
            language = detect(text)
        except Exception:
            language = 'en'
        # Process each line separately for entity recognition
        lines = text.split('\n')
        all_entities = []
        current_position = 0
        for line in lines:
            if line.strip():
                doc = nlp(line)
                for ent in doc.ents:
                    all_entities.append({
                        'text': ent.text,
                        'label': ent.label_,
                        'start': current_position + ent.start_char,
                        'end': current_position + ent.end_char
                    })
            current_position += len(line) + 1
        # Correct spelling and punctuation if enabled and supported
        if spell_check or punctuation:
            corrected_text = correct_spelling(text, nlp(text), spell_check=spell_check, punctuation=punctuation, language=language)
        else:
            corrected_text = text
        return {
            'entities': all_entities,
            'corrected_text': corrected_text,
            'language': language
        }
    except Exception as e:
        logger.error(f"Error in process_text_with_spacy: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            'entities': [],
            'corrected_text': text,
            'language': 'unknown'
        }

def preprocess_captcha(image):
    # Convert to grayscale if not already
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    # Binarize
    _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
    # Remove lines/noise (morphological opening)
    kernel = np.ones((2, 2), np.uint8)
    clean = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
    # Invert back
    clean = cv2.bitwise_not(clean)
    return clean

def detect_script(text):
    scripts = set()
    for char in text:
        if char.isalpha():
            try:
                name = unicodedata.name(char)
                script = name.split(' ')[0]
                scripts.add(script)
            except ValueError:
                continue
    return list(scripts)

@app.route('/api/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            logger.error("No file part in request")
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']
        if file.filename == '':
            logger.error("No selected file")
            return jsonify({'error': 'No selected file'}), 400
        
        spell_check = request.form.get('spell_check', 'true').lower() == 'true'
        punctuation = request.form.get('punctuation', 'true').lower() == 'true'
        language_code = request.form.get('language', 'auto')
        preprocessing = request.form.get('preprocessing', 'true').lower() == 'true'
        segmentation = request.form.get('segmentation', 'true').lower() == 'true'

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            logger.info(f"File saved to {filepath}")
            
            # Process the image
            image = cv2.imread(filepath)
            if image is None:
                logger.error("Failed to read image")
                return jsonify({'error': 'Failed to process image'}), 400
            
            # Conditionally apply preprocessing
            if preprocessing:
                image = deskew(image)
                image = preprocess_image(image)
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                gray = cv2.bitwise_not(gray)
                thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
                thinned = thin_text(thresh)
            else:
                thinned = image  # Use the original image without preprocessing

            # Use selected language for Tesseract
            if language_code == 'auto':
                tesseract_lang = 'eng+ell+deu+spa+pol+rus+hin+tel+tam+ben+chi_sim+jpn+ara+fra+ita+por'
            else:
                tesseract_lang = language_code
            psm_value = 3 if segmentation else 6
            config = f'--oem 3 --psm {psm_value} -l {tesseract_lang}'
            extracted_text = pytesseract.image_to_string(thinned, config=config)
            logger.info("Text extracted successfully")
            
            # Detect language and script from extracted text
            try:
                detected_language = detect(extracted_text)
            except Exception:
                detected_language = 'unknown'
            detected_scripts = detect_script(extracted_text)
            
            # If both spell_check and punctuation are False, return raw text
            if not spell_check and not punctuation:
                processed_text = {
                    'entities': [],
                    'corrected_text': extracted_text,
                    'detected_language': detected_language,
                    'detected_scripts': detected_scripts
                }
            else:
                # Process text with spaCy and postprocessing
                processed_text = process_text_with_spacy(
                    extracted_text,
                    spell_check=spell_check,
                    punctuation=punctuation
                )
                processed_text['detected_language'] = detected_language
                processed_text['detected_scripts'] = detected_scripts
            logger.info("Text processed with spaCy successfully")
            
            # Clean up
            os.remove(filepath)
            logger.info("Temporary file removed")
            
            return jsonify(processed_text)
        
        logger.error("Invalid file type")
        return jsonify({'error': 'Invalid file type'}), 400
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
