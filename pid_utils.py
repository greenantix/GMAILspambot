#!/usr/bin/env python3
"""
PID File Management Utilities

Provides utilities for creating, managing, and cleaning up PID files
for process stability and graceful shutdown handling.
"""

import os
import signal
import atexit
from pathlib import Path
from typing import Optional
from log_config import get_logger

logger = get_logger(__name__)

class PIDFileManager:
    """Manages PID files for process tracking and graceful shutdown."""
    
    def __init__(self, pid_dir: str = "pids", process_name: str = "process"):
        """
        Initialize PID file manager.
        
        Args:
            pid_dir: Directory to store PID files
            process_name: Name of the process (used in PID filename)
        """
        self.pid_dir = Path(pid_dir)
        self.process_name = process_name
        self.pid_file = self.pid_dir / f"{process_name}.pid"
        self.pid = os.getpid()
        self._cleanup_registered = False
    
    def create_pid_file(self) -> bool:
        """
        Create PID file with current process ID.
        
        Returns:
            bool: True if PID file created successfully, False otherwise
        """
        try:
            # Create PID directory if it doesn't exist
            self.pid_dir.mkdir(parents=True, exist_ok=True)
            
            # Check if PID file already exists and process is running
            if self.is_process_running():
                logger.error(f"Process {self.process_name} is already running (PID file exists)")
                return False
            
            # Write current PID to file
            with open(self.pid_file, 'w') as f:
                f.write(str(self.pid))
            
            logger.info(f"Created PID file: {self.pid_file} (PID: {self.pid})")
            
            # Register cleanup handlers
            self._register_cleanup_handlers()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create PID file {self.pid_file}: {e}")
            return False
    
    def remove_pid_file(self) -> bool:
        """
        Remove PID file.
        
        Returns:
            bool: True if PID file removed successfully, False otherwise
        """
        try:
            if self.pid_file.exists():
                # Verify this is our PID file
                stored_pid = self.get_stored_pid()
                if stored_pid and stored_pid == self.pid:
                    self.pid_file.unlink()
                    logger.info(f"Removed PID file: {self.pid_file}")
                    return True
                else:
                    logger.warning(f"PID file {self.pid_file} contains different PID ({stored_pid}), not removing")
                    return False
            else:
                logger.debug(f"PID file {self.pid_file} does not exist")
                return True
                
        except Exception as e:
            logger.error(f"Failed to remove PID file {self.pid_file}: {e}")
            return False
    
    def get_stored_pid(self) -> Optional[int]:
        """
        Get PID stored in the PID file.
        
        Returns:
            int or None: PID from file, None if file doesn't exist or invalid
        """
        try:
            if self.pid_file.exists():
                with open(self.pid_file, 'r') as f:
                    return int(f.read().strip())
        except (ValueError, IOError) as e:
            logger.warning(f"Invalid PID file {self.pid_file}: {e}")
        return None
    
    def is_process_running(self) -> bool:
        """
        Check if process is running based on PID file.
        
        Returns:
            bool: True if process is running, False otherwise
        """
        stored_pid = self.get_stored_pid()
        if not stored_pid:
            return False
        
        try:
            # Send signal 0 to check if process exists
            os.kill(stored_pid, 0)
            return True
        except (OSError, ProcessLookupError):
            # Process doesn't exist, clean up stale PID file
            logger.info(f"Removing stale PID file for non-existent process {stored_pid}")
            try:
                self.pid_file.unlink()
            except OSError:
                pass
            return False
    
    def _register_cleanup_handlers(self):
        """Register cleanup handlers for graceful shutdown."""
        if self._cleanup_registered:
            return
        
        # Register atexit handler
        atexit.register(self.remove_pid_file)
        
        # Register signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, cleaning up PID file...")
            self.remove_pid_file()
            # Let the signal propagate for normal shutdown
            if signum == signal.SIGTERM:
                exit(0)
        
        # Handle common termination signals
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        
        self._cleanup_registered = True
    
    def __enter__(self):
        """Context manager entry."""
        if not self.create_pid_file():
            raise RuntimeError(f"Failed to create PID file for {self.process_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.remove_pid_file()


def get_running_processes(pid_dir: str = "pids") -> dict:
    """
    Get all running processes with PID files.
    
    Args:
        pid_dir: Directory containing PID files
    
    Returns:
        dict: Mapping of process name to PID for running processes
    """
    running = {}
    pid_path = Path(pid_dir)
    
    if not pid_path.exists():
        return running
    
    for pid_file in pid_path.glob("*.pid"):
        process_name = pid_file.stem
        manager = PIDFileManager(pid_dir, process_name)
        
        if manager.is_process_running():
            stored_pid = manager.get_stored_pid()
            if stored_pid:
                running[process_name] = stored_pid
    
    return running


def stop_process_by_name(process_name: str, pid_dir: str = "pids", timeout: int = 10) -> bool:
    """
    Stop a process using its PID file.
    
    Args:
        process_name: Name of the process to stop
        pid_dir: Directory containing PID files
        timeout: Timeout in seconds for graceful shutdown
    
    Returns:
        bool: True if process stopped successfully, False otherwise
    """
    manager = PIDFileManager(pid_dir, process_name)
    stored_pid = manager.get_stored_pid()
    
    if not stored_pid:
        logger.info(f"No PID file found for process {process_name}")
        return True
    
    if not manager.is_process_running():
        logger.info(f"Process {process_name} is not running")
        return True
    
    try:
        logger.info(f"Stopping process {process_name} (PID: {stored_pid})")
        
        # Send SIGTERM for graceful shutdown
        os.kill(stored_pid, signal.SIGTERM)
        
        # Wait for process to terminate
        import time
        for _ in range(timeout):
            if not manager.is_process_running():
                logger.info(f"Process {process_name} stopped gracefully")
                return True
            time.sleep(1)
        
        # Force kill if still running
        if manager.is_process_running():
            logger.warning(f"Process {process_name} did not stop gracefully, force killing...")
            os.kill(stored_pid, signal.SIGKILL)
            time.sleep(1)
            
            if not manager.is_process_running():
                logger.info(f"Process {process_name} force killed")
                return True
            else:
                logger.error(f"Failed to stop process {process_name}")
                return False
        
        return True
        
    except (OSError, ProcessLookupError) as e:
        logger.error(f"Error stopping process {process_name}: {e}")
        return False


def cleanup_stale_pid_files(pid_dir: str = "pids"):
    """
    Clean up stale PID files for non-existent processes.
    
    Args:
        pid_dir: Directory containing PID files
    """
    pid_path = Path(pid_dir)
    
    if not pid_path.exists():
        return
    
    cleaned_count = 0
    for pid_file in pid_path.glob("*.pid"):
        process_name = pid_file.stem
        manager = PIDFileManager(pid_dir, process_name)
        
        if not manager.is_process_running():
            cleaned_count += 1
    
    if cleaned_count > 0:
        logger.info(f"Cleaned up {cleaned_count} stale PID files")