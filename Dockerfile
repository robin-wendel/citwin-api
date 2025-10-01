FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y \
    build-essential \
    gdal-bin \
    python3-dev \
    libgdal-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
