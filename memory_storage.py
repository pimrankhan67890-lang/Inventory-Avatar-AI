# memory_storage.py
import json, os
class MemoryStore:
    def __init__(self, filename="data/memory.json"):
        self.filename = filename
        os.makedirs(os.path.dirname(self.filename), exist_ok=True)
        if not os.path.exists(self.filename):
            with open(self.filename,"w",encoding="utf-8") as f:
                json.dump({}, f)
        self._load()
    def _load(self):
        with open(self.filename,"r",encoding="utf-8") as f:
            try:
                self.data = json.load(f)
            except:
                self.data = {}
    def save(self):
        with open(self.filename,"w",encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
    def get(self,k,d=None): return self.data.get(k,d)
    def set(self,k,v): self.data[k]=v; self.save()
    def delete(self,k): 
        if k in self.data: del self.data[k]; self.save()