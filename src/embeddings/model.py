# here it loads the model and convert text into numerical vector embeddings

import numpy as np
from sentence_transformers import SentenceTransformer

MODEL_NAME = "intfloat/multilingual-e5-small"

model = SentenceTransformer(MODEL_NAME)

def validate_text(text: str) -> str:
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Input must be a non-empty string.")
    return text.strip()

def count_tokens(text: str) -> int:
    return len(model.tokenizer.encode(text, add_special_tokens=False))

def embed_query(text: str) -> np.ndarray:
    validated_text = validate_text(text)
    text = f"query: {validated_text}"
    return model.encode(text, normalize_embeddings=True)

def embed_passages(texts: list[str]) -> np.ndarray:
    validated_texts = [
        validate_text(text) for text in texts
    ]
    texts = [
        f"passage: {text}" for text in validated_texts
    ]
    return model.encode(texts, normalize_embeddings=True)