import logging
import os
import pandas as pd
import json
from neo4j import GraphDatabase
from dotenv import load_dotenv
import inspect


class Neo4jJobStreamProcessor:
    """
    A class to process job role to stream mappings and create relationships in Neo4j.
    This class is responsible for creating relationships between visitor nodes and
    stream nodes based on job roles.
    """


import logging
import os
import json
import inspect
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv


class SessionEmbeddingProcessor:
    """
    A class to generate and store text embeddings for session nodes in Neo4j.
    This class is responsible for creating embeddings that incorporate session data
    and stream descriptions to enrich the search capabilities.
    """

    def __init__(self, config):
        """
        Initialize the Session Embedding Processor.

        Args:
            config (dict): Configuration dictionary containing paths and settings
        """
        self.logger = logging.getLogger(__name__)
        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Initializing Session Embedding Processor"
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

        # Initialize embedding model
        self.model_name = config.get("embeddings", {}).get("model", "all-MiniLM-L6-v2")
        self.batch_size = config.get("embeddings", {}).get("batch_size", 100)

        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Initializing embedding model: {self.model_name}"
        )
        self.model = SentenceTransformer(self.model_name)

        # Initialize statistics
        self.statistics = {
            "total_sessions_processed": 0,
            "sessions_with_embeddings": 0,
            "sessions_with_stream_descriptions": 0,
            "sessions_by_type": {"sessions_this_year": 0, "sessions_past_year": 0},
            "errors": 0,
        }

        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Session Embedding Processor initialized successfully"
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

    def _create_session_embedding(self, session, stream_descriptions=None):
        """
        Create text embedding for a session including optional stream descriptions.

        Args:
            session (dict): Session data dictionary
            stream_descriptions (list): List of stream descriptions

        Returns:
            list: List of embedding values
        """
        # Include title, synopsis_stripped, and theatre__name as required
        base_text = f"{session['title']} {session['synopsis_stripped']} {session['theatre__name']}"

        # Add key_text if available
        if session.get("key_text"):
            base_text = f"{base_text} {session['key_text']}"

        # Add stream descriptions if provided
        if stream_descriptions and len(stream_descriptions) > 0:
            stream_desc_text = " ".join(stream_descriptions)
            text = f"{base_text} {stream_desc_text}"
        else:
            text = base_text

        # Return the embedding as a list (will be converted to JSON)
        return self.model.encode(text).tolist()

    def compute_and_save_embeddings(self, create_only_new=True):
        """
        Compute embeddings for all sessions and save them directly to the nodes.

        Args:
            create_only_new (bool): If True, only create embeddings for nodes that don't already have them

        Returns:
            dict: Statistics about the embedding process
        """
        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Computing and saving session embeddings"
        )

        # Initialize statistics for this run
        stats = {
            "total_sessions_processed": 0,
            "sessions_with_embeddings": 0,
            "sessions_with_stream_descriptions": 0,
            "sessions_by_type": {"sessions_this_year": 0, "sessions_past_year": 0},
            "errors": 0,
        }

        driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))

        # Batch processing function
        def batch_compute_embeddings(tx, create_only_new, batch_size, model):
            batch_stats = {
                "total_sessions_processed": 0,
                "sessions_with_embeddings": 0,
                "sessions_with_stream_descriptions": 0,
                "sessions_by_type": {"sessions_this_year": 0, "sessions_past_year": 0},
            }

            # Build the query to get all sessions, optionally filtering those without embeddings
            filter_clause = (
                "WHERE (s.embedding IS NULL OR s.embedding = '') "
                if create_only_new
                else "WHERE "
            )

            query = f"""
            MATCH (s)
            {filter_clause} (s:Sessions_this_year OR s:Sessions_past_year)
            RETURN s.session_id as session_id, s.title as title, 
                s.stream as stream, s.synopsis_stripped as synopsis_stripped,
                s.theatre__name as theatre__name, labels(s)[0] as type,
                CASE WHEN s.key_text IS NOT NULL THEN s.key_text ELSE '' END as key_text
            """

            sessions = tx.run(query).data()
            batch_stats["total_sessions_processed"] = len(sessions)

            # Fetch all stream descriptions once
            stream_query = """
            MATCH (s:Stream)
            RETURN s.stream as stream, s.description as description
            """
            stream_data = tx.run(stream_query).data()

            # Create a dictionary of stream descriptions for quick lookup
            stream_descriptions = {
                s["stream"].lower(): s["description"]
                for s in stream_data
                if s.get("description")
            }

            # Process sessions in batches to avoid memory issues
            for i in range(0, len(sessions), batch_size):
                batch = sessions[i : i + batch_size]

                for session in batch:
                    # Update session type statistics
                    session_type = session["type"]
                    if session_type == "Sessions_this_year":
                        batch_stats["sessions_by_type"]["sessions_this_year"] += 1
                    else:
                        batch_stats["sessions_by_type"]["sessions_past_year"] += 1

                    # Process the stream field - split by semicolon and handle duplicates
                    session_streams = []
                    stream_descriptions_list = []

                    if session["stream"]:
                        # Split the stream string and strip whitespace
                        stream_list = [
                            stream.strip().lower()
                            for stream in session["stream"].split(";")
                        ]
                        # Remove duplicates by converting to set and back to list
                        stream_list = list(set(stream_list))

                        # Get the streams for embedding context
                        for stream in stream_list:
                            if (
                                stream in stream_descriptions
                                and stream_descriptions[stream]
                            ):
                                session_streams.append(stream)
                                stream_descriptions_list.append(
                                    stream_descriptions[stream]
                                )

                    if stream_descriptions_list:
                        batch_stats["sessions_with_stream_descriptions"] += 1

                    # Create embedding with the session data and stream descriptions
                    embedding = model._create_session_embedding(
                        session, stream_descriptions_list
                    )

                    # Save the embedding back to the node
                    update_query = """
                    MATCH (s)
                    WHERE s.session_id = $session_id
                    SET s.embedding = $embedding
                    """
                    tx.run(
                        update_query,
                        session_id=session["session_id"],
                        embedding=json.dumps(embedding),
                    )

                    batch_stats["sessions_with_embeddings"] += 1

            return batch_stats

        try:
            with driver.session() as session:
                # Pass self as the model to access _create_session_embedding method
                batch_stats = session.execute_write(
                    batch_compute_embeddings, create_only_new, self.batch_size, self
                )

                # Update our statistics
                stats.update(batch_stats)

                self.logger.info(
                    f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Session embeddings - processed: {stats['total_sessions_processed']}, created: {stats['sessions_with_embeddings']}"
                )
                self.logger.info(
                    f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Sessions with stream descriptions: {stats['sessions_with_stream_descriptions']}"
                )
                self.logger.info(
                    f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Sessions by type - this year: {stats['sessions_by_type']['sessions_this_year']}, past year: {stats['sessions_by_type']['sessions_past_year']}"
                )
        except Exception as e:
            self.logger.error(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Error computing session embeddings: {str(e)}"
            )
            stats["errors"] += 1
            raise
        finally:
            driver.close()

        return stats

    def process(self, create_only_new=True):
        """
        Process session nodes in Neo4j and generate embeddings.

        Args:
            create_only_new (bool): If True, only create embeddings for nodes that don't already have them
        """
        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Starting session embedding processing"
        )

        # Test the connection first
        if not self._test_connection():
            self.logger.error(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Cannot proceed with Neo4j processing due to connection failure"
            )
            return

        try:
            # Compute and save embeddings
            stats = self.compute_and_save_embeddings(create_only_new)

            # Update the statistics
            self.statistics.update(stats)

            # Log summary
            self.logger.info(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Session embedding processing summary:"
            )
            self.logger.info(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Total sessions processed: {self.statistics['total_sessions_processed']}"
            )
            self.logger.info(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Sessions with embeddings created: {self.statistics['sessions_with_embeddings']}"
            )
            self.logger.info(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Sessions with stream descriptions: {self.statistics['sessions_with_stream_descriptions']}"
            )
            self.logger.info(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Sessions by type - this year: {self.statistics['sessions_by_type']['sessions_this_year']}, past year: {self.statistics['sessions_by_type']['sessions_past_year']}"
            )

            if self.statistics.get("errors", 0) > 0:
                self.logger.warning(
                    f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Errors encountered during processing: {self.statistics['errors']}"
                )

            self.logger.info(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Session embedding processing completed"
            )
        except Exception as e:
            self.logger.error(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Error in session embedding processing: {str(e)}"
            )
            self.statistics["errors"] += 1
            raise

    def __init__(self, config):
        """
        Initialize the Neo4j Job Stream Processor.

        Args:
            config (dict): Configuration dictionary containing paths and settings
        """
        self.logger = logging.getLogger(__name__)
        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Initializing Neo4j Job Stream Processor"
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
            "relationships_created": 0,
            "relationships_skipped": 0,
            "visitor_nodes_processed": 0,
            "job_roles_processed": 0,
            "stream_matches_found": 0,
        }

        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Neo4j Job Stream Processor initialized successfully"
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

    def load_job_stream_mapping(self, mapping_file_path):
        """
        Load the job role to stream mapping from a CSV file.

        Args:
            mapping_file_path (str): Path to the CSV file containing the mapping.

        Returns:
            dict: Dictionary mapping job roles to streams.
        """
        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Loading job to stream mapping from: {mapping_file_path}"
        )

        try:
            map_job_stream = pd.read_csv(mapping_file_path)

            # Verify the CSV has the expected structure
            if "Job Role" not in map_job_stream.columns:
                self.logger.error(
                    f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - CSV file does not contain 'Job Role' column"
                )
                raise ValueError("CSV file does not contain 'Job Role' column")

            # Convert the DataFrame to a dictionary using job role as the index
            job_stream_mapping = json.loads(
                map_job_stream.set_index("Job Role").to_json(orient="index")
            )

            # Log some stats about the mapping
            self.logger.info(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Loaded mapping for {len(job_stream_mapping)} job roles"
            )

            return job_stream_mapping
        except Exception as e:
            self.logger.error(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Error loading job to stream mapping: {str(e)}"
            )
            raise

    def create_job_stream_relationships(self, job_stream_mapping, create_only_new=True):
        """
        Create relationships between visitor nodes and stream nodes based on job roles.
        This optimized version uses a batch processing approach with a single query
        to improve performance significantly.

        Args:
            job_stream_mapping (dict): Dictionary mapping job roles to streams.
            create_only_new (bool): If True, only create relationships that don't exist.

        Returns:
            dict: Statistics about the relationship creation process.
        """
        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Creating job to stream relationships (optimized)"
        )

        # Initialize statistics
        statistics = {
            "relationships_created": 0,
            "relationships_skipped": 0,
            "visitor_nodes_processed": 0,
            "job_roles_processed": 0,
            "stream_matches_found": 0,
        }

        # Transform the job_stream_mapping into a more efficient format
        # {job_role: [stream1, stream2, ...]}
        job_to_streams = {}
        for job_role, stream_dict in job_stream_mapping.items():
            applicable_streams = []
            for stream_name, applies in stream_dict.items():
                if applies == "YES":
                    applicable_streams.append(stream_name)

            if (
                applicable_streams
            ):  # Only include jobs with at least one applicable stream
                job_to_streams[job_role] = applicable_streams

        driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))

        # Batch processing function
        def batch_create_relationships(tx, job_to_streams, create_only_new):
            batch_stats = {
                "relationships_created": 0,
                "relationships_skipped": 0,
                "visitor_nodes_processed": 0,
                "job_roles_processed": 0,
                "stream_matches_found": 0,
            }

            # Get all unique job roles from the database that match our mapping
            job_roles_query = """
            MATCH (v:Visitor_this_year)
            WHERE v.job_role IS NOT NULL 
              AND v.job_role <> 'NA'
              AND v.job_role IN $job_roles
            RETURN DISTINCT v.job_role as job_role
            """

            job_roles_result = tx.run(
                job_roles_query, job_roles=list(job_to_streams.keys())
            )
            matched_job_roles = [record["job_role"] for record in job_roles_result]
            batch_stats["job_roles_processed"] = len(matched_job_roles)

            # Process each job role
            for job_role in matched_job_roles:
                # Get applicable streams for this job role
                applicable_streams = job_to_streams[job_role]
                batch_stats["stream_matches_found"] += len(applicable_streams)

                # Count visitors with this job role
                count_query = """
                MATCH (v:Visitor_this_year)
                WHERE v.job_role = $job_role
                RETURN count(v) AS visitor_count
                """
                visitor_count = tx.run(count_query, job_role=job_role).single()[
                    "visitor_count"
                ]
                batch_stats["visitor_nodes_processed"] += visitor_count

                # Optimized query that creates all relationships for this job role at once
                if create_only_new:
                    # This version checks for existing relationships first
                    create_query = """
                    MATCH (v:Visitor_this_year)
                    WHERE v.job_role = $job_role
                    
                    UNWIND $streams AS stream_name
                    MATCH (s:Stream)
                    WHERE s.stream = stream_name
                    
                    WITH v, s
                    WHERE NOT exists((v)-[:JOB_TO_STREAM]->(s))
                    
                    CREATE (v)-[r:JOB_TO_STREAM]->(s)
                    RETURN count(r) AS created
                    """

                    result = tx.run(
                        create_query, job_role=job_role, streams=applicable_streams
                    )
                    created = result.single()["created"]

                    # Calculate how many would have been created without the WHERE NOT exists condition
                    potential = visitor_count * len(applicable_streams)
                    skipped = potential - created

                    batch_stats["relationships_created"] += created
                    batch_stats["relationships_skipped"] += skipped
                else:
                    # This version creates all possible relationships without checking
                    create_query = """
                    MATCH (v:Visitor_this_year)
                    WHERE v.job_role = $job_role
                    
                    UNWIND $streams AS stream_name
                    MATCH (s:Stream)
                    WHERE s.stream = stream_name
                    
                    MERGE (v)-[r:JOB_TO_STREAM]->(s)
                    RETURN count(r) AS created
                    """

                    result = tx.run(
                        create_query, job_role=job_role, streams=applicable_streams
                    )
                    created = result.single()["created"]
                    batch_stats["relationships_created"] += created

            return batch_stats

        try:
            with driver.session() as session:
                batch_stats = session.execute_write(
                    batch_create_relationships, job_to_streams, create_only_new
                )

                # Update our statistics
                statistics.update(batch_stats)

                self.logger.info(
                    f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Job to stream relationships - created: {statistics['relationships_created']}, skipped: {statistics['relationships_skipped']}"
                )
                self.logger.info(
                    f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Processed {statistics['visitor_nodes_processed']} visitor nodes with {statistics['job_roles_processed']} matching job roles"
                )
        except Exception as e:
            self.logger.error(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Error creating job to stream relationships: {str(e)}"
            )
            raise
        finally:
            driver.close()

        return statistics

    def process(self, create_only_new=True):
        """
        Process job to stream mappings and create relationships in Neo4j.

        Args:
            create_only_new (bool): If True, only create relationships that don't exist.
        """
        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Starting Neo4j job to stream relationship processing"
        )

        # Test the connection first
        if not self._test_connection():
            self.logger.error(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Cannot proceed with Neo4j processing due to connection failure"
            )
            return

        # Get the mapping file path
        mapping_file_path = os.path.join(self.input_dir, "job_to_stream.csv")

        try:
            # Load the mapping
            job_stream_mapping = self.load_job_stream_mapping(mapping_file_path)

            # Create the relationships
            stats = self.create_job_stream_relationships(
                job_stream_mapping, create_only_new
            )

            # Update the statistics
            self.statistics.update(stats)

            # Log summary
            self.logger.info(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Job to stream relationship processing summary:"
            )
            self.logger.info(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Visitor nodes processed: {self.statistics['visitor_nodes_processed']}"
            )
            self.logger.info(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Job roles matched: {self.statistics['job_roles_processed']}"
            )
            self.logger.info(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Stream matches found: {self.statistics['stream_matches_found']}"
            )
            self.logger.info(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Relationships created: {self.statistics['relationships_created']}"
            )
            self.logger.info(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Relationships skipped: {self.statistics['relationships_skipped']}"
            )

            self.logger.info(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Neo4j job to stream relationship processing completed"
            )
        except Exception as e:
            self.logger.error(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Error in job to stream relationship processing: {str(e)}"
            )
            raise
