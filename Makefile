_python_pkg := automatic_diary

.PHONY: setup
setup:  ## Create virtual environment and install dependencies
	poetry install

.PHONY: test
test:  ## Run unit tests
	poetry run python -m unittest

.PHONY: lint
lint:  ## Run linting
	poetry run flake8 $(_python_pkg)
	poetry run mypy $(_python_pkg) --ignore-missing-imports
	poetry run isort -c $(_python_pkg)

.PHONY: tox
tox:  ## Test with tox
	tox -r

.PHONY: reformat
reformat:  ## Reformat Python code using Black
	black -l 100 --skip-string-normalization $(_python_pkg)

.PHONY: python-shell
python-shell:  ## Run Python shell with all dependencies installed
	poetry run ipython --no-banner --no-confirm-exit

.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-24s\033[0m %s\n", $$1, $$2}'
