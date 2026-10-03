import re
from tokenizer import tokenize
from stemmer import stem
from dataclasses import dataclass, field

@dataclass(frozen=True)
class QueryTerm:
    original: str
    stemmed: str
    type: str

@dataclass
class ParsedQuery:
    terms: list[QueryTerm] = field(default_factory=list)
    required: list[QueryTerm] = field(default_factory=list)
    excluded: list[QueryTerm] = field(default_factory=list)
    phrases: list[list[QueryTerm]] = field(default_factory=list)
    site_filter: str | None = None
    intitle: list[QueryTerm] = field(default_factory=list)
    inurl: list[QueryTerm] = field(default_factory=list)
    related: list[QueryTerm] = field(default_factory=list)

def parse_query(raw_query: str) -> ParsedQuery:
    
    query = ParsedQuery()

    phrase_pattern = re.compile(r'"([^"]+)"')
    for match in phrase_pattern.findall(raw_query):
        original_tokens = tokenize(match)
        stemmed_tokens = stem(original_tokens)

        phrase_terms = []

        for original, stemmed in zip(original_tokens, stemmed_tokens):
            phrase_terms.append(
                QueryTerm(
                    original=original,
                    stemmed=stemmed,
                    type="phrase"
                )
            )

        if phrase_terms:
            query.phrases.append(phrase_terms)

    raw_query = phrase_pattern.sub('', raw_query)

    site_pattern = re.compile(r'\bsite:(\S+)', re.IGNORECASE)
    site_match = site_pattern.search(raw_query)
    if site_match:
        query.site_filter = site_match.group(1).lower()
        raw_query = site_pattern.sub('', raw_query)

    intitle_pattern = re.compile(r'\bintitle:(\S+)', re.IGNORECASE)
    for match in intitle_pattern.findall(raw_query):
        original_tokens = tokenize(match)
        stemmed_tokens = stem(original_tokens)

        for original, stemmed in zip(original_tokens, stemmed_tokens):
            query.intitle.append(
                QueryTerm(
                    original=original,
                    stemmed=stemmed,
                    type="intitle"
                )
            )
    raw_query = intitle_pattern.sub('', raw_query)
    
    inurl_pattern = re.compile(r'\binurl:(\S+)', re.IGNORECASE)
    for match in inurl_pattern.findall(raw_query):
        original_tokens = tokenize(match)
        stemmed_tokens = stem(original_tokens)

        for original, stemmed in zip(original_tokens, stemmed_tokens):
            query.inurl.append(
                QueryTerm(
                    original=original,
                    stemmed=stemmed,
                    type="inurl"
                )
            )
    raw_query = inurl_pattern.sub('', raw_query)
    
    related_pattern = re.compile(r'\brelated:(\S+)', re.IGNORECASE)
    for match in related_pattern.findall(raw_query):
        original_tokens = tokenize(match)
        stemmed_tokens = stem(original_tokens)

        for original, stemmed in zip(original_tokens, stemmed_tokens):
            query.related.append(
                QueryTerm(
                    original=original,
                    stemmed=stemmed,
                    type="related"
                )
            )
    raw_query = related_pattern.sub('', raw_query)

    for token in raw_query.split():
        if token.startswith('-') and len(token) > 1:
            original_tokens = tokenize(token[1:])
            stemmed_tokens = stem(original_tokens)

            for original, stemmed in zip(original_tokens, stemmed_tokens):
                query.excluded.append(
                    QueryTerm(
                        original=original,
                        stemmed=stemmed,
                        type="excluded"
                    )
                )
        elif token.startswith('+') and len(token) > 1:
            original_tokens = tokenize(token[1:])
            stemmed_tokens = stem(original_tokens)

            for original, stemmed in zip(original_tokens, stemmed_tokens):
                query.required.append(
                    QueryTerm(
                        original=original,
                        stemmed=stemmed,
                        type="required"
                    )
                )
        else:
            original_tokens = tokenize(token)
            stemmed_tokens = stem(original_tokens)

            for original, stemmed in zip(original_tokens, stemmed_tokens):
                query.terms.append(
                    QueryTerm(
                        original=original,
                        stemmed=stemmed,
                        type="normal"
                    )
                )

    return query