"""Contenus statiques : invites système, listes de choix, données d'exemple."""

from __future__ import annotations

from .util import fr_date

SYSTEM_PRISME = (
    "Tu es l'assistant institutionnel d'un directeur de cabinet en collectivité territoriale française. "
    "Registre soutenu, précis, factuel, ponctuation française classique, sans emoji ni tiret cadratin. "
    "Tu maîtrises le CGCT, le fonctionnement des exécutifs locaux, les usages protocolaires et la doctrine "
    "d'arbitrage de cabinet. Tu n'inventes jamais d'information : si une donnée précise n'est pas vérifiable, "
    "tu le signales explicitement plutôt que de l'inventer. Tes réponses sont structurées, sobres, "
    "exploitables telles quelles dans un cabinet, et constituent des projets soumis à relecture humaine."
)


def build_system(settings: dict | None = None) -> str:
    s = settings or {}
    out = f"{SYSTEM_PRISME} Date du jour : {fr_date()}."
    if s.get("collectivite"):
        out += f" Collectivité de référence : {s['collectivite']}."
    if s.get("elu"):
        out += f" Exécutif servi : {s['elu']}."
    if s.get("cabinet"):
        out += f" Structure émettrice : {s['cabinet']}."
    return out


DOMAINES_INSTITUTIONNELS = [
    "lagazettedescommunes.com",
    "acteurspublics.fr",
    "courrierdesmaires.fr",
    "maire-info.com",
    "banquedesterritoires.fr",
    "localtis.info",
    "legifrance.gouv.fr",
    "senat.fr",
    "assemblee-nationale.fr",
    "collectivites-locales.gouv.fr",
    "vie-publique.fr",
    "conseil-etat.fr",
    "conseil-constitutionnel.fr",
    "ccomptes.fr",
    "amf.asso.fr",
    "service-public.fr",
]

MODES_VEILLE = {
    "Brief hebdomadaire": (
        "Rédige un brief hebdomadaire de veille institutionnelle (format court, 5 à 7 points synthétiques, "
        "chacun daté et sourcé) sur le sujet suivant, à l'attention d'un directeur de cabinet"
    ),
    "Analyse d'impact": (
        "Rédige une analyse d'impact structurée (contexte, impact sur la collectivité, marge de manœuvre, "
        "recommandation) sur le sujet suivant"
    ),
    "Fiche de briefing cabinet": (
        "Rédige une fiche de briefing cabinet complète (une page, format note) destinée à préparer l'élu "
        "sur le sujet suivant"
    ),
    "Revue de presse territoriale": (
        "Rédige une revue de presse territoriale synthétique (titres, dates, sources, angle pour le cabinet) "
        "sur le sujet suivant"
    ),
}

PERIODES_VEILLE = {
    "Dernières 24 heures": "les dernières 24 heures",
    "7 derniers jours": "les 7 derniers jours",
    "30 derniers jours": "les 30 derniers jours",
    "Sans limite de période": "",
}

FORMATS_COMM = [
    "Communiqué de presse",
    "Discours",
    "Note interne",
    "Courrier officiel",
    "Réponse presse",
    "Post réseaux sociaux",
    "Éditorial de magazine municipal",
]
TONS = ["Institutionnel", "Offensif", "Rassembleur", "Technique", "Solennel"]
AUDIENCES = ["Grand public", "Presse", "Agents", "Élus", "Partenaires institutionnels"]

TYPOLOGIES = [
    "Note de synthèse",
    "Note d'arbitrage",
    "Compte rendu",
    "Ordre du jour",
    "Discours",
    "Courrier officiel",
    "Élément de langage",
]

NIVEAUX_CRISE = [
    {"label": "Vert : vigilance", "color": "#4A7A5A"},
    {"label": "Orange : alerte", "color": "#B8763A"},
    {"label": "Rouge : crise ouverte", "color": "#8B3A3A"},
]

PROTOCOLE_H = [
    ("H+1", "Point de situation flash avec l'élu, verrouillage du message initial."),
    ("H+3", "Cellule de crise restreinte, désignation d'un porte-parole unique."),
    ("H+6", "Premier communiqué de cadrage, information des services concernés."),
    ("H+24", "Point presse ou communiqué complet, coordination avec la préfecture si nécessaire."),
    ("H+48", "Suivi de l'évolution médiatique, ajustement du message."),
    ("H+72", "Bilan de gestion de crise, retour d'expérience pour le cabinet."),
]

INVISIBLE_ENTRIES = [
    (
        "Loyauté",
        "La loyauté du directeur de cabinet ne se négocie pas et ne se démontre pas publiquement : elle se "
        "vérifie dans les arbitrages non rapportés et dans la constance du discours privé.",
    ),
    (
        "Mémoire institutionnelle",
        "Le cabinet est le dépositaire de la mémoire des décisions passées, y compris celles que "
        "l'administration ou l'exécutif préféreraient voir oubliées. Cette mémoire est un outil de "
        "protection, pas une arme.",
    ),
    (
        "Réseaux",
        "Le capital relationnel du directeur de cabinet appartient d'abord à la fonction, non à la personne, "
        "mais sa gestion dans la durée conditionne la trajectoire de carrière après le mandat.",
    ),
    (
        "Arbitrage silencieux",
        "De nombreux arbitrages se font en amont des réunions officielles, dans des échanges informels qui ne "
        "laissent pas de trace écrite. Le rôle du cabinet est d'anticiper le désaccord avant qu'il ne se "
        "formalise.",
    ),
    (
        "Protection de l'exécutif",
        "Protéger l'élu ne signifie pas lui cacher l'information, mais filtrer le bruit pour ne remonter que "
        "ce qui appelle une décision réelle.",
    ),
    (
        "Fin de mandat",
        "La fin de mandat se prépare dès le milieu du mandat : transmission des dossiers, sécurisation "
        "juridique des décisions engagées, et anticipation de la propre reconversion du directeur de cabinet.",
    ),
]

# Fiche d'exemple strictement fictive : aucune donnée réelle sur une collectivité existante.
COMMUNE_EXEMPLE = "Commune d'exemple (fiche fictive)"
COMMUNES_DEMO = {
    COMMUNE_EXEMPLE: {
        "maire": "Maire (étiquette fictive), 1er mandat",
        "adjoints": [
            "1er adjoint : finances et ressources humaines",
            "2e adjointe : urbanisme et aménagement",
            "3e adjoint : sécurité et tranquillité publique",
            "4e adjointe : action sociale et solidarités",
        ],
        "commissions": ["Finances", "Urbanisme", "Sécurité"],
        "projets": ["Requalification du centre-ville (exemple)", "Rénovation d'un groupe scolaire (exemple)"],
        "tensions": ["Arbitrage budgétaire entre investissement et fonctionnement (exemple)"],
        "alertes": ["Contentieux d'urbanisme en cours (exemple fictif)"],
        "agendaCM": ["Budget supplémentaire (exemple)", "Convention de délégation (exemple)"],
        "demo": True,
    }
}
