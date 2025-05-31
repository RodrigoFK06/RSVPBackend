# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies if any (e.g., for cryptography if not handled by wheels)
# RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*
# For now, assuming Python dependencies are self-contained or wheels are available.

# Copy the requirements file into the container
COPY requirements.txt .

# Install Python dependencies
# Using --no-cache-dir can reduce image size slightly
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Gunicorn configuration file
COPY gunicorn.conf.py .

# Copy the .env file - useful for local Docker builds.
# For production, these variables should be injected into the environment.
COPY .env .
# Note: Ensure .env does not contain super sensitive production secrets if this Dockerfile
# is used to build images that are pushed to a public registry.
# For this project, it's assumed to be for local/controlled deployment.

# Copy the rest of the application code into the container
COPY ./app ./app

# Expose the port the app runs on
# This should match the port in Gunicorn's bind address
EXPOSE 8000

# Define the command to run the application using Gunicorn
# This will use the gunicorn.conf.py by default if it's in the working directory
# or specified with -c gunicorn.conf.py
CMD ["gunicorn", "app.main:app", "-c", "gunicorn.conf.py"]
