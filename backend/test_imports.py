try:
    import pdfplumber
    print("pdfplumber imported successfully")
except Exception as e:
    print("pdfplumber failed:", e)

try:
    import docx
    print("python-docx imported successfully")
except Exception as e:
    print("python-docx failed:", e)

try:
    import spacy
    print("spacy imported successfully")
except Exception as e:
    print("spacy failed:", e)
