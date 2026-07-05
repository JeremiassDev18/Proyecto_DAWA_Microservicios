import re


def clean_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-záéíóúüñA-ZÁÉÍÓÚÜÑ0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def clean_corpus(texts: list[str]) -> list[str]:
    return [clean_text(t) for t in texts]
