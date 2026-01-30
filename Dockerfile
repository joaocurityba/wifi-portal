# filepath: c:\Users\PC\Desktop\wifi-portal\wifi-portal-teste\Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn  # Adicione gunicorn

COPY . .
EXPOSE 5000
CMD ["python", "-c", "from app_simple import app; app.run(host='0.0.0.0', port=5000)"]