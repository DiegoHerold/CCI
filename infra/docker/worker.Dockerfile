FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN addgroup --system cci && adduser --system --ingroup cci cci && chown -R cci:cci /app
USER cci
CMD ["python", "-m", "app.worker"]
