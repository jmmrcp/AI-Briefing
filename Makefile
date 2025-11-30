
# Makefile para tareas comunes

PYTHON=python3
APP=app.py
REQ=requirements.txt

setup:
	$(PYTHON) -m venv .venv && . .venv/bin/activate && pip install -r $(REQ)

install:
	pip install -r $(REQ)

dry-run:
	LOG_LEVEL=INFO DRY_RUN=1 $(PYTHON) $(APP)

run:
	LOG_LEVEL=INFO DRY_RUN=0 $(PYTHON) $(APP)

lint:
	pip install flake8 && flake8 $(APP)

clean:
	rm -rf .venv __pycache__ *.log
