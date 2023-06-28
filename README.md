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

## Tests

```
tox

#or

pytest
```
