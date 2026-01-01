"""Spaces log handler - append logs to single file in Spaces."""

import logging
from io import StringIO
from datetime import datetime

import config

try:
    from utils.spaces import SpacesClient
except ImportError:
    SpacesClient = None


class SpacesLogHandler(logging.Handler):
    """Append logs to single file in Spaces and optionally local file."""

    def __init__(self, log_key: str = None, local_log_file: str = None):
        """Initialize handler with log key in Spaces and optional local file."""
        super().__init__()
        self.log_key = log_key or f"{config.SPACES_LOG_PREFIX.rstrip('/')}/run.log"
        self.local_log_file = local_log_file or "data/run.log"
        
        if not config.SPACES_ENABLED or SpacesClient is None:
            self.spaces_client = None
        else:
            try:
                self.spaces_client = SpacesClient()
            except Exception as exc:
                self.spaces_client = None
                print(f"Warning: Spaces log handler disabled: {exc}")

    def emit(self, record: logging.LogRecord):
        """Handle log record: write to local file and buffer for Spaces."""
        try:
            msg = self.format(record)
            
            # Write to local file
            try:
                with open(self.local_log_file, 'a') as f:
                    f.write(msg + '\n')
            except Exception as e:
                print(f"Warning: Failed to write local log: {e}")
            
            # Append to Spaces (append_text handles remote sync)
            if self.spaces_client:
                try:
                    self.spaces_client.append_text(self.log_key, msg + '\n')
                except Exception as e:
                    # Don't crash on S3 error
                    pass
        except Exception as e:
            self.handleError(record)


def setup_spaces_logging(log_key: str = None) -> SpacesLogHandler:
    """Setup Spaces log handler and attach to root logger."""
    return SpacesLogHandler(log_key=log_key)

