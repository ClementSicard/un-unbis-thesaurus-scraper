from typing import Dict, List


class Topic:
    labels: str
    url: str
    related: List["Topic"]
    identifier: str

    def __init__(
        self,
        labels: Dict[str, str],
        url: str,
        related: List[str],
    ) -> None:
        self.labels = labels
        self.url = url
        self.identifier = self._get_identifier()
        self.related = related

    def __repr__(self) -> str:
        return f"Topic({self.labels}, {self.url})"

    def _get_identifier(self) -> str:
        return self.url.split("/")[-1]

    def to_json(self) -> Dict[str, str]:
        return {
            "url": self.url,
            "identifier": self.identifier,
            "labels": self.labels,
            "related": self.related,
        }
