FROM python:3.8.13

RUN apt-get update && \
    apt-get install build-essential -y

COPY / /app/

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache \
    pip3 install -r requirements.txt && \
    pip3 install -e .

CMD python -m group_sync && \
    python -m create_team_dirs && \
    python -m create_workspaces
