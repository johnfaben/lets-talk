FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Seed the database on build
RUN python -c "from app import app; from seed import seed_questions; app.app_context().__enter__(); seed_questions()"

EXPOSE 8099

CMD ["gunicorn", "--bind", "0.0.0.0:8099", "--workers", "2", "app:app"]
