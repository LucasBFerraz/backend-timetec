# Use official Python image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt


# Expose port (Render expects your app to listen on PORT)
EXPOSE 10000

# Start the app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10000"]
