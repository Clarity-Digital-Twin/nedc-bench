# Alpha Pipeline - NEDC v6.0.0 Legacy Wrapper
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    bash \
    && rm -rf /var/lib/apt/lists/*

# Copy the vendored NEDC tool (relative to repo root build context)
COPY nedc_eeg_eval/v6.0.0/ /opt/nedc/

# Copy wrapper package under /app/alpha
COPY alpha/ /app/alpha/

# Copy requirements
COPY alpha/requirements.txt /tmp/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Set required environment variables
ENV NEDC_NFC=/opt/nedc
ENV PYTHONPATH=/opt/nedc/lib:/app

# Set working directory
WORKDIR /app

# Default command (can be overridden)
CMD ["python", "-c", "print('NEDC Alpha Pipeline Ready')"]
