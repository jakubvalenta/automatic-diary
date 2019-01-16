# Automatic Journal

## Pre-requisites

- Python 3
- Pipenv
- jq

## Installation

```
pipenv install
```

## Usage

```
./automatic_journal <config path> <output csv path>
```

The output CSV must be in a git repository.

Example:

```
mkdir /tmp/my_repo
cd /tmp/my_repo &&
git init &&
./automatic_journal ~/.config/automatic-journal/config.json /tmp/my_repo/journal.csv
```

## Supported providers

- caldav
- git
