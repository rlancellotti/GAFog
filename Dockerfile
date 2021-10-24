FROM python:3
COPY ga.py problem.py fogindividual.py flask_app.py ./
RUN pip install flask deap requests
EXPOSE 8080
CMD python flask_app.py