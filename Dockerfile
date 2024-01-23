# Use a base image with Python 3
FROM python:3.10.8

# Set the working directory
WORKDIR /app

# Copy the bot code to the working directory
COPY . /app

# Install the dependencies
RUN pip install -r requirements.txt

# Start the bot
CMD python Bot.py