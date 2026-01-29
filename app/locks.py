"""
File locking and atomic write utilities for data persistence.

Provides:
- file_lock: context manager for file-level locking (Unix/Linux) or no-op on Windows
- atomic_write: write to temporary file then rename (atomic on most filesystems)
- append_safe: thread-safe append to JSON file with locking
"""

import os
import json
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List
from contextlib import contextmanager
import logging

# fcntl only available on Unix/Linux
try:
    import fcntl
    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False

logger = logging.getLogger(__name__)


@contextmanager
def file_lock(filepath: str, timeout: int = 10):
    """
    Context manager for file-based locking using fcntl (Unix/Linux).
    On Windows, this is a no-op (fcntl not available).
    
    Usage:
        with file_lock('/path/to/data.csv'):
            # Critical section - file is locked
            read_and_modify_file()
    
    Args:
        filepath: Path to file to lock
        timeout: Lock acquisition timeout (not enforced, just for documentation)
    
    Yields:
        None
    
    Raises:
        IOError: If file cannot be locked (Unix/Linux only)
    """
    if not HAS_FCNTL:
        # Windows: file locking not available, just proceed
        logger.debug(f"File locking not available (fcntl not on this OS), skipping lock for {filepath}")
        yield
        return
    
    try:
        # Open lock file (create if doesn't exist)
        lock_path = f"{filepath}.lock"
        with open(lock_path, 'w') as lock_file:
            try:
                # Non-blocking lock attempt (will raise if already locked)
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
                yield
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
    except Exception as e:
        logger.error(f"File lock failed for {filepath}: {e}")
        raise


def atomic_write(filepath: str, content: str, encoding: str = 'utf-8') -> None:
    """
    Atomically write content to file using temp file + rename.
    
    Safer than direct writes - file is either old or new, never partial.
    
    Usage:
        atomic_write('/path/to/file.txt', 'new content')
    
    Args:
        filepath: Target file path
        content: String content to write
        encoding: Text encoding (default: utf-8)
    
    Raises:
        IOError: If write or rename fails
    """
    try:
        # Create temp file in same directory (ensures same filesystem)
        dirpath = os.path.dirname(filepath) or '.'
        with tempfile.NamedTemporaryFile(
            mode='w',
            dir=dirpath,
            encoding=encoding,
            delete=False
        ) as tmp_file:
            tmp_path = tmp_file.name
            tmp_file.write(content)
        
        # Atomic rename (on same filesystem)
        os.replace(tmp_path, filepath)
        logger.debug(f"Atomically wrote to {filepath}")
    except Exception as e:
        logger.error(f"Atomic write failed for {filepath}: {e}")
        # Clean up temp file if it exists
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass
        raise


def atomic_write_json(filepath: str, data: Any, indent: int = 2) -> None:
    """
    Atomically write JSON data to file.
    
    Usage:
        atomic_write_json('/path/to/data.json', {'key': 'value'})
    
    Args:
        filepath: Target JSON file path
        data: Python object to serialize as JSON
        indent: JSON indentation level
    
    Raises:
        IOError: If write or rename fails
    """
    content = json.dumps(data, indent=indent, ensure_ascii=False)
    atomic_write(filepath, content)


def read_json_safe(filepath: str, default: Any = None) -> Any:
    """
    Read JSON file with fallback to default on error.
    
    Usage:
        data = read_json_safe('/path/to/data.json', default=[])
    
    Args:
        filepath: Path to JSON file
        default: Value to return if file doesn't exist or JSON is invalid
    
    Returns:
        Parsed JSON or default value
    """
    try:
        if not os.path.exists(filepath):
            return default
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Could not read JSON from {filepath}: {e}")
        return default


def append_safe_json(filepath: str, record: Dict[str, Any]) -> None:
    """
    Thread-safe append of a JSON record to a JSON array file.
    
    Locks file, reads current array, appends new record, writes back atomically.
    
    Usage:
        append_safe_json('/path/to/logs.json', {'user': 'admin', 'action': 'login'})
    
    Args:
        filepath: Path to JSON file (should contain array)
        record: Dict to append to array
    
    Raises:
        IOError: If lock, read, or write fails
    """
    with file_lock(filepath):
        try:
            # Read current data
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = []
            
            # Ensure it's a list
            if not isinstance(data, list):
                logger.warning(f"Expected list in {filepath}, got {type(data)}")
                data = []
            
            # Append record
            data.append(record)
            
            # Write back atomically
            atomic_write_json(filepath, data)
            logger.debug(f"Appended record to {filepath}")
        except Exception as e:
            logger.error(f"Safe append to {filepath} failed: {e}")
            raise


def ensure_directory(dirpath: str, mode: int = 0o750) -> None:
    """
    Create directory if it doesn't exist, with specified permissions.
    
    Usage:
        ensure_directory('/var/www/wifi-portal/data', mode=0o750)
    
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
            os.chmod(dirpath, mode)
    except Exception as e:
        logger.error(f"Could not ensure directory {dirpath}: {e}")
        raise
