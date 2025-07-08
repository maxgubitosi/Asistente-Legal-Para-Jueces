import shutil
import subprocess
import time
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

class EvalDockerManager:
    """Manages Docker setup for evaluation tests"""
    
    def __init__(self, 
                 eval_docker_path: str = "legal-rag-eval-version",
                 eval_port: int = 8001):
        self.eval_docker_path = Path(eval_docker_path)
        self.eval_port = eval_port
        
        if not self.eval_docker_path.exists():
            raise FileNotFoundError(f"Eval Docker directory not found: {eval_docker_path}")
    
    def setup_test_data(self, test_data_path: Path) -> bool:
        """
        Copy test data to eval Docker directory and clear cache.
        
        Args:
            test_data_path: Path to test data (e.g., datasets_evaluation/test2/)
            
        Returns:
            True if setup successful, False otherwise
        """
        try:
            # Target paths
            target_data_path = self.eval_docker_path / "datasets" / "fallos_json"
            cache_path = self.eval_docker_path / "bm25_cache"
            
            logger.info(f"🔄 Setting up test data for eval Docker...")
            logger.info(f"  📁 Source: {test_data_path}")
            logger.info(f"  📁 Target: {target_data_path}")
            
            # Clear existing data
            if target_data_path.exists():
                logger.info("🗑️ Clearing existing data...")
                shutil.rmtree(target_data_path)
            
            # Copy test data
            logger.info("📋 Copying test data...")
            shutil.copytree(test_data_path, target_data_path)
            
            # Clear cache to force recomputation
            if cache_path.exists():
                logger.info("🧹 Clearing cache files...")
                shutil.rmtree(cache_path)
                cache_path.mkdir(exist_ok=True)
            
            logger.info("✅ Test data setup completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error setting up test data: {e}")
            return False
    
    def start_eval_docker(self) -> bool:
        """
        Start the eval Docker container.
        
        Returns:
            True if started successfully, False otherwise
        """
        try:
            logger.info("🐳 Starting eval Docker container...")
            
            # Change to eval docker directory
            original_cwd = Path.cwd()
            
            try:
                # Stop any existing containers
                subprocess.run(
                    ["docker", "compose", "down"],
                    cwd=self.eval_docker_path,
                    capture_output=True,
                    check=False  # Don't fail if no containers running
                )
                
                # Start new container
                result = subprocess.run(
                    ["docker", "compose", "up", "--build", "-d"],
                    cwd=self.eval_docker_path,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    logger.error(f"❌ Docker startup failed: {result.stderr}")
                    return False
                
                logger.info("⏳ Waiting for container to be ready...")
                time.sleep(30)  # Give container time to start
                
                logger.info("✅ Eval Docker container started")
                return True
                
            finally:
                # Always return to original directory
                import os
                os.chdir(original_cwd)
                
        except Exception as e:
            logger.error(f"❌ Error starting eval Docker: {e}")
            return False
    
    def stop_eval_docker(self) -> bool:
        """
        Stop the eval Docker container.
        
        Returns:
            True if stopped successfully, False otherwise
        """
        try:
            logger.info("🛑 Stopping eval Docker container...")
            
            result = subprocess.run(
                ["docker", "compose", "down"],
                cwd=self.eval_docker_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"❌ Docker stop failed: {result.stderr}")
                return False
            
            logger.info("✅ Eval Docker container stopped")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error stopping eval Docker: {e}")
            return False
    
    def is_eval_docker_running(self) -> bool:
        """
        Check if eval Docker container is running.
        
        Returns:
            True if running, False otherwise
        """
        try:
            result = subprocess.run(
                ["docker", "compose", "ps", "-q"],
                cwd=self.eval_docker_path,
                capture_output=True,
                text=True
            )
            
            return bool(result.stdout.strip())
            
        except Exception as e:
            logger.error(f"❌ Error checking Docker status: {e}")
            return False
    
    def get_eval_backend_url(self) -> str:
        """Get the URL for the eval backend"""
        return f"http://localhost:{self.eval_port}" 