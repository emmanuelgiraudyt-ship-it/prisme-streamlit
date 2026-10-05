# PRISME v5.0

**Plateforme de Renseignement Institutionnel et Stratégique pour le Management de l'Élu**, version Streamlit
(édité par EG Conseil & Lobbying). Elle reprend les sept modules de la version React 4.0 et en ajoute trois :
tableau de bord, bibliothèque, paramètres et connexions.

## Modules

| Module | Contenu |
|---|---|
| Tableau de bord | Indicateurs, actions rapides, état des connexions |
| Cartographie politique | Fiches de collectivités mémorisées, synthèse de cabinet, enrichissement web optionnel |
| Veille institutionnelle | Recherche web avec sources citées, restriction par domaines, fenêtre de période |
| Communication Manager | Communiqués, discours, notes, courriers ; brief visuel pour Canva |
| Agenda 60·20·20 | Mesure depuis Google Agenda ou fichier .ics, saisie manuelle |
| Rédaction institutionnelle | Génération puis révision itérative |
| Protocole de crise | Chronomètre, protocole H+1 à H+72, déclaration d'attente, main courante horodatée |
| L'Invisible du Cabinet | Dialogue suivi |
| Bibliothèque | Archives recherchables et réexportables |
| Paramètres et connexions | Identité, tests de connexion, consommation, export et effacement des données |

Chaque production s'exporte en Word (.docx), Markdown, brouillon .eml, et, si configuré, vers Notion, Google Drive
et Gmail (brouillon uniquement : aucun courriel n'est jamais envoyé).

## Démarrage local

```bash
python -m venv .venv && source .venv/bin/activate   # Windows : .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
python scripts/hash_password.py        # colle le hachage dans [users] du fichier secrets.toml
streamlit run app.py
```

Renseignez au minimum `ANTHROPIC_API_KEY` et un compte dans `[users]`. Pour un simple essai local sans mot de
passe : `PRISME_AUTH_DISABLED=true streamlit run app.py`. **Ne jamais activer cette option sur un déploiement
accessible depuis Internet** : n'importe quel visiteur consommerait votre crédit d'API.

## Déploiement

### Streamlit Community Cloud
1. Dépôt GitHub privé contenant ce code.
2. share.streamlit.io, « New app », choisir le dépôt, branche `main`, fichier `app.py`.
3. Advanced settings, Secrets : coller le contenu de `.streamlit/secrets.toml.example` complété.

Attention : le disque de ce service n'est pas garanti persistant. Les archives, fiches et la main courante
stockées dans SQLite peuvent être perdues lors d'un redémarrage. Il convient pour des démonstrations ; pour un
usage en production, préférer Docker avec volume.

### Docker (recommandé pour un usage réel, hébergeur français ou européen)
```bash
docker build -t prisme .
docker run -d -p 8501:8501 -v prisme-data:/data \
  -e ANTHROPIC_API_KEY=... -e PRISME_USERS='{"cabinet":"pbkdf2_sha256$..."}' prisme
```
Placer l'application derrière un proxy HTTPS (Caddy, Nginx, Traefik).

## Connexions

- **Modèle** : `ANTHROPIC_API_KEY`. La recherche web est l'outil natif d'Anthropic ; elle doit être activée dans la
  console de l'organisation, sans quoi l'application répond sans recherche et l'indique. Modèle modifiable par
  `PRISME_MODEL` (défaut : `claude-sonnet-4-6`).
- **Fournisseur alternatif (expérimental)** : `PRISME_PROVIDER=openai` avec `PRISME_OPENAI_BASE_URL`,
  `PRISME_OPENAI_API_KEY`, `PRISME_OPENAI_MODEL` pour Mistral ou tout point d'accès compatible. Pas de recherche web
  dans ce mode.
- **Notion** : créer une intégration interne, la partager avec la page ou la base cible, renseigner `NOTION_TOKEN` et
  `NOTION_PARENT_PAGE_ID` (ou `NOTION_DATABASE_ID`).
- **Google** (Gmail brouillons, Drive, Agenda lecture seule) : créer un client OAuth « Application de bureau »,
  activer les API Gmail, Drive et Calendar, puis exécuter une fois `python scripts/google_oauth_setup.py client_secret.json`
  et reporter les trois valeurs affichées. À vérifier dans la documentation Google : tant que l'écran de
  consentement est en mode « Test », la durée de vie du jeton d'actualisation est limitée ; passer l'application en
  production (ou « Interne » pour un domaine Workspace) pour un usage durable.
- **Canva** : non connecté par API. Le module Communication produit un brief visuel prêt à coller dans Canva.

## Sécurité, comptes et données

- Un identifiant égale un espace de données cloisonné (documents, fiches, main courante, paramètres, consommation).
- Mots de passe stockés sous forme de hachage PBKDF2 (`scripts/hash_password.py`).
- Plafond quotidien de générations par espace (`PRISME_DAILY_LIMIT`, 200 par défaut) et mesure de la consommation.
- Export JSON et effacement définitif des données depuis Paramètres et connexions (portabilité et effacement RGPD).
- Les contenus générés portent une mention de relecture obligatoire ; la décision reste humaine.
- Les fiches de collectivités associent des étiquettes politiques à des élus identifiables : catégories particulières de données (article 9 du RGPD). Pour des démonstrations, utiliser la fiche fictive ; pour des données réelles, limiter la saisie aux informations publiques et héberger en conformité (voir Docker).

## Limites connues

- Les intégrations Notion, Google et le fournisseur alternatif sont testées par simulation (suite de tests), pas
  encore contre des comptes réels : à valider avec vos propres identifiants avant toute démonstration.
- Stockage SQLite : un seul serveur, pas de haute disponibilité.
- Pas de facturation, de SSO ni de journal d'audit intégrés.
- Streamlit Community Cloud est hébergé hors de France : il ne satisfait pas une exigence de qualification SecNumCloud.
- Les fiches de collectivités sont déclaratives ; le logiciel n'en vérifie pas l'exactitude.

## Développement

```bash
ruff check . && pytest -q      # exécuté automatiquement par GitHub Actions à chaque push
```

Feuille de route technique : base PostgreSQL, authentification SSO, facturation à l'usage, journal d'audit,
cœur de production sur modèle souverain.
