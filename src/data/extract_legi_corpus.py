"""Extract a clean corpus from LEGI XML files.

Milestone 1 only prepares homogeneous documents. It does not create chunks,
embeddings, a vector database, retrieval, or LLM calls.
"""

from datetime import date
from html import unescape
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET


RAW_LEGI_DIR = Path("data/raw/legi")
OUTPUT_FILE = Path("data/processed/corpus_legi_clean.json")
SOURCE_LABEL = "LEGI data.gouv.fr"
LABOR_CODE_TITLE = "code du travail"
LABOR_CODE_LEGITEXT_ID = "legitext000006072050"


def local_name(tag: str) -> str:
    """Return an XML tag without its namespace."""
    if "}" in tag:
        return tag.rsplit("}", 1)[1]
    return tag


def clean_text(value: str) -> str:
    """Normalize legal text extracted from XML or escaped HTML."""
    if not value:
        return ""

    value = unescape(value)
    value = re.sub(r"<[^>]+>", " ", value)
    value = value.replace("\xa0", " ")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def text_of_first(root: ET.Element, tag_name: str) -> str:
    """Return the cleaned text of the first element matching tag_name."""
    for element in root.iter():
        if local_name(element.tag) == tag_name:
            text = clean_text(" ".join(element.itertext()))
            if text:
                return text
    return ""


def texts_by_tag(root: ET.Element, tag_name: str) -> list[str]:
    """Return cleaned texts from all elements matching tag_name."""
    values = []
    for element in root.iter():
        if local_name(element.tag) == tag_name:
            text = clean_text(" ".join(element.itertext()))
            if text:
                values.append(text)
    return values


def normalize_article_number(value: str) -> str:
    """Normalize article references such as 'Article L3121-1'."""
    value = clean_text(value).upper()
    value = value.replace("ARTICLE", "").strip()
    value = re.sub(r"\s+", "", value)
    return value


def stable_id(article_number: str) -> str:
    """Build a stable id from the article number."""
    safe_article = re.sub(r"[^A-Z0-9-]+", "_", article_number.upper()).strip("_")
    return f"legi_{safe_article}"


def is_labor_code_article(root: ET.Element, xml_path: Path) -> bool:
    """Check whether an XML article belongs to the French Labor Code."""
    if local_name(root.tag) != "ARTICLE":
        return False

    path_text = xml_path.as_posix().lower()
    if "code_du_travail" in path_text or LABOR_CODE_LEGITEXT_ID in path_text:
        return True

    context_text = clean_text(" ".join(root.itertext())).lower()
    return LABOR_CODE_TITLE in context_text or LABOR_CODE_LEGITEXT_ID in context_text


def extract_title(root: ET.Element, article_number: str) -> str:
    """Extract a useful title when LEGI provides one."""
    for tag_name in ("TITRE", "TITRE_TA", "TITRE_TM", "TITRE_TXT"):
        title = text_of_first(root, tag_name)
        if title and LABOR_CODE_TITLE not in title.lower():
            return title

    return f"Article {article_number}"


def extract_article_text(root: ET.Element) -> str:
    """Extract the legal article body from common LEGI text tags."""
    contents = texts_by_tag(root, "CONTENU")
    if contents:
        return clean_text(" ".join(contents))

    bloc_texts = texts_by_tag(root, "BLOC_TEXTUEL")
    if bloc_texts:
        return clean_text(" ".join(bloc_texts))

    return ""


def build_content(article_number: str, theme: str, title: str, text: str) -> str:
    """Build the text that will later be embedded by the RAG pipeline."""
    return (
        f"Article {article_number}\n"
        f"Theme : {theme}\n"
        f"Titre : {title}\n"
        f"Texte : {text}"
    )


def extract_document(xml_path: Path, extraction_date: str) -> dict | None:
    """Extract one homogeneous document from one LEGI XML file."""
    try:
        root = ET.parse(xml_path).getroot()
    except ET.ParseError as error:
        print(f"[WARN] XML illisible: {xml_path} ({error})")
        return None

    if not is_labor_code_article(root, xml_path):
        return None

    article_number = normalize_article_number(text_of_first(root, "NUM"))
    if not article_number:
        return None

    text = extract_article_text(root)
    if not text:
        return None

    title = extract_title(root, article_number)
    theme = "Code du travail"

    return {
        "id": stable_id(article_number),
        "article": article_number,
        "theme": theme,
        "title": title,
        "text": text,
        "content": build_content(article_number, theme, title, text),
        "source": SOURCE_LABEL,
        "source_file": xml_path.as_posix(),
        "date_extraction": extraction_date,
    }


def iter_xml_files(root_dir: Path):
    """Yield XML files from the LEGI raw directory."""
    yield from sorted(root_dir.rglob("*.xml"))


def extract_documents() -> list[dict]:
    """Extract all usable Labor Code article documents."""
    if not RAW_LEGI_DIR.exists():
        raise FileNotFoundError(
            f"Dossier introuvable: {RAW_LEGI_DIR}. "
            "Placez les fichiers XML LEGI dans data/raw/legi/."
        )

    xml_files = list(iter_xml_files(RAW_LEGI_DIR))
    if not xml_files:
        raise FileNotFoundError(
            f"Aucun fichier XML trouve dans {RAW_LEGI_DIR}. "
            "Placez les fichiers XML LEGI dans data/raw/legi/."
        )

    extraction_date = date.today().isoformat()
    documents = []

    for xml_path in xml_files:
        document = extract_document(xml_path, extraction_date)
        if document is not None:
            documents.append(document)

    return documents


def write_documents(documents: list[dict], output_file: Path) -> None:
    """Write extracted documents to a UTF-8 JSON file."""
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8") as file:
        json.dump(documents, file, ensure_ascii=False, indent=2)
        file.write("\n")


def main() -> None:
    documents = extract_documents()
    write_documents(documents, OUTPUT_FILE)
    print(f"Documents extraits: {len(documents)}")
    print(f"Fichier genere: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
