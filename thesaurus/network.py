import random
from typing import Any, Dict, List, Optional

import networkx as nx
from loguru import logger
from tqdm import tqdm

import thesaurus.consts as consts


class Network:
    """
    Network class that represents the graph of the UNBIS Thesaurus.
    """

    def __init__(self, verbose: bool = False) -> None:
        self.G = nx.Graph(name="UNBIS Thesaurus")
        self.clusters: List[str] = []

        self.verbose = verbose

    def addNode(
        self,
        nodeId: str,
        cluster: int,
        labelEn: Optional[str] = None,
        labelAr: Optional[str] = None,
        labelEs: Optional[str] = None,
        labelFr: Optional[str] = None,
        labelRu: Optional[str] = None,
        labelZh: Optional[str] = None,
        nodeType: str = "topic",
    ) -> None:
        """
        Adds a node to the graph. Also saves the node id to the set of node ids.
        Node size and color are defined in `consts.py` and are based on the node type.

        Parameters
        ----------
        `nodeId` : `str`
            Unique id of the node, same as in UNBIS Thesaurus
        `cluster` : `int`
            Cluster id of the node
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

        # Save node id to set of node ids
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

    def addEdge(
        self,
        source: str,
        target: str,
        edgeType: str = "topic->subtopic",
    ) -> None:
        """
        Adds an edge to the graph. Edge type is defined in `consts.py` and is based on the edge type.

        Parameters
        ----------
        `source` : `str`
            Source node id
        `target` : `str`
            Target node id
        `edgeType` : `str`, optional
            Edge type, by default `"topic->subtopic"`
        """
        assert edgeType in consts.EDGE_TYPES, f"Invalid edge type {edgeType}"

        edge_id = (source, target)

        self.G.add_edge(*edge_id, edge_type=edgeType)

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
