class ContextBuilder:
    def __init__(self, max_tokens: int = 3000, min_score: float = 0.0):
        self.max_tokens = max_tokens
        self.min_score = min_score
        
        if self.max_tokens <= 0:
            raise ValueError("max_tokens must be greater than zero")

    def _estimate_tokens(self, text: str) -> int:
        return len(text) // 4

    def _deduplicate_chunks(self, chunks: list) -> list:
        seen_texts = set()
        unique_chunks = []
        for chunk in chunks:
            clean_text = " ".join(chunk.get("text", "").split())
            if clean_text and clean_text not in seen_texts:
                seen_texts.add(clean_text)
                unique_chunks.append(chunk)
        return unique_chunks

    def build(self, chunks: list) -> dict:
        valid = [c for c in chunks if c.get("score", 1.0) >= self.min_score]

        unique = self._deduplicate_chunks(valid)

        ranked = sorted(unique, key=lambda x: x.get("score", 0.0), reverse=True)

        formatted_blocks = []
        sources = []
        seen_urls = set()
        current_tokens = 0

        for chunk in ranked:
            text = chunk.get("text", "").strip()
            chunk_tokens = self._estimate_tokens(text) + 25  # buffer for XML tags

            if current_tokens + chunk_tokens > self.max_tokens:
                continue

            index = len(formatted_blocks) + 1

            block = f'<document index="{index}">\n{text}\n</document>'
            formatted_blocks.append(block)

            url = chunk.get("url", "")
            title = chunk.get("title", "Untitled")

            if url and url not in seen_urls:
                seen_urls.add(url)
                sources.append({
                    "title": title,
                    "url": url,
                })

            current_tokens += chunk_tokens

        return {
            "context": "\n\n".join(formatted_blocks),
            "sources": sources,
        }
