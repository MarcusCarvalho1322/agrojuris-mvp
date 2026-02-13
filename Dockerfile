FROM python:3.11-slim

WORKDIR /app

COPY mvp_backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY mvp_backend/ ./

ENV PYTHONUNBUFFERED=1

CMD ["python", "start.py"]
