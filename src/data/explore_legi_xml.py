"""Explore LEGI XML files before corpus extraction.

This script is intentionally read-only. It scans data/raw/legi recursively,
prints the XML tags found in the files, and shows short text examples to help
identify where article numbers, titles and legal text are stored.
"""

from collections import Counter, defaultdict
from pathlib import Path
import xml.etree.ElementTree as ET


RAW_LEGI_DIR = Path("data/raw/legi")
MAX_FILES_TO_PARSE = 50
MAX_EXAMPLES_PER_TAG = 5
TEXT_PREVIEW_LENGTH = 180


def local_name(tag: str) -> str:
    """Return an XML tag without its namespace."""
    if "}" in tag:
        return tag.rsplit("}", 1)[1]
    return tag


def clean_preview(text: str) -> str:
    """Normalize whitespace for readable console previews."""
    return " ".join(text.split())[:TEXT_PREVIEW_LENGTH]


def iter_xml_files(root_dir: Path):
    """Yield XML files from the LEGI raw directory."""
    yield from sorted(root_dir.rglob("*.xml"))


def explore_xml_file(xml_path: Path, tag_counter: Counter, examples: dict) -> bool:
    """Parse one XML file and update tag counts and text examples."""
    try:
        tree = ET.parse(xml_path)
    except ET.ParseError as error:
        print(f"[WARN] XML illisible: {xml_path} ({error})")
        return False

    root = tree.getroot()

    for element in root.iter():
        tag = local_name(element.tag)
        tag_counter[tag] += 1

        text = clean_preview(element.text or "")
        if text and len(examples[tag]) < MAX_EXAMPLES_PER_TAG:
            examples[tag].append((xml_path, text))

    return True


def print_tag_summary(tag_counter: Counter) -> None:
    """Print the most common XML tags."""
    print("\nBalises XML rencontrees")
    print("-" * 80)
    for tag, count in tag_counter.most_common():
        print(f"{tag}: {count}")


def print_text_examples(examples: dict) -> None:
    """Print short text examples grouped by XML tag."""
    print("\nExemples de texte par balise")
    print("-" * 80)
    for tag in sorted(examples):
        print(f"\n[{tag}]")
        for xml_path, text in examples[tag]:
            print(f"- {xml_path}: {text}")


def print_candidate_tags(tag_counter: Counter, examples: dict) -> None:
    """Highlight tags that often carry article metadata in LEGI files."""
    candidates = [
        "ARTICLE",
        "ID",
        "NUM",
        "TITRE",
        "TITRE_TXT",
        "CONTENU",
        "BLOC_TEXTUEL",
        "SECTION_TA",
        "TM",
    ]

    print("\nBalises candidates a verifier pour l'extraction")
    print("-" * 80)
    for tag in candidates:
        if tag in tag_counter:
            print(f"{tag}: {tag_counter[tag]} occurrence(s)")
            for xml_path, text in examples.get(tag, [])[:2]:
                print(f"  exemple dans {xml_path}: {text}")


def main() -> None:
    if not RAW_LEGI_DIR.exists():
        print(f"Dossier introuvable: {RAW_LEGI_DIR}")
        print("Placez les fichiers XML LEGI dans data/raw/legi/ puis relancez le script.")
        return

    xml_files = list(iter_xml_files(RAW_LEGI_DIR))
    if not xml_files:
        print(f"Aucun fichier XML trouve dans {RAW_LEGI_DIR}.")
        print("Placez les fichiers XML LEGI dans data/raw/legi/ puis relancez le script.")
        return

    files_to_parse = xml_files[:MAX_FILES_TO_PARSE]
    tag_counter = Counter()
    examples = defaultdict(list)
    parsed_count = 0

    print(f"Fichiers XML trouves: {len(xml_files)}")
    print(f"Fichiers explores: {len(files_to_parse)}")

    for xml_path in files_to_parse:
        if explore_xml_file(xml_path, tag_counter, examples):
            parsed_count += 1

    print(f"Fichiers parses avec succes: {parsed_count}")
    print_tag_summary(tag_counter)
    print_candidate_tags(tag_counter, examples)
    print_text_examples(examples)


if __name__ == "__main__":
    main()
