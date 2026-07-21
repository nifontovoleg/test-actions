# Official Python image
FROM python:3.11-slim

# Working directory
WORKDIR /app

# Dependency file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Application source
COPY main.py .

# Expose HTTP port
EXPOSE 8000

# Default environment
ENV HOST=0.0.0.0
ENV PORT=8000
ENV DEBUG=False

# Start command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
