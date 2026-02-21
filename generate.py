import os
from google import genai
from models import db, Question


def generate_questions():
    """Use Gemini to generate new questions based on top-rated ones."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set")

    # Get top-rated questions as style examples
    top_questions = (
        Question.query
        .order_by((Question.thumbs_up_count - Question.thumbs_down_count).desc())
        .limit(15)
        .all()
    )

    if not top_questions:
        top_questions = Question.query.order_by(db.func.random()).limit(15).all()

    examples = "\n".join(f"- {q.text}" for q in top_questions)

    prompt = f"""Generate 5 unique conversation-starter questions for a parent and child (ages 5-12) to discuss together. Make them fun, thought-provoking, and easy to understand.

Here are some examples of well-liked questions to match the style and tone:
{examples}

Rules:
- Return ONLY the questions, one per line, no numbering or bullets
- Each question should be different from the examples
- Mix of silly/fun, hypothetical, and slightly deeper/reflective questions
- Keep them concise (one sentence each)"""

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
    )

    new_questions = []
    for line in response.text.strip().splitlines():
        line = line.strip().lstrip("-•0123456789.) ")
        if len(line) > 10 and line.endswith("?"):
            existing = Question.query.filter_by(text=line).first()
            if not existing:
                q = Question(text=line, source="generated")
                db.session.add(q)
                new_questions.append(line)

    db.session.commit()
    return new_questions
