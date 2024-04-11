# python image
FROM python:3.11.2-buster

WORKDIR /app

# pip install
COPY ./requirements.txt /app
RUN pip install -r requirements.txt
