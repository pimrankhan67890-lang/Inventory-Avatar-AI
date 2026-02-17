# memory.py
try:
    from sentence_transformers import SentenceTransformer
    import faiss
    import numpy as np
    EMB_MODEL = SentenceTransformer('paraphrase-MiniLM-L6-v2')
    USE_FAISS = True
except Exception:
    EMB_MODEL = None
    USE_FAISS = False

class Memory:
    def __init__(self):
        self.texts = []
        if USE_FAISS:
            self.dim = EMB_MODEL.get_sentence_embedding_dimension()
            self.index = faiss.IndexFlatL2(self.dim)
            self.embs = []
    def add(self, text):
        self.texts.append(text)
        if USE_FAISS:
            v = EMB_MODEL.encode([text])
            self.index.add(np.array(v).astype('float32'))
            self.embs.append(text)
    def query(self, q, topk=3):
        if not USE_FAISS:
            # naive similarity: substring matching
            found = [t for t in self.texts if q.lower() in t.lower()]
            return found[:topk]
        v = EMB_MODEL.encode([q]).astype('float32')
        D,I = self.index.search(v, topk)
        return [self.embs[i] for i in I[0] if i < len(self.embs)]
