import torch
import numpy as np
from sentence_transformers import SentenceTransformer
from langchain.docstore.document import Document
from typing import List, Tuple
import openai
from openai import AzureOpenAI
import os



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



class AzureOpenAIEmbedder:
    def __init__(
        self,
        deployment_name: str,        # nombre exacto del deployment en Azure
        endpoint: str,               # p.ej. "https://maxi-openai-1.openai.azure.com"
        api_key: str,
        api_version: str = "2023-05-15",
    ):
        self.deployment_name = deployment_name

        # Cliente v1
        self.client = AzureOpenAI(
            api_key        = api_key,
            azure_endpoint = endpoint,      # host raíz, sin /openai/deployments...
            api_version    = api_version,
        )

    # ---------- embeddings sobre documentos ----------
    def embed_documents(self, documents: List[Document]) -> Tuple[List[str], np.ndarray]:
        texts = [doc.page_content.strip() for doc in documents
                 if isinstance(doc.page_content, str)]

        embeddings = []
        batch_size = 100          # ajustá si tu cuota lo permite
        for i in range(0, len(texts), batch_size):
            lote = texts[i:i+batch_size]

            response = self.client.embeddings.create(
                model = self.deployment_name,   # ← v1 usa "model"
                input = lote
            )
            embeddings.extend([d.embedding for d in response.data])

        return texts, np.array(embeddings, dtype=np.float32)

    # ---------- embedding de una sola query ----------
    def embed_query(self, query: str) -> List[float]:
        prompt = "Represent this sentence for searching relevant passages: " + query
        response = self.client.embeddings.create(
            model = self.deployment_name,
            input = [prompt],
        )
        return response.data[0].embedding

    # Para compatibilidad con LangChain
    def __call__(self, text: str) -> List[float]:
        return self.embed_query(text)