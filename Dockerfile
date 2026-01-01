FROM python:3.13-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/

# Declare volume for persistent state and articles
VOLUME ["/app/data"]

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the main job
CMD ["python", "-m", "src.jobs.main"]
