.PHONY: sync, setup, update

sync: pyproject.toml
	@uv sync

tables:
	@uv run src/tables.py

data:
	@uv run src/data.py

statcast-latest:
	@uv run src/data.py --statcast --year=$(shell date +'%Y')