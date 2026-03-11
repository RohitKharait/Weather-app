FROM python:3.9-slim-bookworm
RUN apt-get update && apt-get upgrade -y
WORKDIR /app
COPY requirements.txt .
RUN pip install --upgrade pip --root-user-action=ignore && \
    pip install -r requirements.txt --root-user-action=ignore
COPY . .
EXPOSE 5000
CMD ["python", "app.py"]