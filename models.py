from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False, unique=True)
    source = db.Column(db.String(20), nullable=False, default="seed")  # seed or generated
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    times_shown = db.Column(db.Integer, default=0)
    thumbs_up_count = db.Column(db.Integer, default=0)
    thumbs_down_count = db.Column(db.Integer, default=0)

    ratings = db.relationship("Rating", backref="question", lazy=True)


class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey("question.id"), nullable=False)
    session_id = db.Column(db.String(64), nullable=False)
    rating = db.Column(db.String(10), nullable=False)  # up, down, skip
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
