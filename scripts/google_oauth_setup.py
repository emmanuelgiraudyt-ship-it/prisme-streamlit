"""Obtient le jeton d'actualisation Google (à exécuter une fois, en local).

Prérequis : un client OAuth de type « Application de bureau » créé dans Google Cloud Console, avec les API
Gmail, Drive et Calendar activées. Télécharger le JSON du client puis :

    python scripts/google_oauth_setup.py client_secret.json
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from google_auth_oauthlib.flow import InstalledAppFlow  # noqa: E402

from prisme.google_ws import SCOPES  # noqa: E402

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    flow = InstalledAppFlow.from_client_secrets_file(sys.argv[1], SCOPES)
    creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")
    print("\nÀ placer dans les secrets de l'application :\n")
    print(f'GOOGLE_CLIENT_ID = "{creds.client_id}"')
    print(f'GOOGLE_CLIENT_SECRET = "{creds.client_secret}"')
    print(f'GOOGLE_REFRESH_TOKEN = "{creds.refresh_token}"')
