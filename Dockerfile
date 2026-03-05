# filepath: c:\Users\PC\Desktop\wifi-portal\wifi-portal-teste\Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn  # Adicione gunicorn

COPY . .
EXPOSE 5000
CMD ["gunicorn", "--config", "deploy/gunicorn.conf.py", "app_simple:app"]