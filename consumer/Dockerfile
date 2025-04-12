FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Set the working directory to consumer for migrations
WORKDIR /app/consumer

# Run the startup script
CMD ["python", "/app/consumer/startup.py"] 