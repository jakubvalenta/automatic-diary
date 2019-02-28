# Automatic Diary

## Pre-requisites

- Python 3.7
- Linux with libsecret available.

## Installation

Arch Linux:

```
# pacman -S pipenv jq libsecret
$ make setup
```

## Usage

```
./automatic-diary <config path> <output csv path>
```

The output CSV must be in a git repository.

Example:

```
./automatic-diary ~/.config/automatic-diary/config.json diary.csv
```

## Supported providers

- caldav
- csfd
- csv
- facebook
- git
- icalendar
- maildir
- orgmode
- todotxt
- twitter
- txt

## Development

### Installation

```
make setup-dev
```

### Testing and linting

```
make test
make lint
```
