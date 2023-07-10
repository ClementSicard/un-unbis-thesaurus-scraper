import random
from typing import Any, Dict, List, Optional

import networkx as nx
from loguru import logger
from tqdm import tqdm

import thesaurus.consts as consts
from thesaurus.graphdb import GraphDB


class Network:
    """
    Network class that represents the graph of the UNBIS Thesaurus.
    """

    boltURL: Optional[str]
    graphDB: GraphDB
    G: nx.Graph
    clusters: List[str]
    verbose: bool
    useNeo4j: bool = False

    def __init__(self, boltURL: Optional[str] = None, verbose: bool = False) -> None:
        self.boltURL = boltURL

        if self.boltURL is not None:
            logger.info("Initializing Neo4j connector...")
            self.graphDB = GraphDB(self.boltURL, verbose=verbose)
            try:
                self.graphDB.checkConnection()
                self.useNeo4j = True
                logger.success("Done!")
            except ConnectionError:
                logger.error("Could not connect to Neo4j database")
                raise ConnectionError("Could not connect to Neo4j database")

        self.G = nx.Graph(name="UNBIS Thesaurus")
        self.clusters: List[Dict[str, Optional[Any]]] = []

        self.verbose = verbose

    def addNode(
        self,
        nodeId: str,
        cluster: str,
        labelEn: Optional[str] = None,
        labelAr: Optional[str] = None,
        labelEs: Optional[str] = None,
        labelFr: Optional[str] = None,
        labelRu: Optional[str] = None,
        labelZh: Optional[str] = None,
        nodeType: str = "topic",
    ) -> None:
        """
        Adds a node to the graph. Also saves the node ID to the set of node ids.
        Node size and color are defined in `consts.py` and are based on the node type.

        Parameters
        ----------
        `nodeId` : `str`
            Unique ID of the node, same as in UNBIS Thesaurus
        `cluster` : `str`
            Cluster ID of the node
        `labelEn` : `Optional[str]`, optional
            Label in English, by default `None`
        `labelAr` : `Optional[str]`, optional
            Label in Arabic, by default `None`
        `labelEs` : `Optional[str]`, optional
            Label in Spanish, by default `None`
        `labelFr` : `Optional[str]`, optional
            Label in French, by default `None`
        `labelRu` : `Optional[str]`, optional
            Label in Russian, by default `None`
        `labelZh` : `Optional[str]`, optional
            Label in simplified Chinese, by default `None`
        `nodeType` : `str`, optional
            Type of node, by default `"topic"`. Must be one of `"meta_topic"`, `"topic"`, `"subtopic"`
        """

        assert nodeType in consts.NODE_TYPES, f"Invalid type {nodeType}"

        # Save node ID to set of node ids
        node_json = {
            "key": nodeId,
            "x": (random.random() - 0.5) * 1000,
            "y": (random.random() - 0.5) * 1000,
            "cluster": cluster,
            "url": consts.BASE_URL.format(nodeId),
            "node_type": nodeType,
            "tag": "Concept",
            "label_en": labelEn,
            "label_ar": labelAr,
            "label_es": labelEs,
            "label_fr": labelFr,
            "label_ru": labelRu,
            "label_zh": labelZh,
        }

        self.G.add_node(nodeId, **node_json)

        if self.useNeo4j:
            self.graphDB.createOrUpdateNodeIfExists(
                nodeId=nodeId,
                cluster=cluster,
                labelEn=labelEn,
                labelAr=labelAr,
                labelEs=labelEs,
                labelFr=labelFr,
                labelRu=labelRu,
                labelZh=labelZh,
                nodeType=nodeType,
            )

    def addEdge(
        self,
        source: str,
        target: str,
        isRelatedTo: bool = False,
    ) -> None:
        """
        Adds an edge to the graph. If the edge already exists, it does nothing.

        If a Neo4j connector is used, it also adds the edge to the graph database.

        Parameters
        ----------
        `source` : `str`
            Source node id
        `target` : `str`
            Target node id
        `isRelatedTo` : `bool`, optional
            Whether the edge is a "related to" edge, by default `False`
        """

        edge_id = (source, target)

        self.G.add_edge(*edge_id)

        if self.useNeo4j:
            self.graphDB.createEdge(
                source=source,
                target=target,
                isRelatedTo=isRelatedTo,
            )

    def toJson(self) -> Dict[str, Any]:
        """
        Converts the graph to a json format that can be used by the frontend.

        Returns
        -------
        `Dict[str, Any]`
            JSON representation of the graph (as a dict here)
        """
        j: Dict[str, Any] = nx.readwrite.json_graph.node_link_data(self.G, link="edges")

        # Replace weird format for edges
        edges = [[e["source"], e["target"]] for e in j["edges"]]
        j["edges"] = edges

        logger.info("Calculating betweenness centrality...")
        centrality = nx.eigenvector_centrality(self.G)
        logger.success("Done!")

        for node in tqdm(j["nodes"]):
            node["score"] = centrality.get(node["key"], 0)

        # Add clusters to json
        j["clusters"] = self.clusters

        return j
