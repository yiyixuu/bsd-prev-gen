import pytesseract
from PIL import Image
import re
import cv2

# Path to tesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Load and preprocess the image
image_path = r"C:\Users\yiyi\Pictures\Screenshots\Screenshot 2025-06-03 165558.png"
img = cv2.imread(image_path)
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
resized = cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
_, thresh = cv2.threshold(resized, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

# OCR with config
custom_config = r'--psm 7 -c tessedit_char_whitelist=0123456789.+-⌀±'
text = pytesseract.image_to_string(thresh, config=custom_config)

print("Full OCR output:", text)

# Extract only the **main numeric value**, discarding symbols/tolerances
# Match e.g., ⌀136, Ø136, 136±0.5 → 136
match = re.search(r'[\⌀Ø]?\s?(\d+(\.\d+)?)', text)
if match:
    dimension = match.group(1)
    print("Raw dimension:", dimension)
else:
    print("No dimension found.")
