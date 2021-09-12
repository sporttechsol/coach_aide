.PHONY: help venv test report clean prepare firmware

help:
	@echo "  venv        => to create a virtualenv"

venv:
	@python3 -m venv venv
	@venv/bin/pip install -U -r requirements.txt

isort:
	isort bot tests

flake8:
	flake8 bot tests

black:
	black bot tests

test:
	PYTHONPATH=. env `(cat .env | xargs)` venv/bin/python -m pytest -vs tests