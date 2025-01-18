# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose the app directory for uploading files
VOLUME ["/app/upload"]

# Set the entrypoint to the script
ENTRYPOINT ["python3", "convertsongs.py"]
