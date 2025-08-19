"""
Simplified MLflow utilities for logging pipeline configuration and metrics.
Single run approach - no nested runs.
"""
import os
import logging
import mlflow
import yaml
import json
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class MLflowManager:
    """Manages MLflow experiment tracking for the pipeline."""
    
    def __init__(self):
        """Initialize MLflow manager and verify environment setup."""
        self.experiment_id = None
        self.databricks_host = None
        self.mlflow_tracking_uri = None
        self.run_id = None
        self.run = None
        
    def verify_environment(self) -> bool:
        """
        Verify that all required MLflow environment variables are set.
        
        Returns:
            bool: True if all required environment variables are set, False otherwise
        
        Raises:
            Exception: If environment variables are not configured correctly
        """
        self.experiment_id = os.environ.get("MLFLOW_EXPERIMENT_ID")
        self.databricks_host = os.environ.get("DATABRICKS_HOST")
        self.mlflow_tracking_uri = os.environ.get("MLFLOW_TRACKING_URI")
        
        if self.experiment_id is None or self.databricks_host is None or self.mlflow_tracking_uri is None:
            error_msg = (
                "Environment variables are not configured correctly. "
                "Please set MLFLOW_EXPERIMENT_ID, DATABRICKS_HOST, and MLFLOW_TRACKING_URI"
            )
            logger.error(error_msg)
            raise Exception(error_msg)
        
        # Set MLflow tracking URI
        mlflow.set_tracking_uri(self.mlflow_tracking_uri)
        mlflow.set_experiment(self.experiment_id)
        
        logger.info(f"MLflow environment verified successfully")
        logger.info(f"Experiment ID: {self.experiment_id}")
        logger.info(f"Databricks Host: {self.databricks_host}")
        logger.info(f"Tracking URI: {self.mlflow_tracking_uri}")
        
        return True
    
    def start_run(self, config: Dict[str, Any]) -> str:
        """
        Start a single MLflow run for the entire pipeline.
        
        Args:
            config: Pipeline configuration dictionary
            
        Returns:
            str: Run ID
        """
        # Generate run name
        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        event_config = config.get("event", {})
        event_name = event_config.get("name", "pipeline")
        run_name = f"{event_name}_{timestamp}"
        
        logger.info(f"Starting MLflow run: {run_name}")
        
        # Start the run
        self.run = mlflow.start_run(run_name=run_name)
        self.run_id = self.run.info.run_id
        
        # Log configuration as parameters
        logger.info("Logging configuration parameters to MLflow")
        self.log_config_as_params(config)
        
        # Log additional metadata
        mlflow.log_param("pipeline_type", "recommendation_pipeline")
        mlflow.log_param("event_name", event_name)
        mlflow.log_param("timestamp", timestamp)
        mlflow.log_param("pipeline_version", "enhanced")
        
        # Determine processing mode
        main_event_name = event_config.get("main_event_name", "").lower()
        processing_mode = "veterinary" if main_event_name in ["bva", "veterinary", "vet"] else "generic"
        mlflow.log_param("processing_mode", processing_mode)
        
        # Try to log the configuration file as an artifact
        try:
            safe_config = self._remove_sensitive_info(config)
            config_file = f"config_{event_name}_{timestamp}.yaml"
            with open(config_file, 'w') as f:
                yaml.dump(safe_config, f, default_flow_style=False)
            mlflow.log_artifact(config_file)
            os.remove(config_file)
            logger.info("Successfully logged configuration file as artifact")
        except Exception as e:
            logger.warning(f"Could not log configuration artifact: {e}")
        
        logger.info(f"Started MLflow run with ID: {self.run_id}")
        
        return self.run_id
    
    def log_config_as_params(self, config: Dict[str, Any], prefix: str = "") -> None:
        """
        Recursively log configuration parameters to MLflow, excluding sensitive information.
        
        Args:
            config: Configuration dictionary to log
            prefix: Prefix for parameter names (for nested configurations)
        """
        sensitive_keys = {"password", "secret", "key", "token", "credentials", "api_key"}
        
        for key, value in config.items():
            # Skip sensitive information
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                logger.debug(f"Skipping sensitive parameter: {key}")
                continue
            
            param_name = f"{prefix}{key}" if prefix else key
            
            if isinstance(value, dict):
                # For nested dictionaries, recurse with updated prefix
                self.log_config_as_params(value, prefix=f"{param_name}.")
            elif isinstance(value, (list, tuple)):
                # For lists/tuples, convert to string representation
                if len(str(value)) <= 250:  # MLflow param value limit
                    try:
                        mlflow.log_param(param_name, str(value))
                        logger.debug(f"Logged parameter: {param_name} = {value}")
                    except Exception as e:
                        logger.warning(f"Could not log parameter {param_name}: {e}")
            else:
                # For scalar values, log directly
                if value is not None and len(str(value)) <= 250:
                    try:
                        mlflow.log_param(param_name, value)
                        logger.debug(f"Logged parameter: {param_name} = {value}")
                    except Exception as e:
                        logger.warning(f"Could not log parameter {param_name}: {e}")
    
    def log_metrics(self, metrics: Dict[str, Any], prefix: str = "") -> None:
        """
        Log metrics to MLflow.
        
        Args:
            metrics: Dictionary of metrics to log
            prefix: Optional prefix for metric names
        """
        for metric_name, metric_value in metrics.items():
            full_name = f"{prefix}_{metric_name}" if prefix else metric_name
            
            if isinstance(metric_value, (int, float)):
                try:
                    mlflow.log_metric(full_name, metric_value)
                    logger.debug(f"Logged metric: {full_name} = {metric_value}")
                except Exception as e:
                    logger.warning(f"Could not log metric {full_name}: {e}")
    
    def log_summary_metrics(self, processors: Dict[str, Any]) -> None:
        """
        Log summary metrics from all processors.
        
        Args:
            processors: Dictionary of processor instances
        """
        metrics = {}
        
        # Registration processor metrics - check for different attribute names
        if "reg_processor" in processors:
            reg = processors["reg_processor"]
            
            # Initial data loaded
            if hasattr(reg, 'df_bva'):
                metrics['registration_main_event_raw'] = len(reg.df_bva)
            if hasattr(reg, 'df_lvs'):
                metrics['registration_secondary_event_raw'] = len(reg.df_lvs)
            if hasattr(reg, 'df_bva_demo'):
                metrics['registration_demographic_main_raw'] = len(reg.df_bva_demo)
            if hasattr(reg, 'df_lvs_demo'):
                metrics['registration_demographic_secondary_raw'] = len(reg.df_lvs_demo)
            
            # Processed data - this year
            if hasattr(reg, 'df_bva_this_year'):
                metrics['registration_this_year_total'] = len(reg.df_bva_this_year)
                metrics['registration_unique_visitors_this_year'] = reg.df_bva_this_year['BadgeId'].nunique()
            elif hasattr(reg, 'df_bva_25_only_valid'):
                metrics['registration_this_year_valid'] = len(reg.df_bva_25_only_valid)
                metrics['registration_unique_visitors_this_year'] = reg.df_bva_25_only_valid['BadgeId'].nunique()
            
            # Processed data - last year
            if hasattr(reg, 'df_bva_last_year'):
                metrics['registration_last_year_main_total'] = len(reg.df_bva_last_year)
            elif hasattr(reg, 'df_bva_24_only_valid'):
                metrics['registration_last_year_main_valid'] = len(reg.df_bva_24_only_valid)
            
            # Returning visitors
            if hasattr(reg, 'df_bva_returning'):
                metrics['registration_returning_main'] = len(reg.df_bva_returning)
            elif hasattr(reg, 'df_bva_24_25_only_valid'):
                metrics['registration_returning_main_valid'] = len(reg.df_bva_24_25_only_valid)
            
            if hasattr(reg, 'df_lvs_returning'):
                metrics['registration_returning_secondary'] = len(reg.df_lvs_returning)
            elif hasattr(reg, 'df_lva_24_25_only_valid'):
                metrics['registration_returning_secondary_valid'] = len(reg.df_lva_24_25_only_valid)
            
            # Combined registration with demographics
            if hasattr(reg, 'df_reg_demo_this'):
                metrics['registration_with_demographics_this_year'] = len(reg.df_reg_demo_this)
            if hasattr(reg, 'df_reg_demo_last_bva'):
                metrics['registration_with_demographics_last_main'] = len(reg.df_reg_demo_last_bva)
            if hasattr(reg, 'df_reg_demo_last_lva'):
                metrics['registration_with_demographics_last_secondary'] = len(reg.df_reg_demo_last_lva)
        
        # Scan processor metrics - add storage for later use in dataframe
        if "scan_processor" in processors:
            scan = processors["scan_processor"]
            
            # Store dataframes for later inspection  
            if hasattr(scan, 'df_scan_last_bva'):
                metrics['scan_total_last_year_main'] = len(scan.df_scan_last_bva)
                metrics['scan_unique_seminars_last_year_main'] = scan.df_scan_last_bva['seminar_name'].nunique()
                metrics['scan_unique_attendees_last_year_main'] = scan.df_scan_last_bva['BadgeId'].nunique()
            if hasattr(scan, 'df_scan_last_lva'):
                metrics['scan_total_last_year_secondary'] = len(scan.df_scan_last_lva)
                metrics['scan_unique_seminars_last_year_secondary'] = scan.df_scan_last_lva['seminar_name'].nunique()
                metrics['scan_unique_attendees_last_year_secondary'] = scan.df_scan_last_lva['BadgeId'].nunique()
            
            # Check for processed scan data with different names
            if hasattr(scan, 'seminars_scans_past_enhanced_main'):
                metrics['scan_enhanced_main'] = len(scan.seminars_scans_past_enhanced_main)
            if hasattr(scan, 'seminars_scans_past_enhanced_secondary'):
                metrics['scan_enhanced_secondary'] = len(scan.seminars_scans_past_enhanced_secondary)
        
        # Session processor metrics
        if "session_processor" in processors:
            session = processors["session_processor"]
            
            # Check for different attribute names
            if hasattr(session, 'df_session_this'):
                metrics['session_total_this_year'] = len(session.df_session_this)
            elif hasattr(session, 'session_this_filtered_valid_cols'):
                metrics['session_total_this_year'] = len(session.session_this_filtered_valid_cols)
            
            if hasattr(session, 'df_session_last_bva'):
                metrics['session_total_last_year_main'] = len(session.df_session_last_bva)
            elif hasattr(session, 'session_last_filtered_valid_cols_bva'):
                metrics['session_total_last_year_main'] = len(session.session_last_filtered_valid_cols_bva)
            
            if hasattr(session, 'df_session_last_lva'):
                metrics['session_total_last_year_secondary'] = len(session.df_session_last_lva)
            elif hasattr(session, 'session_last_filtered_valid_cols_lva'):
                metrics['session_total_last_year_secondary'] = len(session.session_last_filtered_valid_cols_lva)
            
            if hasattr(session, 'streams'):
                metrics['session_unique_stream_categories'] = len(session.streams)
        
        # Neo4j processor metrics
        if "neo4j_visitor_processor" in processors:
            metrics['neo4j_visitors_processed'] = 1  # Flag that Neo4j visitor processing was done
        
        if "neo4j_session_processor" in processors:
            metrics['neo4j_sessions_processed'] = 1  # Flag that Neo4j session processing was done
        
        if "session_recommendation_processor" in processors:
            rec = processors["session_recommendation_processor"]
            if hasattr(rec, 'total_visitors_processed'):
                metrics['recommendations_visitors_processed'] = rec.total_visitors_processed
            if hasattr(rec, 'total_recommendations_created'):
                metrics['recommendations_total_created'] = rec.total_recommendations_created
        
        # Log all metrics
        self.log_metrics(metrics)
        logger.info(f"Logged {len(metrics)} summary metrics to MLflow")
    
    def log_processing_summary(self, summary_file_path: str) -> None:
        """
        Log the processing summary JSON as an artifact and extract metrics.
        
        Args:
            summary_file_path: Path to the summary JSON file
        """
        try:
            # Log the JSON file as an artifact
            if os.path.exists(summary_file_path):
                mlflow.log_artifact(summary_file_path)
                logger.info(f"Logged summary file as artifact: {summary_file_path}")
                
                # Also extract and log key metrics from the summary
                with open(summary_file_path, 'r') as f:
                    summary = json.load(f)
                
                # Log processing time
                if 'processing_time_seconds' in summary:
                    mlflow.log_metric('total_processing_time_seconds', summary['processing_time_seconds'])
                
                # Log step counts
                if 'steps_completed' in summary:
                    mlflow.log_metric('steps_completed', len(summary['steps_completed']))
                
        except Exception as e:
            logger.warning(f"Could not log summary file: {e}")
    
    def end_run(self, status: str = "FINISHED") -> None:
        """
        End the MLflow run.
        
        Args:
            status: Status of the run (FINISHED, FAILED, etc.)
        """
        mlflow.end_run(status=status)
        logger.info(f"Ended MLflow run with status: {status}")
    
    def _remove_sensitive_info(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Remove sensitive information from configuration dictionary.
        
        Args:
            config: Original configuration dictionary
            
        Returns:
            Dict with sensitive information removed
        """
        import copy
        safe_config = copy.deepcopy(config)
        sensitive_keys = {"password", "secret", "key", "token", "credentials", "api_key"}
        
        def remove_sensitive(d):
            if isinstance(d, dict):
                keys_to_remove = []
                for k, v in d.items():
                    if any(sensitive in k.lower() for sensitive in sensitive_keys):
                        keys_to_remove.append(k)
                    elif isinstance(v, dict):
                        remove_sensitive(v)
                
                for k in keys_to_remove:
                    d[k] = "***REDACTED***"
        
        remove_sensitive(safe_config)
        return safe_config