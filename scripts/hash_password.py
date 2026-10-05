"""Génère un hachage de mot de passe à coller dans la section [users] des secrets."""

import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from prisme.auth import hash_password  # noqa: E402

if __name__ == "__main__":
    pw = getpass.getpass("Mot de passe : ")
    if getpass.getpass("Confirmation : ") != pw or len(pw) < 10:
        sys.exit("Les mots de passe diffèrent ou font moins de 10 caractères.")
    print(hash_password(pw))
