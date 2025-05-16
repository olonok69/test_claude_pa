import ssl
import os
import logging


class NatsSSLContextBuilder:
    """Utility class for building and configuring SSL contexts for NATS connections"""

    def __init__(self):
        """Initialize the SSL context builder"""
        self._configure_logging()
        self._load_certificate_paths()
        self._load_verification_settings()

    def _configure_logging(self):
        """Configure certificate logging based on environment variable"""
        self.cert_logging = (
            os.getenv("NATS_CERTIFICATE_LOGGING", "false").lower() == "true"
        )
        if self.cert_logging:
            logging.info("Certificate logging enabled")

    def _load_certificate_paths(self):
        """Load certificate paths from environment variables"""
        # Get base certificates path
        self.certificates_path = os.getenv("CERTIFICATES_PATH")
        if not self.certificates_path:
            raise EnvironmentError("CERTIFICATES_PATH environment variable not set")

        # Construct full paths
        self.cert_file = os.path.join(self.certificates_path, "nats.pem")
        self.key_file = os.path.join(self.certificates_path, "nats-key.pem")
        self.ca_file = os.path.join(self.certificates_path, "ca.pem")

        if self.cert_logging:
            logging.info("Certificate paths loaded from environment:")
            logging.info(f"Base path: {self.certificates_path}")
            logging.info(f"Certificate file: {self.cert_file}")
            logging.info(f"Key file: {self.key_file}")
            logging.info(f"CA file: {self.ca_file}")

    def _load_verification_settings(self):
        """Load certificate verification settings from environment"""
        self.verify_cert = (
            os.getenv("NATS_VERBOSECERTIFICATEVERIFICATION", "true").lower() == "true"
        )
        if self.cert_logging:
            logging.info(
                f"Certificate verification {'enabled' if self.verify_cert else 'disabled'}"
            )

    def _validate_certificate_files(self):
        """Validate that all required certificate files exist and are valid"""
        if self.cert_logging:
            logging.info(f"Certificate paths configured:")
            logging.info(f"- Certificate: {self.cert_file}")
            logging.info(f"- Private key: {self.key_file}")
            logging.info(f"- CA certificate: {self.ca_file}")

        for file_path in [self.cert_file, self.key_file, self.ca_file]:
            if not os.path.exists(file_path):
                logging.error(f"File does not exist at: {file_path}")
                raise FileNotFoundError(f"Required file not found at: {file_path}")

            if not os.path.isfile(file_path):
                logging.error(f"Path exists but is not a file: {file_path}")
                raise FileNotFoundError(f"Path is not a file: {file_path}")

            if self.cert_logging:
                logging.info(f"Certificate file verified at: {file_path}")

    def create_ssl_context(self) -> ssl.SSLContext:
        """
        Create and configure an SSL context for NATS connections

        Returns:
            ssl.SSLContext: Configured SSL context

        Raises:
            FileNotFoundError: If required certificate files are missing
            ssl.SSLError: If there are issues loading the certificate chain
        """
        self._validate_certificate_files()

        # Create SSL context
        ssl_context = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)

        # Configure verification settings based on environment
        if not self.verify_cert:
            if self.cert_logging:
                logging.info("Certificate verification disabled")
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
        else:
            if self.cert_logging:
                logging.info("Certificate verification enabled")
            if os.path.exists(self.ca_file):
                if self.cert_logging:
                    logging.info(f"Loading CA certificate from: {self.ca_file}")
                ssl_context.load_verify_locations(cafile=self.ca_file)
            else:
                if self.cert_logging:
                    logging.warning(f"CA certificate not found, using system CA store")

        # Load certificate chain
        try:
            ssl_context.load_cert_chain(certfile=self.cert_file, keyfile=self.key_file)
            if self.cert_logging:
                logging.info("Successfully loaded certificate chain")
        except ssl.SSLError as e:
            logging.error(f"Error loading certificate chain: {e}")
            raise

        return ssl_context
