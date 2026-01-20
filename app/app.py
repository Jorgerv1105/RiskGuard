from __future__ import annotations

import os
from datetime import date, datetime

from dotenv import load_dotenv
from flask import Flask, render_template, redirect, url_for, flash, request, send_file
from flask_wtf.csrf import CSRFProtect

from models import db, Asset, Threat, Vulnerability, Control, RiskScenario, Incident
from forms import AssetForm, ThreatForm, VulnerabilityForm, ControlForm, RiskForm, TreatmentForm, ResidualForm, IncidentForm
from utils import KPI, severity_rank
from reports import build_risk_register_pdf

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "riskguard.sqlite3")


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    CSRFProtect(app)

    with app.app_context():
        db.create_all()

    @app.route("/")
    def index():
        risks = RiskScenario.query.all()
        total = len(risks)

        high_or_crit = [r for r in risks if r.inherent_level() in ("Alto", "Critico")]
        with_plan = [r for r in high_or_crit if r.treatment_strategy and r.responsible and r.due_date]
        kpi_plan = pct(len(with_plan), len(high_or_crit))

        due_actions = [r for r in risks if r.due_date]
        on_time = [r for r in due_actions if r.status == "Implementado" and r.completed_at and r.completed_at <= r.due_date]
        kpi_ontime = pct(len(on_time), len(due_actions))

        reduced = [r for r in risks if r.residual_level() and severity_rank(r.residual_level()) < severity_rank(r.inherent_level())]
        accepted = [r for r in risks if r.treatment_strategy == "Aceptar" and r.acceptance_justification and r.acceptance_approved_by]
        incidents_count = sum(len(r.incidents) for r in risks)

        kpis = [
            KPI("Riesgos (total)", str(total)),
            KPI("% Alto/Critico con plan", kpi_plan, "Plan = estrategia + responsable + fecha limite"),
            KPI("% acciones a tiempo", kpi_ontime, "Implementado y dentro del plazo"),
            KPI("Riesgos que bajaron de categoria", str(len(reduced))),
            KPI("Riesgos aceptados con justificacion", str(len(accepted))),
            KPI("Incidentes registrados", str(incidents_count)),
        ]

        # Top riesgos (orden por severidad inherente)
        top = sorted(risks, key=lambda r: (severity_rank(r.inherent_level()), r.inherent_score()), reverse=True)[:8]

        return render_template("index.html", kpis=kpis, top_risks=top)

    @app.route("/methodology")
    def methodology():
        return render_template("methodology.html", title="Metodologia")

    # ------------------- Activos -------------------
    @app.route("/assets")
    def assets_list():
        assets = Asset.query.order_by(Asset.created_at.desc()).all()
        return render_template("assets/list.html", assets=assets)

    @app.route("/assets/new", methods=["GET", "POST"])
    def assets_new():
        form = AssetForm()
        if form.validate_on_submit():
            asset = Asset(
                name=form.name.data,
                asset_type=form.asset_type.data,
                process=form.process_area.data,
                owner=form.owner.data,
                description=form.description.data,
                confidentiality=form.confidentiality.data,
                integrity=form.integrity.data,
                availability=form.availability.data,
            )
            db.session.add(asset)
            db.session.commit()
            flash("Activo creado", "success")
            return redirect(url_for("assets_list"))
        return render_template("assets/form.html", form=form, title="Nuevo activo")

    @app.route("/assets/<int:asset_id>/edit", methods=["GET", "POST"])
    def assets_edit(asset_id: int):
        asset = Asset.query.get_or_404(asset_id)
        form = AssetForm(obj=asset)
        # WTForms only auto-fills fields that match model attribute names.
        # Our form uses process_area to avoid colliding with Form.process().
        if request.method == "GET":
            form.process_area.data = asset.process

        if form.validate_on_submit():
            asset.name = form.name.data
            asset.asset_type = form.asset_type.data
            asset.process = form.process_area.data
            asset.owner = form.owner.data
            asset.description = form.description.data
            asset.confidentiality = form.confidentiality.data
            asset.integrity = form.integrity.data
            asset.availability = form.availability.data

            db.session.commit()
            flash("Activo actualizado", "success")
            return redirect(url_for("assets_list"))
        return render_template("assets/form.html", form=form, title="Editar activo")

    @app.route("/assets/<int:asset_id>/delete", methods=["POST"])
    def assets_delete(asset_id: int):
        asset = Asset.query.get_or_404(asset_id)
        db.session.delete(asset)
        db.session.commit()
        flash("Activo eliminado", "info")
        return redirect(url_for("assets_list"))

    # ------------------- Catalogos -------------------
    @app.route("/threats")
    def threats_list():
        items = Threat.query.order_by(Threat.id.desc()).all()
        return render_template("catalog/list.html", items=items, kind="threats", title="Amenazas")

    @app.route("/threats/new", methods=["GET", "POST"])
    def threats_new():
        form = ThreatForm()
        if form.validate_on_submit():
            item = Threat(name=form.name.data, category=form.category.data, description=form.description.data)
            db.session.add(item)
            db.session.commit()
            flash("Amenaza creada", "success")
            return redirect(url_for("threats_list"))
        return render_template("catalog/form.html", form=form, title="Nueva amenaza")

    @app.route("/threats/<int:item_id>/edit", methods=["GET", "POST"])
    def threats_edit(item_id: int):
        item = Threat.query.get_or_404(item_id)
        form = ThreatForm(obj=item)
        if form.validate_on_submit():
            form.populate_obj(item)
            db.session.commit()
            flash("Amenaza actualizada", "success")
            return redirect(url_for("threats_list"))
        return render_template("catalog/form.html", form=form, title="Editar amenaza")

    @app.route("/threats/<int:item_id>/delete", methods=["POST"])
    def threats_delete(item_id: int):
        item = Threat.query.get_or_404(item_id)
        db.session.delete(item)
        db.session.commit()
        flash("Amenaza eliminada", "info")
        return redirect(url_for("threats_list"))

    @app.route("/vulnerabilities")
    def vulnerabilities_list():
        items = Vulnerability.query.order_by(Vulnerability.id.desc()).all()
        return render_template("catalog/list.html", items=items, kind="vulnerabilities", title="Vulnerabilidades")

    @app.route("/vulnerabilities/new", methods=["GET", "POST"])
    def vulnerabilities_new():
        form = VulnerabilityForm()
        if form.validate_on_submit():
            item = Vulnerability(name=form.name.data, category=form.category.data, description=form.description.data)
            db.session.add(item)
            db.session.commit()
            flash("Vulnerabilidad creada", "success")
            return redirect(url_for("vulnerabilities_list"))
        return render_template("catalog/form.html", form=form, title="Nueva vulnerabilidad")

    @app.route("/vulnerabilities/<int:item_id>/edit", methods=["GET", "POST"])
    def vulnerabilities_edit(item_id: int):
        item = Vulnerability.query.get_or_404(item_id)
        form = VulnerabilityForm(obj=item)
        if form.validate_on_submit():
            form.populate_obj(item)
            db.session.commit()
            flash("Vulnerabilidad actualizada", "success")
            return redirect(url_for("vulnerabilities_list"))
        return render_template("catalog/form.html", form=form, title="Editar vulnerabilidad")

    @app.route("/vulnerabilities/<int:item_id>/delete", methods=["POST"])
    def vulnerabilities_delete(item_id: int):
        item = Vulnerability.query.get_or_404(item_id)
        db.session.delete(item)
        db.session.commit()
        flash("Vulnerabilidad eliminada", "info")
        return redirect(url_for("vulnerabilities_list"))

    @app.route("/controls")
    def controls_list():
        items = Control.query.order_by(Control.id.desc()).all()
        return render_template("controls/list.html", items=items)

    @app.route("/controls/new", methods=["GET", "POST"])
    def controls_new():
        form = ControlForm()
        if form.validate_on_submit():
            item = Control(
                name=form.name.data,
                iso_reference=form.iso_reference.data,
                control_type=form.control_type.data,
                description=form.description.data,
            )
            db.session.add(item)
            db.session.commit()
            flash("Control creado", "success")
            return redirect(url_for("controls_list"))
        return render_template("controls/form.html", form=form, title="Nuevo control")

    @app.route("/controls/<int:item_id>/edit", methods=["GET", "POST"])
    def controls_edit(item_id: int):
        item = Control.query.get_or_404(item_id)
        form = ControlForm(obj=item)
        if form.validate_on_submit():
            form.populate_obj(item)
            db.session.commit()
            flash("Control actualizado", "success")
            return redirect(url_for("controls_list"))
        return render_template("controls/form.html", form=form, title="Editar control")

    @app.route("/controls/<int:item_id>/delete", methods=["POST"])
    def controls_delete(item_id: int):
        item = Control.query.get_or_404(item_id)
        db.session.delete(item)
        db.session.commit()
        flash("Control eliminado", "info")
        return redirect(url_for("controls_list"))

    # ------------------- Riesgos -------------------
    @app.route("/risks")
    def risks_list():
        risks = RiskScenario.query.all()
        # Ordenar por severidad inherente
        risks = sorted(risks, key=lambda r: (severity_rank(r.inherent_level()), r.inherent_score()), reverse=True)
        return render_template("risks/list.html", risks=risks)

    @app.route("/risks/new", methods=["GET", "POST"])
    def risks_new():
        form = RiskForm()
        form.asset_id.choices = [(a.id, f"{a.name} ({a.asset_type})") for a in Asset.query.order_by(Asset.name).all()]
        form.threat_id.choices = [(t.id, f"{t.name} ({t.category})") for t in Threat.query.order_by(Threat.name).all()]
        form.vulnerability_id.choices = [(v.id, f"{v.name} ({v.category})") for v in Vulnerability.query.order_by(Vulnerability.name).all()]

        if request.method == "POST" and not (form.asset_id.choices and form.threat_id.choices and form.vulnerability_id.choices):
            flash("Primero registra al menos 1 activo, 1 amenaza y 1 vulnerabilidad", "warning")

        if form.validate_on_submit():
            risk = RiskScenario(
                asset_id=form.asset_id.data,
                threat_id=form.threat_id.data,
                vulnerability_id=form.vulnerability_id.data,
                probability=int(form.probability.data),
                impact_override=int(form.impact_override.data) if form.impact_override.data else None,
                existing_controls=form.existing_controls.data,
                observations=form.observations.data,
            )
            db.session.add(risk)
            db.session.commit()
            flash("Riesgo creado", "success")
            return redirect(url_for("risks_list"))
        return render_template("risks/form.html", form=form)

    @app.route("/risks/<int:risk_id>/edit", methods=["GET", "POST"])
    def risks_edit(risk_id: int):
        risk = RiskScenario.query.get_or_404(risk_id)
        form = RiskForm()
        form.asset_id.choices = [(a.id, f"{a.name} ({a.asset_type})") for a in Asset.query.order_by(Asset.name).all()]
        form.threat_id.choices = [(t.id, f"{t.name} ({t.category})") for t in Threat.query.order_by(Threat.name).all()]
        form.vulnerability_id.choices = [(v.id, f"{v.name} ({v.category})") for v in Vulnerability.query.order_by(Vulnerability.name).all()]

        if request.method == "GET":
            form.asset_id.data = risk.asset_id
            form.threat_id.data = risk.threat_id
            form.vulnerability_id.data = risk.vulnerability_id
            form.probability.data = str(risk.probability)
            form.impact_override.data = str(risk.impact_override) if risk.impact_override is not None else ""
            form.existing_controls.data = risk.existing_controls
            form.observations.data = risk.observations

        if form.validate_on_submit():
            risk.asset_id = form.asset_id.data
            risk.threat_id = form.threat_id.data
            risk.vulnerability_id = form.vulnerability_id.data
            risk.probability = int(form.probability.data)
            risk.impact_override = int(form.impact_override.data) if form.impact_override.data else None
            risk.existing_controls = form.existing_controls.data
            risk.observations = form.observations.data
            db.session.commit()
            flash("Riesgo actualizado", "success")
            return redirect(url_for("risks_detail", risk_id=risk.id))

        return render_template("risks/edit.html", risk=risk, form=form)

    @app.route("/risks/<int:risk_id>")
    def risks_detail(risk_id: int):
        risk = RiskScenario.query.get_or_404(risk_id)
        return render_template("risks/detail.html", risk=risk)

    @app.route("/risks/<int:risk_id>/treatment", methods=["GET", "POST"])
    def risks_treatment(risk_id: int):
        risk = RiskScenario.query.get_or_404(risk_id)
        form = TreatmentForm(obj=risk)
        form.proposed_controls.choices = [(c.id, f"{c.name}" + (f" [{c.iso_reference}]" if c.iso_reference else "")) for c in Control.query.order_by(Control.name).all()]

        if request.method == "GET":
            form.proposed_controls.data = [c.id for c in risk.proposed_controls]

        if form.validate_on_submit():
            risk.treatment_strategy = form.treatment_strategy.data or None
            risk.responsible = form.responsible.data or None
            risk.due_date = form.due_date.data
            risk.status = form.status.data
            risk.acceptance_justification = form.acceptance_justification.data or None
            risk.acceptance_approved_by = form.acceptance_approved_by.data or None

            # Actualizar controles propuestos
            selected = set(form.proposed_controls.data or [])
            risk.proposed_controls = Control.query.filter(Control.id.in_(selected)).all() if selected else []

            db.session.commit()
            flash("Tratamiento guardado", "success")
            return redirect(url_for("risks_detail", risk_id=risk.id))

        return render_template("risks/treatment.html", risk=risk, form=form)

    @app.route("/risks/<int:risk_id>/residual", methods=["GET", "POST"])
    def risks_residual(risk_id: int):
        risk = RiskScenario.query.get_or_404(risk_id)
        form = ResidualForm()
        if request.method == "GET":
            form.residual_probability.data = str(risk.residual_probability) if risk.residual_probability is not None else ""
            form.residual_impact.data = str(risk.residual_impact) if risk.residual_impact is not None else ""
            form.completed_at.data = risk.completed_at
            form.last_review_at.data = risk.last_review_at.date() if risk.last_review_at else None

        if form.validate_on_submit():
            risk.residual_probability = int(form.residual_probability.data) if form.residual_probability.data else None
            risk.residual_impact = int(form.residual_impact.data) if form.residual_impact.data else None
            risk.completed_at = form.completed_at.data
            if form.last_review_at.data:
                risk.last_review_at = datetime.combine(form.last_review_at.data, datetime.min.time())
            db.session.commit()
            flash("Riesgo residual guardado", "success")
            return redirect(url_for("risks_detail", risk_id=risk.id))

        return render_template("risks/residual.html", risk=risk, form=form)

    @app.route("/risks/<int:risk_id>/delete", methods=["POST"])
    def risks_delete(risk_id: int):
        risk = RiskScenario.query.get_or_404(risk_id)
        db.session.delete(risk)
        db.session.commit()
        flash("Riesgo eliminado", "info")
        return redirect(url_for("risks_list"))

    # ------------------- Incidentes -------------------
    @app.route("/risks/<int:risk_id>/incidents/new", methods=["GET", "POST"])
    def incidents_new(risk_id: int):
        risk = RiskScenario.query.get_or_404(risk_id)
        form = IncidentForm()
        if form.validate_on_submit():
            incident = Incident(
                risk_id=risk.id,
                date=form.date.data,
                severity=form.severity.data or None,
                description=form.description.data,
            )
            db.session.add(incident)
            db.session.commit()
            flash("Incidente registrado", "success")
            return redirect(url_for("risks_detail", risk_id=risk.id))
        return render_template("incidents/form.html", risk=risk, form=form)

    @app.route("/incidents/<int:incident_id>/delete", methods=["POST"])
    def incidents_delete(incident_id: int):
        incident = Incident.query.get_or_404(incident_id)
        rid = incident.risk_id
        db.session.delete(incident)
        db.session.commit()
        flash("Incidente eliminado", "info")
        return redirect(url_for("risks_detail", risk_id=rid))

    # ------------------- Reportes -------------------
    @app.route("/reports/risk-register.pdf")
    def report_risk_register():
        risks = RiskScenario.query.all()
        pdf_path = build_risk_register_pdf(risks)
        return send_file(pdf_path, as_attachment=True, download_name="registro_riesgos.pdf")

    return app


def pct(a: int, b: int) -> str:
    if b <= 0:
        return "0%"
    return f"{round((a / b) * 100)}%"


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
