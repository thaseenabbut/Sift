from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.embeddings.model import count_tokens, validate_text

class Chunker:
    def __init__(self):
        self.splitter = RecursiveCharacterTextSplitter(
            separators=["\n\n", "\n", " ", ""],
            chunk_size=256,
            chunk_overlap=40,
            length_function=count_tokens,
        )
        
    def chunk(self, text: str) -> list[str]:
        validated_text = validate_text(text)
        return self.splitter.split_text(validated_text)
    
chunker = Chunker()