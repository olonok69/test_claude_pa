from presidio_analyzer import PatternRecognizer

zip_code = {
    "text": "John Smith drivers license is AC432223. Zip code: 10023",
    "language": "en",
    "ad_hoc_recognizers": [
        {
            "name": "Zip code Recognizer",
            "supported_language": "en",
            "patterns": [
                {
                    "name": "zip code (weak)",
                    "regex": "(\\b\\d{5}(?:\\-\\d{4})?\\b)",
                    "score": 0.01,
                }
            ],
            "context": ["zip", "code"],
            "supported_entity": "ZIP",
        }
    ],
}

mister = {
    "text": "Mr. John Smith's drivers license is AC432223",
    "language": "en",
    "ad_hoc_recognizers": [
        {
            "name": "Mr. Recognizer",
            "supported_language": "en",
            "deny_list": ["Mr", "Mr.", "Mister"],
            "supported_entity": "MR_TITLE",
        },
        {
            "name": "Ms. Recognizer",
            "supported_language": "en",
            "deny_list": ["Ms", "Ms.", "Miss", "Mrs", "Mrs."],
            "supported_entity": "MS_TITLE",
        },
    ],
}

zip_code = {
    "text": "John Smith drivers license is AC432223. Zip code: 10023",
    "language": "en",
    "ad_hoc_recognizers": [
        {
            "name": "Zip code Recognizer",
            "supported_language": "en",
            "patterns": [
                {
                    "name": "zip code (weak)",
                    "regex": "(\\b\\d{5}(?:\\-\\d{4})?\\b)",
                    "score": 0.01,
                }
            ],
            "context": ["zip", "code"],
            "supported_entity": "ZIP",
        }
    ],
}

mister = {
    "deny_list": [
        "Sir",
        "Ma'am",
        "Madam",
        "Mr.",
        "Mrs.",
        "Ms.",
        "Miss",
        "Dr.",
        "Professor",
        "sir",
        "ma'am",
        "madam",
        "mr.",
        "mrs.",
        "ms.",
        "miss",
        "dr.",
        "professor",
    ],
    "language": "en",
    "supported_entity": "TITLE",
}

mister_es = {
    "deny_list": ["Sr.", "señor", "Sra.", "señora", "señorita"],
    "language": "es",
    "supported_entity": "TITLE",
}
mister_de = {
    "deny_list": ["Herr", "Herren", "Frau", "Frauen"],
    "language": "de",
    "supported_entity": "TITLE",
}

mister_it = {
    "deny_list": [
        "signori",
        "signore",
        "signor",
        "signora",
        "donne",
        "signorotto",
        "mancare",
    ],
    "language": "it",
    "supported_entity": "TITLE",
}

configuration = {
    "nlp_engine_name": "spacy",
    "models": [
        {"lang_code": "es", "model_name": "es_core_news_lg"},
    ],
}

titles_recognizer = PatternRecognizer(
    supported_entity=mister_es.get("supported_entity"),
    supported_language=mister_es.get("supported_language"),
    deny_list=mister_es.get("deny_list"),
)

titles_recognizer_en = PatternRecognizer(
    supported_entity=mister.get("supported_entity"),
    supported_language=mister.get("supported_language"),
    deny_list=mister.get("deny_list"),
)

titles_recognizer_de = PatternRecognizer(
    supported_entity=mister_de.get("supported_entity"),
    supported_language=mister_de.get("supported_language"),
    deny_list=mister_de.get("deny_list"),
)
