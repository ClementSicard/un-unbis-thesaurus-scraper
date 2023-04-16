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
    "CLUSTER": "http://www.w3.org/2004/02/skos/core#inScheme",
}


COLORS = {
    "meta_topic": "#FA5A3D",
    "topic": "#FA5A3D",
    "subtopic": "#5A75DB",
    "meta_topic->topic": "black",
    "topic->subtopic": "black",
    "subtopic->related": "black",
}

UNKNOWN_CLUSTER = None

SIZES = {
    "meta_topic": 25.0,
    "topic": 10.0,
    "subtopic": 5.0,
}

BASE_URL = "https://metadata.un.org/thesaurus/{}"
JSON_BASE_URL = BASE_URL + ".json"

NODE_TYPES = ["meta_topic", "topic", "subtopic"]
EDGE_TYPES = ["meta_topic->topic", "topic->subtopic", "subtopic->related"]

CLUSTERS = [
    {
        "key": "01",
        "color": "#f44336",
        "clusterLabel": "POLITICAL AND LEGAL QUESTIONS",
    },
    {
        "key": "02",
        "color": "#9c27b0",
        "clusterLabel": "ECONOMIC DEVELOPMENT AND DEVELOPMENT FINANCE",
    },
    {
        "key": "03",
        "color": "#3f51b5",
        "clusterLabel": "NATURAL RESOURCES AND THE ENVIRONMENT",
    },
    {
        "key": "04",
        "color": "#2196f3",
        "clusterLabel": "AGRICULTURE, FORESTRY AND FISHING",
    },
    {
        "key": "05",
        "color": "#009688",
        "clusterLabel": "INDUSTRY",
    },
    {
        "key": "06",
        "color": "#4caf50",
        "clusterLabel": "TRANSPORT AND COMMUNICATIONS",
    },
    {
        "key": "07",
        "color": "#8bc34a",
        "clusterLabel": "INTERNATIONAL TRADE",
    },
    {
        "key": "08",
        "color": "#cddc39",
        "clusterLabel": "POPULATION",
    },
    {
        "key": "09",
        "color": "#ffeb3b",
        "clusterLabel": "HUMAN SETTLEMENTS",
    },
    {
        "key": "10",
        "color": "#ffc107",
        "clusterLabel": "HEALTH",
    },
    {
        "key": "11",
        "color": "#ff9800",
        "clusterLabel": "EDUCATION",
    },
    {
        "key": "12",
        "color": "#ff5722",
        "clusterLabel": "EMPLOYMENT",
    },
    {
        "key": "13",
        "color": "#795548",
        "clusterLabel": "HUMANITARIAN AID AND RELIEF",
    },
    {
        "key": "14",
        "color": "#9e9e9e",
        "clusterLabel": "SOCIAL CONDITIONS AND EQUITY",
    },
    {
        "key": "15",
        "color": "#607d8b",
        "clusterLabel": "CULTURE",
    },
    {
        "key": "16",
        "color": "#e91e63",
        "clusterLabel": "SCIENCE AND TECHNOLOGY",
    },
    {
        "key": "17",
        "color": "#673ab7",
        "clusterLabel": "GEOGRAPHICAL DESCRIPTORS",
    },
    {
        "key": "18",
        "color": "#795548",
        "clusterLabel": "ORGANIZATIONAL QUESTIONS",
    },
]


TAGS = [
    {
        "key": "Concept",
        "image": "concept.svg",
    }
]
