.PHONY: run setup setup-dev test lint reformat help

run:  ## Run automatic diary
	./automatic-diary

setup:  ## Create Pipenv virtual environment and install dependencies.
	pipenv --three --site-packages
	pipenv install

setup-dev:  ## Install development dependencies
	pipenv install --dev

test:  ## Run unit tests
	tox -e py37

lint:  ## Run linting
	tox -e lint

reformat:  ## Reformat Python code using Black
	black -l 79 --skip-string-normalization automatic_diary

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-24s\033[0m %s\n", $$1, $$2}'
