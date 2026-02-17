# doc_tools.py
import io
from pdfminer.high_level import extract_text as pdf_extract_text
try:
    import docx2txt
except Exception:
    docx2txt = None

def read_pdf(path_or_bytes):
    """
    path_or_bytes: either path to file or bytes
    """
    try:
        if isinstance(path_or_bytes, bytes):
            # write to temp file
            import tempfile
            tf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            tf.write(path_or_bytes)
            tf.flush()
            tf.close()
            txt = pdf_extract_text(tf.name)
            return txt
        else:
            return pdf_extract_text(path_or_bytes)
    except Exception as e:
        return f"[PDF read error] {e}"

def read_docx(path_or_bytes):
    if docx2txt is None:
        return "[docx2txt not installed]"
    try:
        if isinstance(path_or_bytes, bytes):
            import tempfile
            tf = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
            tf.write(path_or_bytes)
            tf.flush()
            tf.close()
            return docx2txt.process(tf.name)
        else:
            return docx2txt.process(path_or_bytes)
    except Exception as e:
        return f"[DOCX read error] {e}"
