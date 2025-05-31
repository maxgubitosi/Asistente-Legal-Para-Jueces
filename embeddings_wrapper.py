import torch
import numpy as np
from sentence_transformers import SentenceTransformer
from langchain.docstore.document import Document

class LangchainSentenceTransformer:
    def __init__(self, model_name="mixedbread-ai/mxbai-embed-large-v1"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = SentenceTransformer(model_name).to(self.device)
        self.query_prefix = "Represent this sentence for searching relevant passages: "
        self._cleaned_documents = []

    def embed_documents(self, documents):

        print(f"[INFO] Filtering {len(documents)} chunks...")
        filtered = []
        for doc in documents:
            text = getattr(doc, "page_content", str(doc)).strip()
            if isinstance(text, str): filtered.append(Document(page_content=text))
        self._cleaned_documents = filtered
        texts = [doc.page_content for doc in filtered]
        print(f"[INFO] Embedding {len(texts)} clean chunks...")
        
        embeddings = self.model.encode(
            texts,
            show_progress_bar=True,
            convert_to_numpy=True,
            device=self.device
        )
        return texts, embeddings

    def embed_query(self, query):
        return self.model.encode(
            [self.query_prefix + str(query)],
            convert_to_numpy=True,
            device=self.device
        )[0]

    def __call__(self, text: str) -> list[float]:
        return self.embed_query(text)