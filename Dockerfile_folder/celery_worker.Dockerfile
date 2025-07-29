FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

CMD ["celery", "-A", "services.worker", "worker", "--loglevel=info"]