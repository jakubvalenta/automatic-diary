# Automatic Diary

## Pre-requisites

- Python 3.7

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
./automatic-diary <config path> <output csv path>
```

The output CSV must be in a git repository.

Example:

```
./automatic-diary ~/.config/automatic-diary/config.json diary.csv
```

## Supported providers

- caldav
- git

## Development

### Dependencies

- schellcheck: for shell script linting

### Installation

```
make setup-dev
```

### Linting

```
make lint
```
