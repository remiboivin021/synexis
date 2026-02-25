FROM debian:bookworm-slim


RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    curl \
    ca-certificates && \
    rm -rf /var/lib/apt/lists/*


RUN useradd -m -d /home/synexis -s /bin/bash synexis

USER synexis
WORKDIR /home/synexis/

ENV VIRTUAL_ENV="/home/synexis/.venv"
ENV PATH="/home/synexis/.local/bin:$VIRTUAL_ENV/bin:$PATH"

RUN curl -fsSL https://astral.sh/uv/install.sh -o /tmp/uv-installer.sh && \
    sh /tmp/uv-installer.sh && \
    rm /tmp/uv-installer.sh

RUN uv python install 3.14

COPY --chown=synexis:synexis src ./src
COPY --chown=synexis:synexis docker/start-web.sh ./start-web.sh
COPY --chown=synexis:synexis pyproject.toml .
COPY --chown=synexis:synexis config.yaml.example ./config.yaml

RUN uv venv --python 3.14 --seed "$VIRTUAL_ENV" && \
    "$VIRTUAL_ENV/bin/pip" install --upgrade pip && \
    "$VIRTUAL_ENV/bin/pip" install .

RUN mkdir -p /home/synexis/data/extracted_text

EXPOSE 10000
RUN chmod +x /home/synexis/start-web.sh
CMD ["/home/synexis/start-web.sh"]
