FROM python:3.13-slim-bookworm

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    FLASK_ENV=production

WORKDIR /app

# Install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# (Optional) Create a non-root user for security
RUN adduser --disabled-password --no-create-home --gecos '' appuser && chown -R appuser /app
USER appuser

EXPOSE 9654

# Use Gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:9654", "--access-logfile", "-", "app.app:app"]
