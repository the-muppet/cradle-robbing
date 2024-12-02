FROM python:3.12-slim

WORKDIR /app

ENV PYTHONPATH=/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend /app/backend

EXPOSE 8005

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8005", "--reload"]