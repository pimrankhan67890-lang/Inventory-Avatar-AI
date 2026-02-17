import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

class Memory:
    def __init__(self):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.index = faiss.IndexFlatL2(384)
        self.texts = []

    def add(self, text):
        if not text.strip():
            return
        vec = self.model.encode([text]).astype("float32")
        self.index.add(vec)
        self.texts.append(text)

    def search(self, query, k=5):
        if not self.texts:
            return []
        qv = self.model.encode([query]).astype("float32")
        D, I = self.index.search(qv, k)
        return [self.texts[i] for i in I[0] if i < len(self.texts)]

memory = Memory()