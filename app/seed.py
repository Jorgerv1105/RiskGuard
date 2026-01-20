from __future__ import annotations

from app import create_app
from models import db, Asset, Threat, Vulnerability, Control, RiskScenario


def run():
    app = create_app()
    with app.app_context():
        # No re-seed if already has data
        if Asset.query.first():
            print("DB ya tiene datos. Nada que hacer.")
            return

        # Activos
        a1 = Asset(name="Base de datos clientes", asset_type="Datos", process="Ventas", owner="TI", confidentiality=3, integrity=3, availability=2, description="Contiene datos personales y de facturacion")
        a2 = Asset(name="Servidor web publico", asset_type="Servicio", process="Marketing", owner="TI", confidentiality=2, integrity=2, availability=3, description="Portal web corporativo expuesto a Internet")

        # Amenazas
        t1 = Threat(name="Acceso no autorizado", category="Externa", description="Ataques de fuerza bruta, credenciales robadas")
        t2 = Threat(name="Inyeccion SQL", category="Externa", description="Explotacion de consultas no parametrizadas")

        # Vulnerabilidades
        v1 = Vulnerability(name="Contrasenas debiles", category="Organizacional", description="Politica de contrasenas no aplicada")
        v2 = Vulnerability(name="Falta de validacion de entradas", category="Tecnologica", description="Campos sin sanitizar")

        # Controles (referencia ISO puede ser ajustada por el grupo)
        c1 = Control(name="Autenticacion multifactor", iso_reference="ISO 27002:2022 - Gestion de accesos", control_type="Preventivo", description="MFA para cuentas privilegiadas")
        c2 = Control(name="Validacion y sanitizacion", iso_reference="ISO 27002:2022 - Desarrollo seguro", control_type="Preventivo", description="Validar entradas y usar consultas parametrizadas")
        c3 = Control(name="Backups y restauracion probada", iso_reference="ISO 27002:2022 - Respaldo", control_type="Correctivo", description="Copias y pruebas de recuperacion")

        db.session.add_all([a1, a2, t1, t2, v1, v2, c1, c2, c3])
        db.session.commit()

        # Riesgos
        r1 = RiskScenario(asset_id=a1.id, threat_id=t1.id, vulnerability_id=v1.id, probability=4, existing_controls="Control de acceso basico", observations="Reforzar controles y capacitar.")
        r1.treatment_strategy = "Mitigar"
        r1.proposed_controls = [c1]
        r1.responsible = "Analista de seguridad"
        r1.status = "En progreso"

        r2 = RiskScenario(asset_id=a2.id, threat_id=t2.id, vulnerability_id=v2.id, probability=5, existing_controls="WAF basico", observations="Corregir codigo y monitorear.")
        r2.treatment_strategy = "Mitigar"
        r2.proposed_controls = [c2]
        r2.responsible = "DevOps"
        r2.status = "Pendiente"

        db.session.add_all([r1, r2])
        db.session.commit()

        print("Datos de ejemplo creados.")


if __name__ == "__main__":
    run()
