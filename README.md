# 🇺🇳 United Nations UNBIS Thesaurus Taxonomy database scraper

<!-- Add code style badge -->

![Style](https://img.shields.io/badge/style-black-black) ![Packages](https://img.shields.io/badge/package%20manager-poetry-blue) ![Linter](https://img.shields.io/badge/linter-ruff-orange) ![Version](https://img.shields.io/github/v/release/ClementSicard/un-unbis-thesaurus-scraper?display_name=tag&label=version&logo=python&logoColor=white)

<!-- Add code coverage badge -->

## About

The scraper works as follows:

1. Start fetching the first page of the UNBIS Thesaurus Taxonomy database.
2. Recursively, query in parallel all subtopics related to the current topic.
3. Collect information about all topics and subtopics.
4. Create a graph structure using [`networkx`](https://networkx.org/documentation/stable/index.html), then export it to JSON

## Get the data

The main script is in [`example/main.py`](example/main.py). First install the requirements in [`requirements.txt`], then use the script as follows:

```
usage: main.py [-h] [-v] [-o OUTPUT]

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         Whether to print verbose logs
  -o OUTPUT, --output OUTPUT
                        Output file path
```

For instance, to scrape and save the result JSON in `data.json`:

```bash
python example/main.py -o data.json
```
