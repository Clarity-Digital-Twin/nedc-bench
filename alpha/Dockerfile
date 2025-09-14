# Alpha Pipeline - NEDC v6.0.0 Legacy Wrapper
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    bash \
    && rm -rf /var/lib/apt/lists/*

# Copy the vendored NEDC tool
COPY ../nedc_eeg_eval/v6.0.0/ /opt/nedc/

# Copy wrapper code
COPY wrapper/ /app/

# Copy requirements
COPY requirements.txt /tmp/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Set required environment variables
ENV NEDC_NFC=/opt/nedc
ENV PYTHONPATH=/opt/nedc/lib:/app

# Set working directory
WORKDIR /app

# Default command (can be overridden)
CMD ["python", "-c", "print('NEDC Alpha Pipeline Ready')"]