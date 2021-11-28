.PHONY: clean-build clean-pyc venv isort flake8 black test

clean-build:
	@rm -fr build/
	@rm -fr dist/
	@rm -fr .eggs/
	@find . -name '*.egg-info' -exec rm -fr {} +
	@find . -name '*.egg' -exec rm -f {} +

clean-pyc:
	@find . -name '*.pyc' -exec rm -f {} +
	@find . -name '*.pyo' -exec rm -f {} +
	@find . -name '*~' -exec rm -f {} +
	@find . -name '__pycache__' -exec rm -fr {} +

venv:
	@python3 -m venv venv
	@venv/bin/pip install -U -r requirements.txt

isort:
	isort app tests alembic

flake8:
	flake8 app tests alembic

black:
	black app tests alembic

fix: isort black flake8

clean: clean-build clean-pyc

test:
	PYTHONPATH=. env `(cat .env | xargs)` venv/bin/python -m pytest -vs tests