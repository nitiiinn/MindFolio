import io
import re

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable
)
from reportlab.platypus import Image as RLImage

from llm.prompt import load_quiz_prompt


def generate_quiz_content(router, retriever):
    """
    Use the RAG pipeline to extract content and generate an MCQ Quiz.
    """
    queries = [
        "What are the most important facts, dates, and names mentioned?",
        "What key concepts and definitions are crucial to understand?",
        "What processes, methodologies, or sequences are described?",
        "What are the main arguments, conclusions, or takeaways?",
    ]

    all_context = []
    for q in queries:
        context_docs = retriever.invoke(q)
        for doc in context_docs:
            content = doc.page_content.strip()
            if content and content not in all_context:
                all_context.append(content)

    combined_context = "\n\n".join(all_context)

    quiz_prompt = load_quiz_prompt()
    result = router.complete(
        "quiz_generation",
        [{
            "role": "user",
            "content": quiz_prompt.format(content=combined_context),
        }],
    )

    return {
        "raw_text": result,
        "context_chunks": len(all_context),
        "model_label": router.get_model_label("quiz_generation"),
    }


def _parse_quiz(raw_text):
    """Parse the LLM output into a structured list of questions."""
    questions = []
    current_q = None
    
    for line in raw_text.split('\n'):
        line = line.strip()
        if not line:
            continue
            
        # Match question start like "**Q1. text**" or "Q1. text"
        q_match = re.match(r'^\*?\*?Q\d+\.?\s*(.*?)\*?\*?$', line)
        if q_match:
            if current_q and 'correct' in current_q:
                questions.append(current_q)
            current_q = {
                'question': q_match.group(1).strip(),
                'options': [],
                'correct': '',
                'explanation': ''
            }
        elif current_q is not None:
            if line.startswith('A)') or line.startswith('B)') or line.startswith('C)') or line.startswith('D)'):
                current_q['options'].append(line)
            elif 'Correct Answer' in line or 'Correct' in line:
                # Extract just the letter (A, B, C, D)
                match = re.search(r'([A-D])', line)
                if match:
                    current_q['correct'] = match.group(1)
            elif 'Explanation' in line:
                current_q['explanation'] = line.split(':', 1)[-1].strip() if ':' in line else line.replace('**Explanation**', '').strip()
            elif not current_q['options'] and not 'Correct' in line and not 'Explanation' in line:
                # Continuation of multi-line question
                current_q['question'] += ' ' + line
            elif current_q['options'] and current_q['correct'] and current_q['explanation']:
                # Continuation of explanation
                current_q['explanation'] += ' ' + line
                
    if current_q and 'correct' in current_q:
        questions.append(current_q)
        
    return questions


def build_quiz_pdf(quiz_data):
    """
    Build an interactive MCQ Quiz PDF using ReportLab.
    Returns the PDF as a BytesIO stream.
    Questions first, then an Answer Key at the end.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        topMargin=50, bottomMargin=50,
        leftMargin=60, rightMargin=60
    )

    styles = getSampleStyleSheet()

    # Custom styles
    cover_title_style = ParagraphStyle(
        "QuizCoverTitle", parent=styles["Title"],
        fontSize=32, textColor=colors.HexColor("#0f172a"),
        spaceAfter=8, alignment=TA_CENTER,
        fontName="Helvetica-Bold",
    )
    cover_subtitle_style = ParagraphStyle(
        "QuizCoverSub", parent=styles["Normal"],
        fontSize=13, textColor=colors.HexColor("#4f46e5"),
        alignment=TA_CENTER, spaceAfter=20,
    )
    question_style = ParagraphStyle(
        "QuizQuestion", parent=styles["Normal"],
        fontSize=12, textColor=colors.HexColor("#1e1b4b"),
        spaceBefore=12, spaceAfter=8,
        fontName="Helvetica-Bold",
        leading=16,
    )
    option_style = ParagraphStyle(
        "QuizOption", parent=styles["Normal"],
        fontSize=11, textColor=colors.HexColor("#374151"),
        leftIndent=20, spaceAfter=4,
        leading=14,
    )
    answer_header_style = ParagraphStyle(
        "AnswerHeader", parent=styles["Heading1"],
        fontSize=20, textColor=colors.HexColor("#059669"),
        spaceBefore=20, spaceAfter=15,
        fontName="Helvetica-Bold",
        alignment=TA_CENTER,
    )
    answer_text_style = ParagraphStyle(
        "AnswerText", parent=styles["Normal"],
        fontSize=10.5, textColor=colors.HexColor("#1f2937"),
        leading=14, spaceAfter=10,
    )

    elements = []

    # ── Cover Page ──
    elements.append(Spacer(1, 40))


    elements.append(Paragraph("🎯 MCQ Practice Quiz", cover_title_style))
    elements.append(Paragraph(
        "Test your knowledge before the exam", cover_subtitle_style
    ))

    elements.append(HRFlowable(
        width="50%", thickness=3,
        color=colors.HexColor("#4f46e5"),
        spaceBefore=10, spaceAfter=10,
        hAlign="CENTER",
    ))

    questions = _parse_quiz(quiz_data["raw_text"])

    info_data = [
        ["Total Questions", str(len(questions))],
        ["Generated by", "PDF Intelligence Hub"],
        ["Model", quiz_data.get("model_label", "N/A")],
    ]
    info_table = Table(info_data, colWidths=[120, 220])
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

    # ── Questions Section ──
    for i, q in enumerate(questions, 1):
        # Format the question properly for XML
        q_text = q['question'].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        elements.append(Paragraph(f"{i}. {q_text}", question_style))
        
        for opt in q['options']:
            opt_text = opt.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            elements.append(Paragraph(opt_text, option_style))
            
        elements.append(Spacer(1, 8))

    elements.append(PageBreak())
    
    # ── Answer Key Section ──
    elements.append(Paragraph("✅ Answer Key & Explanations", answer_header_style))
    elements.append(HRFlowable(
        width="100%", thickness=2,
        color=colors.HexColor("#10b981"),
        spaceBefore=5, spaceAfter=15,
    ))
    
    for i, q in enumerate(questions, 1):
        correct_escaped = str(q['correct']).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        explanation_escaped = str(q['explanation']).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        ans_text = f"<b>Q{i}:</b> <b>{correct_escaped}</b> — {explanation_escaped}"
        
        # Use a table to give each answer a slight background
        ans_data = [[Paragraph(ans_text, answer_text_style)]]
        ans_table = Table(ans_data, colWidths=[doc.width])
        ans_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f0fdf4")),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("ROUNDEDCORNERS", [4, 4, 4, 4]),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#a7f3d0")),
        ]))
        elements.append(ans_table)
        elements.append(Spacer(1, 8))

    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer
