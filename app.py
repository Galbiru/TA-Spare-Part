import cv2
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# input nama gambar
gambar = input("Masukkan nama gambar: ")

# baca gambar
img = cv2.imread(gambar)

# grayscale
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# OCR
text = pytesseract.image_to_string(gray)

# ubah jadi huruf besar
text = text.upper()

# klasifikasi
if "SSD" in text:
    kategori = "SSD"

elif "RAM" in text:
    kategori = "RAM"

elif "LCD" in text:
    kategori = "LCD"

else:
    kategori = "Tidak Diketahui"

# output
print("Hasil OCR:", text)
print("Kategori:", kategori)