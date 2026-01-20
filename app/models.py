from __future__ import annotations

from datetime import datetime, date

from flask_sqlalchemy import SQLAlchemy

from utils import cid_to_impact, risk_level


db = SQLAlchemy()


# Many-to-many: riesgos <-> controles propuestos
risk_controls = db.Table(
    "risk_controls",
    db.Column("risk_id", db.Integer, db.ForeignKey("risk_scenario.id"), primary_key=True),
    db.Column("control_id", db.Integer, db.ForeignKey("control.id"), primary_key=True),
)


class Asset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    asset_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    owner = db.Column(db.String(120))
    process = db.Column(db.String(120))

    # CID: 1-3
    confidentiality = db.Column(db.Integer, nullable=False, default=1)
    integrity = db.Column(db.Integer, nullable=False, default=1)
    availability = db.Column(db.Integer, nullable=False, default=1)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    risks = db.relationship("RiskScenario", back_populates="asset", cascade="all, delete-orphan")

    @property
    def cid_total(self) -> int:
        return int(self.confidentiality) + int(self.integrity) + int(self.availability)

    @property
    def impact_value(self) -> int:
        return cid_to_impact(self.cid_total)


class Threat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text)


class Vulnerability(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text)


class Control(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False)
    iso_reference = db.Column(db.String(120), nullable=True)
    control_type = db.Column(db.String(40), nullable=True)
    description = db.Column(db.Text)


class RiskScenario(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    asset_id = db.Column(db.Integer, db.ForeignKey("asset.id"), nullable=False)
    threat_id = db.Column(db.Integer, db.ForeignKey("threat.id"), nullable=False)
    vulnerability_id = db.Column(db.Integer, db.ForeignKey("vulnerability.id"), nullable=False)

    existing_controls = db.Column(db.Text)

    # Inherente
    probability = db.Column(db.Integer, nullable=False, default=3)  # 1-5
    impact_override = db.Column(db.Integer, nullable=True)  # 1-5 optional

    # Tratamiento
    treatment_strategy = db.Column(db.String(20), nullable=True)  # Mitigar/Transferir/Aceptar/Evitar
    responsible = db.Column(db.String(120), nullable=True)
    due_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(30), nullable=False, default="Pendiente")
    acceptance_justification = db.Column(db.Text, nullable=True)
    acceptance_approved_by = db.Column(db.String(120), nullable=True)

    # Residual
    residual_probability = db.Column(db.Integer, nullable=True)
    residual_impact = db.Column(db.Integer, nullable=True)
    completed_at = db.Column(db.Date, nullable=True)

    # Comunicacion
    observations = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_review_at = db.Column(db.DateTime, nullable=True)

    asset = db.relationship("Asset", back_populates="risks")
    threat = db.relationship("Threat")
    vulnerability = db.relationship("Vulnerability")
    proposed_controls = db.relationship("Control", secondary=risk_controls, lazy="subquery")
    incidents = db.relationship("Incident", back_populates="risk", cascade="all, delete-orphan")

    def impact_value(self) -> int:
        # Si el grupo desea ajustar impacto por escenario, puede usar override 1-5
        if self.impact_override:
            return int(self.impact_override)
        return int(self.asset.impact_value)

    def inherent_score(self) -> int:
        return int(self.probability) * int(self.impact_value())

    def inherent_level(self) -> str:
        return risk_level(self.inherent_score())

    def residual_score(self) -> int | None:
        if self.residual_probability is None and self.residual_impact is None:
            return None
        rp = int(self.residual_probability) if self.residual_probability is not None else int(self.probability)
        ri = int(self.residual_impact) if self.residual_impact is not None else int(self.impact_value())
        return rp * ri

    def residual_level(self) -> str | None:
        score = self.residual_score()
        return risk_level(score) if score is not None else None


class Incident(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    risk_id = db.Column(db.Integer, db.ForeignKey("risk_scenario.id"), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    description = db.Column(db.Text, nullable=False)
    severity = db.Column(db.String(20), nullable=True)

    risk = db.relationship("RiskScenario", back_populates="incidents")
