FROM python:3.11-slim

RUN apt-get update && \
    apt-get curl && \
    apt-get clean

WORKDIR /opt
COPY ./requirements.txt ./requirements.txt

RUN pip install -r requirements.txt && rm requirements.txt

COPY ./src .

CMD ["uvicorn", "main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "8000"]