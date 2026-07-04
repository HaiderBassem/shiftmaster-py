FROM python:3.11-slim

# environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml ./
RUN pip install --upgrade pip \
    && pip install .

# Copy the project files
COPY . .

# Ensure the script has Linux line endings and is executable
RUN sed -i 's/\r$//' scripts/start.sh && chmod +x scripts/start.sh

# Expose port
EXPOSE 8000

# Set entrypoint to our script
ENTRYPOINT ["bash", "scripts/start.sh"]

# Default command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
