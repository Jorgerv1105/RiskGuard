from __future__ import annotations

from datetime import date

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, IntegerField, DateField, SubmitField, SelectMultipleField
from wtforms.validators import DataRequired, Length, NumberRange, Optional

ASSET_TYPES = [
    ("Hardware", "Hardware"),
    ("Software", "Software"),
    ("Datos", "Datos"),
    ("Servicio", "Servicio"),
    ("Persona", "Persona"),
]

CATEGORIES_THREAT = [
    ("Externa", "Externa"),
    ("Interna", "Interna"),
    ("Error humano", "Error humano"),
    ("Fallo tecnico", "Fallo tecnico"),
]

CATEGORIES_VULN = [
    ("Tecnologica", "Tecnologica"),
    ("Organizacional", "Organizacional"),
    ("Proceso", "Proceso"),
]

PROB_SCALE = [(str(i), str(i)) for i in range(1, 6)]
IMPACT_SCALE = [(str(i), str(i)) for i in (1, 2, 3, 4, 5)]

TREATMENT_STRATEGIES = [
    ("Mitigar", "Mitigar"),
    ("Transferir", "Transferir"),
    ("Aceptar", "Aceptar"),
    ("Evitar", "Evitar"),
]

STATUS = [
    ("Pendiente", "Pendiente"),
    ("En progreso", "En progreso"),
    ("Implementado", "Implementado"),
]

CONTROL_TYPES = [
    ("Preventivo", "Preventivo"),
    ("Detectivo", "Detectivo"),
    ("Correctivo", "Correctivo"),
    ("Otro", "Otro"),
]


class AssetForm(FlaskForm):
    name = StringField("Nombre del activo", validators=[DataRequired(), Length(max=120)])
    asset_type = SelectField("Tipo", choices=ASSET_TYPES, validators=[DataRequired()])
    # IMPORTANT: don't name a field "process" because it collides with WTForms' Form.process()
    process_area = StringField("Proceso/Area (opcional)", validators=[Optional(), Length(max=120)])
    owner = StringField("Responsable/Propietario (opcional)", validators=[Optional(), Length(max=120)])
    description = TextAreaField("Descripcion (opcional)", validators=[Optional()])
    confidentiality = IntegerField("Confidencialidad (1-3)", validators=[DataRequired(), NumberRange(min=1, max=3)])
    integrity = IntegerField("Integridad (1-3)", validators=[DataRequired(), NumberRange(min=1, max=3)])
    availability = IntegerField("Disponibilidad (1-3)", validators=[DataRequired(), NumberRange(min=1, max=3)])
    submit = SubmitField("Guardar")


class ThreatForm(FlaskForm):
    name = StringField("Amenaza", validators=[DataRequired(), Length(max=120)])
    category = SelectField("Categoria", choices=CATEGORIES_THREAT, validators=[DataRequired()])
    description = TextAreaField("Descripcion (opcional)", validators=[Optional()])
    submit = SubmitField("Guardar")


class VulnerabilityForm(FlaskForm):
    name = StringField("Vulnerabilidad", validators=[DataRequired(), Length(max=120)])
    category = SelectField("Categoria", choices=CATEGORIES_VULN, validators=[DataRequired()])
    description = TextAreaField("Descripcion (opcional)", validators=[Optional()])
    submit = SubmitField("Guardar")


class ControlForm(FlaskForm):
    name = StringField("Control", validators=[DataRequired(), Length(max=160)])
    iso_reference = StringField("Referencia ISO 27002:2022 (opcional)", validators=[Optional(), Length(max=120)])
    control_type = SelectField("Tipo de control (opcional)", choices=CONTROL_TYPES, validators=[Optional()])
    description = TextAreaField("Descripcion (opcional)", validators=[Optional()])
    submit = SubmitField("Guardar")


class RiskForm(FlaskForm):
    asset_id = SelectField("Activo", coerce=int, validators=[DataRequired()])
    threat_id = SelectField("Amenaza", coerce=int, validators=[DataRequired()])
    vulnerability_id = SelectField("Vulnerabilidad", coerce=int, validators=[DataRequired()])

    probability = SelectField("Probabilidad (1-5)", choices=PROB_SCALE, validators=[DataRequired()])
    impact_override = SelectField("Impacto (opcional, 1-5). Si se deja vacio, usa impacto del activo.", choices=[("", "(usar impacto del activo)")] + IMPACT_SCALE, validators=[Optional()])

    existing_controls = TextAreaField("Controles existentes (opcional)", validators=[Optional()])
    observations = TextAreaField("Observaciones/Recomendaciones (opcional)", validators=[Optional()])

    submit = SubmitField("Crear riesgo")


class TreatmentForm(FlaskForm):
    treatment_strategy = SelectField("Estrategia", choices=[("", "(seleccionar)")] + TREATMENT_STRATEGIES, validators=[Optional()])
    proposed_controls = SelectMultipleField("Controles propuestos", coerce=int, validators=[Optional()])
    responsible = StringField("Responsable (opcional)", validators=[Optional(), Length(max=120)])
    due_date = DateField("Fecha limite (opcional)", validators=[Optional()])
    status = SelectField("Estado", choices=STATUS, validators=[DataRequired()])

    acceptance_justification = TextAreaField("Justificacion (solo si Aceptar)", validators=[Optional()])
    acceptance_approved_by = StringField("Aprobado por (solo si Aceptar)", validators=[Optional(), Length(max=120)])

    submit = SubmitField("Guardar tratamiento")


class ResidualForm(FlaskForm):
    residual_probability = SelectField("Probabilidad residual (1-5)", choices=[("", "(sin evaluar)")] + PROB_SCALE, validators=[Optional()])
    residual_impact = SelectField("Impacto residual (1-5)", choices=[("", "(sin evaluar)")] + IMPACT_SCALE, validators=[Optional()])
    completed_at = DateField("Fecha de implementacion (opcional)", validators=[Optional()])
    last_review_at = DateField("Fecha de revision (opcional)", validators=[Optional()])
    submit = SubmitField("Guardar riesgo residual")


class IncidentForm(FlaskForm):
    date = DateField("Fecha", default=date.today, validators=[DataRequired()])
    severity = SelectField("Severidad (opcional)", choices=[("", "(sin)") , ("Baja", "Baja"), ("Media", "Media"), ("Alta", "Alta")], validators=[Optional()])
    description = TextAreaField("Descripcion", validators=[DataRequired()])
    submit = SubmitField("Registrar incidente")
