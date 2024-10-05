FROM python:3.12-slim

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 80

CMD ["streamlit", "run", "app.py", "--server.port=80", "--server.address=0.0.0.0"]
