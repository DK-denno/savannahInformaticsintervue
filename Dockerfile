# Use an official Python runtime as a parent image
FROM python:3.10

# Set environment variables for Python buffering
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt
# RUN apt-get update && apt-get install -y iputils-ping


# Expose the port on which Django will run (change if needed)
EXPOSE 8000

# Run the Django development server
CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000"]