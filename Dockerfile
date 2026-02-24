FROM python:3.14-alpine

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apk add --no-cache \
    build-base \
    linux-headers \
    libffi-dev

RUN adduser -D -H synexis
USER synexis
WORKDIR /home/synexis/

COPY --chown=synexis:synexis . .
RUN mv config.yaml.example config.yaml
RUN pip install --upgrade pip setuptools wheel \
    && pip install .

RUN mkdir -p /home/synexis/data/extracted_text

EXPOSE 8080

CMD ["searchctl", "web", "--config", "config.yaml", "--host", "0.0.0.0", "--port", "10000", "--allow-remote"]
