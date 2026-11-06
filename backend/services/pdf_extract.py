import pymupdf


def extract_text(pdf_bytes: bytes) -> str:
    """Extrait tout le texte d'un PDF. Retourne '' si le PDF n'a pas de texte."""
    if not pdf_bytes:
        return ""
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    try:
        parts = []
        for page in doc:
            text = page.get_text() or ""
            if text:
                parts.append(text)
        result = "\n".join(parts)
        return result  # jamais None, toujours str
    finally:
        doc.close()