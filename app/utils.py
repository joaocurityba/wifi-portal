"""
Utility functions for WiFi Portal Application.
"""

import os
import logging

logger = logging.getLogger(__name__)


def ensure_directory(dirpath: str, mode: int = 0o750) -> None:
    """
    Create directory if it doesn't exist, with specified permissions.
    
    Usage:
        ensure_directory('/var/www/wifi-portal/logs', mode=0o750)
    
    Args:
        dirpath: Directory path to ensure
        mode: Unix file permissions
    """
    try:
        if not os.path.exists(dirpath):
            os.makedirs(dirpath, mode=mode)
            logger.info(f"Created directory {dirpath} with mode {oct(mode)}")
        else:
            # Optionally update permissions if dir exists
            try:
                os.chmod(dirpath, mode)
            except Exception:
                # Ignore permission errors on existing directories
                pass
    except Exception as e:
        logger.error(f"Could not ensure directory {dirpath}: {e}")
        raise
