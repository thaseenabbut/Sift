# splits webpage text into chunks and tunrs them into embeddings and returns both

import numpy as np

from src.embeddings.chunker import Chunker
from src.embeddings.model import embed_passages


class Generator:
    def __init__(self):
        self.chunker = Chunker()
        self.embedding = embed_passages
        
    def generate(self, text: str) -> tuple[list[str], np.ndarray]:
            chunks = self.chunker.chunk(text)
            if not chunks:
                raise ValueError("No chunks generated from the given text")
            
            embedding = self.embedding(chunks)
            
            return chunks, embedding
        