"""Extract only useful Code du travail XML files from a LEGI tar.gz archive.

The full LEGI archive can contain millions of files. This script reads the
archive sequentially with tarfile and extracts only XML article files whose
article number belongs to the project themes.
"""

from collections import Counter
from datetime import date
from pathlib import Path
import re
import sys
import tarfile
import xml.etree.ElementTree as ET


OUTPUT_DIR = Path("data/raw/legi")
LABOR_CODE_LEGITEXT_ID = "legitext000006072050"
ARTICLE_REF_PATTERN = re.compile(r"^([A-Z]+)([0-9]+(?:-[0-9]+)+)$")
ARTICLE_NUMBER_PATTERN = re.compile(
    rb"<NUM>\s*(?:Article\s*)?([A-Z][0-9]+(?:-[0-9]+)+)\s*</NUM>",
    re.IGNORECASE,
)
MAX_XML_BYTES = 2_000_000


# Specific ranges are checked before the broader contract range.
# L1237-11 to L1237-19 also belongs to the licenciement interval.
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
        "theme": "Contrat de travail CDI/CDD",
        "start": "L1221-1",
        "end": "L1248-11",
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


def normalize_article_number(value: str) -> str:
    """Normalize article references such as 'Article L3121-1'."""
    value = value.upper()
    value = value.replace("ARTICLE", "").strip()
    value = re.sub(r"\s+", "", value)
    return value


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


def article_number_from_bytes(xml_bytes: bytes) -> str:
    """Fast-path extraction of an article number from XML bytes."""
    match = ARTICLE_NUMBER_PATTERN.search(xml_bytes)
    if not match:
        return ""

    return normalize_article_number(match.group(1).decode("utf-8", errors="ignore"))


def article_number_from_xml(xml_bytes: bytes) -> str:
    """Fallback XML parsing when the fast regex path is not enough."""
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return ""

    if local_name(root.tag) != "ARTICLE":
        return ""

    for element in root.iter():
        if local_name(element.tag) == "NUM":
            text = "".join(element.itertext())
            return normalize_article_number(text)

    return ""


def text_of_first(root: ET.Element, tag_name: str) -> str:
    """Return stripped text from the first XML element matching tag_name."""
    for element in root.iter():
        if local_name(element.tag) == tag_name:
            text = "".join(element.itertext()).strip()
            if text:
                return text
    return ""


def article_metadata_from_xml(xml_bytes: bytes) -> dict:
    """Read article metadata needed to keep the current article version."""
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return {}

    if local_name(root.tag) != "ARTICLE":
        return {}

    article_number = normalize_article_number(text_of_first(root, "NUM"))
    if not article_number:
        return {}

    return {
        "legi_id": text_of_first(root, "ID"),
        "article": article_number,
        "etat": text_of_first(root, "ETAT").upper(),
        "date_debut": text_of_first(root, "DATE_DEBUT"),
        "date_fin": text_of_first(root, "DATE_FIN"),
    }


def parse_iso_date(value: str) -> date | None:
    """Parse a LEGI ISO date, returning None when it is missing or invalid."""
    if not value:
        return None

    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def is_current_version(metadata: dict, reference_date: date) -> bool:
    """Return True only for versions legally in force at reference_date."""
    if metadata.get("etat") != "VIGUEUR":
        return False

    date_debut = parse_iso_date(metadata.get("date_debut", ""))
    date_fin = parse_iso_date(metadata.get("date_fin", ""))

    if date_debut is None or date_debut > reference_date:
        return False

    if date_fin is not None and date_fin <= reference_date:
        return False

    return True


def version_score(metadata: dict) -> tuple:
    """Rank article versions, prioritizing current legal text."""
    date_debut = parse_iso_date(metadata.get("date_debut", "")) or date.min
    date_fin = parse_iso_date(metadata.get("date_fin", "")) or date.max

    return (
        date_debut,
        1 if metadata.get("date_fin") == "2999-01-01" else 0,
        date_fin,
        metadata.get("legi_id", ""),
    )


def output_path_for_member(member_name: str, article_number: str) -> Path:
    """Build a stable output path for one extracted article XML."""
    safe_article = re.sub(r"[^A-Z0-9-]+", "_", article_number.upper()).strip("_")
    source_stem = Path(member_name).stem
    file_name = f"{safe_article}_{source_stem}.xml"
    return OUTPUT_DIR / file_name


def should_skip_member(member: tarfile.TarInfo) -> bool:
    """Return True for archive members that cannot be useful XML articles."""
    if not member.isfile():
        return True

    member_name = member.name.lower()

    if not member_name.endswith(".xml"):
        return True

    if LABOR_CODE_LEGITEXT_ID not in member_name:
        return True

    if "/article/" not in member_name:
        return True

    if member.size <= 0 or member.size > MAX_XML_BYTES:
        return True

    return False


