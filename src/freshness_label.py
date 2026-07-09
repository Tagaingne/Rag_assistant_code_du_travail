# src/freshness_label.py
#
# Traduit le statut "fraicheur" calcule par ReferenceRetrieverAgent en un
# libelle affichable, partage par les 3 interfaces (CLI, Streamlit, FastAPI).

FRESHNESS_LABELS = {
    "a_jour": "à jour (vérifié en direct sur Légifrance)",
    "modifie": "modifié depuis l'indexation (vérifié en direct)",
    "obsolete": "abrogé ou plus en vigueur (vérifié en direct)",
    "verification_indisponible": "vérification Légifrance indisponible",
    "non_verifiable": "non vérifiable",
}


def format_freshness_label(metadata: dict) -> str:
    fraicheur = metadata.get("fraicheur")
    if not fraicheur:
        return ""
    return FRESHNESS_LABELS.get(fraicheur, "")
