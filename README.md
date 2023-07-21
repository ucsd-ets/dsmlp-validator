# DSMLP Validator

The DSMLP validator is an admission controller that validates a pod's uid and gid against AWSed.

It checks the pod security context, and the security contexts of containers and init containers.

It is deployed with the [dsmlp-validator](https://github.com/ucsd-ets/sic-charts/tree/main/charts/dsmlp-validator) chart.


# Development Environment

Here's how to set the project up under Ubuntu.

```
sudo apt install python3.9 python3.9-venv
python3.9 -m venv .venv
source .venv/bin/activate
pip install pip-tools
pip-sync requirements.txt
pip install .[test]
pip install --editable .
```

## Testing

How to run the tests:


```
pytest

#or

tox
```

# Dev server

Setup `.env` file:

```
AWSED_ENDPOINT=
AWSED_API_KEY=
```

Running with Python

```
waitress-serve --listen=*:8080 --call 'dsmlp.admission_controller:create_app'
```

Running with Docker

```
DOCKER_BUILDKIT=1 docker build -t dsmlp-validator .
docker run --rm -it -p 9997:8080 dsmlp-validator:latest
```

Send a request with curl

```
curl -X POST localhost:8080/validate -H 'Content-Type: application/json' -d @tests/admission-review.json
```

# Source layout

```
|- src
|  |- dsmlp
|  |  |- app      # main app
|  |  |- ext      # plugin implementations
|  |  |- plugin   # plugin interfaces
|  |- admission_controller.py # flask entrypoint
|- tests
```

# Cert

openssl req -subj '/CN=dsmlp-validater-dsmlp-validator.default.svc' -new -newkey rsa:2048 -sha256 -days 365 -nodes -x509 -keyout server.key -out server.crt
