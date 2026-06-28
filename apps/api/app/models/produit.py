"""Table `produits` — catalogue de référence (manioc, igname, plantain…).

Données de référence partagées, alimentées par migration. Les producteurs
publient des `offres` qui pointent vers un produit de ce catalogue.
"""
import uuid

from sqlalchemy import Boolean, Enum as SAEnum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.enums import Unite


class Produit(Base):
    __tablename__ = "produits"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    nom: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    categorie: Mapped[str] = mapped_column(String(60), nullable=False)
    unite: Mapped[Unite] = mapped_column(
        SAEnum(Unite, native_enum=False, length=20), nullable=False
    )
    actif: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
