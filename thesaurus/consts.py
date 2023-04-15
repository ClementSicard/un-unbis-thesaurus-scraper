HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) \
        Chrome/44.0.2403.157 Safari/537.36",
    "Accept": "application/ld+json",
}

KEYS = {
    "ID": "@id",
    "LANG": "@language",
    "VALUE": "@value",
    "LABELS": "http://purl.org/dc/terms/title",
    "SUBTOPIC_LABELS": "http://www.w3.org/2004/02/skos/core#prefLabel",
    "TOPICS": "http://www.w3.org/2004/02/skos/core#hasTopConcept",
    "SUBTOPICS": "http://www.w3.org/2004/02/skos/core#narrower",
    "RELATED": "http://www.w3.org/2004/02/skos/core#related",
}


COLORS = {
    "meta_topic": "#FA5A3D",
    "topic": "#FA5A3D",
    "subtopic": "#5A75DB",
    "meta_topic->topic": "black",
    "topic->subtopic": "black",
    "subtopic->related": "black",
}

SIZES = {
    "meta_topic": 25.0,
    "topic": 10.0,
    "subtopic": 5.0,
}

JSON_BASE_URL = "https://metadata.un.org/thesaurus/{}.json"

NODE_TYPES = ["meta_topic", "topic", "subtopic"]
EDGE_TYPES = ["meta_topic->topic", "topic->subtopic", "subtopic->related"]
