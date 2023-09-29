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

# Copy the source code into the container.
COPY . .

# Run the application.
CMD [ "python", "./app.py" ]
