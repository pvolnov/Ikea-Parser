FROM python:3.8
WORKDIR /app
COPY . .

RUN python -m pip install pipenv
RUN pipenv install --system --deploy --ignore-pipfile

CMD ["python", "main.py"]
