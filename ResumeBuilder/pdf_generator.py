"""
Module 5: Generate PDF
-----------------------
Builds a formatted resume PDF from the data stored in the database,
using ReportLab. Saves the file into /pdf and returns the path so
app.py can send it to the user for download (Module 6).
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable
)

PDF_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pdf")
os.makedirs(PDF_DIR, exist_ok=True)


def _styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="NameHeading", fontSize=22, leading=26, textColor=colors.HexColor("#1a1a2e"),
        spaceAfter=2, fontName="Helvetica-Bold"
    ))
    styles.add(ParagraphStyle(
        name="ContactLine", fontSize=10, textColor=colors.HexColor("#555555"),
        spaceAfter=10
    ))
    styles.add(ParagraphStyle(
        name="SectionHeading", fontSize=13, textColor=colors.HexColor("#16213e"),
        spaceBefore=12, spaceAfter=4, fontName="Helvetica-Bold"
    ))
    styles.add(ParagraphStyle(
        name="Body", fontSize=10, leading=14, textColor=colors.HexColor("#222222")
    ))
    styles.add(ParagraphStyle(
        name="ItemTitle", fontSize=10.5, leading=14, fontName="Helvetica-Bold"
    ))
    return styles


def generate_resume_pdf(resume_id, data):
    """
    data: dict returned by db.get_resume_data(resume_id)
    Returns: absolute file path of the generated PDF
    """
    file_path = os.path.join(PDF_DIR, f"resume_{resume_id}.pdf")
    doc = SimpleDocTemplate(
        file_path, pagesize=A4,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm,
        leftMargin=1.8 * cm, rightMargin=1.8 * cm
    )
    styles = _styles()
    story = []

    personal = data.get("personal")

    # ---- Header: photo + name/contact ----
    name = personal["full_name"] if personal and personal["full_name"] else "Your Name"
    email = personal["email"] if personal else ""
    phone = personal["phone"] if personal else ""
    address = personal["address"] if personal else ""
    summary = personal["summary"] if personal else ""
    photo_path = personal["photo"] if personal and personal["photo"] else None

    header_cells = []
    text_block = [
        Paragraph(name, styles["NameHeading"]),
        Paragraph(" | ".join([v for v in [email, phone, address] if v]), styles["ContactLine"]),
    ]
    if photo_path and os.path.exists(photo_path):
        img = Image(photo_path, width=2.6 * cm, height=2.6 * cm)
        table = Table([[text_block, img]], colWidths=[13 * cm, 3 * cm])
        table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ]))
        story.append(table)
    else:
        story.extend(text_block)

    story.append(HRFlowable(width="100%", color=colors.HexColor("#cccccc"), thickness=1))

    if summary:
        story.append(Paragraph("Summary", styles["SectionHeading"]))
        story.append(Paragraph(summary, styles["Body"]))

    # ---- Education ----
    if data.get("education"):
        story.append(Paragraph("Education", styles["SectionHeading"]))
        for row in data["education"]:
            line = f"{row['degree'] or ''} — {row['institution'] or ''}"
            meta = " | ".join([v for v in [row["year"], row["grade"]] if v])
            story.append(Paragraph(line, styles["ItemTitle"]))
            if meta:
                story.append(Paragraph(meta, styles["Body"]))
            story.append(Spacer(1, 4))

    # ---- Skills ----
    if data.get("skills"):
        story.append(Paragraph("Skills", styles["SectionHeading"]))
        skill_list = ", ".join([s["skill_name"] for s in data["skills"] if s["skill_name"]])
        story.append(Paragraph(skill_list, styles["Body"]))

    # ---- Projects ----
    if data.get("projects"):
        story.append(Paragraph("Projects", styles["SectionHeading"]))
        for row in data["projects"]:
            story.append(Paragraph(row["title"] or "", styles["ItemTitle"]))
            if row["description"]:
                story.append(Paragraph(row["description"], styles["Body"]))
            meta = " | ".join([v for v in [row["tech_used"], row["link"]] if v])
            if meta:
                story.append(Paragraph(meta, styles["Body"]))
            story.append(Spacer(1, 4))

    # ---- Experience / Internships ----
    if data.get("experience"):
        story.append(Paragraph("Experience / Internships", styles["SectionHeading"]))
        for row in data["experience"]:
            title = f"{row['role'] or ''} — {row['company'] or ''}"
            story.append(Paragraph(title, styles["ItemTitle"]))
            if row["duration"]:
                story.append(Paragraph(row["duration"], styles["Body"]))
            if row["description"]:
                story.append(Paragraph(row["description"], styles["Body"]))
            story.append(Spacer(1, 4))

    # ---- Certifications ----
    if data.get("certifications"):
        story.append(Paragraph("Certifications", styles["SectionHeading"]))
        for row in data["certifications"]:
            line = f"{row['name'] or ''} — {row['issuer'] or ''} ({row['year'] or ''})"
            story.append(Paragraph(line, styles["Body"]))

    # ---- Achievements ----
    if data.get("achievements"):
        story.append(Paragraph("Achievements", styles["SectionHeading"]))
        for row in data["achievements"]:
            story.append(Paragraph(f"• {row['description']}", styles["Body"]))

    doc.build(story)
    return file_path
