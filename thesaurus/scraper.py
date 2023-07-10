import json
import sys
from typing import Dict, Optional, Set

from bs4 import BeautifulSoup
from loguru import logger
from tqdm import tqdm

import thesaurus.consts as consts
import thesaurus.utils as utils
from thesaurus.consts import JSON
from thesaurus.network import Network


class UNBISThesaurusScraper:
    """
    This class is responsible for crawling the UNBIS Thesaurus and recursively
    creating a graph of the topics and subtopics. It uses the `Network`
    class to create the graph.
    """

    def __init__(self, verbose: bool, boltURL: Optional[str] = None) -> None:
        self.verbose = verbose
        self.urlDownloader = utils.FastURLDownloader(verbose=self.verbose)
        self.BASE_URL = "https://metadata.un.org/thesaurus/categories?lang=en"

        # Save all the ids to avoid duplicates
        self.network = Network(verbose=self.verbose, boltURL=boltURL)
        self.metaTopicsIds: Set[str] = set()
        self.topicIds: Set[str] = set()
        self.subtopicIds: Set[str] = set()

    def crawl(self) -> JSON:
        """
        Crawls the whole UNBIS Thesaurus and returns the graph JSON.
        It first gets the meta topics, then the topics, and finally
        the subtopics, by getting each JSON file for each topic and
        parsing its content.

        Returns
        -------
        `JSON`
            The graph JSON
        """
        try:
            logger.info("Started crawling the UNBIS Thesaurus...")
            self.metaTopicsIds = self.getMetaTopicsIds()
            self.topicIds = self.crawlMetaTopics(ids=self.metaTopicsIds)
            self.subtopicIds = self.crawlTopics(ids=self.topicIds)

            logger.info("Recusrively crawling subsubtopics...")
            i = 1
            unexplored = self.subtopicIds
            while True:
                unexplored = self.crawlSubtopics(ids=unexplored)
                self.subtopicIds.update(unexplored)

                logger.debug(f"Unexplored: {len(unexplored)} at iteration {i}")
                if len(unexplored) == 0:
                    break
                i += 1

            if self.verbose:
                logger.debug(f"Meta topics: {self.metaTopicsIds}")
                logger.debug(f"Meta topics: {len(self.metaTopicsIds)}")
                logger.debug(f"Topics: {len(self.topicIds)}")
                logger.debug(f"Subtopics: {len(self.subtopicIds)}")
                logger.debug(f"Number of nodes: {len(self.network.G.nodes)}")
                logger.debug(f"Number of edges: {len(self.network.G.edges)}")

            return self.network.toJson()
        except Exception as e:
            logger.error(e)
            # Delete everything in the DB if it exists
            if self.network.useNeo4j:
                self.network.graphDB.askToDeleteEverything()
            exit(1)
        except KeyboardInterrupt:
            logger.error("Keyboard interrupt. Stopping now.")

            # Delete everything in the DB if it exists
            if self.network.useNeo4j:
                self.network.graphDB.askToDeleteEverything()
            exit(0)

    def getMetaTopicsIds(self) -> Set[str]:
        """
        This function parses the home page of the Thesaurus and returns the
        meta topics ids. It doesn't add nodes to the graph - it only returns
        the ids.

        Returns
        -------
        `Set[str]`
            The set of meta topic ids
        """
        metaTopicsIds: Set[str] = set()
        html = self.urlDownloader.getHtmlFromURL(self.BASE_URL)
        soup = BeautifulSoup(html, "html.parser")

        class_ = "row collapsible"
        rawMetaTopics = soup.find_all(class_=class_)

        for rawMetaTopic in rawMetaTopics:
            metaTopicName = rawMetaTopic.find(class_="bc-link domain").text
            metaTopicId = metaTopicName.split(" - ")[0]
            metaTopicsIds.add(metaTopicId)

        if self.verbose:
            logger.success(f"Found {len(metaTopicsIds)} meta topics.")
            logger.debug(f"Number of nodes: {len(self.network.G.nodes)}")
            logger.debug(f"Number of edges: {len(self.network.G.edges)}")

        return metaTopicsIds

    def crawlMetaTopics(self, ids: Set[str]) -> Set[str]:
        """
        Crawls the meta topics and adds them to the graph.

        Parameters
        ----------
        `ids` : `Set[str]`
            The list of meta topic IDs

        Returns
        -------
        `Set[str]`
            The set of topic IDs
        """
        topicIds: Set[str] = set()

        urls = [consts.JSON_BASE_URL.format(id_) for id_ in ids]

        if self.verbose:
            logger.info(f"Getting {len(urls)} JSONs for meta topics...")

        jsons = self.urlDownloader.getURLs(urls, toJson=True)

        if self.verbose:
            logger.success("Done!")

        for rawJson in tqdm(
            jsons,
            desc="Crawling meta-topics",
            disable=not self.verbose,
            unit="metatopic",
            total=len(jsons),
            file=sys.stderr,
        ):
            # Add meta-topic node
            rawJson = rawJson[0]

            metaTopicUrl = rawJson[consts.KEYS["ID"]]
            metaTopicId = self._extractIdFromURL(metaTopicUrl)
            labels = self._extractLabels(rawJson)

            self.network.addNode(
                nodeId=metaTopicId,
                cluster=metaTopicId,
                labelEn=labels.get("en"),
                labelAr=labels.get("ar"),
                labelEs=labels.get("es"),
                labelFr=labels.get("fr"),
                labelRu=labels.get("ru"),
                labelZh=labels.get("zh"),
                nodeType="MetaTopic",
            )

            self.network.clusters.append(
                {
                    "key": metaTopicId,
                    "cluster_label_en": labels.get("en"),
                    "cluster_label_ar": labels.get("ar"),
                    "cluster_label_es": labels.get("es"),
                    "cluster_label_fr": labels.get("fr"),
                    "cluster_label_ru": labels.get("ru"),
                    "cluster_label_zh": labels.get("zh"),
                    "color": consts.CLUSTERS_COLORS[int(metaTopicId) - 1],
                }
            )

            # Extract topics from meta-topic
            _topicIds = self._extractTopicIDs(rawJson)

            # Update the set of topic ids
            topicIds.update(_topicIds)

            # Add edges between meta-topic and topics
            for topicId in _topicIds:
                self.network.addEdge(
                    source=metaTopicId,
                    target=topicId,
                )

        if self.verbose:
            logger.success(f"Found {len(topicIds)} topics.")
            logger.debug(f"Number of nodes: {len(self.network.G.nodes)}")
            logger.debug(f"Number of edges: {len(self.network.G.edges)}")

        return topicIds

    def crawlTopics(self, ids: Set[str]) -> Set[str]:
        """
        Crawls the topics and adds them to the graph.

        Parameters
        ----------
        `ids` : `List[str]`
            The list of topic IDs

        Returns
        -------
        `Set[str]`
            The set of subtopic IDs
        """
        subtopicIds: Set[str] = set()

        urls = [consts.JSON_BASE_URL.format(id_) for id_ in ids]

        if self.verbose:
            logger.info(f"Getting {len(urls)} JSONs for topics...")

        jsons = self.urlDownloader.getURLs(urls, toJson=True)

        if self.verbose:
            logger.success("Done!")

        for rawJson in tqdm(
            jsons,
            desc="Crawling topics",
            disable=not self.verbose,
            unit="topic",
            total=len(jsons),
            file=sys.stderr,
        ):
            # Add topic node
            rawJson = rawJson[0]

            topicUrl = rawJson[consts.KEYS["ID"]]
            topicId = self._extractIdFromURL(topicUrl)
            labels = self._extractLabels(rawJson)
            cluster = self._extractCluster(rawJson)

            self.network.addNode(
                nodeId=topicId,
                cluster=cluster,
                labelEn=labels.get("en"),
                labelAr=labels.get("ar"),
                labelEs=labels.get("es"),
                labelFr=labels.get("fr"),
                labelRu=labels.get("ru"),
                labelZh=labels.get("zh"),
                nodeType="Topic",
            )

            # Extract subtopics from topic
            _subtopicIds = self._extractSubtopicIDs(rawJson)

            # Update the set of subtopic ids
            subtopicIds.update(_subtopicIds)

            # Add an edge from a topic to its cluster
            self.network.addEdge(
                source=cluster,
                target=topicId,
            )

            # Add edges between topic and subtopics
            if not _subtopicIds:
                logger.error(f"No subtopics found for topic {topicId}")
                logger.warning(f"JSON: {json.dumps(rawJson, indent=4)}")

            for subtopicId in _subtopicIds:
                self.network.addEdge(
                    source=topicId,
                    target=subtopicId,
                )

        if self.verbose:
            logger.success(f"Found {len(subtopicIds)} subtopics.")
            logger.debug(f"Number of nodes: {len(self.network.G.nodes)}")
            logger.debug(f"Number of edges: {len(self.network.G.edges)}")

        return subtopicIds

    def crawlSubtopics(self, ids: Set[str]) -> Set[str]:
        """
        Crawls the subtopics and adds them to the graph.

        Parameters
        ----------
        `ids` : `Set[str]`
            The list of subtopic IDs

        Returns
        -------
        `Set[str]`
            The list of subsubtopic IDs
        """
        subSubtopicIds: Set[str] = set()

        urls = [consts.JSON_BASE_URL.format(id_) for id_ in ids]

        if self.verbose:
            logger.info(f"Getting {len(urls)} JSONs for subtopics...")

        jsons = self.urlDownloader.getURLs(urls, toJson=True)

        if self.verbose:
            logger.success("Done!")

        for rawJson in tqdm(
            jsons,
            desc="Crawling subtopics",
            disable=not self.verbose,
            unit="subtopic",
            total=len(jsons),
            file=sys.stderr,
        ):
            if not rawJson:
                logger.warning("Empty JSON")
                continue
            # Add subtopic node
            rawJson = rawJson[0]

            subtopicUrl = rawJson[consts.KEYS["ID"]]
            subtopicId = self._extractIdFromURL(subtopicUrl)
            labels = self._extractLabels(rawJson, isSubtopic=True)
            cluster = self._extractCluster(rawJson)

            self.network.addNode(
                nodeId=subtopicId,
                cluster=cluster,
                labelEn=labels.get("en"),
                labelAr=labels.get("ar"),
                labelEs=labels.get("es"),
                labelFr=labels.get("fr"),
                labelRu=labels.get("ru"),
                labelZh=labels.get("zh"),
                nodeType="Topic",
            )

            # Add edges to related topics
            relatedTopics = self._extractRelatedSubtopics(rawJson)

            # Add an edge from a topic to its cluster
            self.network.addEdge(
                source=cluster,
                target=subtopicId,
            )

            for relatedTopic in relatedTopics:
                if relatedTopic not in self.subtopicIds:
                    if self.verbose:
                        logger.warning(f"Related topic {relatedTopic} not found!")

                    subSubtopicIds.add(relatedTopic)

                self.network.addEdge(
                    source=subtopicId,
                    target=relatedTopic,
                    isRelatedTo=True,
                )

            # Extract subtopics from topic
            _subSubtopicIds = self._extractSubtopicIDs(rawJson)

            # Update the set of subtopic ids
            subSubtopicIds.update(_subSubtopicIds)

        if self.verbose:
            logger.success(
                f"Found {len(subSubtopicIds)} subsubtopics/related subtopics."
            )
            logger.debug(f"Number of nodes: {len(self.network.G.nodes)}")
            logger.debug(f"Number of edges: {len(self.network.G.edges)}")

        return subSubtopicIds

    def exportToJson(self, filePath: str) -> None:
        """
        Exports the network to a JSON file, which can be used to create a
        Sigma.js network. It has the form:

        ```json
        {
            "nodes": [...],
            "edges": [...],
            "clusters": [...]
        }
        ```

        Parameters
        ----------
        `filePath` : `str`
            The path to write the JSON file to
        """
        import json
        import os

        # Create the directory upstream if they don't exist
        dirname = os.path.dirname(filePath)
        if dirname:
            os.makedirs(dirname, exist_ok=True)

        with open(filePath, "w") as f:
            json.dump(self.network.toJson(), f, indent=4, ensure_ascii=False)

        logger.debug(f"Total nodes: {len(self.network.G.nodes)}")
        logger.debug(f"Total edges: {len(self.network.G.edges)}")
        logger.success(f"Saved network JSON to {filePath}!")

    def _extractLabels(
        self,
        json_: JSON,
        isSubtopic: bool = False,
    ) -> Dict[str, str]:
        """
        Extracts the labels from their JSON object. It is of the form:

        ```json
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
        `json_` : `JSON`
            JSON object containing the labels
        `isSubtopic` : `bool`, optional
            Flag to indicate a subtopic context. The function will use different keys
            depending on its value. By default `False`

        Returns
        -------
        `Dict[str, str]`
            Correctly formatted JSON object containing the labels
        """

        labels: Dict[str, str] = {}
        key = consts.KEYS["SUBTOPIC_LABELS"] if isSubtopic else consts.KEYS["LABELS"]

        for obj in json_[key]:  # type: ignore
            lang = obj[consts.KEYS["LANG"]]
            label = obj[consts.KEYS["VALUE"]]
            labels[lang] = label

        return labels

    def _extractIdFromURL(self, url: str) -> str:
        """
        A URL is of the form:

        ```url
        http://metadata.un.org/thesaurus/{id}
        ```

        This function extracts the ID from the URL.

        Parameters
        ----------
        `url` : `str`
            The URL to extract the ID from

        Returns
        -------
        `str`
            The extracted ID
        """
        return url.split("/")[-1]

    def _extractTopicIDs(self, json_: JSON) -> Set[str]:
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
        `json_` : `JSON`
            The JSON object containing the topic ids

        Returns
        -------
        `Set[str]`
            The list of parsed topic ids
        """
        return self._extractTopics(json_, consts.KEYS["TOPICS"], verbose=True)

    def _extractSubtopicIDs(self, json_: JSON) -> Set[str]:
        """
        Extracts the subtopic ids from the `"narrower"` key for topics.
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
        `json_` : `JSON`
            The JSON object containing the subtopic IDs

        Returns
        -------
        `Set[str]`
            The list of parsed subtopic IDs
        """
        return self._extractTopics(json_, consts.KEYS["SUBTOPICS"], verbose=True)

    def _extractRelatedSubtopics(self, json_: JSON) -> Set[str]:
        """
        Extracts the related subtopic IDs from the `related` key for subtopics.
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
        `json_` : `JSON`
            The JSON object containing the related subtopic IDs

        Returns
        -------
        `Set[str]`
            The list of parsed related subtopic IDs
        """
        return self._extractTopics(json_, consts.KEYS["RELATED"], verbose=True)

    def _extractTopics(
        self,
        json_: JSON,
        key: str,
        verbose: bool = False,
    ) -> Set[str]:
        """
        Generic function to extract topics for all types of nodes.

        Parameters
        ----------
        `json_` : `JSON`
            The JSON object containing the topics
        `key` : `str`
            The key to extract the topics from (e.g. `hasTopConcept`)
        `verbose` : `bool`, optional
            Controls the verbose of the output, by default `False`

        Returns
        -------
        `Set[str]`
            The list of parsed topics
        """
        topics: Set[str] = set()

        if key not in json_:
            return topics

        for obj in json_[key]:
            url = obj[consts.KEYS["ID"]]
            id_ = self._extractIdFromURL(url)
            topics.add(id_)

        return topics

    def _extractCluster(self, json_: JSON) -> str:
        """
        Extracts the cluster ID from the `consts.KEYS["CLUSTER"]` key for topics and subtopics.

        Parameters
        ----------
        `json_` : `JSON`
            The JSON object containing the cluster ID

        Returns
        -------
        `str`
            The cluster ID if found, `consts.UNKNOWN_CLUSTER` otherwise
        """
        if consts.KEYS["CLUSTER"] not in json_:
            if self.verbose:
                logger.error(
                    f"Key {consts.KEYS['CLUSTER']} not found in JSON object in {json_[consts.KEYS['ID']]}"
                )
            return consts.UNKNOWN_CLUSTER
        else:
            clusters = json_[consts.KEYS["CLUSTER"]]
            return self._extractIdFromURL(clusters[0][consts.KEYS["ID"]])
