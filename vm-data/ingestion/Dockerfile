FROM python:3.12-slim
RUN pip install --no-cache-dir pika==1.3.2 "boto3>=1.36,<2"
COPY ingestion.py /app/ingestion.py
CMD ["python", "/app/ingestion.py"]
