"""Création du compte administrateur initial au démarrage.

Si `ADMIN_TELEPHONE` et `ADMIN_PASSWORD` sont définis ET qu'aucun compte
ADMIN/OPS n'existe encore, un compte privilégié est créé. Permet de débloquer
l'accès OPS en production sans accès shell. Idempotent : ne s'exécute qu'une fois.
"""
from sqlalchemy import select

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.enums import Role, UserStatus
from app.models.user import User


def seed_admin() -> None:
    if not settings.admin_telephone or not settings.admin_password:
        return
    db = SessionLocal()
    try:
        # Ne rien faire si un compte privilégié existe déjà (one-time).
        if db.scalar(select(User).where(User.role.in_([Role.ADMIN, Role.OPS]))):
            return
        if db.scalar(select(User).where(User.telephone == settings.admin_telephone)):
            return
        try:
            role = Role(settings.admin_role)
        except ValueError:
            role = Role.ADMIN
        db.add(
            User(
                telephone=settings.admin_telephone,
                nom=settings.admin_nom,
                mot_de_passe_hash=hash_password(settings.admin_password),
                role=role,
                statut=UserStatus.ACTIF,
            )
        )
        db.commit()
        print(f"[bootstrap] Compte {role.value} créé : {settings.admin_telephone}")
    except Exception as exc:  # ne jamais empêcher le démarrage de l'API
        print(f"[bootstrap] échec création admin : {exc}")
    finally:
        db.close()
