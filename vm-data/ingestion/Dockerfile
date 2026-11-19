FROM python:3.12-slim
RUN pip install --no-cache-dir pika==1.3.2 pymongo==4.10.1
COPY ingestion.py /app/ingestion.py
CMD ["python", "/app/ingestion.py"]
