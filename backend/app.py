import cv2
import numpy as np
import pytesseract
from PIL import Image
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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
        # You can adjust or comment out this step if it reduces accuracy
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
        # You can adjust kernel size or iterations, or skip this step if not needed
        kernel = np.ones((1, 1), np.uint8)
        thinned = cv2.erode(image, kernel, iterations=2)
        return thinned
    except Exception as e:
        logger.error(f"Error in thin_text: {str(e)}")
        return image

# Load image
image = cv2.imread('Everchem-Speciality-CHEMICALS_14_png.rf.4f30f57869ec4b719b598ef1ff789aae.jpg')

# Check if the image was loaded successfully
if image is None:
    print("Error: Image not loaded. Check the file path.")
    exit()

# Deskew the image
image = deskew(image)

# Optional: Preprocess the image (Gaussian Blur + Sharpening)
# Comment out the next line if preprocessing reduces accuracy for your images
image = preprocess_image(image)

# Convert to grayscale
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# Invert the grayscale image
gray = cv2.bitwise_not(gray)

# Threshold the image
thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

# Optional: Thin out the text
# Comment out the next line if thinning reduces accuracy for your images
thinned = thin_text(thresh)

# Display the processed image using PIL
Image.fromarray(cv2.cvtColor(thinned, cv2.COLOR_GRAY2RGB)).show()

# OCR: Extract text using Tesseract
config = r'--oem 3 --psm 6'
raw_text = pytesseract.image_to_string(thinned, config=config)

# Print the extracted text
print("Extracted Text:")
print(raw_text)