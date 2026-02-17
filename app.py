# app.py
# Minimal Streamlit front-end. Run: streamlit run app.py
import streamlit as st
import subprocess
from ai_inventory_optimizer import summarize_and_answer

st.set_page_config(page_title="AI Inventory Optimizer", layout="centered")

st.title("AI Inventory Optimizer — Beta")
q = st.text_input("Research Query", "")

if st.button("Run Deep Research"):
    if not q.strip():
        st.warning("Please enter a query.")
    else:
        with st.spinner("Running..."):
            # call the same pipeline
            result = summarize_and_answer(q)
        st.subheader("Result")
        st.write(result)