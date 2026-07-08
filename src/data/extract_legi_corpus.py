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
ARTICLE_REF_PATTERN = re.compile(r"^([A-Z]+)([0-9]+(?:-[0-9]+)+)$")


# The rupture conventionnelle range is checked before the broader licenciement
# range because L1237-11 to L1237-19 belongs to both numeric intervals.
THEME_RANGES = [
    {
        "theme": "Duree du travail et heures supplementaires",
        "start": "L3121-1",
        "end": "L3121-36",
    },
    {
        "theme": "Conges payes",
        "start": "L3141-1",
        "end": "L3141-32",
    },
    {
        "theme": "Contrat de travail CDI/CDD",
        "start": "L1221-1",
        "end": "L1248-11",
    },
    {
        "theme": "Rupture conventionnelle",
        "start": "L1237-11",
        "end": "L1237-19",
    },
    {
        "theme": "Licenciement",
        "start": "L1231-1",
        "end": "L1237-20",
    },
    {
        "theme": "Salaire minimum SMIC",
        "start": "L3231-1",
        "end": "L3232-9",
    },
    {
        "theme": "Representation du personnel",
        "start": "L2311-1",
        "end": "L2316-26",
    },
    {
        "theme": "Harcelement et discrimination",
        "start": "L1152-1",
        "end": "L1155-2",
    },
]


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


def parse_article_reference(article_number: str) -> tuple[str, tuple[int, ...]] | None:
    """Parse an article number into a prefix and comparable numeric tuple."""
    match = ARTICLE_REF_PATTERN.match(article_number)
    if not match:
        return None

    prefix = match.group(1)
    numbers = tuple(int(part) for part in match.group(2).split("-"))
    return prefix, numbers


def pad_numbers(numbers: tuple[int, ...], length: int) -> tuple[int, ...]:
    """Pad article numeric parts so lexicographic comparisons are stable."""
    return numbers + (0,) * (length - len(numbers))


def article_in_range(article_number: str, start: str, end: str) -> bool:
    """Return True when an article number is inside an inclusive range."""
    parsed_article = parse_article_reference(article_number)
    parsed_start = parse_article_reference(start)
    parsed_end = parse_article_reference(end)

    if not parsed_article or not parsed_start or not parsed_end:
        return False

    article_prefix, article_numbers = parsed_article
    start_prefix, start_numbers = parsed_start
    end_prefix, end_numbers = parsed_end

    if article_prefix != start_prefix or article_prefix != end_prefix:
        return False

    max_length = max(len(article_numbers), len(start_numbers), len(end_numbers))
    article_numbers = pad_numbers(article_numbers, max_length)
    start_numbers = pad_numbers(start_numbers, max_length)
    end_numbers = pad_numbers(end_numbers, max_length)

    return start_numbers <= article_numbers <= end_numbers


def theme_for_article(article_number: str) -> str | None:
    """Map an article number to one of the required project themes."""
    for theme_range in THEME_RANGES:
        if article_in_range(
            article_number,
            theme_range["start"],
            theme_range["end"],
        ):
            return theme_range["theme"]

    return None


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

    if local_name(root.tag) != "ARTICLE":
        return None

    article_number = normalize_article_number(text_of_first(root, "NUM"))
    if not article_number:
        return None

    theme = theme_for_article(article_number)
    if theme is None:
        return None

    text = extract_article_text(root)
    if not text:
        return None

    title = extract_title(root, article_number)

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
