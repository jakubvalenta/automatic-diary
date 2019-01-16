.PHONY: run setup setup-dev lint lint-shell lint-python help

run:  ## Run automatic journal
	./automatic_journal

setup:  ## Create Pipenv virtual environment and install dependencies.
	pipenv --three --site-packages
	pipenv install

setup-dev:  ## Install development dependencies
	pipenv install --dev

lint: | lint-shell lint-python  ## Run all linting

lint-shell:  ## Run only shell script linting
	git ls-tree -r HEAD --name-only | \
		grep -E '(.sh$$|^[^\.]+$$)' | \
		awk '/^#!.*sh/{print FILENAME}  {nextfile}' | \
		xargs echo

lint-python:  ## Run only Python linting
	tox -e lint

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-24s\033[0m %s\n", $$1, $$2}'