# ai_inventory_optimizer.py
import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image
from io import StringIO, BytesIO
import os
from dotenv import load_dotenv

load_dotenv()

# optional modules
from whisper_local import transcribe_audio_bytes
from search_brain import ask_brain
from reporter import make_pdf
from voice_tools import speak_text
from doc_tools import read_pdf, read_docx

# optional memory
try:
    from memory import Memory
    mem = Memory()
except Exception:
    mem = None

st.set_page_config(page_title="AI Inventory - Beta", layout="wide")
st.title("🧠 AI Inventory — Beta")
st.caption("Upload CSV/Excel or Image / Paste text — get forecasting, dashboard, and research answers")

# Column name hints
DATE_NAMES = ["date","day","bill_date","invoice_date"]
QTY_NAMES = ["qty","quantity","units","units_sold","count"]
PRODUCT_NAMES = ["product","item","name","product_name","material"]
PRICE_NAMES = ["price","selling_price","mrp","rate"]
COST_NAMES = ["cost","buy_price","purchase","cost_per_unit"]

def find_column(cols, keywords):
    for c in cols:
        for k in keywords:
            if k in c.lower():
                return c
    return None

# OCR options: Google Vision -> PaddleOCR -> pytesseract
def ocr_image_to_text(image_bytes):
    # try Google Vision if env set
    gpath = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if gpath:
        try:
            from google.cloud import vision
            client = vision.ImageAnnotatorClient()
            image = vision.Image(content=image_bytes)
            response = client.document_text_detection(image=image)
            return response.full_text_annotation.text
        except Exception:
            pass
    # try PaddleOCR
    try:
        from paddleocr import PaddleOCR
        ocr = PaddleOCR(use_angle_cls=True, lang='en')
        import numpy as np
        from PIL import Image
        img = Image.open(BytesIO(image_bytes)).convert("RGB")
        arr = np.array(img)
        res = ocr.ocr(arr, cls=True)
        lines = [r[1][0] for r in res[0]]
        return "\n".join(lines)
    except Exception:
        pass
    # fallback pytesseract
    try:
        import pytesseract
        img = Image.open(BytesIO(image_bytes))
        return pytesseract.image_to_string(img)
    except Exception:
        return ""

# File upload UI
st.header("📥 Upload data")
uploaded = st.file_uploader("CSV / Excel / Image / PDF / DOCX", type=["csv","xlsx","png","jpg","jpeg","pdf","docx"])
paste_text = st.text_area("Or paste CSV text here (header row required)")

df = None
raw_text = None

if paste_text:
    try:
        df = pd.read_csv(StringIO(paste_text))
    except Exception:
        raw_text = paste_text

if uploaded:
    name = uploaded.name.lower()
    data = uploaded.read()
    if name.endswith(".csv"):
        df = pd.read_csv(BytesIO(data))
    elif name.endswith(".xlsx") or name.endswith(".xls"):
        df = pd.read_excel(BytesIO(data))
    elif name.endswith(".pdf"):
        raw_text = read_pdf(data)
    elif name.endswith(".docx"):
        raw_text = read_docx(data)
    elif name.endswith((".png",".jpg","jpeg")):
        raw_text = ocr_image_to_text(data)
        # try to parse text into CSV table if looks like table
        # simple heuristic: if comma present, parse CSV
        if "," in raw_text and "\n" in raw_text:
            try:
                df = pd.read_csv(StringIO(raw_text))
            except Exception:
                pass

