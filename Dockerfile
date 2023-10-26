# Set base image (host OS)
FROM python:3.11-slim-bookworm 

# By default, listen on port 5000
EXPOSE 5000/tcp

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any dependencies
RUN pip install -r requirements.txt --upgrade

# Install dependencies
RUN apt update && apt install -y curl

# Install gunicorn for prod
RUN pip install gunicorn

# Copy the source code into the container.
COPY . .

# Use Gunicorn to run the application.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "-w 4", "app:app", "--timeout 120", "--worker-class gevent"]
