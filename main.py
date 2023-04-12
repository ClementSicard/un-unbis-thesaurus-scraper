from scraper import UNBISThesaurusScraper


def main() -> None:
    scraper = UNBISThesaurusScraper()
    scraper.crawl()
    scraper.visualize_network()


if __name__ == "__main__":
    main()
