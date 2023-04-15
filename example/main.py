from argparse import ArgumentParser
from typing import Any, Dict

from thesaurus.scraper import UNBISThesaurusScraper


def main(args: Dict[str, Any]) -> None:
    scraper = UNBISThesaurusScraper(verbose=args["verbose"])
    scraper.crawl()
    scraper.export_to_json(args["output"])


def parse_args() -> Dict[str, Any]:
    parser = ArgumentParser()
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Whether to print verbose logs",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Output file path",
        default="downloads/output.json",
    )
    return vars(parser.parse_args())


if __name__ == "__main__":
    args = parse_args()
    main(args=args)
