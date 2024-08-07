FROM python:3.12-alpine
WORKDIR /src
COPY . .
ENV POETRY_HOME=/opt/poetry
# install dependencies
RUN apk update && apk add curl git && \
    curl -sSL https://install.python-poetry.org | python3 -

RUN pip install .

CMD ["python", "-m", "connext_monitor"]
