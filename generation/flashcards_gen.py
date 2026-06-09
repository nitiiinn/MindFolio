import io
import re

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether
)
from reportlab.platypus import Image as RLImage

from llm.prompt import load_flashcards_prompt


def generate_flashcards_content(router, retriever):
    """
    Use the RAG pipeline to extract content and generate Q&A flashcards.
    """
    queries = [
        "What are the most important facts, concepts, and definitions in these documents?",
        "What key processes, methods, or procedures are described?",
        "What data, results, or conclusions are most significant?",
        "What are the relationships, comparisons, or cause-and-effect connections explained?",
        "What formulas, equations, dates, or numerical data are mentioned?",
        "What examples, case studies, or real-world applications are discussed?",
    ]

    all_context = []
    for q in queries:
        context_docs = retriever.invoke(q)
        for doc in context_docs:
            content = doc.page_content.strip()
            if content and content not in all_context:
                all_context.append(content)

    combined_context = "\n\n".join(all_context)

    flashcards_prompt = load_flashcards_prompt()
    result = router.complete(
        "flashcards",
        [{
            "role": "user",
            "content": flashcards_prompt.format(content=combined_context),
        }],
    )

    # Parse Q&A pairs
    cards = _parse_flashcards(result)

    return {
        "cards": cards,
        "raw_text": result,
        "context_chunks": len(all_context),
        "model_label": router.get_model_label("flashcards"),
    }


def _parse_flashcards(raw_text):
    """Parse the LLM output into a list of {question, answer} dicts."""
    cards = []
    lines = raw_text.strip().split("\n")

    current_q = None
    current_a = None

    for line in lines:
        line = line.strip()
        if line.upper().startswith("Q:") or line.upper().startswith("Q :"):
            # Save previous card if exists
            if current_q and current_a:
                cards.append({"question": current_q, "answer": current_a})
            current_q = line.split(":", 1)[1].strip()
            current_a = None
        elif line.upper().startswith("A:") or line.upper().startswith("A :"):
            current_a = line.split(":", 1)[1].strip()
        elif current_a is not None and line:
            # Continuation of answer
            current_a += " " + line
        elif current_q is not None and current_a is None and line:
            # Continuation of question
            current_q += " " + line

    # Don't forget the last card
    if current_q and current_a:
        cards.append({"question": current_q, "answer": current_a})

    return cards


def build_flashcards_pdf(flashcards_data):
    """
    Build a flashcard-style PDF using ReportLab.
    Each page has 2 flashcards. Returns the PDF as a BytesIO stream.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        topMargin=40, bottomMargin=40,
        leftMargin=50, rightMargin=50
    )

    styles = getSampleStyleSheet()

    # Custom styles
    cover_title = ParagraphStyle(
        "FCTitle", parent=styles["Title"],
        fontSize=30, textColor=colors.HexColor("#1e1b4b"),
        spaceAfter=8, alignment=TA_CENTER,
        fontName="Helvetica-Bold",
    )
    cover_sub = ParagraphStyle(
        "FCSub", parent=styles["Normal"],
        fontSize=12, textColor=colors.HexColor("#7c3aed"),
        alignment=TA_CENTER, spaceAfter=20,
    )
    card_number_style = ParagraphStyle(
        "CardNum", parent=styles["Normal"],
        fontSize=7, textColor=colors.HexColor("#9ca3af"),
        alignment=TA_CENTER, spaceAfter=0, spaceBefore=0,
    )
    question_style = ParagraphStyle(
        "FCQuestion", parent=styles["Normal"],
        fontSize=11, textColor=colors.HexColor("#1e1b4b"),
        fontName="Helvetica-Bold",
        leading=14, alignment=TA_CENTER,
        spaceBefore=2, spaceAfter=2,
    )
    answer_style = ParagraphStyle(
        "FCAnswer", parent=styles["Normal"],
        fontSize=10, textColor=colors.HexColor("#374151"),
        leading=13, alignment=TA_CENTER,
        spaceBefore=2, spaceAfter=2,
    )

    elements = []
    cards = flashcards_data.get("cards", [])

    # ── Cover Page ──
    elements.append(Spacer(1, 50))


    elements.append(Paragraph("🃏 Study Flashcards", cover_title))
    elements.append(Paragraph(
        "AI-Generated Q&amp;A Cards from Your Documents", cover_sub
    ))
    elements.append(HRFlowable(
        width="50%", thickness=2,
        color=colors.HexColor("#7c3aed"),
        spaceBefore=10, spaceAfter=10,
        hAlign="CENTER",
    ))

    info_data = [
        ["Total Cards", str(len(cards))],
        ["Source Chunks", str(flashcards_data.get("context_chunks", "N/A"))],
        ["Generated by", "PDF Intelligence Hub"],
        ["Model", flashcards_data.get("model_label", "N/A")],
    ]
    info_table = Table(info_data, colWidths=[120, 200])
    info_table.setStyle(TableStyle([
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#6b7280")),
        ("TEXTCOLOR", (1, 0), (1, -1), colors.HexColor("#1f2937")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(info_table)
    elements.append(PageBreak())

    # ── Flashcard Pages (4 cards per page) ──
    # Alternating color schemes for visual variety
    color_pairs = [
        ("#eef2ff", "#4338ca", "#f5f3ff"),   # Indigo
        ("#ecfdf5", "#065f46", "#f0fdf4"),   # Emerald
        ("#fef3c7", "#92400e", "#fffbeb"),   # Amber
        ("#fce7f3", "#9d174d", "#fdf2f8"),   # Pink
        ("#e0e7ff", "#3730a3", "#eef2ff"),   # Blue
        ("#f3e8ff", "#6b21a8", "#faf5ff"),   # Purple
    ]

    page_width = letter[0] - 100  # account for margins
    card_width = page_width

    for i in range(0, len(cards), 4):
        page_cards = cards[i:i + 4]

        for j, card in enumerate(page_cards):
            card_idx = i + j
            bg_color, accent_color, q_bg = color_pairs[card_idx % len(color_pairs)]

            # Clean text for XML compatibility
            q_text = card["question"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            a_text = card["answer"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

            # Card number
            elements.append(Paragraph(
                f"Card {card_idx + 1} of {len(cards)}", card_number_style
            ))
            elements.append(Spacer(1, 2))

            # Question box
            q_content = [[
                Paragraph("❓ QUESTION", ParagraphStyle(
                    "QLabel", fontSize=7, textColor=colors.HexColor(accent_color),
                    fontName="Helvetica-Bold", alignment=TA_CENTER, spaceAfter=2,
                )),
            ], [
                Paragraph(q_text, question_style),
            ]]
            q_table = Table(q_content, colWidths=[card_width])
            q_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(q_bg)),
                ("BOX", (0, 0), (-1, -1), 2, colors.HexColor(accent_color)),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("ROUNDEDCORNERS", [8, 8, 0, 0]),
            ]))
            elements.append(q_table)

            # Answer box
            a_content = [[
                Paragraph("✅ ANSWER", ParagraphStyle(
                    "ALabel", fontSize=7, textColor=colors.HexColor("#059669"),
                    fontName="Helvetica-Bold", alignment=TA_CENTER, spaceAfter=2,
                )),
            ], [
                Paragraph(a_text, answer_style),
            ]]
            a_table = Table(a_content, colWidths=[card_width])
            a_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(bg_color)),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#d1d5db")),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("ROUNDEDCORNERS", [0, 0, 8, 8]),
            ]))
            elements.append(a_table)
            elements.append(Spacer(1, 8))

        # Page break after every 4 cards (except last page)
        if i + 4 < len(cards):
            elements.append(PageBreak())

    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer
