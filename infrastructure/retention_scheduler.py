"""
Event Store Retention Scheduler
Provides automated scheduling for retention cleanup operations
"""

import asyncio
import logging
import schedule
import time
import threading
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass
from enum import Enum

from .retention_manager import retention_manager, redis_retention_manager

logger = logging.getLogger(__name__)


class ScheduleFrequency(Enum):
    """Schedule frequencies for retention operations"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


@dataclass
class RetentionSchedule:
    """Configuration for retention scheduling"""
    enabled: bool = True
    frequency: ScheduleFrequency = ScheduleFrequency.DAILY
    time: str = "02:00"  # 2 AM
    custom_cron: Optional[str] = None
    redis_enabled: bool = True
    redis_max_length: int = 10000
    notification_webhook: Optional[str] = None


class RetentionScheduler:
    """Manages scheduled retention operations"""
    
    def __init__(self, config: RetentionSchedule = None):
        self.config = config or RetentionSchedule()
        self.running = False
        self.scheduler_thread = None
        self.last_run = None
        self.next_run = None
        
        # Setup schedule based on configuration
        self._setup_schedule()
    
    def _setup_schedule(self):
        """Configure the retention schedule"""
        schedule.clear()  # Clear any existing schedules
        
        if not self.config.enabled:
            logger.info("Retention scheduling is disabled")
            return
        
        if self.config.frequency == ScheduleFrequency.DAILY:
            schedule.every().day.at(self.config.time).do(self._run_retention_job)
        elif self.config.frequency == ScheduleFrequency.WEEKLY:
            schedule.every().monday.at(self.config.time).do(self._run_retention_job)
        elif self.config.frequency == ScheduleFrequency.MONTHLY:
            # Run on first day of month
            schedule.every().day.at(self.config.time).do(self._monthly_check_and_run)
        
        # Calculate next run time
        jobs = schedule.get_jobs()
        if jobs:
            self.next_run = min(job.next_run for job in jobs)
            logger.info(f"Retention scheduler configured: next run at {self.next_run}")
    
    def _monthly_check_and_run(self):
        """Check if it's the first day of the month and run if so"""
        if datetime.now().day == 1:
            return self._run_retention_job()
    
    def _run_retention_job(self):
        """Execute the scheduled retention job"""
        try:
            logger.info("🗄️ Starting scheduled retention cleanup")
            
            # Run in new event loop for thread safety
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # File-based retention
                results = loop.run_until_complete(retention_manager.apply_retention_policies())
                
                # Redis retention
                redis_results = None
                if self.config.redis_enabled:
                    redis_results = loop.run_until_complete(
                        redis_retention_manager.apply_redis_retention(
                            max_length=self.config.redis_max_length
                        )
                    )
                
                # Update last run time
                self.last_run = datetime.now()
                
                # Log results
                logger.info(f"✅ Scheduled retention cleanup completed")
                logger.info(f"   Files processed: {len(results['processed_files'])}")
                logger.info(f"   Events archived: {results['total_events_archived']}")
                logger.info(f"   Events deleted: {results['total_events_deleted']}")
                
                if redis_results and "error" not in redis_results:
                    logger.info(f"   Redis events trimmed: {redis_results.get('trimmed_events', 0)}")
                
                # Send notification if configured
                if self.config.notification_webhook:
                    loop.run_until_complete(self._send_notification(results, redis_results))
                
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"❌ Error in scheduled retention cleanup: {e}")
    
    async def _send_notification(self, file_results: Dict, redis_results: Optional[Dict]):
        """Send notification about retention results"""
        try:
            import aiohttp
            
            message = {
                "type": "retention_cleanup",
                "timestamp": datetime.utcnow().isoformat(),
                "results": {
                    "files_processed": len(file_results["processed_files"]),
                    "events_archived": file_results["total_events_archived"],
                    "events_deleted": file_results["total_events_deleted"],
                    "errors": file_results.get("errors", [])
                }
            }
            
            if redis_results and "error" not in redis_results:
                message["results"]["redis_trimmed"] = redis_results.get("trimmed_events", 0)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.config.notification_webhook, json=message) as response:
                    if response.status == 200:
                        logger.info("Retention notification sent successfully")
                    else:
                        logger.warning(f"Retention notification failed: {response.status}")
                        
        except Exception as e:
            logger.warning(f"Failed to send retention notification: {e}")
    
    def start(self):
        """Start the retention scheduler"""
        if self.running:
            logger.warning("Retention scheduler is already running")
            return
        
        if not self.config.enabled:
            logger.info("Retention scheduling is disabled")
            return
        
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        
        logger.info(f"🕒 Retention scheduler started (next run: {self.next_run})")
    
    def stop(self):
        """Stop the retention scheduler"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5.0)
        
        logger.info("🛑 Retention scheduler stopped")
    
    def _scheduler_loop(self):
        """Main scheduler loop running in background thread"""
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
                # Update next run time
                jobs = schedule.get_jobs()
                if jobs:
                    self.next_run = min(job.next_run for job in jobs)
                    
            except Exception as e:
                logger.error(f"Error in retention scheduler loop: {e}")
                time.sleep(60)  # Continue after error
    
    def get_status(self) -> Dict[str, Any]:
        """Get scheduler status"""
        return {
            "running": self.running,
            "enabled": self.config.enabled,
            "frequency": self.config.frequency.value,
            "time": self.config.time,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "redis_enabled": self.config.redis_enabled,
            "redis_max_length": self.config.redis_max_length
        }
    
    def force_run(self) -> Dict[str, Any]:
        """Force immediate retention run (for testing/manual triggers)"""
        logger.info("🔥 Forcing immediate retention cleanup")
        self._run_retention_job()
        return {"status": "completed", "timestamp": datetime.utcnow().isoformat()}


# Environment-based configuration
def load_scheduler_config() -> RetentionSchedule:
    """Load scheduler configuration from environment variables"""
    import os
    
    config = RetentionSchedule()
    
    # Basic settings
    config.enabled = os.getenv("RETENTION_SCHEDULER_ENABLED", "true").lower() == "true"
    config.time = os.getenv("RETENTION_SCHEDULER_TIME", "02:00")
    config.notification_webhook = os.getenv("RETENTION_NOTIFICATION_WEBHOOK")
    
    # Frequency
    frequency_str = os.getenv("RETENTION_SCHEDULER_FREQUENCY", "daily").lower()
    try:
        config.frequency = ScheduleFrequency(frequency_str)
    except ValueError:
        logger.warning(f"Invalid frequency '{frequency_str}', using daily")
        config.frequency = ScheduleFrequency.DAILY
    
    # Redis settings
    config.redis_enabled = os.getenv("RETENTION_REDIS_ENABLED", "true").lower() == "true"
    try:
        config.redis_max_length = int(os.getenv("RETENTION_REDIS_MAX_LENGTH", "10000"))
    except ValueError:
        logger.warning("Invalid RETENTION_REDIS_MAX_LENGTH, using 10000")
        config.redis_max_length = 10000
    
    logger.info(f"Retention scheduler config loaded: {config.frequency.value} at {config.time}")
    return config


# Global scheduler instance
retention_scheduler = RetentionScheduler(load_scheduler_config())


# Integration with application lifecycle
async def start_retention_scheduler():
    """Start retention scheduler (called during app startup)"""
    retention_scheduler.start()


async def stop_retention_scheduler():
    """Stop retention scheduler (called during app shutdown)"""
    retention_scheduler.stop()


# Health check integration
async def retention_health_check() -> Dict[str, Any]:
    """Health check for retention scheduler"""
    status = retention_scheduler.get_status()
    
    # Check if scheduler is working properly
    healthy = True
    if status["enabled"] and not status["running"]:
        healthy = False
    
    # Check if last run was recent (for daily schedules)
    if status["last_run"] and status["frequency"] == "daily":
        last_run = datetime.fromisoformat(status["last_run"])
        if (datetime.now() - last_run).days > 2:  # Allow some tolerance
            healthy = False
    
    return {
        "healthy": healthy,
        "status": status,
        "message": "Retention scheduler operational" if healthy else "Retention scheduler issues detected"
    }


if __name__ == "__main__":
    # For testing
    import sys
    import logging
    
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        print("Testing retention scheduler...")
        
        # Create test config with immediate execution
        test_config = RetentionSchedule(
            enabled=True,
            frequency=ScheduleFrequency.DAILY,
            time=datetime.now().strftime("%H:%M")
        )
        
        scheduler = RetentionScheduler(test_config)
        scheduler.start()
        
        # Force immediate run for testing
        scheduler.force_run()
        
        print("Test completed")
    else:
        print("Available commands: test")