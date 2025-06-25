FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install only non-conflicting system packages
RUN apt-get update && apt-get install -y \
    curl gnupg apt-transport-https \
    gcc g++ \
    libssl-dev \
    unixodbc-dev \
    && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y \
       msodbcsql18=18.5.1.1-1 \
    && apt-mark hold msodbcsql18 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Upgrade pip to a compatible version
RUN pip install --upgrade pip

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

EXPOSE 8008

CMD ["python", "serversse.py"]