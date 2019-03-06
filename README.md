# Automatic Diary

*Locating myself in the stream of life*

Automatic Diary is a program that compiles information about your life from
various digital sources into one easy to read stream.

![Automatic Diary screenshot](./automatic_diary_screenshot.png)

_On the screenshot above, you can see: calendar events (blue), completed todo
list items (yellow), software development work (gray), sport activity (green),
and films watched (red)._

## Why

Automatic Diary can be useful to those who:

(a) have bad memory,\
(b) want to remember what they did,\
(c) but don't have the time to write a real diary.

## What is collected

- [X] Calendar events (via CalDAV service and iCalendar file reading)
- [X] Emails sent and received (via Maildir reading)
- [X] Sport activity (via spreadsheet parsing)
- [X] Facebook and Twitter posts (via Facebook/Twitter data archive parsing)
- [X] Software development work (via Git repository log)
- [X] Completed todo list items (via todo.txt parsing)
- [X] Films watched (via ČSFD website parsing)
- [X] Custom diary notes (via plain-text and Org-mode files parsing)

## What is not collected

Please be aware of the activities that are not collected by Automatic Diary:

- emotions
- conversations
- uplanned activities (meeting someone, visiting a place)
- house work
- repairs
- unpublished projects
- reading books
- health
- sleep
- what other people did

## Future

Automatic Diary could be extended to collect also the following data but right
now it is considered low priority:

- [ ] Custom notes and ideas
- [ ] Articles and blog posts written
- [ ] Phone calls and text messages (SMS)
- [ ] Social media private messages and messaging apps
- [ ] Browser history
- [ ] Music listened (via Last.fm)
- [ ] OpenStreetMap contributions
- [ ] Money transfers
- [ ] News headlines
- [ ] Weather

## Installation

### Prerequisites

- Python 3.7
- Linux with libsecret available.

### Installation on Arch Linux

``` shell
# pacman -S pipenv jq libsecret
$ make setup
```

## Configuration

First you need to configure all the providers -- sources from which the data for
your automatic diary stream will be read. The following providers are supported:

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

All providers are configured using a single `config.json` file. Use
[config-sample.json](./config-sample.json) as a template for your own
configuration.

### CalDAV (caldav)

- Input: CalDAV server

- Output: Names and locations of calendar events

- Configuration:

    ``` json
    {
        "url": "<server url>",
        "username": "<server authentication username>",
        "password_key": "<server authentication password -- libsecret key>",
        "password_val": "<server authentication password -- libsecret value>",
        "cache_dir": "<cache directory path>"
    }
    ```

### ČSFD (csfd)

- Input: User profile on https://www.csfd.cz/ (film database website, something
  like IMDB)

- Output: Titles of films rated

- Configuration:

    ``` json
    {
        "profile_url": "<csfd.cz profile url>",
        "cache_dir": "<cache directory path>"
    }
    ```

### CSV (csv)

- Input: CSV spreadsheet (.csv) file

- Output: Rows formatted using a template

- Configuration

    ``` json
    {
        "path": "<csv file path>",
        "date_source": "{{<column name>}}",
        "date_format": "<strptime date format>",
        "text_source": "<template string in the Mustache format>"
    }
    ```

### Facebook (facebook)

- Input: Downloaded Facebook archive

- Output: Texts of statuses

- Configuration

    ``` json
    {
        "path": "<path to wall.htm or timeline.htm>",
        "username": "<facebook username>"
    }
    ```

### Git (git)

- Input: Directory with checked-out Git repositories and an author name

- Output: Commit messages by the author from all repositories

- Configuration

    ``` json
    "config": {
        "base_path": "<path to directory - will be searched recursively for git repos>",
        "author": "<author name>"
    }
    ```

### iCalendar (icalendar)

- Input: Calendar events stored offline in the iCalendar (.ics) format

- Output: Names and locations of calendar events

- Configuration:

    ``` json
    {
        "paths": [
            "<path to an .ics file>",
            ...
        ]
    }
    ```

    Not that events from all the listed .ics files will be merged -- duplicate
    events removed.

### Maildir (maildir)

- Input: Emails stored offline in the Maildir format

- Output: Subjects of emails

- Configuration:

    ``` json
    {
        "received_pathname": "<glob pathname of directories with received emails>",
        "sent_pathname": "<glob pathname of directories with sent emails>"
    }
    ```

### Org-mode (orgmode)

- Input: Org-mode (.org) file in format:

        * <2019-01-17 Thu>

        Lorem ipsum
        foo.

        bar

        * <2019-01-18 Fri>

        spam spam
        ...

- Output: Example:

    ``` csv
    2019-01-17,Lorem ipsum foo.
    2019-01-17,bar
    2019-01-18,spam spam
    ```

    ``` json
    {
        "path": "<path to the .org file>"
    }
    ```

### Todo.txt (todotxt)

- Input: Todo.txt completed tasks file

- Output: Texts of completed tasks

- Configuration

    ``` json
    {
        "path": "<done.txt file path>"
    }
    ```

### Twitter (twitter)

- Input: Downloaded Twitter archive

- Output: Texts of tweets

- Configuration

    ``` json
    {
        "path": "<path to twitter archive directory>"
    }
    ```

### Plain text file (txt)

- Input: Plain text (.txt) file in format:

    ```
    2015-12-02 St
        Some
        Text
        Lorem
            Ipsum
                Hierarchy
                Spam
    2015-12-03 Čt
        Foobar
        ...
    ```

- Output: Example:

    ``` csv
    2015-12-02,Some
    2015-12-02,Text
    2015-12-02,Lorem: Ipsum: Hierarchy
    2015-12-02,Lorem: Ipsum: Spam
    2015-12-03,Foobar
    ```

- Configuration

    ``` json
    {
        "path": "<path to the .txt file>"
    }
    ```

## Usage

### Generating CSV

The basic output of Automatic Diary is a CSV file. Generate it by running:

``` shell
./automatic-diary <config path> <output csv path>
```

Example:

``` shell
./automatic-diary ~/.config/automatic-diary/config.json ~/Desktop/automatic_diary.csv
```

The CSV output is in format:

``` csv
<datetime>,<provider>,<subprovider>,<text>
```

Example CSV output:

``` csv
2019-01-23T15:31:54-08:00,git,human-activities,model: Log exceptions while scanning
2019-01-24T09:00:00+01:00,caldav,https://dav.mailbox.org/caldav/Y2FsOi8vMC8yNg,DHL Packstation
2019-01-25,todotxt,done.txt,Opravit Ondrovi kolo
```

See the help for all command line options:

``` shell
./automatic-diary --help
```

### Visualization

The output CSV file can also be rendered as an HTML document which looks kind of
like a calendar. See the screenshot above. Generate this HTML document by
running:

``` shell
./automatic-diary-visualize <csv path> <output html path>
```

Example:

``` shell
./automatic-diary-visualize ~/Desktop/automatic_diary.csv ~/Desktop/automatic_diary.html
```

See the help for all command line options:

``` shell
./automatic-diary-visualize --help
```

## Development

### Installation

``` shell
make setup-dev
```

### Testing and linting

``` shell
make test
make lint
```

### Help

``` shell
make help
```
