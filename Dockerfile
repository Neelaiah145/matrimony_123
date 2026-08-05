FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["sh", "-c", "echo 'STEP 1'; python manage.py migrate && echo 'STEP 2'; python manage.py check && echo 'STEP 3'; gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --log-level debug --access-logfile - --error-logfile -"]