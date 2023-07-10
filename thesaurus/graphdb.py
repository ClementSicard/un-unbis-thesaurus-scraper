from typing import Any, Dict, List, Optional

from loguru import logger
from neo4j import EagerResult, GraphDatabase
from neo4j._data import Record

from thesaurus.consts import GraphDBConsts


class GraphDB:
    """
    GraphDB class is a class that handles the connection to a `neo4j` GraphDB.
    """

    _instance: Optional["GraphDB"] = None

    def __new__(cls, *_: Any, **__: Any) -> "GraphDB":
        """
        GraphDB constructor to ensure singleton pattern.

        Returns
        -------
        `GraphDB`
            The GraphDB instance
        """
        if not isinstance(cls._instance, cls):
            cls._instance = object.__new__(cls)
            logger.info("Created a new GraphDB instance")

        return cls._instance

    def __init__(self, boltURL: str, verbose: bool = False) -> None:
        """
        GraphDB constructor
        """
        self.URI = boltURL
        self.AUTH = GraphDBConsts.AUTH
        self.driver = GraphDatabase.driver(self.URI, auth=self.AUTH)

        self.verbose = verbose

    def __del__(self) -> None:
        """
        GraphDB destructor: when object gets destroyed, close the driver
        """
        self.driver.close()

    def query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        returnSummary: bool = False,
    ) -> List[Record] | EagerResult:
        """
        Execute a query on the GraphDB.

        Parameters
        ----------
        `query` : `str`
            Query to execute
        `params` : `Optional[Dict[str, Any]]`, optional
            Parameters of the query to be replaced, by default `None`
        `returnSummary` : `bool`, optional
            Return the summary or not. If `True`, returns the summary,
            otherwise returns the records, by default `False`
        `verbose` : `bool`, optional
            Controls the verbose of the output, by default `False`

        Returns
        -------
        `List[Record] | EagerResult`
            List of records returned by the query
        """
        querySummary = self.driver.execute_query(
            query_=query,
            parameters_=params,
        )

        records, summary, _ = querySummary

        if self.verbose and len(records) == 0 and "topictosubtopic" in query.lower():
            logger.debug(
                "The query `{query}` with params `{params}` returned {records_count} records in {time} ms.".format(
                    query=summary.query,
                    params=params,
                    records_count=len(records),
                    time=summary.result_available_after,
                ),
            )

        return summary if returnSummary else records

    def checkConnection(self) -> None:
        """
        Check if the connection to the GraphDB is successful.

        Raises
        ------
        `ConnectionError`
            If the connection is not successful
        """
        try:
            self.driver.verify_connectivity()
        except Exception as e:
            raise ConnectionError(
                f"Could not connect to the GraphDB at {self.URI} with auth {self.AUTH}"
            ) from e

    def createOrUpdateNodeIfExists(
        self,
        nodeId: str,
        cluster: Optional[str] = None,
        labelEn: Optional[str] = None,
        labelAr: Optional[str] = None,
        labelEs: Optional[str] = None,
        labelFr: Optional[str] = None,
        labelRu: Optional[str] = None,
        labelZh: Optional[str] = None,
        nodeType: str = "Topic",
    ) -> None:
        """
        Create a node in the GraphDB.

        The corresponding Cypher query is:

        ```cypher
        MERGE (n: {nodeType} {
            id: $nodeId,
        })
        SET
            n.cluster: $cluster,
            n.labelEn: $labelEn,
            n.labelAr: $labelAr,
            n.labelEs: $labelEs,
            n.labelFr: $labelFr,
            n.labelRu: $labelRu,
            n.labelZh: $labelZh
        ```

        This allows to create a node with the given `nodeId` and `cluster` if it does not exist,
        and set the labels to the given values if they are not `None`.
        If it exists, it does nothing.

        Parameters
        ----------
        `nodeId` : `str`
            Unique ID of the node, same as in UNBIS Thesaurus
        `cluster` : `Optional[str]`, optional
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
            Label in Chinese, by default `None`
        `nodeType` : `str`, optional
            Node type, by default `"topic"`
        """
        query = f"""
        MERGE (n: {nodeType} {{ id: $nodeId }})
        SET
            n.cluster = $cluster,
            n.labelEn = $labelEn,
            n.labelAr = $labelAr,
            n.labelEs = $labelEs,
            n.labelFr = $labelFr,
            n.labelRu = $labelRu,
            n.labelZh = $labelZh
        """

        params = {
            "nodeId": nodeId,
            "cluster": cluster,
            "labelEn": labelEn if labelEn else "",
            "labelAr": labelAr if labelAr else "",
            "labelEs": labelEs if labelEs else "",
            "labelFr": labelFr if labelFr else "",
            "labelRu": labelRu if labelRu else "",
            "labelZh": labelZh if labelZh else "",
        }

        self.query(query, params)

    def createEmptyNodeIfNotExists(
        self,
        nodeId: str,
        nodeType: str = "Topic",
    ) -> None:
        """
        Create a node in the GraphDB.

        The corresponding Cypher query is:

        ```cypher
        MERGE (n: {nodeType} { id: $nodeId })

        ```

        This allows to create a node with the given `nodeId` and `cluster` if it does not exist,
        and set the labels to the given values if they are not `None`.
        If it exists, it does nothing.

        Parameters
        ----------
        `nodeId` : `str`
            Unique ID of the node, same as in UNBIS Thesaurus
        `cluster` : `int`
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
            Label in Chinese, by default `None`
        `nodeType` : `str`, optional
            Node type, by default `"topic"`
        """
        query = f"""
        MERGE (n: {nodeType} {{ id: $nodeId }})
        """

        params = {"nodeId": nodeId}

        self.query(query, params)

    def createEdge(
        self,
        source: str,
        target: str,
        isRelatedTo: bool = False,
    ) -> List[Record] | EagerResult:
        """
        Create an edge in the GraphDB.

        The corresponding Cypher query is:

        ```cypher
        MATCH (source {id: $source})
        MERGE (target {id: $target})
        MERGE (source)-[r:HAS_SUBTOPIC]->(target)
        ```

        Parameters
        ----------
        `source` : `str`
            Source node ID
        `target` : `str`
            Target node ID
        `isRelatedTo` : `bool`, optional
            Whether the edge is related to the source node or not, by default `False`
        """

        # First create the target node if it does not exist
        self.createEmptyNodeIfNotExists(nodeId=target)

        if not isRelatedTo:
            query = r"""
            MATCH (source {id: $source})
            MERGE (target {id: $target})
            MERGE (source)-[r:HAS_SUBTOPIC]->(target)
            """
        else:
            query = r"""
            MATCH (source {id: $source})
            MERGE (target {id: $target})
            MERGE (source)-[r:RELATED_TO]-(target)
            """

        params = {
            "source": source,
            "target": target,
        }

        return self.query(query, params)

    def askToDeleteEverything(self) -> None:
        """
        Delete everything in the GraphDB.
        """
        logger.warning(
            "Are you sure you want to delete everything in the Neo4j instance? (Y/n) "
        )
        accept = input()

        if accept == "Y":
            query = """
            MATCH (n)
            DETACH DELETE n
            """

            self.query(query)

            logger.success("Deleted everything in the Neo4j instance!")
        else:
            logger.info("Aborting deletion")
