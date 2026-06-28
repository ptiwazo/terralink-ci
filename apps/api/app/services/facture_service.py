"""Facturation OHADA (CLAUDE.md §2.3, §4, Phase 5).

Numérotation **séquentielle, continue, sans trou, par exercice**. Le compteur
`facture_sequences` est verrouillé (FOR UPDATE) et incrémenté dans la même
transaction que l'insertion de la facture : un échec annule tout, aucun numéro
n'est gaspillé.
"""
import os
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.commande import Commande
from app.models.enums import CommandeStatut
from app.models.facture import Facture, FactureSequence
from app.services import audit_service

# États où la vente est réalisée et donc facturable.
FACTURABLES = {
    CommandeStatut.FONDS_LIBERES,
    CommandeStatut.CLOTUREE,
    CommandeStatut.RESOLUE_LIBEREE,
}


class FactureError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def get_par_commande(db: Session, commande_id: uuid.UUID) -> Facture | None:
    return db.scalar(select(Facture).where(Facture.commande_id == commande_id))


def _prochain_numero(db: Session, exercice: int) -> tuple[int, str]:
    """Alloue le prochain numéro de l'exercice sous verrou (sans trou)."""
    seq = db.scalar(
        select(FactureSequence)
        .where(FactureSequence.exercice == exercice)
        .with_for_update()
    )
    if seq is None:
        seq = FactureSequence(exercice=exercice, dernier_numero=0)
        db.add(seq)
        db.flush()
    seq.dernier_numero += 1
    numero = f"{exercice}-{seq.dernier_numero:07d}"
    return seq.dernier_numero, numero


def _generer_pdf(facture: Facture, commande: Commande) -> str:
    """Génère le PDF de la facture et renvoie le chemin (pdf_ref)."""
    os.makedirs(settings.factures_dir, exist_ok=True)
    chemin = os.path.join(settings.factures_dir, f"{facture.numero}.pdf")

    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas

    c = canvas.Canvas(chemin, pagesize=A4)
    largeur, hauteur = A4
    y = hauteur - 30 * mm
    c.setFont("Helvetica-Bold", 18)
    c.drawString(20 * mm, y, "TerraLink CI — FACTURE")
    c.setFont("Helvetica", 11)
    y -= 12 * mm
    c.drawString(20 * mm, y, f"Numéro : {facture.numero}")
    y -= 7 * mm
    c.drawString(20 * mm, y, f"Date : {facture.created_at:%d/%m/%Y}" if facture.created_at else "")
    y -= 7 * mm
    c.drawString(20 * mm, y, f"Exercice : {facture.exercice}")
    y -= 7 * mm
    c.drawString(20 * mm, y, f"Commande : {commande.id}")
    y -= 7 * mm
    c.drawString(20 * mm, y, f"Mode de paiement : {commande.mode_paiement.value}")

    y -= 15 * mm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(20 * mm, y, "Détail")
    c.setFont("Helvetica", 11)
    for ligne in commande.lignes:
        y -= 7 * mm
        c.drawString(
            20 * mm,
            y,
            f"{ligne.quantite} × {ligne.produit.nom} @ {ligne.prix_unitaire} FCFA "
            f"= {ligne.quantite * ligne.prix_unitaire} FCFA",
        )

    y -= 15 * mm
    c.setFont("Helvetica", 12)
    c.drawString(20 * mm, y, f"Montant HT : {facture.montant_ht} FCFA")
    y -= 7 * mm
    c.drawString(20 * mm, y, f"TVA : {facture.tva} FCFA")
    y -= 7 * mm
    c.setFont("Helvetica-Bold", 13)
    c.drawString(20 * mm, y, f"Montant TTC : {facture.montant_ttc} FCFA")

    c.showPage()
    c.save()
    return chemin


def emettre(db: Session, commande: Commande, acteur) -> Facture:
    if commande.statut not in FACTURABLES:
        raise FactureError(
            "La commande n'est pas dans un état facturable (vente non réalisée)", 409
        )
    existante = get_par_commande(db, commande.id)
    if existante is not None:
        return existante  # idempotent : une facture par commande

    exercice = datetime.now(timezone.utc).year
    _, numero = _prochain_numero(db, exercice)
    sequence = int(numero.split("-")[1])

    montant_ht = commande.montant_total
    tva = (montant_ht * settings.facture_tva_bps) // 10000
    facture = Facture(
        numero=numero,
        exercice=exercice,
        sequence=sequence,
        commande_id=commande.id,
        montant_ht=montant_ht,
        tva=tva,
        montant_ttc=montant_ht + tva,
    )
    db.add(facture)
    db.flush()
    facture.pdf_ref = _generer_pdf(facture, commande)
    audit_service.journaliser(
        db,
        acteur_id=acteur.id,
        action="FACTURE_EMISE",
        ressource_type="facture",
        ressource_id=facture.id,
        details={"numero": numero, "ttc": facture.montant_ttc},
    )
    db.commit()
    db.refresh(facture)
    return facture


def lister(db: Session) -> list[Facture]:
    return list(db.scalars(select(Facture).order_by(Facture.numero)))
