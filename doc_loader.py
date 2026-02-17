from pypdf import PdfReader
from docx import Document
import tempfile

def read_pdf(upload):
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(upload.read())
        path = f.name

    reader = PdfReader(path)
    return "\n".join(p.extract_text() or "" for p in reader.pages)


def read_docx(upload):
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(upload.read())
        path = f.name

    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs)