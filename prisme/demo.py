"""Mode démonstration : réponses pré-rédigées et fictives, sans aucun appel à un modèle."""

from __future__ import annotations

MARK = "[Exemple de démonstration : texte pré-rédigé, non généré par un modèle, données fictives.]"
NOTICE = "Mode démonstration : exemple pré-rédigé, aucun modèle n'a été appelé."
REVISION_NOTE = "[Révision de démonstration : aucune modification réelle n'a été apportée au texte.]"


def _doc(body: str) -> str:
    return f"{MARK}\n\n{body.strip()}"


CARTOGRAPHIE = _doc(
    """
Équilibre politique. L'exécutif de la Commune d'exemple repose sur une majorité stable, structurée autour d'un
premier adjoint chargé des finances et des ressources humaines, qui concentre l'essentiel des arbitrages
budgétaires. Les délégations sensibles, urbanisme et sécurité, sont tenues par des adjoints distincts : le risque de
confusion des rôles est limité, mais une coordination régulière en bureau municipal reste nécessaire.

Dossiers à enjeu. La requalification du centre-ville et la rénovation du groupe scolaire mobilisent l'essentiel de la
capacité d'investissement. Leur calendrier de financement doit être consolidé avant le prochain débat d'orientation
budgétaire.

Points de vigilance. L'arbitrage entre investissement et fonctionnement constitue la principale tension identifiée.
Le contentieux d'urbanisme signalé appelle un suivi juridique rapproché et une information préalable de l'élu avant
toute prise de parole publique.

Recommandation pour la semaine. Réunir le premier adjoint et la direction générale pour arrêter une position
commune sur le calendrier de financement, puis préparer une note d'arbitrage destinée au maire.
"""
)

VEILLE = _doc(
    """
Brief hebdomadaire de veille institutionnelle (exemple)
Sujet illustratif : évolution des concours financiers de l'État aux collectivités

1. Cadre général. Les concours financiers de l'État font l'objet d'un débat annuel à l'occasion de l'examen du projet
de loi de finances : le cabinet suit le calendrier parlementaire et les amendements relatifs à la dotation globale
de fonctionnement.
2. Impact attendu. Une variation de la dotation se répercute sur l'épargne brute et sur la capacité d'autofinancement
des projets d'investissement.
3. Point de vigilance. Vérifier la date de notification des montants définitifs avant de caler le budget primitif.
4. Action recommandée. Simuler deux scénarios (maintien, baisse) dans la prospective financière et préparer un élément
de langage pour l'exécutif.
5. Sources. Aucune source consultée : exemple fictif. En mode réel, chaque point est daté et sourcé.
"""
)

COMMUNIQUE = _doc(
    """
Communiqué de presse (exemple)

La Commune d'exemple engage la requalification de son centre-ville

L'exécutif municipal a présenté ce jour le calendrier de requalification du centre-ville. L'opération vise à améliorer
l'accessibilité, à renforcer la place des piétons et à soutenir l'activité commerciale de proximité.

Une concertation ouverte aux habitants et aux commerçants se tiendra avant le lancement des travaux, dont le
calendrier sera communiqué à l'issue de cette phase.

Contact presse : service communication de la commune (exemple).
"""
)

DISCOURS = _doc(
    """
Discours (exemple)

Mesdames et Messieurs, chers habitants,

Je suis heureux de vous retrouver ce soir pour ouvrir la concertation sur l'avenir de notre centre-ville. Ce projet
ne se fera pas sans vous : vos usages, vos attentes et vos réserves en constituent la matière première.

Notre méthode est simple. Nous écouterons d'abord, nous arbitrerons ensuite, et nous rendrons compte de chaque
décision. Je vous remercie de votre présence et de votre engagement.
"""
)

SYNTHESE = _doc(
    """
Note de synthèse (exemple)

Objet : calendrier de financement de la rénovation d'un groupe scolaire

1. État des lieux. L'opération est estimée en phase d'avant-projet ; le plan de financement reste à consolider.
2. Analyse. Le recours à l'emprunt pèse sur la capacité de désendettement ; les subventions mobilisables dépendent du
calendrier de dépôt des dossiers.
3. Propositions. Déposer les demandes de subvention avant l'arrêt de l'avant-projet définitif ; échelonner les
travaux sur deux exercices.
4. Échéancier. Validation du plan de financement en bureau municipal, puis inscription au prochain budget.
"""
)

