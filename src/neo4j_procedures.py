from neo4j import GraphDatabase
import csv
import logging



def load_csv_to_neo4j(
    uri,
    user,
    password,
    csv_file_path,
    node_label,
    properties_map,
    relationship_label=None,
    relationship_source_property=None,
    relationship_target_property=None,
):
    """
    Loads data from a CSV file into Neo4j.

    Args:
        uri (str): Neo4j URI (e.g., "bolt://localhost:7687").
        user (str): Neo4j username.
        password (str): Neo4j password.
        csv_file_path (str): Path to the CSV file.
        node_label (str): Label to apply to the nodes.
        properties_map (dict): A dictionary mapping CSV column names to Neo4j property names.
        relationship_label (str, optional): Label to apply to relationships. Defaults to None.
        relationship_source_property (str, optional): CSV column name for the source node ID. Defaults to None.
        relationship_target_property (str, optional): CSV column name for the target node ID. Defaults to None.
    """

    driver = GraphDatabase.driver(uri, auth=(user, password))

    def create_nodes(tx, csv_file_path, node_label, properties_map):
        with open(csv_file_path, "r", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                properties = {
                    properties_map[k]: row[k] for k in properties_map if row[k]
                }  # Added check for empty values
                query = f"CREATE (n:{node_label} $properties)"
                tx.run(query, properties=properties)
        logging.info(
            f"Nodes created successfully from {csv_file_path} with label {node_label}"
        )

    def create_relationships(
        tx,
        csv_file_path,
        relationship_label,
        source_property,
        target_property,
        properties_map,
    ):
        with open(csv_file_path, "r", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                source_id = row.get(source_property)
                target_id = row.get(target_property)
                if (
                    source_id and target_id
                ):  # check to make sure both source and target exist
                    source_prop_neo4j = properties_map.get(source_property)
                    target_prop_neo4j = properties_map.get(target_property)

                    query = f"""
                    MATCH (a), (b)
                    WHERE a.{source_prop_neo4j} = $source_id AND b.{target_prop_neo4j} = $target_id
                    CREATE (a)-[r:{relationship_label}]->(b)
                    """
                    tx.run(query, source_id=source_id, target_id=target_id)
            logging.info(
                f"Relationships created successfully from {csv_file_path} with label {relationship_label}"
            )

    with driver.session() as session:
        session.execute_write(create_nodes, csv_file_path, node_label, properties_map)
        if (
            relationship_label
            and relationship_source_property
            and relationship_target_property
        ):
            session.execute_write(
                create_relationships,
                csv_file_path,
                relationship_label,
                relationship_source_property,
                relationship_target_property,
                properties_map,
            )

    driver.close()


def create_stream_nodes(uri, user, password, streams):
    """
    Create Stream nodes in Neo4j.
    Args:
        uri (str): Neo4j URI (e.g., "bolt://localhost:7687").
        user (str): Neo4j username.
        password (str): Neo4j password.
        streams (list): List of stream names to create nodes for.
    """

    # Create connection to Neo4j
    driver = GraphDatabase.driver(uri, auth=(user, password))

    # Open a session
    with driver.session() as session:
        for stream in streams:
            # Create Stream node with 'stream' property
            session.run("CREATE (s:Stream {stream: $stream})", stream=stream)

    # Close connection
    driver.close()
    logging.info("Stream nodes created successfully!")


def create_stream_relationships(uri, user, password, session_node, stream_node):
    """
    Create relationships between Session and Stream nodes in Neo4j.
    Args:
        uri (str): Neo4j URI (e.g., "bolt://localhost:7687").
        user (str): Neo4j username.
        password (str): Neo4j password.
        session_node (str): The label of the session node.
        stream_node (str): The label of the stream node.
    """

    # Connect to Neo4j
    driver = GraphDatabase.driver(uri, auth=(user, password))

    with driver.session() as session:
        result = session.run(
            f"""
            MATCH (s:{session_node})
            RETURN s.session_id AS session_id, s.stream AS stream
        """
        )

        for record in result:
            session_id = record["session_id"]
            streams = record["stream"]

            stream_list = [stream.strip().lower() for stream in streams.split(";")]

            for stream in stream_list:
                # Check if the relationship already exists
                relationship_exists = session.run(
                    f"""
                    MATCH (s:{session_node} {{session_id: $session_id}})-[:HAS_STREAM]->(st:{stream_node} {{stream: $stream_name}})
                    RETURN count(*) > 0 AS exists
                """,
                    session_id=session_id,
                    stream_name=stream,
                ).single()["exists"]

                if not relationship_exists:
                    session.run(
                        f"""
                        MATCH (s:{session_node} {{session_id: $session_id}})
                        MATCH (st:{stream_node} {{stream: $stream_name}})
                        CREATE (s)-[:HAS_STREAM]->(st)
                    """,
                        session_id=session_id,
                        stream_name=stream,
                    )

    driver.close()
    logging.info("Relationships created successfully!")
