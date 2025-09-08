"""
Contract Compliance Monitoring and Alerting
Continuous monitoring of contract compliance with alerting and reporting
"""

import asyncio
import logging
import schedule
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path

from .contract_validator import contract_validator, ComplianceStatus

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class ComplianceAlert:
    """Contract compliance alert"""
    severity: AlertSeverity
    message: str
    timestamp: datetime
    test_name: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MonitoringConfig:
    """Configuration for contract compliance monitoring"""
    enabled: bool = True
    check_interval_minutes: int = 30
    alert_on_degraded: bool = True
    alert_on_failure: bool = True
    store_history: bool = True
    max_history_days: int = 30
    notification_webhook: Optional[str] = None
    failure_threshold: int = 3  # Consecutive failures before critical alert


class ContractComplianceMonitor:
    """Monitors contract compliance continuously and generates alerts"""
    
    def __init__(self, config: MonitoringConfig = None):
        self.config = config or MonitoringConfig()
        self.running = False
        self.monitor_thread = None
        self.last_check = None
        self.next_check = None
        
        # Compliance history
        self.compliance_history = []
        self.consecutive_failures = 0
        self.current_alerts = []
        
        # Load configuration from environment
        self._load_env_config()
        
        # Setup monitoring schedule
        self._setup_schedule()
    
    def _load_env_config(self):
        """Load monitoring configuration from environment variables"""
        import os
        
        # Override with environment variables
        if enabled := os.getenv("CONTRACT_MONITORING_ENABLED"):
            self.config.enabled = enabled.lower() == "true"
        
        if interval := os.getenv("CONTRACT_MONITORING_INTERVAL"):
            try:
                self.config.check_interval_minutes = int(interval)
            except ValueError:
                logger.warning(f"Invalid CONTRACT_MONITORING_INTERVAL: {interval}")
        
        if webhook := os.getenv("CONTRACT_MONITORING_WEBHOOK"):
            self.config.notification_webhook = webhook
        
        if threshold := os.getenv("CONTRACT_FAILURE_THRESHOLD"):
            try:
                self.config.failure_threshold = int(threshold)
            except ValueError:
                logger.warning(f"Invalid CONTRACT_FAILURE_THRESHOLD: {threshold}")
    
    def _setup_schedule(self):
        """Setup the monitoring schedule"""
        if not self.config.enabled:
            return
        
        schedule.clear("contract_monitoring")
        
        # Schedule regular compliance checks
        schedule.every(self.config.check_interval_minutes).minutes.do(
            self._run_compliance_check
        ).tag("contract_monitoring")
        
        # Schedule daily cleanup
        schedule.every().day.at("03:00").do(
            self._cleanup_old_history
        ).tag("contract_monitoring")
        
        # Calculate next check time
        jobs = schedule.get_jobs("contract_monitoring")
        if jobs:
            self.next_check = min(job.next_run for job in jobs)
    
    def start_monitoring(self):
        """Start continuous contract compliance monitoring"""
        if self.running:
            logger.warning("Contract compliance monitor is already running")
            return
        
        if not self.config.enabled:
            logger.info("Contract compliance monitoring is disabled")
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            name="contract_monitor",
            daemon=True
        )
        self.monitor_thread.start()
        
        logger.info(f"🔍 Contract compliance monitoring started (interval: {self.config.check_interval_minutes}min)")
    
    def stop_monitoring(self):
        """Stop contract compliance monitoring"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=10.0)
        
        schedule.clear("contract_monitoring")
        logger.info("🛑 Contract compliance monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop running in background thread"""
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
                # Update next check time
                jobs = schedule.get_jobs("contract_monitoring")
                if jobs:
                    self.next_check = min(job.next_run for job in jobs)
                    
            except Exception as e:
                logger.error(f"Error in contract monitoring loop: {e}")
                time.sleep(60)
    
    def _run_compliance_check(self):
        """Execute scheduled compliance check"""
        try:
            logger.info("🔍 Running scheduled contract compliance check")
            
            # Run in new event loop for thread safety
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                results = loop.run_until_complete(contract_validator.validate_all_contracts())
                self._process_compliance_results(results)
                
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"Error in scheduled compliance check: {e}")
            self._generate_error_alert(str(e))
    
    def _process_compliance_results(self, results: Dict[str, Any]):
        """Process compliance check results and generate alerts"""
        self.last_check = datetime.utcnow()
        
        # Store in history
        if self.config.store_history:
            self.compliance_history.append({
                "timestamp": self.last_check.isoformat(),
                "overall_status": results["overall_status"],
                "tests_passed": results["tests_passed"],
                "tests_failed": results["tests_failed"],
                "tests_degraded": results["tests_degraded"],
                "execution_time": results["execution_time_seconds"]
            })
        
        # Generate alerts based on results
        current_status = results["overall_status"]
        
        if current_status == "non_compliant":
            self.consecutive_failures += 1
            
            if self.consecutive_failures >= self.config.failure_threshold:
                alert = ComplianceAlert(
                    severity=AlertSeverity.CRITICAL,
                    message=f"Contract compliance CRITICAL: {self.consecutive_failures} consecutive failures",
                    timestamp=self.last_check,
                    test_name="overall_compliance",
                    details={
                        "consecutive_failures": self.consecutive_failures,
                        "failed_tests": results["tests_failed"],
                        "total_tests": results["tests_run"]
                    }
                )
                self._add_alert(alert)
            elif self.config.alert_on_failure:
                alert = ComplianceAlert(
                    severity=AlertSeverity.WARNING,
                    message=f"Contract compliance FAILED: {results['tests_failed']}/{results['tests_run']} tests failed",
                    timestamp=self.last_check,
                    test_name="overall_compliance",
                    details=results
                )
                self._add_alert(alert)
        
        elif current_status == "degraded" and self.config.alert_on_degraded:
            alert = ComplianceAlert(
                severity=AlertSeverity.WARNING,
                message=f"Contract compliance DEGRADED: {results['tests_degraded']} tests degraded",
                timestamp=self.last_check,
                test_name="overall_compliance", 
                details=results
            )
            self._add_alert(alert)
            
        else:
            # Reset consecutive failures on success
            if self.consecutive_failures > 0:
                logger.info(f"Contract compliance recovered after {self.consecutive_failures} failures")
                self.consecutive_failures = 0
                
                # Generate recovery alert
                alert = ComplianceAlert(
                    severity=AlertSeverity.INFO,
                    message="Contract compliance RECOVERED: All tests now passing",
                    timestamp=self.last_check,
                    test_name="overall_compliance",
                    details=results
                )
                self._add_alert(alert)
        
        # Check for specific test failures
        for test_result in results["results"]:
            if test_result["status"] in ["non_compliant", "error"] and test_result.get("errors"):
                alert = ComplianceAlert(
                    severity=AlertSeverity.WARNING,
                    message=f"Test '{test_result['test_name']}' failed: {test_result['message']}",
                    timestamp=self.last_check,
                    test_name=test_result["test_name"],
                    details=test_result
                )
                self._add_alert(alert)
        
        logger.info(f"Contract compliance check completed: {current_status} ({results['tests_passed']}/{results['tests_run']} passed)")
    
    def _generate_error_alert(self, error_message: str):
        """Generate alert for monitoring system errors"""
        alert = ComplianceAlert(
            severity=AlertSeverity.CRITICAL,
            message=f"Contract monitoring system error: {error_message}",
            timestamp=datetime.utcnow(),
            test_name="monitoring_system",
            details={"error": error_message}
        )
        self._add_alert(alert)
    
    def _add_alert(self, alert: ComplianceAlert):
        """Add alert and trigger notifications"""
        self.current_alerts.append(alert)
        
        # Log alert
        log_level = {
            AlertSeverity.INFO: logging.INFO,
            AlertSeverity.WARNING: logging.WARNING,
            AlertSeverity.CRITICAL: logging.ERROR
        }[alert.severity]
        
        logger.log(log_level, f"Contract Alert ({alert.severity.value}): {alert.message}")
        
        # Send notification if configured
        if self.config.notification_webhook:
            asyncio.create_task(self._send_notification(alert))
    
    async def _send_notification(self, alert: ComplianceAlert):
        """Send alert notification to configured webhook"""
        try:
            import aiohttp
            
            payload = {
                "type": "contract_compliance_alert",
                "severity": alert.severity.value,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat(),
                "test_name": alert.test_name,
                "details": alert.details
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.config.notification_webhook, json=payload) as response:
                    if response.status == 200:
                        logger.debug(f"Alert notification sent: {alert.test_name}")
                    else:
                        logger.warning(f"Alert notification failed: {response.status}")
                        
        except Exception as e:
            logger.warning(f"Failed to send alert notification: {e}")
    
    def _cleanup_old_history(self):
        """Clean up old compliance history"""
        if not self.config.store_history:
            return
        
        cutoff_date = datetime.utcnow() - timedelta(days=self.config.max_history_days)
        
        original_count = len(self.compliance_history)
        self.compliance_history = [
            record for record in self.compliance_history
            if datetime.fromisoformat(record["timestamp"]) > cutoff_date
        ]
        
        removed_count = original_count - len(self.compliance_history)
        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} old compliance history records")
        
        # Clean up old alerts
        self.current_alerts = [
            alert for alert in self.current_alerts
            if alert.timestamp > cutoff_date
        ]
    
    async def force_compliance_check(self) -> Dict[str, Any]:
        """Force immediate compliance check"""
        logger.info("🔥 Forcing immediate contract compliance check")
        
        results = await contract_validator.validate_all_contracts()
        self._process_compliance_results(results)
        
        return results
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring status"""
        return {
            "enabled": self.config.enabled,
            "running": self.running,
            "check_interval_minutes": self.config.check_interval_minutes,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "next_check": self.next_check.isoformat() if self.next_check else None,
            "consecutive_failures": self.consecutive_failures,
            "current_alerts_count": len(self.current_alerts),
            "history_records_count": len(self.compliance_history),
            "failure_threshold": self.config.failure_threshold
        }
    
    def get_compliance_trend(self, days: int = 7) -> Dict[str, Any]:
        """Get compliance trend over specified days"""
        if not self.compliance_history:
            return {"trend": "no_data", "records": 0}
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        recent_records = [
            record for record in self.compliance_history
            if datetime.fromisoformat(record["timestamp"]) > cutoff_date
        ]
        
        if not recent_records:
            return {"trend": "no_recent_data", "records": 0}
        
        # Calculate trend metrics
        total_checks = len(recent_records)
        compliant_checks = sum(1 for r in recent_records if r["overall_status"] == "compliant")
        failed_checks = sum(1 for r in recent_records if r["overall_status"] == "non_compliant")
        degraded_checks = sum(1 for r in recent_records if r["overall_status"] == "degraded")
        
        success_rate = (compliant_checks / total_checks * 100) if total_checks > 0 else 0
        
        # Determine trend
        if success_rate >= 95:
            trend = "excellent"
        elif success_rate >= 80:
            trend = "good"
        elif success_rate >= 60:
            trend = "concerning"
        else:
            trend = "poor"
        
        return {
            "trend": trend,
            "success_rate": round(success_rate, 1),
            "records": total_checks,
            "compliant_checks": compliant_checks,
            "failed_checks": failed_checks,
            "degraded_checks": degraded_checks,
            "period_days": days
        }
    
    def get_recent_alerts(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent alerts within specified hours"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        recent_alerts = [
            alert for alert in self.current_alerts
            if alert.timestamp > cutoff_time
        ]
        
        return [
            {
                "severity": alert.severity.value,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat(),
                "test_name": alert.test_name,
                "details": alert.details
            }
            for alert in recent_alerts
        ]


# Environment-based configuration
def load_monitoring_config() -> MonitoringConfig:
    """Load monitoring configuration from environment"""
    import os
    
    return MonitoringConfig(
        enabled=os.getenv("CONTRACT_MONITORING_ENABLED", "true").lower() == "true",
        check_interval_minutes=int(os.getenv("CONTRACT_MONITORING_INTERVAL", "30")),
        alert_on_degraded=os.getenv("CONTRACT_ALERT_DEGRADED", "true").lower() == "true",
        alert_on_failure=os.getenv("CONTRACT_ALERT_FAILURE", "true").lower() == "true",
        notification_webhook=os.getenv("CONTRACT_MONITORING_WEBHOOK"),
        failure_threshold=int(os.getenv("CONTRACT_FAILURE_THRESHOLD", "3"))
    )


# Global monitor instance
contract_monitor = ContractComplianceMonitor(load_monitoring_config())


# Integration functions
async def start_contract_monitoring():
    """Start contract compliance monitoring (called during app startup)"""
    contract_monitor.start_monitoring()


async def stop_contract_monitoring():
    """Stop contract compliance monitoring (called during app shutdown)"""
    contract_monitor.stop_monitoring()


async def contract_compliance_health_check() -> Dict[str, Any]:
    """Health check for contract compliance monitoring"""
    status = contract_monitor.get_monitoring_status()
    trend = contract_monitor.get_compliance_trend(days=1)  # Last 24 hours
    recent_alerts = contract_monitor.get_recent_alerts(hours=4)
    
    # Determine health based on recent performance
    healthy = True
    if status["consecutive_failures"] >= 2:
        healthy = False
    elif len([a for a in recent_alerts if a["severity"] == "critical"]) > 0:
        healthy = False
    
    return {
        "healthy": healthy,
        "monitoring_enabled": status["enabled"],
        "monitoring_running": status["running"],
        "last_check": status["last_check"],
        "consecutive_failures": status["consecutive_failures"],
        "recent_trend": trend["trend"],
        "recent_success_rate": trend.get("success_rate", 0),
        "critical_alerts_4h": len([a for a in recent_alerts if a["severity"] == "critical"]),
        "message": "Contract compliance monitoring operational" if healthy else "Contract compliance issues detected"
    }


if __name__ == "__main__":
    # For testing
    import logging
    
    logging.basicConfig(level=logging.INFO)
    
    print("Testing contract compliance monitor...")
    
    monitor = ContractComplianceMonitor(MonitoringConfig(
        enabled=True,
        check_interval_minutes=1  # 1 minute for testing
    ))
    
    monitor.start_monitoring()
    
    try:
        # Force a check for testing
        asyncio.run(monitor.force_compliance_check())
        
        # Show status
        status = monitor.get_monitoring_status()
        print(f"Monitor status: {json.dumps(status, indent=2)}")
        
        # Wait a bit to see monitoring in action
        time.sleep(65)
        
    finally:
        monitor.stop_monitoring()
    
    print("Test completed")