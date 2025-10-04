# Dockerfile

# Stage 1: Build Stage
# Use a slim, official Python image for efficiency
FROM python:3.11-slim as builder

# Set the working directory inside the container
WORKDIR /app

# Prevent Python from writing .pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Copy only the requirements file first to take advantage of Docker layer caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Production Stage (using the same slim image)
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy installed packages from the builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Copy the application source code (src/ and tests/)
# This copies everything from the host's current directory into /app inside the container
COPY src /app/src
COPY tests /app/tests
COPY requirements.txt /app/
COPY run.py /app/

# Port the application listens on
EXPOSE 8000

# Command to run the application using Uvicorn
# The command format is: uvicorn [module:app_object] --host [ip] --port [port]
# We use the standard uvicorn worker configuration
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
