"""
prompt.py — All the AI prompt templates used in the application.

Each function returns a SimplePrompt object with a template string.
Templates use {placeholders} that get filled in with actual data at runtime.

Prompts in this file:
  - load_prompt()                → Q&A (chat with your PDF)
  - load_notes_prompt()          → Study notes generation
  - load_quiz_prompt()           → MCQ quiz generation
  - load_flashcards_prompt()     → Flashcard generation
  - load_query_rewriter_prompt() → Rewrite queries for better search
  - load_verifier_prompt()       → Check answers for hallucinations
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class SimplePrompt:
    """A simple wrapper that holds a prompt template string.

    Usage:
        prompt = SimplePrompt(template="Hello {name}!")
        result = prompt.format(name="Nitin")  # → "Hello Nitin!"
    """
    template: str

    def format(self, **kwargs) -> str:
        return self.template.format(**kwargs)



def load_prompt():
    return SimplePrompt(
        template="""
You are a helpful AI assistant.

Answer the question ONLY from the provided context.

Previous Conversation Summary:
{history_summary}

Query:
{query}

Context:
{content}

Answer:
""".strip()
    )


def load_notes_prompt():
    """Prompt that instructs the model to generate detailed study notes with examples."""

    return SimplePrompt(
        template="""You are an expert professor creating exceptionally long, comprehensive, and highly detailed study notes from the provided text. Your goal is to write notes that read like a full textbook chapter or detailed lecture transcript. You must provide deep, exhaustive explanations and rich context.

RULES:
- **Length & Depth**: Do NOT just provide short definitions, summaries, or brief bullet points. You must write extensively. Expand on every single concept with fully fleshed-out paragraphs that explain the "why", "how", and "what if".
- **Examples**: For EVERY major concept, definition, or theory, you MUST provide at least one concrete, real-world example to ensure complete concept understanding. Explicitly label them with "Example:".
- **Structure**: Organize the notes logically with clear `# Main Headings` and `## Subheadings`.
- **Thoroughness**: Leave no stone unturned. Cover all nuances, edge cases, and background details mentioned in the text.
- **Formatting**: Bold important terms using **term** syntax, embedded within rich, lengthy explanations.
- **Processes**: If there are steps, processes, or chronological events, explain each step in immense detail.

OUTPUT FORMAT:
# [Main Topic Title]
Write a very comprehensive overview of the main topic here, spanning multiple long paragraphs to thoroughly set the context and introduce the core ideas.

## [Subtopic 1]
Write deep, extensive, paragraph-based explanations of this subtopic. Connect ideas smoothly. 
Provide explicit examples for the concepts discussed here (e.g., "**Example:** ...").
(Include as many long paragraphs as needed to exhaustively cover the subtopic).

## [Subtopic 2]
(Continue with incredibly detailed explanations, breaking down complex ideas into understandable, very long-form content with examples.)

(Cover ALL information in the text using this exhaustively detailed, expansive format. Do not summarize; expand and elaborate.)

Context:
{content}

Extensive and Comprehensive Study Notes:"""
    )


def load_quiz_prompt():
    """Prompt that instructs the model to generate a multiple-choice quiz."""

    return SimplePrompt(
        template="""You are an expert educator. From the provided context, create a comprehensive Multiple Choice Question (MCQ) quiz to test a student's knowledge. Target 15-25 questions covering all key topics, definitions, facts, and concepts.

OUTPUT FORMAT (follow exactly for each question):

**Q1. [Question text here]**
A) [Option A]
B) [Option B]
C) [Option C]
D) [Option D]
**Correct Answer**: [Letter]
**Explanation**: [Brief 1-2 sentence explanation of why the answer is correct and others are wrong]

Rules:
- Generate 15-25 questions.
- Each question MUST have exactly 4 options (A, B, C, D).
- Only ONE option can be correct.
- Include a mix of easy, medium, and hard questions.
- Test facts, definitions, conceptual understanding, and applications.
- Provide a clear, brief explanation for the correct answer.
- Do NOT include any introductory or concluding remarks. Just output the questions in the exact format requested.

Context:
{content}

MCQ Quiz:"""
    )


def load_flashcards_prompt():
    """Prompt that instructs the model to generate many Q&A flashcards."""

    return SimplePrompt(
        template="""You are an expert educator. From the provided context, create as many study flashcards as possible. Target 20-30 flashcards covering every important piece of information.

OUTPUT FORMAT (follow exactly - each card must use this format):
Q: [Question text here]
A: [Answer text here]

Q: [Question text here]
A: [Answer text here]

Rules:
- Generate 20-30 flashcards — be thorough and cover everything
- Mix question types: definitions, factual recall, conceptual, comparisons, and true/false
- Answers should be concise (1-2 sentences max)
- Cover EVERY topic, subtopic, and key detail from the content
- Include questions on: terms, processes, formulas, dates, relationships, causes/effects
- Do NOT number the cards
- Separate each Q/A pair with a blank line
- Do NOT repeat similar questions

Context:
{content}

Flashcards:"""
    )


def load_query_rewriter_prompt():
    """Prompt that rewrites a student question into standalone search queries."""

    return SimplePrompt(
        template="""You are a query rewriting assistant for a RAG system.

Rewrite the student's question into 3 concise standalone search queries that will retrieve the best supporting chunks from a vector database.

Rules:
- Preserve the original meaning.
- Resolve any pronouns (e.g., "it", "they", "this") using the Chat History.
- Include important entities, topics, or constraints from the question.
- Keep each rewrite short and search-oriented.
- Do not add commentary, numbering, bullets, or quotes.
- Output exactly 3 lines, one query per line.

Chat History:
{chat_history}

Student Question:
{query}

Rewritten Queries:"""
    )


def load_verifier_prompt():
    """Prompt that audits an answer against retrieved context."""

    return SimplePrompt(
        template="""You are a factual verifier for a study assistant.

Audit the draft answer against the retrieved context only. If any part of the draft answer is unsupported, fix it so the final answer is fully grounded in the context.

Return valid JSON only using this schema:
{{
  "answer": "corrected grounded answer",
  "hallucination_score": 0,
  "reason": "short explanation of what was corrected or confirmed"
}}

Scoring guidance:
- 0 means the draft answer is fully grounded in the context.
- 100 means the draft answer is almost entirely unsupported.

Student Question:
{query}

Retrieved Context:
{content}

Draft Answer:
{answer}
"""
    )

def load_history_summarizer_prompt():
    """Prompt that summarizes chat history into a concise paragraph."""
    
    return SimplePrompt(
        template="""You are a conversation summarizer. 
Summarize the following chat history into a concise paragraph. Focus on the main topics discussed, user preferences, and any important entities or facts established. Do not answer the user's questions, just summarize the past interaction.

Chat History:
{chat_history}

Summary:"""
    )
