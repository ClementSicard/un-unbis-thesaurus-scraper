import json
import os
from itertools import product
from typing import Any, Dict, List, Optional

import consts
import numpy as np
import requests
from bs4 import BeautifulSoup
from loguru import logger
from topic import Topic
from tqdm import tqdm
from utils import get_urls


class UNBISThesaurusScraper:
    def __init__(self) -> None:
        self.topics = {"topics": []}
        self.BASE_URL = "https://metadata.un.org/thesaurus/alphabetical?lang=en"

        self.html = self._get_html(self.BASE_URL)
        self.parser = BeautifulSoup(self.html, "html.parser")

        self.raw_topics = self.get_raw_topics()
        self.nb_topics = len(self.raw_topics)

        # i -> topic
        self.mapping = {
            i: topic["href"].split("?")[0].split("/")[-1]
            for i, topic in enumerate(self.raw_topics)
        }

        # topic -> i
        self.reverse_mapping = {topic: i for i, topic in self.mapping.items()}

        self.adjacency_matrix = np.zeros((self.nb_topics, self.nb_topics))

        logger.info(f"Loaded {self.nb_topics} raw topics")

    def add_topic(self, topic):
        self.topics["topics"].append(topic)

    def _get_html(
        self,
        url: str,
        headers: Optional[Dict[str, Any]] = None,
        to_json: bool = False,
    ) -> str:
        r = requests.get(url, headers=headers)

        if to_json:
            return r.json()

        return r.content.decode("utf-8")

    def get_raw_topics(self) -> List[str]:
        selector = "#collapseGroup"
        return self.parser.select(selector)[0].find_all(class_="bc-link")

    def get_topic(self, json_page: Dict[str, Any]) -> Topic:
        related_topics = (
            [
                related["@id"].split("/")[-1]
                for related in json_page[consts.KEYS["BROADER"]]
            ]
            if consts.KEYS["BROADER"] in json_page
            else []
        )

        labels = (
            {
                label["@language"]: label["@value"]
                for label in json_page[consts.KEYS["LABELS"]]
            }
            if consts.KEYS["LABELS"] in json_page
            else {}
        )

        url = json_page["@id"]

        # logger.debug(labels["en"])

        return Topic(labels=labels, url=url, related=related_topics)

    def _get_topics(self):
        topics_htmls = get_urls([topic["href"] for topic in self.raw_topics])

        for topic_html in topics_htmls:
            topic = self.get_topic(topic_html)
            self.add_topic(topic.to_json())

        with open("all_topics.json", "w", encoding="utf-8") as f:
            json.dump(self.topics, f, ensure_ascii=False)

    def crawl(self):
        if not os.path.exists("all_topics.json"):
            self._get_topics()

        with open("all_topics.json", "r", encoding="utf-8") as f:
            self.topics = json.load(f)

        for topic in tqdm(self.topics["topics"]):
            for related in topic["related"]:
                self.adjacency_matrix[
                    self.reverse_mapping[topic["identifier"]],
                    self.reverse_mapping[related],
                ] = 1
                self.adjacency_matrix[
                    self.reverse_mapping[related],
                    self.reverse_mapping[topic["identifier"]],
                ] = 1

        np.save("adjacency_matrix.npy", self.adjacency_matrix)
        logger.success("Saved adjacency matrix to adjacency_matrix.npy")

    def visualize_network(self) -> None:
        import gravis as gv
        import networkx as nx

        g = nx.Graph()

        logger.info("Adding all nodes...")
        for topic in tqdm(self.topics["topics"]):
            g.add_node(topic["labels"]["en"], identifier=topic["identifier"])
        logger.success(f"Added {g.number_of_nodes()} nodes")

        logger.info("Adding all edges...")
        for i, j in tqdm(product(range(self.nb_topics), range(self.nb_topics))):
            edge_exists = g.has_edge(
                self.topics["topics"][i]["labels"]["en"],
                self.topics["topics"][j]["labels"]["en"],
            ) or g.has_edge(
                self.topics["topics"][j]["labels"]["en"],
                self.topics["topics"][i]["labels"]["en"],
            )

            if self.adjacency_matrix[i, j] == 1 and not edge_exists:
                g.add_edge(
                    self.topics["topics"][i]["labels"]["en"],
                    self.topics["topics"][j]["labels"]["en"],
                )
        logger.success(f"Added {g.number_of_edges()} edges!")

        fig = gv.d3(
            g,
            layout_algorithm_active=True,
            graph_height=1000,
            use_edge_size_normalization=True,
        )
        fig.export_html("topics.html", overwrite=True)
        fig.display()
