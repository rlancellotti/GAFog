FROM python:3
COPY dot.py flask_app.py graph.dot.mako ./
RUN pip install flask mako
RUN apt update -y
RUN apt install graphviz -y
EXPOSE 8080
CMD python flask_app.py
#CMD sh