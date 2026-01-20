from __future__ import annotations

import os
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from models import RiskScenario


def build_risk_register_pdf(risks: list[RiskScenario]) -> str:
    """Genera un PDF con el registro de riesgos.

    Nota: antes se dibujaba “a mano” con drawString() y los textos largos
    se montaban encima de otras columnas. Ahora usamos Table + Paragraph
    para que el texto haga wrap dentro de cada celda.
    """
    base_dir = os.path.abspath(os.path.dirname(__file__))
    out_dir = os.path.join(base_dir, "..", "exports")
    os.makedirs(out_dir, exist_ok=True)

    filename = f"registro_riesgos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    out_path = os.path.join(out_dir, filename)

    # Usamos landscape para que entren mejor todas las columnas.
    pagesize = landscape(letter)
    doc = SimpleDocTemplate(
        out_path,
        pagesize=pagesize,
        leftMargin=0.5 * inch,
        rightMargin=0.5 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.5 * inch,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "RGTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=16,
        spaceAfter=10,
    )
    meta_style = ParagraphStyle(
        "RGMeta",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        spaceAfter=10,
    )
    header_style = ParagraphStyle(
        "RGHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=9,
        alignment=TA_CENTER,
    )
    cell_style = ParagraphStyle(
        "RGCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=9,
    )

    headers = ["ID", "Activo", "Amenaza", "Vuln.", "P", "I", "Score", "Nivel", "Estrategia", "Estado"]
    # Anchos en inches (landscape letter). Ajustados para que sumen aprox. 9.6 in.
    col_widths = [0.4, 2.0, 1.6, 1.6, 0.35, 0.35, 0.55, 0.8, 1.2, 0.75]

    # Sort by score desc
    risks_sorted = sorted(risks, key=lambda r: r.inherent_score(), reverse=True)

    # Construimos la tabla con Paragraph para que el texto haga wrap.
    data: list[list[Paragraph]] = [[Paragraph(h, header_style) for h in headers]]
    for r in risks_sorted:
        vals = [
            str(r.id),
            r.asset.name,
            r.threat.name,
            r.vulnerability.name,
            str(r.probability),
            str(r.impact_value()),
            str(r.inherent_score()),
            r.inherent_level(),
            r.treatment_strategy or "-",
            r.status,
        ]
        data.append([Paragraph(str(v), cell_style) for v in vals])

    table = Table(data, colWidths=[w * inch for w in col_widths], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )

    elements = [
        Paragraph("Registro de Riesgos - RiskGuard", title_style),
        Paragraph(f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M')}", meta_style),
        Spacer(1, 0.1 * inch),
        table,
    ]

    doc.build(elements)
    return out_path
