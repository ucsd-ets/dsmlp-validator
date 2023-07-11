# DSMLP Validating Admission Controller

Validates pods for uid and gid.

# Dev Environment

**Run Server**

```
python -m dsmlp.admission_controller
```

**Source layout**

```
|- src
|  |- dsmlp
|     |- app
      |- ext
      |- plugin
|- tests
```

## Ubuntu 20 Focal/WSL 2

```
sudo apt install python3.9 python3.9-venv
python3.9 -m venv .venv
source .venv/bin/activate
pip install pip-tools
pip-sync requirements.txt
pip install .[test]
pip install --editable .
```

```
DOCKER_BUILDKIT=1 docker build -t dsmlp-validator .
docker run --rm -it -p 9997:8080 dsmlp-validator:latest
curl -X POST  localhost:9997/validate -H 'Content-Type: application/json' -d @tests/admission-review.json
```
## Tests

```
tox

#or

pytest
```

# Cert

openssl req -subj '/CN=dsmlp-validater-dsmlp-validator.default.svc' -new -newkey rsa:2048 -sha256 -days 365 -nodes -x509 -keyout server.key -out server.crt
