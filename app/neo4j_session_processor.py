import logging
import os
import pandas as pd
import json
from neo4j import GraphDatabase
from dotenv import load_dotenv
import csv
import inspect


class Neo4jSessionProcessor:
    """
    A class to process session data and upload it to Neo4j database.
    This class is responsible for loading CSV files and creating session nodes,
    stream nodes, and relationships between them in Neo4j.
    """

    def __init__(self, config):
        """
        Initialize the Neo4j Session Processor.

        Args:
            config (dict): Configuration dictionary containing paths and settings
        """
        self.logger = logging.getLogger(__name__)
        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Initializing Neo4j Session Processor"
        )

        self.config = config
        self.output_dir = os.path.join(config["output_dir"], "output")

        # Load the environment variables to get Neo4j credentials
        load_dotenv(config["env_file"])
        self.uri = os.getenv("NEO4J_URI")
        self.username = os.getenv("NEO4J_USERNAME")
        self.password = os.getenv("NEO4J_PASSWORD")

        if not self.uri or not self.username or not self.password:
            self.logger.error(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Missing Neo4j credentials in .env file"
            )
            raise ValueError("Missing Neo4j credentials in .env file")

        self.statistics = {
            "nodes_created": {
                "sessions_this_year": 0,
                "sessions_past_year_bva": 0,
                "sessions_past_year_lva": 0,
                "streams": 0,
            },
            "nodes_skipped": {
                "sessions_this_year": 0,
                "sessions_past_year_bva": 0,
                "sessions_past_year_lva": 0,
                "streams": 0,
            },
            "relationships_created": {
                "sessions_this_year_has_stream": 0,
                "sessions_past_year_has_stream": 0,
            },
            "relationships_skipped": {
                "sessions_this_year_has_stream": 0,
                "sessions_past_year_has_stream": 0,
            },
        }

        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Neo4j Session Processor initialized successfully"
        )

    def _test_connection(self):
        """Test the connection to Neo4j database"""
        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Testing connection to Neo4j"
        )

        try:
            driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))
            with driver.session() as session:
                result = session.run("MATCH (n) RETURN count(n) AS count")
                count = result.single()["count"]
                self.logger.info(
                    f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Successfully connected to Neo4j. Database contains {count} nodes"
                )
            driver.close()
            return True
        except Exception as e:
            self.logger.error(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Failed to connect to Neo4j: {str(e)}"
            )
            return False

    def load_csv_to_neo4j(
        self,
        csv_file_path,
        node_label,
        properties_map,
        unique_property="session_id",
        create_only_new=True,
    ):
        """
        Load data from a CSV file into Neo4j.

        Args:
            csv_file_path (str): Path to the CSV file.
            node_label (str): Label to apply to the nodes.
            properties_map (dict): A dictionary mapping CSV column names to Neo4j property names.
            unique_property (str): The property to use as unique identifier.
            create_only_new (bool): If True, only create nodes that don't exist in the database.

        Returns:
            tuple: (nodes_created, nodes_skipped)
        """
        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Loading CSV to Neo4j: {csv_file_path}"
        )

        nodes_created = 0
        nodes_skipped = 0

        driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))

        def create_nodes(
            tx,
            csv_file_path,
            node_label,
            properties_map,
            unique_property,
            create_only_new,
        ):
            nonlocal nodes_created, nodes_skipped

            with open(csv_file_path, "r", encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)

                for row in reader:
                    properties = {
                        prop_neo4j: row[col]
                        for col, prop_neo4j in properties_map.items()
                        if col in row and row[col]
                    }

                    # Skip empty rows
                    if not properties:
                        continue

                    # Make sure the unique property exists
                    if unique_property not in properties:
                        self.logger.warning(
                            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Skipping record without unique property: {unique_property}"
                        )
                        continue

                    unique_value = properties[unique_property]

                    if create_only_new:
                        # Check if node already exists
                        check_query = f"MATCH (n:{node_label} {{{unique_property}: $unique_value}}) RETURN count(n) as count"
                        result = tx.run(check_query, unique_value=unique_value).single()

                        if result and result["count"] > 0:
                            nodes_skipped += 1
                            continue

                    # Create node
                    query = f"CREATE (n:{node_label} $properties)"
                    tx.run(query, properties=properties)
                    nodes_created += 1

        try:
            with driver.session() as session:
                session.execute_write(
                    create_nodes,
                    csv_file_path,
                    node_label,
                    properties_map,
                    unique_property,
                    create_only_new,
                )

            self.logger.info(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - CSV loaded to Neo4j. Created {nodes_created} nodes, skipped {nodes_skipped} nodes"
            )
        except Exception as e:
            self.logger.error(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Error loading CSV to Neo4j: {str(e)}"
            )
            raise
        finally:
            driver.close()

        return nodes_created, nodes_skipped

    def create_stream_nodes(self, streams_json_path, create_only_new=True):
        """
        Create stream nodes in Neo4j from a JSON file.

        Args:
            streams_json_path (str): Path to the JSON file containing stream data.
            create_only_new (bool): If True, only create nodes that don't exist in the database.

        Returns:
            tuple: (nodes_created, nodes_skipped)
        """
        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Creating stream nodes from: {streams_json_path}"
        )

        nodes_created = 0
        nodes_skipped = 0

        try:
            with open(streams_json_path, "r") as f:
                streams = json.load(f)

            driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))

            def create_nodes(tx, streams, create_only_new):
                nonlocal nodes_created, nodes_skipped

                for stream_key, description in streams.items():
                    if create_only_new:
                        # Check if node already exists
                        check_query = "MATCH (s:Stream {stream: $stream}) RETURN count(s) as count"
                        result = tx.run(check_query, stream=stream_key).single()

                        if result and result["count"] > 0:
                            nodes_skipped += 1
                            continue

                    # Create node
                    query = (
                        "CREATE (s:Stream {stream: $stream, description: $description})"
                    )
                    tx.run(query, stream=stream_key, description=description)
                    nodes_created += 1

            with driver.session() as session:
                session.execute_write(create_nodes, streams, create_only_new)

            self.logger.info(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Stream nodes created: {nodes_created}, skipped: {nodes_skipped}"
            )
            driver.close()

        except Exception as e:
            self.logger.error(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Error creating stream nodes: {str(e)}"
            )
            raise

        return nodes_created, nodes_skipped

    def create_stream_relationships(
        self, session_node_label, stream_node_label="Stream", create_only_new=True
    ):
        """
        Create relationships between session nodes and stream nodes.

        Args:
            session_node_label (str): Label of the session nodes.
            stream_node_label (str): Label of the stream nodes.
            create_only_new (bool): If True, only create relationships that don't exist.

        Returns:
            tuple: (relationships_created, relationships_skipped)
        """
        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Creating relationships between {session_node_label} and {stream_node_label}"
        )

        relationships_created = 0
        relationships_skipped = 0

        driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))

        def create_relationships(
            tx, session_node_label, stream_node_label, create_only_new
        ):
            nonlocal relationships_created, relationships_skipped

            # Get all session nodes with their stream property
            result = tx.run(
                f"""
                MATCH (s:{session_node_label})
                RETURN s.session_id AS session_id, s.stream AS stream
                """
            )

            for record in result:
                session_id = record["session_id"]
                streams_str = record["stream"]

                if not streams_str:
                    continue

                # Split stream string by semicolon and normalize
                stream_list = [
                    stream.strip().lower() for stream in streams_str.split(";")
                ]

                for stream in stream_list:
                    if create_only_new:
                        # Check if relationship already exists
                        check_query = f"""
                            MATCH (s:{session_node_label} {{session_id: $session_id}})-[r:HAS_STREAM]->(st:{stream_node_label} {{stream: $stream}})
                            RETURN count(r) as count
                        """
                        result = tx.run(
                            check_query, session_id=session_id, stream=stream
                        ).single()

                        if result and result["count"] > 0:
                            relationships_skipped += 1
                            continue

                    # Create relationship
                    create_query = f"""
                        MATCH (s:{session_node_label} {{session_id: $session_id}})
                        MATCH (st:{stream_node_label} {{stream: $stream}})
                        CREATE (s)-[r:HAS_STREAM]->(st)
                    """

                    try:
                        tx.run(create_query, session_id=session_id, stream=stream)
                        relationships_created += 1
                    except Exception as e:
                        # Log specific errors for relationship creation
                        if "not found" in str(e).lower():
                            self.logger.warning(
                                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Stream '{stream}' not found for session {session_id}"
                            )
                        else:
                            self.logger.warning(
                                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Error creating relationship: {str(e)}"
                            )

        try:
            with driver.session() as session:
                session.execute_write(
                    create_relationships,
                    session_node_label,
                    stream_node_label,
                    create_only_new,
                )

            self.logger.info(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Relationships created: {relationships_created}, skipped: {relationships_skipped}"
            )
        except Exception as e:
            self.logger.error(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Error creating relationships: {str(e)}"
            )
            raise
        finally:
            driver.close()

        return relationships_created, relationships_skipped

    def process(self, create_only_new=True):
        """
        Process session data and upload to Neo4j.

        Args:
            create_only_new (bool): If True, only create nodes and relationships that don't exist.
        """
        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Starting Neo4j session and stream data processing"
        )

        # Test the connection first
        if not self._test_connection():
            self.logger.error(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Cannot proceed with Neo4j upload due to connection failure"
            )
            return

        # Process sessions from this year
        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Processing sessions from this year"
        )
        try:
            csv_file_path = os.path.join(
                self.output_dir, "session_this_filtered_valid_cols.csv"
            )
            data = pd.read_csv(csv_file_path)
            properties_map = {col: col for col in data.columns}
            node_label = "Sessions_this_year"

            nodes_created, nodes_skipped = self.load_csv_to_neo4j(
                csv_file_path, node_label, properties_map, "session_id", create_only_new
            )

            self.statistics["nodes_created"]["sessions_this_year"] = nodes_created
            self.statistics["nodes_skipped"]["sessions_this_year"] = nodes_skipped
        except Exception as e:
            self.logger.error(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Error processing sessions from this year: {str(e)}"
            )

        # Process sessions from last year BVA
        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Processing sessions from last year BVA"
        )
        try:
            csv_file_path = os.path.join(
                self.output_dir, "session_last_filtered_valid_cols_bva.csv"
            )
            data = pd.read_csv(csv_file_path)
            properties_map = {col: col for col in data.columns}
            node_label = "Sessions_past_year"

            nodes_created, nodes_skipped = self.load_csv_to_neo4j(
                csv_file_path, node_label, properties_map, "session_id", create_only_new
            )

            self.statistics["nodes_created"]["sessions_past_year_bva"] = nodes_created
            self.statistics["nodes_skipped"]["sessions_past_year_bva"] = nodes_skipped
        except Exception as e:
            self.logger.error(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Error processing sessions from last year BVA: {str(e)}"
            )

        # Process sessions from last year LVA
        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Processing sessions from last year LVA"
        )
        try:
            csv_file_path = os.path.join(
                self.output_dir, "session_last_filtered_valid_cols_lva.csv"
            )
            data = pd.read_csv(csv_file_path)
            properties_map = {col: col for col in data.columns}
            node_label = "Sessions_past_year"

            nodes_created, nodes_skipped = self.load_csv_to_neo4j(
                csv_file_path, node_label, properties_map, "session_id", create_only_new
            )

            self.statistics["nodes_created"]["sessions_past_year_lva"] = nodes_created
            self.statistics["nodes_skipped"]["sessions_past_year_lva"] = nodes_skipped
        except Exception as e:
            self.logger.error(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Error processing sessions from last year LVA: {str(e)}"
            )

        # Create stream nodes
        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Creating stream nodes"
        )
        try:
            streams_json_path = os.path.join(self.output_dir, "streams.json")

            nodes_created, nodes_skipped = self.create_stream_nodes(
                streams_json_path, create_only_new
            )

            self.statistics["nodes_created"]["streams"] = nodes_created
            self.statistics["nodes_skipped"]["streams"] = nodes_skipped
        except Exception as e:
            self.logger.error(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Error creating stream nodes: {str(e)}"
            )

        # Create relationships between sessions this year and streams
        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Creating stream relationships for sessions this year"
        )
        try:
            rels_created, rels_skipped = self.create_stream_relationships(
                "Sessions_this_year", "Stream", create_only_new
            )

            self.statistics["relationships_created"][
                "sessions_this_year_has_stream"
            ] = rels_created
            self.statistics["relationships_skipped"][
                "sessions_this_year_has_stream"
            ] = rels_skipped
        except Exception as e:
            self.logger.error(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Error creating stream relationships for sessions this year: {str(e)}"
            )

        # Create relationships between sessions past year and streams
        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Creating stream relationships for sessions past year"
        )
        try:
            rels_created, rels_skipped = self.create_stream_relationships(
                "Sessions_past_year", "Stream", create_only_new
            )

            self.statistics["relationships_created"][
                "sessions_past_year_has_stream"
            ] = rels_created
            self.statistics["relationships_skipped"][
                "sessions_past_year_has_stream"
            ] = rels_skipped
        except Exception as e:
            self.logger.error(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Error creating stream relationships for sessions past year: {str(e)}"
            )

        # Log summary statistics
        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Neo4j session data processing summary:"
        )
        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Sessions this year: {self.statistics['nodes_created']['sessions_this_year']} created, {self.statistics['nodes_skipped']['sessions_this_year']} skipped"
        )
        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Sessions past year BVA: {self.statistics['nodes_created']['sessions_past_year_bva']} created, {self.statistics['nodes_skipped']['sessions_past_year_bva']} skipped"
        )
        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Sessions past year LVA: {self.statistics['nodes_created']['sessions_past_year_lva']} created, {self.statistics['nodes_skipped']['sessions_past_year_lva']} skipped"
        )
        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Stream nodes: {self.statistics['nodes_created']['streams']} created, {self.statistics['nodes_skipped']['streams']} skipped"
        )
        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Stream relationships this year: {self.statistics['relationships_created']['sessions_this_year_has_stream']} created, {self.statistics['relationships_skipped']['sessions_this_year_has_stream']} skipped"
        )
        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Stream relationships past year: {self.statistics['relationships_created']['sessions_past_year_has_stream']} created, {self.statistics['relationships_skipped']['sessions_past_year_has_stream']} skipped"
        )

        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Neo4j session data processing completed"
        )
