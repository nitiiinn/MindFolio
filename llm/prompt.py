from langchain_core.prompts import PromptTemplate


def load_prompt():

    prompt = PromptTemplate(
        template="""
You are a helpful AI assistant.

Answer the question ONLY from the provided context.

Query:
{query}

Context:
{content}

Answer:
""",
        input_variables=['query', 'content']
    )

    return prompt


def load_notes_prompt():
    """Prompt that instructs the LLM to generate structured study notes."""

    prompt = PromptTemplate(
        template="""You are an expert study-notes creator. From the provided context, create highly detailed, extensive, and well-structured study notes (also known as briefing notes).

IMPORTANT: Do not make the notes too short. Provide thorough explanations, substantial details, and deep insights for every section. Each concept and definition should have a detailed 2-3 sentence explanation. Ensure you extract as much valuable information as possible.

OUTPUT FORMAT (follow exactly):
## MAIN TOPICS
- List all the main topics and themes covered in detail

## KEY CONCEPTS
- Concept 1: Detailed explanation covering nuances and importance (2-3 sentences)
- Concept 2: Detailed explanation covering nuances and importance (2-3 sentences)
(list all important concepts with substantial depth)

## IMPORTANT DEFINITIONS
- Term 1: Comprehensive definition
- Term 2: Comprehensive definition
(list all key terms and comprehensive definitions)

## SUMMARY POINTS
- Point 1: Detailed takeaway
- Point 2: Detailed takeaway
(list the most important takeaways expansively)

## FORMULAS & DATA (if any)
- Formula/data point 1 with full context
- Formula/data point 2 with full context

Context:
{content}

Detailed Study Notes:""",
        input_variables=['content']
    )

    return prompt


def load_report_prompt():
    """Prompt that instructs the LLM to generate a professional report."""

    prompt = PromptTemplate(
        template="""You are an expert report writer. From the provided context, create a professional, detailed report.

OUTPUT FORMAT (follow exactly):
## EXECUTIVE SUMMARY
Write a concise executive summary (2-3 paragraphs).

## KEY FINDINGS
- Finding 1: Description
- Finding 2: Description
(list all significant findings)

## DETAILED ANALYSIS
Provide a thorough analysis of the content, organized by topic. Use paragraphs, not just bullet points.

## DATA & STATISTICS (if any)
- Data point 1
- Data point 2

## CONCLUSIONS
Write clear conclusions based on the analysis.

## RECOMMENDATIONS
- Recommendation 1
- Recommendation 2

Context:
{content}

Professional Report:""",
        input_variables=['content']
    )

    return prompt


def load_flashcards_prompt():
    """Prompt that instructs the LLM to generate Q&A flashcards."""

    prompt = PromptTemplate(
        template="""You are an expert educator. From the provided context, create study flashcards as question-answer pairs. Create between 8 and 15 flashcards covering the most important information.

OUTPUT FORMAT (follow EXACTLY — each card must use this format):
Q: [Question text here]
A: [Answer text here]

Q: [Question text here]
A: [Answer text here]

Rules:
- Each question should test understanding of a key concept
- Answers should be concise but complete (1-3 sentences)
- Cover diverse topics from the content
- Include both factual recall and conceptual understanding questions
- Do NOT number the cards
- Separate each Q/A pair with a blank line

Context:
{content}

Flashcards:""",
        input_variables=['content']
    )

    return prompt