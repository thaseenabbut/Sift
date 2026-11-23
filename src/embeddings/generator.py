from src.embeddings.chunker import Chunker
from src.embeddings.model import embed_passages
import numpy as np

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
        
generator = Generator()