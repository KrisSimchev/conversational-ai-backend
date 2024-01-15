# Use the official Python image
FROM python:3.8-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt /app/

# Install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy the application files to the container
COPY . /app/

# Expose the port that Flask will run on
EXPOSE 8080

# Command to run the application
CMD ["python", "app.py"]
