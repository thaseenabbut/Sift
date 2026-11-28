
def get_citations(context: dict) -> list[dict]:
    if not context:
        return []

    return context.get("sources", [])