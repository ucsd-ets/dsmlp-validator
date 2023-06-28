# DSMLP Validating Admission Controller

Validates pods for uid and gid.

# Dev Environment

## Ubuntu/WSL 2

```
sudo apt install python3.8-venv
python3 -m venv .venv
source .venv/bin/activate
pip install pip-tools
pip-sync requirements.txt
#pip install -r requirements.txt
pip install .[test]
pip install --editable .
```

## Tests

```
tox
```
