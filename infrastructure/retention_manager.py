"""
Event Store Retention Policy Manager
Handles event archival, cleanup, and lifecycle management for file-based and Redis event stores
"""

import os
import json
import gzip
import shutil
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)


class RetentionPolicy(Enum):
    """Event retention policies"""
    ARCHIVE_AND_DELETE = "archive_and_delete"  # Archive then delete original
    DELETE_ONLY = "delete_only"               # Direct deletion
    ARCHIVE_ONLY = "archive_only"             # Archive but keep original


@dataclass
class RetentionConfig:
    """Configuration for event retention policies"""
    policy: RetentionPolicy
    retention_days: int
    archive_retention_days: Optional[int] = None  # How long to keep archives
    archive_location: Optional[str] = None
    compress_archives: bool = True
    batch_size: int = 1000  # Process events in batches
    
    def __post_init__(self):
        if self.archive_location is None:
            self.archive_location = "data/archives"
        if self.archive_retention_days is None:
            self.archive_retention_days = self.retention_days * 3  # Keep archives 3x longer


class EventRetentionManager:
    """Manages event store retention policies with archival and cleanup"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.archive_dir = None
        
        # Default retention configurations by event store
        self.retention_configs = {
            "application_events.jsonl": RetentionConfig(
                policy=RetentionPolicy.ARCHIVE_AND_DELETE,
                retention_days=90,
                archive_retention_days=365
            ),
            "auth_domain_events.jsonl": RetentionConfig(
                policy=RetentionPolicy.ARCHIVE_AND_DELETE,
                retention_days=180,  # Keep auth events longer for compliance
                archive_retention_days=1095  # 3 years
            ),
            "match_history.jsonl": RetentionConfig(
                policy=RetentionPolicy.ARCHIVE_AND_DELETE,
                retention_days=30,
                archive_retention_days=180
            ),
            "auth_events.jsonl": RetentionConfig(
                policy=RetentionPolicy.ARCHIVE_AND_DELETE,
                retention_days=60,
                archive_retention_days=365
            )
        }
        
        # Load environment-based overrides
        self._load_env_config()
    
    def _load_env_config(self):
        """Load retention configuration from environment variables"""
        # Global defaults
        if global_retention := os.getenv("EVENT_RETENTION_DAYS"):
            try:
                days = int(global_retention)
                for config in self.retention_configs.values():
                    config.retention_days = days
            except ValueError:
                logger.warning(f"Invalid EVENT_RETENTION_DAYS: {global_retention}")
        
        # Archive location override
        if archive_location := os.getenv("EVENT_ARCHIVE_LOCATION"):
            for config in self.retention_configs.values():
                config.archive_location = archive_location
        
        # Compression setting
        if compress_setting := os.getenv("EVENT_ARCHIVE_COMPRESS", "true"):
            compress = compress_setting.lower() == "true"
            for config in self.retention_configs.values():
                config.compress_archives = compress
    
    def setup_archive_directories(self):
        """Create archive directory structure"""
        for filename, config in self.retention_configs.items():
            archive_path = Path(config.archive_location)
            archive_path.mkdir(parents=True, exist_ok=True)
            
            # Create subdirectories by event type
            event_type = filename.replace('.jsonl', '').replace('_events', '')
            (archive_path / event_type).mkdir(exist_ok=True)
            
            logger.info(f"Archive directory ready: {archive_path / event_type}")
    
    async def apply_retention_policies(self) -> Dict[str, Any]:
        """Apply retention policies to all configured event stores"""
        self.setup_archive_directories()
        
        results = {
            "processed_files": [],
            "total_events_processed": 0,
            "total_events_archived": 0,
            "total_events_deleted": 0,
            "errors": []
        }
        
        for filename, config in self.retention_configs.items():
            file_path = self.data_dir / filename
            
            if not file_path.exists():
                logger.info(f"Event store file not found, skipping: {filename}")
                continue
            
            try:
                logger.info(f"Applying retention policy to {filename}")
                file_result = await self._process_event_file(file_path, config)
                
                results["processed_files"].append({
                    "filename": filename,
                    "events_processed": file_result["events_processed"],
                    "events_archived": file_result["events_archived"],
                    "events_deleted": file_result["events_deleted"],
                    "archive_file": file_result.get("archive_file")
                })
                
                results["total_events_processed"] += file_result["events_processed"]
                results["total_events_archived"] += file_result["events_archived"]
                results["total_events_deleted"] += file_result["events_deleted"]
                
            except Exception as e:
                error_msg = f"Error processing {filename}: {str(e)}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
        
        # Clean up old archives
        await self._cleanup_old_archives()
        
        return results
    
    async def _process_event_file(self, file_path: Path, config: RetentionConfig) -> Dict[str, Any]:
        """Process a single event file according to its retention policy"""
        cutoff_date = datetime.utcnow() - timedelta(days=config.retention_days)
        
        events_to_keep = []
        events_to_archive = []
        
        # Read and categorize events
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                if not line.strip():
                    continue
                
                try:
                    event = json.loads(line.strip())
                    event_time = datetime.fromisoformat(event.get('timestamp', ''))
                    
                    if event_time < cutoff_date:
                        events_to_archive.append(event)
                    else:
                        events_to_keep.append(event)
                        
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"Invalid event at line {line_num} in {file_path}: {e}")
                    continue
        
        result = {
            "events_processed": len(events_to_keep) + len(events_to_archive),
            "events_archived": 0,
            "events_deleted": 0,
            "archive_file": None
        }
        
        # Handle archiving
        if events_to_archive:
            if config.policy in [RetentionPolicy.ARCHIVE_AND_DELETE, RetentionPolicy.ARCHIVE_ONLY]:
                archive_file = await self._archive_events(events_to_archive, file_path, config)
                result["archive_file"] = str(archive_file)
                result["events_archived"] = len(events_to_archive)
            
            if config.policy in [RetentionPolicy.ARCHIVE_AND_DELETE, RetentionPolicy.DELETE_ONLY]:
                result["events_deleted"] = len(events_to_archive)
        
        # Rewrite the main file with only events to keep
        if events_to_archive:  # Only rewrite if we actually removed events
            backup_path = file_path.with_suffix(file_path.suffix + '.backup')
            shutil.copy2(file_path, backup_path)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                for event in events_to_keep:
                    f.write(json.dumps(event, separators=(',', ':')) + '\n')
            
            logger.info(f"Processed {file_path.name}: kept {len(events_to_keep)}, archived {len(events_to_archive)}")
        
        return result
    
    async def _archive_events(self, events: List[Dict], source_file: Path, config: RetentionConfig) -> Path:
        """Archive events to compressed storage"""
        # Create archive filename with timestamp
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        event_type = source_file.stem.replace('_events', '')
        
        archive_dir = Path(config.archive_location) / event_type
        archive_filename = f"{event_type}_archive_{timestamp}.jsonl"
        
        if config.compress_archives:
            archive_filename += ".gz"
            archive_path = archive_dir / archive_filename
            
            with gzip.open(archive_path, 'wt', encoding='utf-8') as f:
                for event in events:
                    f.write(json.dumps(event, separators=(',', ':')) + '\n')
        else:
            archive_path = archive_dir / archive_filename
            with open(archive_path, 'w', encoding='utf-8') as f:
                for event in events:
                    f.write(json.dumps(event, separators=(',', ':')) + '\n')
        
        logger.info(f"Archived {len(events)} events to {archive_path}")
        return archive_path
    
    async def _cleanup_old_archives(self):
        """Clean up archives that exceed their retention period"""
        for filename, config in self.retention_configs.items():
            if not config.archive_retention_days:
                continue
                
            archive_dir = Path(config.archive_location) / filename.replace('_events.jsonl', '')
            if not archive_dir.exists():
                continue
            
            cutoff_date = datetime.utcnow() - timedelta(days=config.archive_retention_days)
            deleted_count = 0
            
            for archive_file in archive_dir.glob("*_archive_*.jsonl*"):
                try:
                    # Extract timestamp from filename
                    timestamp_str = archive_file.stem.split('_archive_')[1].split('.')[0]
                    archive_date = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    
                    if archive_date < cutoff_date:
                        archive_file.unlink()
                        deleted_count += 1
                        logger.info(f"Deleted old archive: {archive_file}")
                        
                except (ValueError, IndexError) as e:
                    logger.warning(f"Could not parse archive date from {archive_file}: {e}")
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old archives from {archive_dir}")
    
    async def get_retention_status(self) -> Dict[str, Any]:
        """Get status of event stores and their retention policies"""
        status = {
            "retention_policies": {},
            "file_stats": {},
            "archive_stats": {},
            "recommendations": []
        }
        
        for filename, config in self.retention_configs.items():
            file_path = self.data_dir / filename
            
            policy_info = {
                "policy": config.policy.value,
                "retention_days": config.retention_days,
                "archive_retention_days": config.archive_retention_days,
                "compress_archives": config.compress_archives
            }
            
            if file_path.exists():
                file_stats = file_path.stat()
                file_info = {
                    "exists": True,
                    "size_mb": round(file_stats.st_size / (1024 * 1024), 2),
                    "modified": datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
                    "estimated_events": await self._count_events(file_path)
                }
                
                # Calculate estimated old events
                cutoff_date = datetime.utcnow() - timedelta(days=config.retention_days)
                old_events = await self._count_old_events(file_path, cutoff_date)
                file_info["old_events_estimate"] = old_events
                
                if old_events > 100:
                    status["recommendations"].append(f"{filename}: {old_events} events ready for archival")
            else:
                file_info = {"exists": False}
            
            status["retention_policies"][filename] = policy_info
            status["file_stats"][filename] = file_info
            
            # Archive stats
            archive_dir = Path(config.archive_location) / filename.replace('_events.jsonl', '')
            if archive_dir.exists():
                archive_files = list(archive_dir.glob("*_archive_*.jsonl*"))
                total_archive_size = sum(f.stat().st_size for f in archive_files)
                status["archive_stats"][filename] = {
                    "archive_count": len(archive_files),
                    "total_size_mb": round(total_archive_size / (1024 * 1024), 2)
                }
            else:
                status["archive_stats"][filename] = {"archive_count": 0, "total_size_mb": 0}
        
        return status
    
    async def _count_events(self, file_path: Path) -> int:
        """Count total events in a file"""
        count = 0
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        count += 1
        except Exception as e:
            logger.warning(f"Error counting events in {file_path}: {e}")
        return count
    
    async def _count_old_events(self, file_path: Path, cutoff_date: datetime) -> int:
        """Count events older than cutoff date"""
        count = 0
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        event = json.loads(line.strip())
                        event_time = datetime.fromisoformat(event.get('timestamp', ''))
                        if event_time < cutoff_date:
                            count += 1
                    except (json.JSONDecodeError, ValueError):
                        continue
        except Exception as e:
            logger.warning(f"Error counting old events in {file_path}: {e}")
        return count


class RedisRetentionManager:
    """Manages Redis event stream retention"""
    
    def __init__(self):
        self.redis_client = None
        try:
            from infrastructure.event_bus import RedisEventBus
            self.redis_bus = RedisEventBus()
            self.redis_client = self.redis_bus.redis_client
        except ImportError:
            logger.warning("Redis not available for retention management")
    
    async def apply_redis_retention(self, stream_name: str = "seraaj:events:global", 
                                  max_length: int = 10000, approximate: bool = True) -> Dict[str, Any]:
        """Apply retention policy to Redis stream"""
        if not self.redis_client:
            return {"error": "Redis not available"}
        
        try:
            # Use XTRIM to limit stream length
            result = await self.redis_client.xtrim(
                stream_name, 
                maxlen=max_length, 
                approximate=approximate
            )
            
            # Get current stream info
            stream_info = await self.redis_client.xinfo_stream(stream_name)
            
            return {
                "stream": stream_name,
                "trimmed_events": result,
                "current_length": stream_info.get("length", 0),
                "max_length": max_length
            }
            
        except Exception as e:
            logger.error(f"Error applying Redis retention to {stream_name}: {e}")
            return {"error": str(e)}


# Singleton instance
retention_manager = EventRetentionManager()
redis_retention_manager = RedisRetentionManager()


async def run_retention_cleanup():
    """CLI function to run retention cleanup"""
    print("🗄️ Starting Event Store Retention Cleanup...")
    
    # File-based retention
    results = await retention_manager.apply_retention_policies()
    
    print(f"\n✅ File Retention Results:")
    print(f"   Total events processed: {results['total_events_processed']}")
    print(f"   Events archived: {results['total_events_archived']}")
    print(f"   Events deleted: {results['total_events_deleted']}")
    print(f"   Files processed: {len(results['processed_files'])}")
    
    if results['errors']:
        print(f"\n⚠️ Errors encountered:")
        for error in results['errors']:
            print(f"   - {error}")
    
    # Redis retention
    if redis_retention_manager.redis_client:
        redis_result = await redis_retention_manager.apply_redis_retention()
        if "error" not in redis_result:
            print(f"\n✅ Redis Retention Results:")
            print(f"   Stream: {redis_result['stream']}")
            print(f"   Trimmed events: {redis_result['trimmed_events']}")
            print(f"   Current length: {redis_result['current_length']}")
    
    print("\n🎉 Retention cleanup completed!")


if __name__ == "__main__":
    asyncio.run(run_retention_cleanup())