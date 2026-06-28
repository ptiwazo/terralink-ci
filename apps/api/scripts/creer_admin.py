"""Crée un utilisateur ADMIN ou OPS (rôles non auto-inscriptibles).

À exécuter une fois après le déploiement, depuis le Shell Render (rootDir apps/api) :

    python scripts/creer_admin.py +2250700000099 "Agent OPS" MotDePasseFort OPS

Le rôle par défaut est ADMIN. Idempotent : ne recrée pas un téléphone existant.
"""
import sys

from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.enums import Role, UserStatus
from app.models.user import User


def main() -> None:
    if len(sys.argv) < 4:
        print("Usage: python scripts/creer_admin.py <telephone> <nom> <mot_de_passe> [ADMIN|OPS]")
        sys.exit(1)
    telephone, nom, mot_de_passe = sys.argv[1], sys.argv[2], sys.argv[3]
    role = Role(sys.argv[4]) if len(sys.argv) > 4 else Role.ADMIN

    db = SessionLocal()
    try:
        if db.scalar(select(User).where(User.telephone == telephone)):
            print(f"Un utilisateur existe déjà pour {telephone} — rien à faire.")
            return
        db.add(
            User(
                telephone=telephone,
                nom=nom,
                mot_de_passe_hash=hash_password(mot_de_passe),
                role=role,
                statut=UserStatus.ACTIF,
            )
        )
        db.commit()
        print(f"Créé : {telephone} ({role.value})")
    finally:
        db.close()


if __name__ == "__main__":
    main()
