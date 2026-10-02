import re
from tokenizer import tokenize
from stemmer import stem
from dataclasses import dataclass, field

@dataclass
class ParsedQuery:
    terms: list[str] = field(default_factory=list)
    required: list[str] = field(default_factory=list)
    excluded: list[str] = field(default_factory=list)
    phrases: list[list[str]] = field(default_factory=list)
    site_filter: str | None = None
    intitle: list[str] = field(default_factory=list)
    inurl: list[str] = field(default_factory=list)
    related: list[str] = field(default_factory=list)

def parse_query(raw_query: str) -> ParsedQuery:
    
    query = ParsedQuery()

    phrase_pattern = re.compile(r'"([^"]+)"')
    for match in phrase_pattern.findall(raw_query):
        stemmed_phrase = stem(tokenize(match))
        if stemmed_phrase:
            query.phrases.append(stemmed_phrase)
    raw_query = phrase_pattern.sub('', raw_query)

    site_pattern = re.compile(r'\bsite:(\S+)', re.IGNORECASE)
    site_match = site_pattern.search(raw_query)
    if site_match:
        query.site_filter = site_match.group(1).lower()
        raw_query = site_pattern.sub('', raw_query)

    intitle_pattern = re.compile(r'\bintitle:(\S+)', re.IGNORECASE)
    for match in intitle_pattern.findall(raw_query):
        query.intitle.extend(stem(tokenize(match)))
    raw_query = intitle_pattern.sub('', raw_query)
    
    inurl_pattern = re.compile(r'\binurl:(\S+)', re.IGNORECASE)
    for match in inurl_pattern.findall(raw_query):
        query.inurl.extend(stem(tokenize(match)))
    raw_query = inurl_pattern.sub('', raw_query)
    
    related_pattern = re.compile(r'\brelated:(\S+)', re.IGNORECASE)
    for match in related_pattern.findall(raw_query):
        query.related.extend(stem(tokenize(match)))
    raw_query = related_pattern.sub('', raw_query)

    for token in raw_query.split():
        if token.startswith('-') and len(token) > 1:
            query.excluded.extend(stem(tokenize(token[1:])))
        elif token.startswith('+') and len(token) > 1:
            query.required.extend(stem(tokenize(token[1:])))
        else:
            query.terms.extend(stem(tokenize(token)))

    return query

