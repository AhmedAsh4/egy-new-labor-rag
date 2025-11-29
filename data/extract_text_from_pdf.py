import pdfplumber
import arabic_reshaper
from bidi.algorithm import get_display

def extract_and_fix_arabic(pdf_path):
    full_text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            raw_text = page.extract_text()
            if raw_text:
                reshaped_text = arabic_reshaper.reshape(raw_text)
                bidi_text = get_display(reshaped_text)
                full_text += bidi_text + "\n"
    return full_text

if __name__ == "__main__":
    extracted = extract_and_fix_arabic("data/files/labor law.pdf")
    with open("data/files/labor law.txt", "w", encoding="utf-8-sig") as f:
        f.write(extracted)
