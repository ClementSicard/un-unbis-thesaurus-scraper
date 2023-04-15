import random
from typing import Optional

import src.consts as consts
from loguru import logger


class Network:
    def __init__(self, verbose: bool = False) -> None:
        self.json = {
            "nodes": [],
            "edges": [],
        }

        self.verbose = verbose
        self.node_ids = set()
        self.edge_ids = set()

    def add_node(
        self,
        node_id: str,
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

        if node_id not in self.node_ids:
            # Save node id to set of node ids
            self.node_ids.add(node_id)

            node_json = {
                "key": node_id,
                "x": random.random(),
                "y": random.random(),
                "attributes": {
                    "node_type": node_type,
                    "color": consts.COLORS[node_type],
                    "size": consts.SIZES[node_type],
                    "label": label_en,
                    "label_ar": label_ar,
                    "label_es": label_es,
                    "label_fr": label_fr,
                    "label_ru": label_ru,
                    "label_zh": label_zh,
                },
            }

            self.json["nodes"].append(node_json)
        else:
            logger.warning(f"Node {node_id} already exists")

    def add_edge(
        self,
        edge_id: str,
        source: str,
        target: str,
        size: float = 1.0,
        label: Optional[str] = None,
        edge_type: str = "topic->subtopic",
    ) -> None:
        assert edge_type in consts.EDGE_TYPES, f"Invalid edge type {edge_type}"

        if edge_id not in self.edge_ids:
            # Save edge id to set of edge ids
            self.edge_ids.add(edge_id)

            edge_json = {
                "key": edge_id,
                "source": source,
                "target": target,
                "attributes": {
                    "edge_type": edge_type,
                    "size": size,
                    "label": label,
                    "color": consts.COLORS[edge_type],
                },
            }

            self.json["edges"].append(edge_json)
        else:
            logger.warning(f"Edge {edge_id} already exists")
