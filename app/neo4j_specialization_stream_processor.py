import logging
import os
import pandas as pd
import json
from neo4j import GraphDatabase
from dotenv import load_dotenv
import inspect


class Neo4jSpecializationStreamProcessor:
    """
    A class to process specialization to stream mappings and create relationships in Neo4j.
    This class is responsible for creating relationships between visitor nodes and
    stream nodes based on practice specializations.
    """

    def __init__(self, config):
        """
        Initialize the Neo4j Specialization Stream Processor.

        Args:
            config (dict): Configuration dictionary containing paths and settings
        """
        self.logger = logging.getLogger(__name__)
        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Initializing Neo4j Specialization Stream Processor"
        )

        self.config = config
        self.input_dir = config["output_dir"]

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
            "relationships_created": {
                "visitor_this_year": 0,
                "visitor_last_year_bva": 0,
                "visitor_last_year_lva": 0,
            },
            "relationships_skipped": {
                "visitor_this_year": 0,
                "visitor_last_year_bva": 0,
                "visitor_last_year_lva": 0,
            },
            "visitor_nodes_processed": {
                "visitor_this_year": 0,
                "visitor_last_year_bva": 0,
                "visitor_last_year_lva": 0,
            },
            "specializations_processed": 0,
            "stream_matches_found": 0,
        }

        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Neo4j Specialization Stream Processor initialized successfully"
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

    def load_mappings(self):
        """
        Load the specialization mappings from CSV files.

        Returns:
            tuple: (map_specialization, specialization_stream_mapping)
        """
        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Loading specialization mappings"
        )

        try:
            # Load specialization mapping
            map_specialization = {
                "Wildlife": "Other",
                "Small Animal": "Companion Animal",
                "Mixed": "Other",
                "Dairy": "Farm",
                "Poultry": "Farm",
                "Cattle": "Farm",
                "Pigs": "Farm",
                "Sheep": "Farm",
            }

            # Load specialization to stream mapping
            specialization_stream_file = os.path.join(
                self.input_dir, "spezialization_to_stream.csv"
            )
            map_specialization_stream = pd.read_csv(specialization_stream_file)

            # Convert to dictionary
            specialization_stream_mapping = json.loads(
                map_specialization_stream.set_index("spezialization").to_json(
                    orient="index"
                )
            )

            # Log some stats about the mapping
            self.logger.info(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Loaded mapping for {len(specialization_stream_mapping)} specializations"
            )

            return map_specialization, specialization_stream_mapping
        except Exception as e:
            self.logger.error(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Error loading specialization mappings: {str(e)}"
            )
            raise

    def create_specialization_stream_relationships(
        self, map_specialization, specialization_stream_mapping, create_only_new=True
    ):
        """
        Create relationships between visitor nodes and stream nodes based on practice specializations.
        This optimized version uses batch processing to improve performance.

        Args:
            map_specialization (dict): Dictionary mapping specialization names to standard format
            specialization_stream_mapping (dict): Dictionary mapping specializations to applicable streams
            create_only_new (bool): If True, only create relationships that don't exist

        Returns:
            dict: Statistics about the relationship creation process
        """
        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Creating specialization to stream relationships (optimized)"
        )

        statistics = {
            "relationships_created": {
                "visitor_this_year": 0,
                "visitor_last_year_bva": 0,
                "visitor_last_year_lva": 0,
            },
            "relationships_skipped": {
                "visitor_this_year": 0,
                "visitor_last_year_bva": 0,
                "visitor_last_year_lva": 0,
            },
            "visitor_nodes_processed": {
                "visitor_this_year": 0,
                "visitor_last_year_bva": 0,
                "visitor_last_year_lva": 0,
            },
            "specializations_processed": 0,
            "stream_matches_found": 0,
        }

        # Convert specialization_stream_mapping to a more efficient format
        # {specialization: [stream1, stream2, ...]}
        specialization_to_streams = {}
        for spec, stream_dict in specialization_stream_mapping.items():
            applicable_streams = []
            for stream_name, applies in stream_dict.items():
                if applies == "YES":
                    applicable_streams.append(stream_name)

            if (
                applicable_streams
            ):  # Only include specializations with at least one applicable stream
                specialization_to_streams[spec] = applicable_streams
                statistics["specializations_processed"] += 1
                statistics["stream_matches_found"] += len(applicable_streams)

        driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))

        # Process Visitor_this_year nodes
        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Processing Visitor_this_year nodes"
        )
        (
            statistics["visitor_nodes_processed"]["visitor_this_year"],
            statistics["relationships_created"]["visitor_this_year"],
            statistics["relationships_skipped"]["visitor_this_year"],
        ) = self._process_visitor_type(
            driver,
            "Visitor_this_year",
            "what_type_does_your_practice_specialise_in",
            map_specialization,
            specialization_to_streams,
            create_only_new,
        )

        # Process Visitor_last_year_bva nodes
        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Processing Visitor_last_year_bva nodes"
        )
        (
            statistics["visitor_nodes_processed"]["visitor_last_year_bva"],
            statistics["relationships_created"]["visitor_last_year_bva"],
            statistics["relationships_skipped"]["visitor_last_year_bva"],
        ) = self._process_visitor_type(
            driver,
            "Visitor_last_year_bva",
            "what_areas_do_you_specialise_in",
            map_specialization,
            specialization_to_streams,
            create_only_new,
        )

        # Process Visitor_last_year_lva nodes
        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Processing Visitor_last_year_lva nodes"
        )
        (
            statistics["visitor_nodes_processed"]["visitor_last_year_lva"],
            statistics["relationships_created"]["visitor_last_year_lva"],
            statistics["relationships_skipped"]["visitor_last_year_lva"],
        ) = self._process_visitor_type(
            driver,
            "Visitor_last_year_lva",
            "what_areas_do_you_specialise_in",
            map_specialization,
            specialization_to_streams,
            create_only_new,
        )

        driver.close()
        return statistics

    def _process_visitor_type(
        self,
        driver,
        node_label,
        specialization_field,
        map_specialization,
        specialization_to_streams,
        create_only_new,
    ):
        """
        Process a specific type of visitor nodes to create specialization to stream relationships.

        Args:
            driver: Neo4j driver
            node_label (str): Label of the visitor nodes
            specialization_field (str): Name of the field containing specialization info
            map_specialization (dict): Dictionary mapping specialization names to standard format
            specialization_to_streams (dict): Dictionary mapping specializations to applicable streams
            create_only_new (bool): If True, only create relationships that don't exist

        Returns:
            tuple: (visitor_nodes_processed, relationships_created, relationships_skipped)
        """
        visitor_nodes_processed = 0
        relationships_created = 0
        relationships_skipped = 0

        def process_visitor_nodes(
            tx,
            node_label,
            specialization_field,
            map_specialization,
            specialization_to_streams,
            create_only_new,
        ):
            nonlocal visitor_nodes_processed, relationships_created, relationships_skipped

            # Get all unique specializations from the database that match our mapping
            specializations_query = f"""
            MATCH (v:{node_label})
            WHERE v.{specialization_field} IS NOT NULL 
              AND v.{specialization_field} <> 'NA'
            RETURN DISTINCT v.{specialization_field} as specialization_text
            """

            spec_results = tx.run(specializations_query)

            # Process each specialization text
            for record in spec_results:
                specialization_text = record["specialization_text"]

                # Split by semicolon as they can contain multiple specializations
                spec_list = [spec.strip() for spec in specialization_text.split(";")]

                # Get all visitors with this specialization text
                visitors_query = f"""
                MATCH (v:{node_label})
                WHERE v.{specialization_field} = $specialization_text
                RETURN count(v) AS visitor_count
                """

                visitors_result = tx.run(
                    visitors_query, specialization_text=specialization_text
                )
                visitor_count = visitors_result.single()["visitor_count"]
                visitor_nodes_processed += visitor_count

                # Process each specialization in the list
                for spec in spec_list:
                    # Map specialization if needed
                    mapped_spec = map_specialization.get(spec, spec)

                    # Check if this specialization exists in our mapping
                    if mapped_spec in specialization_to_streams:
                        applicable_streams = specialization_to_streams[mapped_spec]

                        # Optimized query that processes all visitors with this specialization at once
                        if create_only_new:
                            create_query = f"""
                            MATCH (v:{node_label})
                            WHERE v.{specialization_field} = $specialization_text
                            
                            UNWIND $streams AS stream_name
                            MATCH (s:Stream)
                            WHERE toLower(s.stream) = toLower(stream_name)
                            
                            WITH v, s
                            WHERE NOT exists((v)-[:SPECIALIZATION_TO_STREAM]->(s))
                            
                            CREATE (v)-[r:SPECIALIZATION_TO_STREAM]->(s)
                            RETURN count(r) AS created
                            """

                            result = tx.run(
                                create_query,
                                specialization_text=specialization_text,
                                streams=applicable_streams,
                            )
                            created = result.single()["created"]

                            # Calculate potential relationships
                            potential = visitor_count * len(applicable_streams)
                            skipped = potential - created

                            relationships_created += created
                            relationships_skipped += skipped
                        else:
                            create_query = f"""
                            MATCH (v:{node_label})
                            WHERE v.{specialization_field} = $specialization_text
                            
                            UNWIND $streams AS stream_name
                            MATCH (s:Stream)
                            WHERE toLower(s.stream) = toLower(stream_name)
                            
                            MERGE (v)-[r:SPECIALIZATION_TO_STREAM]->(s)
                            RETURN count(r) AS created
                            """

                            result = tx.run(
                                create_query,
                                specialization_text=specialization_text,
                                streams=applicable_streams,
                            )
                            created = result.single()["created"]
                            relationships_created += created

        try:
            with driver.session() as session:
                session.execute_write(
                    process_visitor_nodes,
                    node_label,
                    specialization_field,
                    map_specialization,
                    specialization_to_streams,
                    create_only_new,
                )
        except Exception as e:
            self.logger.error(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Error processing {node_label} nodes: {str(e)}"
            )

        return visitor_nodes_processed, relationships_created, relationships_skipped

    def process(self, create_only_new=True):
        """
        Process specialization to stream mappings and create relationships in Neo4j.

        Args:
            create_only_new (bool): If True, only create relationships that don't exist.
        """
        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Starting Neo4j specialization to stream relationship processing"
        )

        # Test the connection first
        if not self._test_connection():
            self.logger.error(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Cannot proceed with Neo4j processing due to connection failure"
            )
            return

        try:
            # Load the mappings
            map_specialization, specialization_stream_mapping = self.load_mappings()

            # Create the relationships
            stats = self.create_specialization_stream_relationships(
                map_specialization, specialization_stream_mapping, create_only_new
            )

            # Update the statistics
            self.statistics.update(stats)

            # Calculate total statistics
            total_created = sum(self.statistics["relationships_created"].values())
            total_skipped = sum(self.statistics["relationships_skipped"].values())
            total_processed = sum(self.statistics["visitor_nodes_processed"].values())

            # Log summary
            self.logger.info(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Specialization to stream relationship processing summary:"
            )
            self.logger.info(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Visitor nodes processed: {total_processed}"
            )
            self.logger.info(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Specializations processed: {self.statistics['specializations_processed']}"
            )
            self.logger.info(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Stream matches found: {self.statistics['stream_matches_found']}"
            )
            self.logger.info(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Relationships created: {total_created}"
            )
            self.logger.info(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Relationships skipped: {total_skipped}"
            )

            self.logger.info(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Neo4j specialization to stream relationship processing completed"
            )
        except Exception as e:
            self.logger.error(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Error in specialization to stream relationship processing: {str(e)}"
            )
            raise
