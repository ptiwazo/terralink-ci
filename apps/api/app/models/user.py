"""Table `users`.

Identifiant principal = téléphone (contexte ivoirien, cf. CLAUDE.md §4).
On stocke des Enum en VARCHAR + CHECK (`native_enum=False`) pour rester
portable et garder des migrations simples.
"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.enums import Role, UserStatus


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    telephone: Mapped[str] = mapped_column(
        String(20), unique=True, index=True, nullable=False
    )
    nom: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mot_de_passe_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[Role] = mapped_column(
        SAEnum(Role, native_enum=False, length=20), nullable=False
    )
    statut: Mapped[UserStatus] = mapped_column(
        SAEnum(UserStatus, native_enum=False, length=20),
        nullable=False,
        default=UserStatus.ACTIF,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
