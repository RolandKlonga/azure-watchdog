# Use a tiny version of Python as the base
FROM python:3.9-slim

# Install the system tools we need (ping)
# We use 'apt-get' because this is a Linux container
RUN apt-get update && apt-get install -y iputils-ping

# Install the Python library for Discord
RUN pip install requests

# Copy your script into the container
COPY monitor.py /app/monitor.py

# Set the working directory
WORKDIR /app

# The command to run when the container starts
CMD ["python", "-u", "monitor.py"]
