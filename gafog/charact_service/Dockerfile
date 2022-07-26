FROM python:3-alpine

MAINTAINER Stefano Rossi

COPY app /app

WORKDIR /app

RUN pip install -r requirements.txt

EXPOSE 7777

CMD ["python", "flask_app_alt.py"]