def clear_existing_xml_files() -> int:
    """Remove stale XML files from the target raw directory."""
    output_dir = OUTPUT_DIR.resolve()
    removed_count = 0

    for old_xml in OUTPUT_DIR.rglob("*.xml"):
        resolved_xml = old_xml.resolve()
        if output_dir not in resolved_xml.parents:
            raise RuntimeError(f"Chemin XML inattendu hors dossier cible: {old_xml}")

        old_xml.unlink()
        removed_count += 1

    return removed_count


def extract_target_xml_files(archive_path: Path) -> None:
    """Extract required Code du travail article XML files from a tar.gz archive."""
    if not archive_path.exists():
        raise FileNotFoundError(f"Archive introuvable: {archive_path}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    files_seen = 0
    xml_seen = 0
    xml_parsed = 0
    ignored_non_current = 0
    best_articles = {}
    theme_counts = Counter()
    extracted_files = []
    reference_date = date.today()

    print(f"Archive: {archive_path}", flush=True)
    print("Lecture sequentielle de l'archive, sans extraction complete.", flush=True)
    print(
        "Filtrage fort: uniquement les XML sous "
        f"{LABOR_CODE_LEGITEXT_ID} et /article/.",
        flush=True,
    )

    with tarfile.open(archive_path, mode="r:gz") as archive:
        for member in archive:
            files_seen += 1

            if files_seen % 100_000 == 0:
                print(
                    f"[progress] fichiers parcourus={files_seen}, "
                    f"xml analyses={xml_parsed}, articles retenus={len(best_articles)}",
                    flush=True,
                )

            if should_skip_member(member):
                continue

            xml_seen += 1
            file_object = archive.extractfile(member)
            if file_object is None:
                continue

            xml_bytes = file_object.read()
            xml_parsed += 1

            article_number = article_number_from_bytes(xml_bytes)
            if not article_number:
                article_number = article_number_from_xml(xml_bytes)

            if not article_number:
                continue

            theme = theme_for_article(article_number)
            if theme is None:
                continue

            metadata = article_metadata_from_xml(xml_bytes)
            if not metadata:
                continue

            if not is_current_version(metadata, reference_date):
                ignored_non_current += 1
                continue

            candidate = {
                "member_name": member.name,
                "xml_bytes": xml_bytes,
                "theme": theme,
                "metadata": metadata,
                "score": version_score(metadata),
            }

            previous = best_articles.get(article_number)
            if previous is None or candidate["score"] > previous["score"]:
                best_articles[article_number] = candidate

    removed_count = clear_existing_xml_files()

    for article_number, candidate in sorted(best_articles.items()):
        theme_counts[candidate["theme"]] += 1
        output_path = output_path_for_member(
            candidate["member_name"],
            article_number,
        )
        output_path.write_bytes(candidate["xml_bytes"])
        extracted_files.append(output_path)

    print("\nExtraction ciblee terminee", flush=True)
    print("-" * 80, flush=True)
    print(f"Nombre de fichiers parcourus: {files_seen}", flush=True)
    print(f"Nombre de fichiers XML rencontres: {xml_seen}", flush=True)
    print(f"Nombre de fichiers XML analyses: {xml_parsed}", flush=True)
    print(
        f"Nombre d'articles du Code du travail trouves: {len(best_articles)}",
        flush=True,
    )
    print(f"Versions non en vigueur ignorees: {ignored_non_current}", flush=True)
    print(f"Anciens XML supprimes de {OUTPUT_DIR}: {removed_count}", flush=True)
    print(
        f"Nombre de fichiers extraits dans {OUTPUT_DIR}: {len(extracted_files)}",
        flush=True,
    )

    print("\nArticles extraits par theme", flush=True)
    print("-" * 80, flush=True)
    for theme, count in sorted(theme_counts.items()):
        print(f"{theme}: {count}", flush=True)

    print("\nFichiers extraits", flush=True)
    print("-" * 80, flush=True)
    for output_path in extracted_files:
        print(output_path, flush=True)


def main(argv: list[str]) -> None:
    if len(argv) != 2:
        raise SystemExit(
            "Usage: python src/data/extract_code_travail_from_archive.py "
            "\"C:/Users/33785/Downloads/Freemium_legi_global_20250713-140000.tar.gz\""
        )

    archive_path = Path(argv[1])
    try:
        extract_target_xml_files(archive_path)
    except (FileNotFoundError, tarfile.TarError) as error:
        raise SystemExit(f"Erreur: {error}") from error


if __name__ == "__main__":
    main(sys.argv)