if df is not None:
    st.subheader("📊 Raw Data")
    st.dataframe(df.head())

    cols = df.columns.tolist()
    date_col = find_column(cols, DATE_NAMES)
    qty_col = find_column(cols, QTY_NAMES)
    prod_col = find_column(cols, PRODUCT_NAMES)
    price_col = find_column(cols, PRICE_NAMES)
    cost_col = find_column(cols, COST_NAMES)

    st.subheader("🔧 Confirm Columns")
    date_col = st.selectbox("Date column", cols, index=cols.index(date_col) if date_col in cols else 0)
    prod_col = st.selectbox("Product column", cols, index=cols.index(prod_col) if prod_col in cols else 0)
    qty_col = st.selectbox("Quantity column", cols, index=cols.index(qty_col) if qty_col in cols else 0)
    price_col = st.selectbox("Price column", cols, index=cols.index(price_col) if price_col in cols else 0)
    cost_col = st.selectbox("Cost column", cols, index=cols.index(cost_col) if cost_col in cols else 0)

    # clean
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df[qty_col] = pd.to_numeric(df[qty_col], errors="coerce").fillna(0)
    df[price_col] = pd.to_numeric(df[price_col], errors="coerce").fillna(0)
    df[cost_col] = pd.to_numeric(df[cost_col], errors="coerce").fillna(0)
    df["profit"] = (df[price_col] - df[cost_col]) * df[qty_col]

    # Dashboard
    st.subheader("🏪 Shop Dashboard")
    c1,c2,c3 = st.columns(3)
    c1.metric("Total Units Sold", int(df[qty_col].sum()))
    c2.metric("Total Revenue", int((df[price_col]*df[qty_col]).sum()))
    c3.metric("Total Profit", int(df["profit"].sum()))
    st.bar_chart(df.groupby(prod_col)[qty_col].sum())

    # Forecast (per product)
    st.subheader("📈 Forecast")
    forecast_days = st.slider("Forecast days", 7, 90, 30)
    forecasts = {}
    for p, sub in df.groupby(prod_col):
        daily = sub.groupby(date_col)[qty_col].sum().sort_index()
        if len(daily) < 2:
            forecasts[p] = int(daily.sum())
            continue
        x = np.arange(len(daily))
        coeffs = np.polyfit(x, daily.values, 1)
        slope = coeffs[0]
        avg = daily.mean()
        future = avg + slope * forecast_days
        forecasts[p] = max(int(future), 0)
    st.dataframe(pd.DataFrame.from_dict(forecasts, orient="index", columns=["Predicted Units"]))

    # Smart Query
    st.subheader("💬 Ask Your Data / Research")
    q = st.text_input("Ask something like: best product? compare items? research market for paints?")
    if st.button("Ask AI"):
        if not q:
            st.warning("Write a question.")
        else:
            # local memory: store query
            if mem:
                mem.add(q)
            # If user wants deep research, use ask_brain which searches web and queries LLM
            if "research" in q.lower() or "compare" in q.lower() or "market" in q.lower():
                with st.spinner("Searching the web + reasoning..."):
                    out = ask_brain(q)
                st.write(out)
                speak_text(str(out)[:800])
            else:
                ql = q.lower()
                if "best" in ql:
                    best = df.groupby(prod_col)["profit"].sum().idxmax()
                    st.success(f"Best product by profit: {best}")
                    speak_text(f"Best product by profit is {best}")
                elif "top" in ql:
                    best = df.groupby(prod_col)[qty_col].sum().idxmax()
                    st.success(f"Top selling product: {best}")
                    speak_text(f"Top selling product is {best}")
                elif "profit" in ql:
                    st.success(f"Total profit = {df['profit'].sum():,.0f}")
                    speak_text(f"Total profit is {int(df['profit'].sum()):,}")
                else:
                    st.info("Try: best product, top sales, total profit, or add 'research' for web research.")

    # Reorder suggestions
    st.subheader("📦 Reorder Suggestions")
    daily_avg = df.groupby(prod_col)[qty_col].mean()
    reorder = daily_avg * 7
    st.dataframe(pd.DataFrame({"Daily Avg": daily_avg, "Reorder Level (7d)": reorder.astype(int)}))

    # Export PDF
    st.subheader("📄 Export & Share")
    if st.button("Export report PDF"):
        report = f"AI Inventory - Report\n\nSummary:\nTotal units: {int(df[qty_col].sum())}\nTotal revenue: {int((df[price_col]*df[qty_col]).sum())}\nTotal profit: {int(df['profit'].sum())}\n\nForecast:\n"
        for k,v in forecasts.items():
            report += f"{k}: {v}\n"
        fname = make_pdf(report)
        with open(fname,"rb") as f:
            st.download_button("Download PDF", f, "ai_inventory_report.pdf", "application/pdf")
else:
    # No dataframe — show text if OCR produced raw_text
    if raw_text:
        st.subheader("📋 Extracted Text from Document / Image")
        st.text_area("Extracted text", raw_text, height=300)

        if st.button("Try parse as CSV"):
            try:
                df2 = pd.read_csv(StringIO(raw_text))
                st.success("Parsed CSV from extracted text.")
                st.dataframe(df2.head())
            except Exception as e:
                st.error("Parsing failed: " + str(e))

# Voice: upload short audio to transcribe -> ask
st.markdown("---")
st.subheader("🎤 Voice / Microphone (upload recording)")

audio_file = st.file_uploader("Upload wav/mp3 for transcription", type=["wav","mp3","m4a"])
if audio_file:
    b = audio_file.read()
    with st.spinner("Transcribing..."):
        r = transcribe_audio_bytes(b)
        text = r.get("text","")
    st.write("Transcribed:", text)
    if st.button("Ask this to AI"):
        if "research" in text.lower():
            out = ask_brain(text)
            st.write(out)
            speak_text(out)
        else:
            st.write("AI echo:", text)
            speak_text(text)