ARBITRAGE = _doc(
    """
Note d'arbitrage (exemple)

Objet : choix du mode de financement d'un équipement scolaire

1. Contexte. Les besoins de rénovation sont établis ; le calendrier budgétaire impose de trancher avant le prochain
débat d'orientation.
2. Éléments de décision. Capacité d'autofinancement disponible, taux d'emprunt, subventions mobilisables.
3. Options. A : étalement des travaux sur deux exercices. B : recours à l'emprunt sur un exercice. C : report.
4. Recommandation. Option A, qui préserve l'épargne brute et laisse le temps de sécuriser les subventions.
5. Calendrier. Arbitrage de l'élu cette semaine ; inscription au prochain conseil municipal.
"""
)

CRISE = _doc(
    """
Déclaration d'attente (exemple)

Un incident est survenu ce jour sur le territoire de la commune. Les services de secours et les services municipaux
sont mobilisés et prennent en charge les personnes concernées. À ce stade, seuls les faits établis peuvent être
communiqués : les causes ne sont pas encore déterminées. Nos pensées vont aux personnes touchées et à leurs proches.
Un nouveau point d'information sera fait à 18 heures.
"""
)

INVISIBLE = [
    _doc(
        """
Un désaccord avec un directeur général des services se traite d'abord hors du cadre formel : un entretien bilatéral,
avant toute réunion, pour comprendre ce qui motive sa position (contrainte juridique, charge de travail, risque
financier). Le cabinet gagne à arriver avec une option de repli plutôt qu'avec un refus. Si le désaccord persiste, il
se tranche devant l'élu, sur un document écrit qui expose les deux positions et leurs conséquences.
"""
    ),
    (
        "Si l'élu tranche contre votre avis, vérifiez d'abord que l'information juridique et financière lui a été "
        "donnée complètement, puis exécutez loyalement en consignant l'arbitrage. Votre rôle n'est pas de gagner, mais "
        "de rendre la décision exécutable et de protéger l'exécutif des risques identifiés. Un écrit sobre rappelant "
        "les réserves émises, versé au dossier, vous protège sans mettre en cause la décision."
    ),
    (
        "Retenez, au-delà du cas d'espèce, que la valeur d'un cabinet tient à sa constance : mêmes règles, mêmes "
        "délais, même discrétion d'un dossier à l'autre. C'est elle qui rend ses avis crédibles auprès de l'élu comme "
        "de l'administration."
    ),
]

AGENDA = (
    '{"strategique": 52, "operationnel": 28, "imprevus": 20, "commentaire": "Exemple de démonstration : la part '
    "stratégique reste inférieure à la cible de 60 %, au profit des réunions de suivi. Protéger deux créneaux "
    'hebdomadaires de travail de fond serait un premier levier."}'
)

CANVA = _doc(
    """
Brief visuel (exemple)

Titre : La requalification du centre-ville
Accroche : Un centre-ville pensé avec ses habitants.
Hiérarchie : titre en grand, accroche en italique, date et lieu de la concertation en pied de visuel.
Palette : fond noir (#0A0A0A), accent or (#D4A828), texte ivoire (#E8E3D8).
Format recommandé : publication verticale 1080 x 1350 pixels.
"""
)

GENERIC = _doc(
    "Document d'exemple. En mode réel, le modèle rédige ici un texte adapté à votre demande, dans le registre "
    "institutionnel attendu."
)

DEMOS = {
    "cartographie": CARTOGRAPHIE,
    "veille": VEILLE,
    "communication": COMMUNIQUE,
    "communication:Discours": DISCOURS,
    "redaction": SYNTHESE,
    "redaction:Note d'arbitrage": ARBITRAGE,
    "crise": CRISE,
    "agenda": AGENDA,
    "canva": CANVA,
    "test": "OK (mode démonstration)",
}


def respond(key: str | None = None, history: list[dict] | None = None, echo: str | None = None) -> str:
    """Retourne la réponse pré-rédigée associée à `key` (ou rejoue `echo` pour une révision)."""
    if echo is not None:
        return echo if REVISION_NOTE in echo else f"{echo.rstrip()}\n\n{REVISION_NOTE}"
    if key == "invisible":
        return INVISIBLE[(len(history or []) // 2) % len(INVISIBLE)]
    if key in DEMOS:
        return DEMOS[key]
    base = str(key or "").split(":")[0]
    return DEMOS.get(base, GENERIC)
