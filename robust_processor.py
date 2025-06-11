#!/usr/bin/env python3
"""
Robust Email Processor - Auto-restart on crashes
Handles LM Studio timeouts and connection issues gracefully
"""

import subprocess
import time
import os
import signal
import logging
from datetime import datetime

def setup_logging():
    """Setup logging for the robust processor."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler('logs/robust_processor.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger('RobustProcessor')

def check_lm_studio():
    """Check if LM Studio is responding."""
    try:
        import requests
        response = requests.get('http://localhost:1234/v1/models', timeout=5)
        return response.status_code == 200
    except:
        return False

def restart_lm_studio():
    """Attempt to restart LM Studio if it's not responding."""
    logger = logging.getLogger('RobustProcessor')
    logger.warning("LM Studio not responding, attempting restart...")
    
    # Kill existing LM Studio processes
    try:
        subprocess.run(['pkill', '-f', 'lm-studio'], timeout=10)
        time.sleep(5)
    except:
        pass
    
    # Start LM Studio (this might need adjustment based on your setup)
    try:
        subprocess.Popen(['lm-studio'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        logger.info("LM Studio restart attempted")
        time.sleep(30)  # Give it time to start
        return check_lm_studio()
    except:
        logger.error("Failed to restart LM Studio")
        return False

def run_bulk_processor():
    """Run the bulk processor with crash handling."""
    logger = setup_logging()
    
    max_retries = 5
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            logger.info(f"Starting bulk processor (attempt {retry_count + 1}/{max_retries})")
            
            # Check LM Studio before starting
            if not check_lm_studio():
                logger.warning("LM Studio not responding, attempting to restart...")
                if not restart_lm_studio():
                    logger.error("Could not get LM Studio working, continuing anyway...")
            
            # Run the bulk processor
            process = subprocess.Popen(
                ['python', 'bulk_processor.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Monitor the process
            while True:
                return_code = process.poll()
                if return_code is not None:
                    # Process finished
                    stdout, stderr = process.communicate()
                    
                    if return_code == 0:
                        logger.info("Bulk processor completed successfully!")
                        return True
                    else:
                        logger.error(f"Bulk processor crashed with code {return_code}")
                        logger.error(f"STDERR: {stderr}")
                        break
                
                # Check if LM Studio is still responding every 60 seconds
                time.sleep(60)
                if not check_lm_studio():
                    logger.warning("LM Studio stopped responding during processing")
                    process.terminate()
                    break
            
            retry_count += 1
            if retry_count < max_retries:
                wait_time = min(60 * retry_count, 300)  # Wait 1-5 minutes between retries
                logger.info(f"Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
        
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
            if 'process' in locals():
                process.terminate()
            return False
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            retry_count += 1
    
    logger.error(f"Failed after {max_retries} attempts")
    return False

if __name__ == "__main__":
    print("🛡️ Robust Gmail Processor - Auto-restart on crashes")
    print("📊 Monitors LM Studio and restarts processing as needed")
    print("🔄 Will retry up to 5 times on crashes")
    print("")
    
    success = run_bulk_processor()
    
    if success:
        print("✅ Email processing completed successfully!")
    else:
        print("❌ Email processing failed after multiple attempts")
    
    print("👋 Robust processor finished.")