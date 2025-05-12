import logging
import os
import pandas as pd
from neo4j import GraphDatabase
from dotenv import load_dotenv
import inspect


class Neo4jVisitorRelationshipProcessor:
    """
    A class to create relationships between visitors from this year and past events.
    This processor creates Same_Visitor relationships and attended_session relationships.
    """

    def __init__(self, config):
        """
        Initialize the Neo4j Visitor Relationship Processor.

        Args:
            config (dict): Configuration dictionary containing paths and settings
        """
        self.logger = logging.getLogger(__name__)
        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Initializing Neo4j Visitor Relationship Processor"
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
            "relationships_created": {
                "same_visitor_bva": 0,
                "same_visitor_lva": 0,
                "attended_session_bva": 0,
                "attended_session_lva": 0,
            },
            "relationships_skipped": {
                "same_visitor_bva": 0,
                "same_visitor_lva": 0,
                "attended_session_bva": 0,
                "attended_session_lva": 0,
            },
        }

        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Neo4j Visitor Relationship Processor initialized successfully"
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

    def create_same_visitor_relationships_bva(self, create_only_new=True):
        """
        Creates Same_Visitor relationships for all Visitor_this_year nodes to Visitor_last_year_bva nodes.

        Args:
            create_only_new (bool): If True, only create relationships that don't exist in the database.

        Returns:
            tuple: (relationships_created, relationships_skipped)
        """
        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Creating Same_Visitor relationships for BVA"
        )

        relationships_created = 0
        relationships_skipped = 0

        driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))

        try:
            with driver.session() as session:
                # Check if relationships already exist if create_only_new is True
                if create_only_new:
                    check_query = """
                        MATCH (this_year:Visitor_this_year)-[r:Same_Visitor {type: 'bva'}]->(:Visitor_last_year_bva)
                        RETURN count(r) as count
                    """
                    result = session.run(check_query).single()
                    if result and result["count"] > 0:
                        self.logger.info(
                            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Found {result['count']} existing Same_Visitor relationships for BVA"
                        )
                        relationships_skipped = result["count"]
                        return relationships_created, relationships_skipped

                # Create relationships
                query = """
                    MATCH (this_year:Visitor_this_year)
                    WHERE this_year.BadgeId_last_year_bva <> "NA" AND this_year.BadgeId_last_year_bva IS NOT NULL
                    MATCH (last_year:Visitor_last_year_bva {BadgeId: this_year.BadgeId_last_year_bva})
                    CREATE (this_year)-[:Same_Visitor {type: 'bva'}]->(last_year)
                    RETURN count(*) as count
                """
                result = session.run(query).single()
                relationships_created = result["count"] if result else 0

                self.logger.info(
                    f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Created {relationships_created} Same_Visitor relationships for BVA"
                )

        except Exception as e:
            self.logger.error(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Error creating Same_Visitor relationships for BVA: {str(e)}"
            )
            raise
        finally:
            driver.close()

        return relationships_created, relationships_skipped

    def create_same_visitor_relationships_lva(self, create_only_new=True):
        """
        Creates Same_Visitor relationships for all Visitor_this_year nodes to Visitor_last_year_lva nodes.

        Args:
            create_only_new (bool): If True, only create relationships that don't exist in the database.

        Returns:
            tuple: (relationships_created, relationships_skipped)
        """
        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Creating Same_Visitor relationships for LVA"
        )

        relationships_created = 0
        relationships_skipped = 0

        driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))

        try:
            with driver.session() as session:
                # Check if relationships already exist if create_only_new is True
                if create_only_new:
                    check_query = """
                        MATCH (this_year:Visitor_this_year)-[r:Same_Visitor {type: 'lva'}]->(:Visitor_last_year_lva)
                        RETURN count(r) as count
                    """
                    result = session.run(check_query).single()
                    if result and result["count"] > 0:
                        self.logger.info(
                            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Found {result['count']} existing Same_Visitor relationships for LVA"
                        )
                        relationships_skipped = result["count"]
                        return relationships_created, relationships_skipped

                # Create relationships
                query = """
                    MATCH (this_year:Visitor_this_year)
                    WHERE this_year.BadgeId_last_year_lva <> "NA" AND this_year.BadgeId_last_year_lva IS NOT NULL
                    MATCH (last_year:Visitor_last_year_lva {BadgeId: this_year.BadgeId_last_year_lva})
                    CREATE (this_year)-[:Same_Visitor {type: 'lva'}]->(last_year)
                    RETURN count(*) as count
                """
                result = session.run(query).single()
                relationships_created = result["count"] if result else 0

                self.logger.info(
                    f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Created {relationships_created} Same_Visitor relationships for LVA"
                )

        except Exception as e:
            self.logger.error(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Error creating Same_Visitor relationships for LVA: {str(e)}"
            )
            raise
        finally:
            driver.close()

        return relationships_created, relationships_skipped

    def create_attended_session_relationships_bva(self, create_only_new=True):
        """
        Creates attended_session relationships between Visitor_last_year_bva nodes
        and Sessions_past_year nodes.

        Args:
            create_only_new (bool): If True, only create relationships that don't exist in the database.

        Returns:
            tuple: (relationships_created, relationships_skipped)
        """
        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Creating attended_session relationships for BVA"
        )

        relationships_created = 0
        relationships_skipped = 0

        # Load scan data for BVA from the previous year
        scan_file_path = os.path.join(self.output_dir, "scan_bva_past.csv")
        if not os.path.exists(scan_file_path):
            self.logger.error(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Scan file not found: {scan_file_path}"
            )
            return relationships_created, relationships_skipped

        # Load the badge IDs of visitors that attended both years
        filter_file_path = os.path.join(self.output_dir, "df_reg_demo_last_bva.csv")
        if not os.path.exists(filter_file_path):
            self.logger.error(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Filter file not found: {filter_file_path}"
            )
            return relationships_created, relationships_skipped

        try:
            # Load data
            scan_data = pd.read_csv(scan_file_path)
            filter_data = pd.read_csv(filter_file_path)

            # Get list of badge IDs to filter by
            badge_ids = list(filter_data["BadgeId"].unique())
            self.logger.info(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Loaded {len(badge_ids)} badge IDs for filtering scan data"
            )

            # Filter scan data to only include visitors in the filter list
            scan_data = scan_data[scan_data["Badge Id"].isin(badge_ids)]
            self.logger.info(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Filtered scan data contains {len(scan_data)} records"
            )

            if len(scan_data) == 0:
                self.logger.warning(
                    f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - No scan data records found after filtering"
                )
                return relationships_created, relationships_skipped

            # Create relationships in Neo4j
            driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))

            def create_relationships(tx, row):
                query = """
                MATCH (v:Visitor_last_year_bva {BadgeId: $visitor_badge_id})
                MATCH (s:Sessions_past_year {key_text: $session_key_text})
                CREATE (v)-[:attended_session {scan_date: $scan_date, file: $file, seminar_name: $seminar_name}]->(s)
                """
                tx.run(
                    query,
                    visitor_badge_id=row["Badge Id"],
                    session_key_text=row["key_text"],
                    scan_date=str(row["Scan Date"]),
                    file=row["File"],
                    seminar_name=row["Seminar Name"],
                )

            # Check if relationships already exist if create_only_new is True
            if create_only_new:
                with driver.session() as session:
                    check_query = """
                        MATCH (:Visitor_last_year_bva)-[r:attended_session]->(:Sessions_past_year)
                        RETURN count(r) as count
                    """
                    result = session.run(check_query).single()
                    if result and result["count"] > 0:
                        self.logger.info(
                            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Found {result['count']} existing attended_session relationships for BVA"
                        )
                        relationships_skipped = result["count"]
                        driver.close()
                        return relationships_created, relationships_skipped

            # Create relationships
            with driver.session() as session:
                for _, row in scan_data.iterrows():
                    try:
                        session.execute_write(create_relationships, row)
                        relationships_created += 1
                    except Exception as e:
                        self.logger.error(
                            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Error creating relationship for badge ID {row['Badge Id']}: {str(e)}"
                        )

            driver.close()

            self.logger.info(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Created {relationships_created} attended_session relationships for BVA"
            )

        except Exception as e:
            self.logger.error(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Error creating attended_session relationships for BVA: {str(e)}"
            )
            raise

        return relationships_created, relationships_skipped

    def create_attended_session_relationships_lva(self, create_only_new=True):
        """
        Creates attended_session relationships between Visitor_last_year_lva nodes
        and Sessions_past_year nodes.

        Args:
            create_only_new (bool): If True, only create relationships that don't exist in the database.

        Returns:
            tuple: (relationships_created, relationships_skipped)
        """
        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Creating attended_session relationships for LVA"
        )

        relationships_created = 0
        relationships_skipped = 0

        # Load scan data for LVA from the previous year
        scan_file_path = os.path.join(self.output_dir, "scan_lva_past.csv")
        if not os.path.exists(scan_file_path):
            self.logger.error(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Scan file not found: {scan_file_path}"
            )
            return relationships_created, relationships_skipped

        # Load the badge IDs of visitors that attended both years
        filter_file_path = os.path.join(self.output_dir, "df_reg_demo_last_lva.csv")
        if not os.path.exists(filter_file_path):
            self.logger.error(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Filter file not found: {filter_file_path}"
            )
            return relationships_created, relationships_skipped

        try:
            # Load data
            scan_data = pd.read_csv(scan_file_path)
            filter_data = pd.read_csv(filter_file_path)

            # Get list of badge IDs to filter by
            badge_ids = list(filter_data["BadgeId"].unique())
            self.logger.info(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Loaded {len(badge_ids)} badge IDs for filtering scan data"
            )

            # Filter scan data to only include visitors in the filter list
            scan_data = scan_data[scan_data["Badge Id"].isin(badge_ids)]
            self.logger.info(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Filtered scan data contains {len(scan_data)} records"
            )

            if len(scan_data) == 0:
                self.logger.warning(
                    f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - No scan data records found after filtering"
                )
                return relationships_created, relationships_skipped

            # Create relationships in Neo4j
            driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))

            def create_relationships(tx, row):
                query = """
                MATCH (v:Visitor_last_year_lva {BadgeId: $visitor_badge_id})
                MATCH (s:Sessions_past_year {key_text: $session_key_text})
                CREATE (v)-[:attended_session {scan_date: $scan_date, file: $file, seminar_name: $seminar_name}]->(s)
                """
                tx.run(
                    query,
                    visitor_badge_id=row["Badge Id"],
                    session_key_text=row["key_text"],
                    scan_date=str(row["Scan Date"]),
                    file=row["File"],
                    seminar_name=row["Seminar Name"],
                )

            # Check if relationships already exist if create_only_new is True
            if create_only_new:
                with driver.session() as session:
                    check_query = """
                        MATCH (:Visitor_last_year_lva)-[r:attended_session]->(:Sessions_past_year)
                        RETURN count(r) as count
                    """
                    result = session.run(check_query).single()
                    if result and result["count"] > 0:
                        self.logger.info(
                            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Found {result['count']} existing attended_session relationships for LVA"
                        )
                        relationships_skipped = result["count"]
                        driver.close()
                        return relationships_created, relationships_skipped

            # Create relationships
            with driver.session() as session:
                for _, row in scan_data.iterrows():
                    try:
                        session.execute_write(create_relationships, row)
                        relationships_created += 1
                    except Exception as e:
                        self.logger.error(
                            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Error creating relationship for badge ID {row['Badge Id']}: {str(e)}"
                        )

            driver.close()

            self.logger.info(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Created {relationships_created} attended_session relationships for LVA"
            )

        except Exception as e:
            self.logger.error(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Error creating attended_session relationships for LVA: {str(e)}"
            )
            raise

        return relationships_created, relationships_skipped

    def process(self, create_only_new=True):
        """
        Process visitor relationship data and upload to Neo4j.

        Args:
            create_only_new (bool): If True, only create relationships that don't exist in the database.
        """
        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Starting Neo4j visitor relationship processing"
        )

        # Test the connection first
        if not self._test_connection():
            self.logger.error(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Cannot proceed with Neo4j upload due to connection failure"
            )
            return

        # Create Same_Visitor relationships for BVA
        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Creating Same_Visitor relationships for BVA"
        )
        try:
            relationships_created, relationships_skipped = (
                self.create_same_visitor_relationships_bva(create_only_new)
            )
            self.statistics["relationships_created"][
                "same_visitor_bva"
            ] = relationships_created
            self.statistics["relationships_skipped"][
                "same_visitor_bva"
            ] = relationships_skipped
        except Exception as e:
            self.logger.error(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Error creating Same_Visitor relationships for BVA: {str(e)}"
            )

        # Create Same_Visitor relationships for LVA
        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Creating Same_Visitor relationships for LVA"
        )
        try:
            relationships_created, relationships_skipped = (
                self.create_same_visitor_relationships_lva(create_only_new)
            )
            self.statistics["relationships_created"][
                "same_visitor_lva"
            ] = relationships_created
            self.statistics["relationships_skipped"][
                "same_visitor_lva"
            ] = relationships_skipped
        except Exception as e:
            self.logger.error(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Error creating Same_Visitor relationships for LVA: {str(e)}"
            )

        # Create attended_session relationships for BVA
        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Creating attended_session relationships for BVA"
        )
        try:
            relationships_created, relationships_skipped = (
                self.create_attended_session_relationships_bva(create_only_new)
            )
            self.statistics["relationships_created"][
                "attended_session_bva"
            ] = relationships_created
            self.statistics["relationships_skipped"][
                "attended_session_bva"
            ] = relationships_skipped
        except Exception as e:
            self.logger.error(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Error creating attended_session relationships for BVA: {str(e)}"
            )

        # Create attended_session relationships for LVA
        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Creating attended_session relationships for LVA"
        )
        try:
            relationships_created, relationships_skipped = (
                self.create_attended_session_relationships_lva(create_only_new)
            )
            self.statistics["relationships_created"][
                "attended_session_lva"
            ] = relationships_created
            self.statistics["relationships_skipped"][
                "attended_session_lva"
            ] = relationships_skipped
        except Exception as e:
            self.logger.error(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Error creating attended_session relationships for LVA: {str(e)}"
            )

        # Log summary statistics
        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Neo4j visitor relationship processing summary:"
        )
        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Same_Visitor relationships for BVA: {self.statistics['relationships_created']['same_visitor_bva']} created, {self.statistics['relationships_skipped']['same_visitor_bva']} skipped"
        )
        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Same_Visitor relationships for LVA: {self.statistics['relationships_created']['same_visitor_lva']} created, {self.statistics['relationships_skipped']['same_visitor_lva']} skipped"
        )
        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - attended_session relationships for BVA: {self.statistics['relationships_created']['attended_session_bva']} created, {self.statistics['relationships_skipped']['attended_session_bva']} skipped"
        )
        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - attended_session relationships for LVA: {self.statistics['relationships_created']['attended_session_lva']} created, {self.statistics['relationships_skipped']['attended_session_lva']} skipped"
        )

        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Neo4j visitor relationship processing completed"
        )
