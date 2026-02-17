from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import tempfile

def make_pdf(text):
    file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    c = canvas.Canvas(file.name, pagesize=A4)

    y = 800
    for line in text.split("\n"):
        c.drawString(40, y, line[:100])
        y -= 18
        if y < 50:
            c.showPage()
            y = 800

    c.save()
    return file.name
