FROM python:3
COPY dot.py flask_app.py graph.dot.mako requirements.txt ./
RUN pip install -r requirements.txt
RUN apt update -y
RUN apt install graphviz -y
EXPOSE 8080
CMD python flask_app.py
#CMD sh