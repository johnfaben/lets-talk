import os
from flask import Flask, jsonify, request, render_template
from dotenv import load_dotenv
from models import db, Question, Rating

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "sqlite:///questions.db"
)

db.init_app(app)

with app.app_context():
    db.create_all()


@app.route("/")
def index():
    return render_template("index.html")


@app.get("/api/question")
def get_question():
    session_id = request.args.get("session_id", "")

    # Get IDs this session already rated
    rated_ids = (
        db.session.query(Rating.question_id)
        .filter_by(session_id=session_id)
        .subquery()
    )

    # Try unrated questions first, weighted by net positive rating
    question = (
        Question.query
        .filter(Question.id.notin_(db.session.query(rated_ids.c.question_id)))
        .order_by(
            (Question.thumbs_up_count - Question.thumbs_down_count).desc(),
            db.func.random(),
        )
        .first()
    )

    # If all questions rated, pick a random well-liked one
    if not question:
        question = (
            Question.query
            .order_by(
                (Question.thumbs_up_count - Question.thumbs_down_count).desc(),
                db.func.random(),
            )
            .first()
        )

    if not question:
        return jsonify({"error": "No questions available"}), 404

    question.times_shown += 1
    db.session.commit()

    return jsonify({
        "id": question.id,
        "text": question.text,
        "source": question.source,
    })


@app.post("/api/rate")
def rate_question():
    data = request.get_json()
    question_id = data.get("question_id")
    session_id = data.get("session_id")
    rating_value = data.get("rating")

    if not all([question_id, session_id, rating_value]):
        return jsonify({"error": "Missing fields"}), 400

    if rating_value not in ("up", "down", "skip"):
        return jsonify({"error": "Invalid rating"}), 400

    question = db.session.get(Question, question_id)
    if not question:
        return jsonify({"error": "Question not found"}), 404

    # Update denormalized counts
    if rating_value == "up":
        question.thumbs_up_count += 1
    elif rating_value == "down":
        question.thumbs_down_count += 1

    rating = Rating(
        question_id=question_id,
        session_id=session_id,
        rating=rating_value,
    )
    db.session.add(rating)
    db.session.commit()

    return jsonify({"ok": True})


@app.post("/api/generate")
def generate():
    from generate import generate_questions

    try:
        new_questions = generate_questions()
        return jsonify({"generated": new_questions, "count": len(new_questions)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# CLI command to seed the database
@app.cli.command("seed")
def seed_command():
    from seed import seed_questions
    seed_questions()


if __name__ == "__main__":
    app.run(debug=True, port=8099)
