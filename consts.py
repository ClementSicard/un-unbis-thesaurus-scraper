HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) \
        Chrome/44.0.2403.157 Safari/537.36",
    "Accept": "application/ld+json",
}

_KEYS = {
    "BROADER": "core#broader",
    "LABELS": "core#prefLabel",
    "RELATED": "core#related",
}

KEYS = {k: f"http://www.w3.org/2004/02/skos/{v}" for k, v in _KEYS.items()}
