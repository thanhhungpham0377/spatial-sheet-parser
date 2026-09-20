FROM python:3.11-slim

WORKDIR /app

# Install system dependencies if any
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and install package
COPY . .
RUN pip install --no-cache-dir -e .

EXPOSE 8080
ENV PORT=8080
ENV HOST=0.0.0.0

CMD ["python", "-m", "spatial_sheet_parser.web"]
