from typing import Any, Dict, List, Set, Union

from bs4 import BeautifulSoup
from loguru import logger

import thesaurus.consts as consts
import thesaurus.utils as utils
from thesaurus.network import Network


class UNBISThesaurusScraper:
    def __init__(
        self,
        verbose: bool,
    ) -> None:
        self.verbose = verbose
        self.url_dl = utils.FastURLDownloader(verbose=self.verbose)
        self.BASE_URL = "https://metadata.un.org/thesaurus/categories?lang=en"

        # Save all the ids to avoid duplicates
        self.network = Network(verbose=self.verbose)

        self.meta_topics_ids = set()
        self.topic_ids = set()
        self.subtopic_ids = set()

    def crawl(self) -> Dict[str, Any]:
        """
        Crawls the whole UNBIS Thesaurus and returns the graph JSON.
        It first gets the meta topics, then the topics, and finally
        the subtopics, by getting each JSON file for each topic and
        parsing its content.

        Returns
        -------
        `Dict[str, Any]`
            The graph JSON
        """
        logger.info("Started crawling the UNBIS Thesaurus...")
        self.meta_topics_ids = self.get_meta_topics()
        self.topic_ids = self.crawl_meta_topics(ids=self.meta_topics_ids)
        self.subtopic_ids = self.crawl_topics(ids=self.topic_ids)

        logger.info("Recusrively crawling subsubtopics...")
        i = 1
        unexplored = self.subtopic_ids
        while True:
            unexplored = self.crawl_subtopics(ids=unexplored)
            self.subtopic_ids.update(unexplored)

            logger.debug(f"Unexplored: {len(unexplored)} at iteration {i}")
            if len(unexplored) == 0:
                break
            i += 1

        if self.verbose:
            logger.debug(f"Meta topics: {self.meta_topics_ids}")
            logger.debug(f"Meta topics: {len(self.meta_topics_ids)}")
            logger.debug(f"Topics: {len(self.topic_ids)}")
            logger.debug(f"Subtopics: {len(self.subtopic_ids)}")
            logger.debug(f"Number of nodes: {len(self.network.G.nodes)}")
            logger.debug(f"Number of edges: {len(self.network.G.edges)}")

        return self.network.to_json()

    def get_meta_topics(self) -> List[str]:
        """
        This function parses the home page of the Thesaurus and returns the
        meta topics ids. It doesn't add nodes to the graph - it only returns
        the ids.

        Returns
        -------
        `List[str]`
            The list of meta topic ids
        """
        meta_topic_ids = set()
        html = self.url_dl.get_html(self.BASE_URL)
        soup = BeautifulSoup(html, "html.parser")

        class_ = "row collapsible"
        raw_meta_topics = soup.find_all(class_=class_)

        for raw_meta_topic in raw_meta_topics:
            meta_topic_name = raw_meta_topic.find(class_="bc-link domain").text
            meta_topic_id = meta_topic_name.split(" - ")[0]
            meta_topic_ids.add(meta_topic_id)

        if self.verbose:
            logger.success(f"Found {len(meta_topic_ids)} meta topics.")
            logger.debug(f"Number of nodes: {len(self.network.G.nodes)}")
            logger.debug(f"Number of edges: {len(self.network.G.edges)}")

        return meta_topic_ids

    def crawl_meta_topics(self, ids: List[str]) -> List[str]:
        topic_ids = set()

        urls = [consts.JSON_BASE_URL.format(id_) for id_ in ids]

        if self.verbose:
            logger.info(f"Getting {len(urls)} JSONs for meta topics...")

        jsons = self.url_dl.get_urls(urls, to_json=True)

        if self.verbose:
            logger.success("Done!")

        for raw_json in jsons:
            # Add meta-topic node
            raw_json = raw_json[0]

            meta_topic_url = raw_json[consts.KEYS["ID"]]
            meta_topic_id = self._extract_id_from_url(meta_topic_url)
            labels = self._extract_labels(raw_json)

            self.network.add_node(
                node_id=meta_topic_id,
                cluster=meta_topic_id,
                label_en=labels.get("en"),
                label_ar=labels.get("ar"),
                label_es=labels.get("es"),
                label_fr=labels.get("fr"),
                label_ru=labels.get("ru"),
                label_zh=labels.get("zh"),
                node_type="meta_topic",
            )

            # Extract topics from meta-topic
            _topic_ids = self._extract_topic_ids(raw_json)

            # Update the set of topic ids
            topic_ids.update(_topic_ids)

            # Add edges between meta-topic and topics
            for topic_id in _topic_ids:
                self.network.add_edge(
                    source=meta_topic_id,
                    target=topic_id,
                    edge_type="meta_topic->topic",
                )

        if self.verbose:
            logger.success(f"Found {len(topic_ids)} topics.")
            logger.debug(f"Number of nodes: {len(self.network.G.nodes)}")
            logger.debug(f"Number of edges: {len(self.network.G.edges)}")

        return topic_ids

    def crawl_topics(self, ids: List[str]) -> List[str]:
        subtopic_ids = set()

        urls = [consts.JSON_BASE_URL.format(id_) for id_ in ids]

        if self.verbose:
            logger.info(f"Getting {len(urls)} JSONs for topics...")

        jsons = self.url_dl.get_urls(urls, to_json=True)

        if self.verbose:
            logger.success("Done!")

        for raw_json in jsons:
            # Add topic node
            raw_json = raw_json[0]

            topic_url = raw_json[consts.KEYS["ID"]]
            topic_id = self._extract_id_from_url(topic_url)
            labels = self._extract_labels(raw_json)
            cluster = self._extract_cluster(raw_json)

            self.network.add_node(
                node_id=topic_id,
                cluster=cluster,
                label_en=labels.get("en"),
                label_ar=labels.get("ar"),
                label_es=labels.get("es"),
                label_fr=labels.get("fr"),
                label_ru=labels.get("ru"),
                label_zh=labels.get("zh"),
                node_type="topic",
            )

            # Extract subtopics from topic
            _subtopic_ids = self._extract_subtopic_ids(raw_json)

            # Update the set of subtopic ids
            subtopic_ids.update(_subtopic_ids)

            # Add an edge from a topic to its cluster
            self.network.add_edge(
                source=cluster,
                target=topic_id,
            )

            # Add edges between topic and subtopics
            for subtopic_id in _subtopic_ids:
                self.network.add_edge(
                    source=topic_id,
                    target=subtopic_id,
                    edge_type="topic->subtopic",
                )

        if self.verbose:
            logger.success(f"Found {len(subtopic_ids)} subtopics.")
            logger.debug(f"Number of nodes: {len(self.network.G.nodes)}")
            logger.debug(f"Number of edges: {len(self.network.G.edges)}")

        return subtopic_ids

    def crawl_subtopics(self, ids: List[str]) -> None:
        subsubtopic_ids = set()

        urls = [consts.JSON_BASE_URL.format(id_) for id_ in ids]

        if self.verbose:
            logger.info(f"Getting {len(urls)} JSONs for subtopics...")

        jsons = self.url_dl.get_urls(urls, to_json=True)

        if self.verbose:
            logger.success("Done!")

        for raw_json in jsons:
            # Add subtopic node
            raw_json = raw_json[0]

            subtopic_url = raw_json[consts.KEYS["ID"]]
            subtopic_id = self._extract_id_from_url(subtopic_url)
            labels = self._extract_labels(raw_json, is_subtopic=True)
            cluster = self._extract_cluster(raw_json)

            self.network.add_node(
                node_id=subtopic_id,
                cluster=cluster,
                label_en=labels.get("en"),
                label_ar=labels.get("ar"),
                label_es=labels.get("es"),
                label_fr=labels.get("fr"),
                label_ru=labels.get("ru"),
                label_zh=labels.get("zh"),
                node_type="subtopic",
            )

            # Add edges to related topics
            related_topics = self._extract_related_subtopics(raw_json)

            # Add an edge from a topic to its cluster
            self.network.add_edge(
                source=cluster,
                target=subtopic_id,
            )

            for related_topic in related_topics:
                if related_topic not in self.subtopic_ids:
                    if self.verbose:
                        logger.warning(f"Related topic {related_topic} not found!")

                    subsubtopic_ids.add(related_topic)

                self.network.add_edge(
                    source=subtopic_id,
                    target=related_topic,
                    edge_type="subtopic->related",
                )

            # Extract subtopics from topic
            _subsubtopic_ids = self._extract_subtopic_ids(raw_json)

            # Update the set of subtopic ids
            subsubtopic_ids.update(_subsubtopic_ids)

        if self.verbose:
            logger.success(
                f"Found {len(subsubtopic_ids)} subsubtopics/related subtopics."
            )
            logger.debug(f"Number of nodes: {len(self.network.G.nodes)}")
            logger.debug(f"Number of edges: {len(self.network.G.edges)}")

        return subsubtopic_ids

    def export_to_json(self, file_path: str) -> None:
        """
        Exports the network to a JSON file, which can be used to create a
        Sigma.js network. It has the form:

        ```json
        {
            "nodes": [...],
            "edges": [...]
        }
        ```

        Parameters
        ----------
        `file_path` : `str`
            The path to write the JSON file to
        """
        import json
        import os

        # Create the directory upstream if they don't exist
        dirname = os.path.dirname(file_path)
        if dirname:
            os.makedirs(dirname, exist_ok=True)

        with open(file_path, "w") as f:
            json.dump(self.network.to_json(), f, indent=4, ensure_ascii=False)

        logger.debug(f"Total nodes: {len(self.network.G.nodes)}")
        logger.debug(f"Total edges: {len(self.network.G.edges)}")
        logger.success(f"Saved network JSON to {file_path}!")

    def _extract_labels(
        self,
        json_: Dict[str, Any],
        is_subtopic: bool = False,
    ) -> Dict[str, str]:
        """
        Extracts the labels from their JSON object. It is of the form:

        ```
        [
            {
                "@language": "en",
                "@value": "Agriculture"
            },
            ...
        ]
        ```

        Parameters
        ----------
        `json_` : `Dict[str, Any]`
            JSON object containing the labels

        Returns
        -------
        `Dict[str, str]`
            Correctly formatted JSON object containing the labels
        """
        labels = {}
        key = consts.KEYS["SUBTOPIC_LABELS"] if is_subtopic else consts.KEYS["LABELS"]

        for obj in json_[key]:
            lang = obj[consts.KEYS["LANG"]]
            label = obj[consts.KEYS["VALUE"]]
            labels[lang] = label

        return labels

    def _extract_id_from_url(self, url: str) -> str:
        """
        A URL is of the form:

        ```url
        http://metadata.un.org/thesaurus/{id}
        ```

        This function extracts the id from the URL.

        Parameters
        ----------
        `url` : `str`
            The URL to extract the id from

        Returns
        -------
        `str`
            The extracted id
        """
        return url.split("/")[-1]

    def _extract_topic_ids(self, json_: Dict[str, Any]) -> Set[str]:
        """
        Extracts the topic ids from the `hasTopConcept` key for meta-topics.
        It is of the form:

        ```json
        {
            ...
            "http://www.w3.org/2004/02/skos/core#hasTopConcept":
            [
                {
                    "@id": "http://metadata.un.org/thesaurus/020200"
                },
                ...
            ],
            ...
        }
        ```

        Parameters
        ----------
        `json_` : `Dict[str, Any]`
            The JSON object containing the topic ids

        Returns
        -------
        `Set[str]`
            The list of parsed topic ids
        """
        return self._extract_topics(json_, consts.KEYS["TOPICS"])

    def _extract_subtopic_ids(self, json_: Dict[str, Any]) -> Set[str]:
        """
        Extracts the subtopic ids from the `narrower` key for topics.
        It is of the form:

        ```json
        {
            ...
            "http://www.w3.org/2004/02/skos/core#narrower":
            [
                {
                    "@id": "http://metadata.un.org/thesaurus/020200"
                },
                ...
            ],
            ...
        }
        ```

        Parameters
        ----------
        `json_` : `Dict[str, Any]`
            The JSON object containing the subtopic ids

        Returns
        -------
        `Set[str]`
            The list of parsed subtopic ids
        """
        return self._extract_topics(json_, consts.KEYS["SUBTOPICS"])

    def _extract_related_subtopics(self, json_: Dict[str, Any]) -> Set[str]:
        """
        Extracts the related subtopic ids from the `related` key for subtopics.
        It is of the form:

        ```json
        {
            ...
            "http://www.w3.org/2004/02/skos/core#related":
            [
                {
                    "@id": "http://metadata.un.org/thesaurus/020200"
                },
                ...
            ],
            ...
        }
        ```

        Parameters
        ----------
        `json_` : `Dict[str, Any]`
            The JSON object containing the related subtopic ids

        Returns
        -------
        `Set[str]`
            The list of parsed related subtopic ids
        """
        return self._extract_topics(json_, consts.KEYS["RELATED"])

    def _extract_topics(self, json_: Dict[str, Any], key: str) -> Set[str]:
        """
        Generic function to extract topics for all types of nodes.

        Parameters
        ----------
        `json_` : `Dict[str, Any]`
            The JSON object containing the topics
        `key` : `str`
            The key to extract the topics from (e.g. `hasTopConcept`)

        Returns
        -------
        `Set[str]`
            The list of parsed topics
        """
        topics = set()
        if key not in json_:
            return topics

        for obj in json_[key]:
            url = obj[consts.KEYS["ID"]]
            id_ = self._extract_id_from_url(url)
            topics.add(id_)

        return topics

    def _extract_cluster(self, json_: Dict[str, Any]) -> Union[int, None]:
        if consts.KEYS["CLUSTER"] not in json_:
            if self.verbose:
                logger.error(
                    f"Key {consts.KEYS['CLUSTER']} not found in JSON object in {json_[consts.KEYS['ID']]}"
                )
            return consts.UNKNOWN_CLUSTER
        else:
            clusters = json_[consts.KEYS["CLUSTER"]]
            return self._extract_id_from_url(clusters[0][consts.KEYS["ID"]])
