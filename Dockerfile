# Use an official Python runtime as a parent image
FROM python:3.10

# Set the working directory inside the container
WORKDIR /app

# Copy everything from the current directory (outside the app folder) into the container
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Set the Python path to include the /app folder
ENV PYTHONPATH=/app

# Start the bot
CMD ["python", "app/bot.py"]
