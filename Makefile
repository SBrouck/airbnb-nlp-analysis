PY ?= .venv/bin/python
export PYTHONPATH := src

.PHONY: env data analysis figures test all

env:
	uv venv --python 3.12 .venv
	uv pip install --python $(PY) -r requirements.txt

data:       ## Inside Airbnb San Francisco snapshot -> data/raw/ (not versioned)
	$(PY) -m reviewtext.data

analysis:   ## score reviews, aggregate per listing -> results/
	$(PY) -m reviewtext.analysis

figures:    ## figures/*.svg from results/
	$(PY) -m reviewtext.figures

test:
	$(PY) -m pytest -q tests

all: data analysis figures
