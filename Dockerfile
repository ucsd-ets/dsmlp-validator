FROM python:3.9.5

RUN apt-get update && \
    apt-get install -y build-essential nginx

COPY / /app/

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache \
    pip3 install -r requirements.txt && \
    pip3 install .

EXPOSE 8080/tcp

#CMD flask --app dsmlp.admission_controller run --host=0.0.0.0
CMD waitress-serve --listen=*:8080 --call 'dsmlp.admission_controller:create_app'
# CMD gunicorn -w 4 -b 0.0.0.0 --certfile=/app/pki/tls.crt --keyfile=/app/pki/tls.key 'dsmlp.admission_controller:create_app()'
# CMD /app/entrypoint.sh
