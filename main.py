import json
from argparse import ArgumentParser
from typing import Any, Dict

from loguru import logger

from thesaurus.scraper import UNBISThesaurusScraper


def main(args: Dict[str, Any]) -> None:
    """
    Main function

    Parameters
    ----------
    `args` : `Dict[str, Any]`
        Dictionary of CLI arguments
    """
    scraper = UNBISThesaurusScraper(verbose=args["verbose"], boltURL=args["bolt_url"])
    scraper.crawl()
    scraper.exportToJson(args["output"])


def parseArgs() -> Dict[str, Any]:
    """
    Parse command line arguments

    Returns
    -------
    `Dict[str, Any]`
        Dictionary of arguments
    """
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

    parser.add_argument(
        "--bolt_url",
        type=str,
        help="Bolt URL for Neo4j",
    )

    return vars(parser.parse_args())


if __name__ == "__main__":
    args = parseArgs()
    logger.debug(f"Args: {json.dumps(args, indent=4, ensure_ascii=False)}")
    main(args=args)
