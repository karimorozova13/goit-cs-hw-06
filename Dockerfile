FROM python:3.10

WORKDIR /app

COPY main.py .
COPY index.html .
COPY error.html .
COPY message.html .
COPY style.css .
COPY logo.png .

RUN pip install pymongo

CMD ["python", "main.py"]
