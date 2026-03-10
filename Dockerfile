FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt --no-warn-script-location
COPY . .
EXPOSE 5000
CMD ["python", "app.py"]