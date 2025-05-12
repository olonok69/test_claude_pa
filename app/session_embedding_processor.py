import logging
import json
import os
import inspect
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv


class SessionEmbeddingProcessor:
    """
    Neo4j processor for computing and storing embeddings for session nodes.

    This processor creates text embeddings for session nodes in Neo4j using sentence transformers,
    incorporating session attributes and stream descriptions to enrich the embeddings.
    """

    def __init__(self, config):
        """
        Initialize the SessionEmbeddingProcessor.

        Args:
            config: Configuration dictionary
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

        # If env variables not found, fall back to config
        if not self.uri:
            self.uri = config.get("neo4j", {}).get("uri", "bolt://localhost:7687")
        if not self.username:
            self.username = config.get("neo4j", {}).get("username", "neo4j")
        if not self.password:
            self.password = config.get("neo4j", {}).get("password", "")

        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Using Neo4j URI: {self.uri}"
        )

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
                result = session.run("MATCH (n) RETURN count(n) AS count LIMIT 1")
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

    def process(self, create_only_new=True):
        """
        Process and create embeddings for session nodes in Neo4j.

        Args:
            create_only_new: If True, only create embeddings for nodes that don't already have them

        Returns:
            True if processing was successful
        """
        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Starting session embedding processing"
        )

        # Test the connection first
        if not self._test_connection():
            self.logger.error(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Cannot proceed with Neo4j processing due to connection failure"
            )
            return False

        try:
            # Connect to Neo4j
            driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))

            # Execute embedding processing
            with driver.session() as session:
                session.execute_write(
                    self._compute_and_save_embeddings, create_only_new
                )

            self.logger.info(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Session embedding processing completed successfully"
            )
            self.logger.info(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Total sessions processed: {self.statistics['total_sessions_processed']}"
            )
            self.logger.info(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Sessions with embeddings: {self.statistics['sessions_with_embeddings']}"
            )
            self.logger.info(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Sessions with stream descriptions: {self.statistics['sessions_with_stream_descriptions']}"
            )

            return True

        except Exception as e:
            self.logger.error(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Error in session embedding processing: {e}",
                exc_info=True,
            )
            self.statistics["errors"] += 1
            return False
        finally:
            if "driver" in locals():
                driver.close()

    def _compute_and_save_embeddings(self, tx, create_only_new):
        """
        Compute embeddings for all sessions and save them directly to the nodes.

        Args:
            tx: Neo4j transaction
            create_only_new: If True, only create embeddings for nodes that don't already have them

        Returns:
            True if processing was successful
        """
        # Build the query to get all sessions, optionally filtering those without embeddings
        if create_only_new:
            query = """
            MATCH (s)
            WHERE (s:Sessions_this_year OR s:Sessions_past_year) AND (s.embedding IS NULL OR s.embedding = '')
            RETURN s.session_id as session_id, s.title as title, 
                s.stream as stream, s.synopsis_stripped as synopsis_stripped,
                s.theatre__name as theatre__name, labels(s)[0] as type,
                CASE WHEN s.key_text IS NOT NULL THEN s.key_text ELSE '' END as key_text
            """
        else:
            query = """
            MATCH (s)
            WHERE (s:Sessions_this_year OR s:Sessions_past_year)
            RETURN s.session_id as session_id, s.title as title, 
                s.stream as stream, s.synopsis_stripped as synopsis_stripped,
                s.theatre__name as theatre__name, labels(s)[0] as type,
                CASE WHEN s.key_text IS NOT NULL THEN s.key_text ELSE '' END as key_text
            """

        sessions = tx.run(query).data()
        self.statistics["total_sessions_processed"] = len(sessions)

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

        # Track progress
        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Processing embeddings for {len(sessions)} sessions..."
        )

        # Process sessions in batches to avoid memory issues
        batch_size = self.batch_size
        for i in range(0, len(sessions), batch_size):
            batch = sessions[i : i + batch_size]
            self.logger.info(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Processing batch {i//batch_size + 1}/{(len(sessions) + batch_size - 1)//batch_size}"
            )

            for session in batch:
                # Update session type statistics
                session_type = session["type"]
                if session_type == "Sessions_this_year":
                    self.statistics["sessions_by_type"]["sessions_this_year"] += 1
                else:
                    self.statistics["sessions_by_type"]["sessions_past_year"] += 1

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
                            stream_descriptions_list.append(stream_descriptions[stream])

                if stream_descriptions_list:
                    self.statistics["sessions_with_stream_descriptions"] += 1

                # Create embedding with the session data and stream descriptions
                embedding = self._create_session_embedding(
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

                self.statistics["sessions_with_embeddings"] += 1

        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - All session embeddings have been computed and saved."
        )
        return True

    def _create_session_embedding(self, session, stream_descriptions=None):
        """
        Create text embedding for a session including optional stream descriptions.

        Args:
            session: Session data dictionary
            stream_descriptions: List of stream descriptions

        Returns:
            List of embedding values
        """
        # Include title, synopsis_stripped, and theatre__name as required
        base_text = f"{session['title']} {session['synopsis_stripped']} {session['theatre__name']}"

        # Add key_text if available
        if session["key_text"]:
            base_text = f"{base_text} {session['key_text']}"

        # Add stream descriptions if provided
        if stream_descriptions and len(stream_descriptions) > 0:
            stream_desc_text = " ".join(stream_descriptions)
            text = f"{base_text} {stream_desc_text}"
        else:
            text = base_text

        # Return the embedding as a list (will be converted to JSON)
        return self.model.encode(text).tolist()
