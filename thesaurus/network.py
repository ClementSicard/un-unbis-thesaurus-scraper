import random
from typing import Optional

import networkx as nx
from tqdm import tqdm

import thesaurus.consts as consts


class Network:
    def __init__(self, verbose: bool = False) -> None:
        self.G = nx.Graph(name="UNBIS Thesaurus")

        self.verbose = verbose

    def add_node(
        self,
        node_id: str,
        cluster: int,
        label_en: Optional[str] = None,
        label_ar: Optional[str] = None,
        label_es: Optional[str] = None,
        label_fr: Optional[str] = None,
        label_ru: Optional[str] = None,
        label_zh: Optional[str] = None,
        node_type: str = "topic",
    ) -> None:
        """
        Adds a node to the graph. Also saves the node id to the set of node ids.
        Node size and color are defined in `consts.py` and are based on the node type.

        Parameters
        ----------
        `node_id` : `str`
            Unique id of the node, same as in UNBIS Thesaurus
        `label_en` : `Optional[str]`, optional
            Label in English, by default None
        `label_ar` : `Optional[str]`, optional
            Label in Arabic, by default None
        `label_es` : `Optional[str]`, optional
            Label in Spanish, by default None
        `label_fr` : `Optional[str]`, optional
            Label in French, by default None
        `label_ru` : `Optional[str]`, optional
            Label in Russian, by default None
        `label_zh` : `Optional[str]`, optional
            Label in Chinese, by default None
        `type_` : `str`, optional
            Type of node, by default "topic". Must be one of "meta_topic", "topic", "subtopic"
        """
        assert node_type in consts.NODE_TYPES, f"Invalid type {node_type}"

        # Save node id to set of node ids
        node_json = {
            "key": node_id,
            "x": (random.random() - 0.5) * 1000,
            "y": (random.random() - 0.5) * 1000,
            "cluster": cluster,
            "url": consts.BASE_URL.format(node_id),
            "node_type": node_type,
            "tag": "Concept",
            "label": label_en,
            "label_ar": label_ar,
            "label_es": label_es,
            "label_fr": label_fr,
            "label_ru": label_ru,
            "label_zh": label_zh,
        }

        self.G.add_node(node_id, **node_json)

    def add_edge(
        self,
        source: str,
        target: str,
        edge_type: str = "topic->subtopic",
    ) -> None:
        assert edge_type in consts.EDGE_TYPES, f"Invalid edge type {edge_type}"

        edge_id = (source, target)

        self.G.add_edge(*edge_id, edge_type=edge_type)

    def to_json(self) -> dict:
        """
        Returns
        -------
        `dict`
            JSON representation of the graph
        """
        j = nx.readwrite.json_graph.node_link_data(self.G, link="edges")

        # Replace weird format for edges
        edges = [[e["source"], e["target"]] for e in j["edges"]]
        j["edges"] = edges

        centrality = nx.betweenness_centrality(self.G)
        for node in tqdm(j["nodes"]):
            node["score"] = centrality.get(node["key"], 0)

        # Add clusters & tags
        j["clusters"] = consts.CLUSTERS
        j["tags"] = consts.TAGS

        return j
