# Automatic Journal

## Installation

### Arch Linux

```
# pacman -S pipenv jq libsecret
$ make setup
```

### Windows and Mac

Not supported because of the libsecret dependency.

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

## Development

### Dependencies

- schellcheck: for shell script linting

### Linting

```
make lint
```
