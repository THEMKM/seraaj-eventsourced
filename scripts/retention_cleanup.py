#!/usr/bin/env python3
"""
Event Store Retention Cleanup CLI Tool
Provides command-line interface for event archival and cleanup operations
"""

import asyncio
import argparse
import sys
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from infrastructure.retention_manager import (
    retention_manager,
    redis_retention_manager,
    RetentionPolicy,
    RetentionConfig
)


def print_status_report(status: dict):
    """Print detailed status report"""
    print("\n📊 Event Store Retention Status Report")
    print("=" * 50)
    
    # File statistics
    print("\n📁 File-based Event Stores:")
    for filename, stats in status["file_stats"].items():
        if stats["exists"]:
            print(f"   {filename}:")
            print(f"     Size: {stats['size_mb']} MB")
            print(f"     Events: ~{stats['estimated_events']}")
            print(f"     Old events: {stats.get('old_events_estimate', 0)}")
            print(f"     Modified: {stats['modified']}")
        else:
            print(f"   {filename}: Not found")
    
    # Archive statistics
    print("\n📦 Archives:")
    for filename, archive_stats in status["archive_stats"].items():
        if archive_stats["archive_count"] > 0:
            print(f"   {filename}: {archive_stats['archive_count']} archives, {archive_stats['total_size_mb']} MB")
    
    # Retention policies
    print("\n⚙️ Retention Policies:")
    for filename, policy in status["retention_policies"].items():
        print(f"   {filename}:")
        print(f"     Policy: {policy['policy']}")
        print(f"     Retention: {policy['retention_days']} days")
        print(f"     Archive retention: {policy['archive_retention_days']} days")
    
    # Recommendations
    if status["recommendations"]:
        print(f"\n💡 Recommendations:")
        for rec in status["recommendations"]:
            print(f"   • {rec}")
    else:
        print(f"\n✅ No cleanup recommendations at this time")


async def status_command():
    """Show retention status"""
    status = await retention_manager.get_retention_status()
    print_status_report(status)


async def cleanup_command(dry_run: bool = False, force: bool = False):
    """Run retention cleanup"""
    if dry_run:
        print("🧪 DRY RUN MODE - No changes will be made")
        status = await retention_manager.get_retention_status()
        
        total_old_events = sum(
            stats.get('old_events_estimate', 0) 
            for stats in status["file_stats"].values() 
            if stats.get("exists", False)
        )
        
        if total_old_events == 0:
            print("✅ No events require cleanup")
            return
        
        print(f"📋 Would process ~{total_old_events} events:")
        for filename, stats in status["file_stats"].items():
            old_count = stats.get('old_events_estimate', 0)
            if old_count > 0:
                policy = status["retention_policies"][filename]["policy"]
                print(f"   • {filename}: {old_count} events ({policy})")
        
        print(f"\n💡 Run with --execute to perform cleanup")
        return
    
    if not force:
        print("⚠️ This will archive/delete old events according to retention policies.")
        confirm = input("Continue? (y/N): ").lower().strip()
        if confirm not in ['y', 'yes']:
            print("❌ Cancelled")
            return
    
    print("🔄 Running retention cleanup...")
    results = await retention_manager.apply_retention_policies()
    
    print(f"\n✅ Cleanup completed!")
    print(f"   Files processed: {len(results['processed_files'])}")
    print(f"   Events processed: {results['total_events_processed']}")
    print(f"   Events archived: {results['total_events_archived']}")
    print(f"   Events deleted: {results['total_events_deleted']}")
    
    if results['errors']:
        print(f"\n⚠️ Errors encountered:")
        for error in results['errors']:
            print(f"   - {error}")
    
    # Show detailed file results
    if results['processed_files']:
        print(f"\n📋 File processing details:")
        for file_result in results['processed_files']:
            print(f"   {file_result['filename']}:")
            print(f"     Processed: {file_result['events_processed']}")
            print(f"     Archived: {file_result['events_archived']}")
            print(f"     Deleted: {file_result['events_deleted']}")
            if file_result.get('archive_file'):
                print(f"     Archive: {file_result['archive_file']}")


async def redis_command(max_length: int = 10000):
    """Manage Redis stream retention"""
    if not redis_retention_manager.redis_client:
        print("❌ Redis not available")
        return
    
    print(f"🔄 Applying Redis retention (max length: {max_length})")
    result = await redis_retention_manager.apply_redis_retention(max_length=max_length)
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
    else:
        print(f"✅ Redis retention applied:")
        print(f"   Stream: {result['stream']}")
        print(f"   Trimmed: {result['trimmed_events']} events")
        print(f"   Current length: {result['current_length']}")


async def config_command(filename: str = None, retention_days: int = None, 
                        policy: str = None):
    """Show or modify retention configuration"""
    if not any([filename, retention_days, policy]):
        # Show current configuration
        print("\n⚙️ Current Retention Configuration:")
        for fname, config in retention_manager.retention_configs.items():
            print(f"\n   {fname}:")
            print(f"     Policy: {config.policy.value}")
            print(f"     Retention: {config.retention_days} days")
            print(f"     Archive retention: {config.archive_retention_days} days")
            print(f"     Archive location: {config.archive_location}")
            print(f"     Compress archives: {config.compress_archives}")
        return
    
    if filename and filename not in retention_manager.retention_configs:
        print(f"❌ Unknown file: {filename}")
        print(f"Available files: {list(retention_manager.retention_configs.keys())}")
        return
    
    # Modify configuration
    if filename and retention_days:
        retention_manager.retention_configs[filename].retention_days = retention_days
        print(f"✅ Set retention for {filename} to {retention_days} days")
    
    if filename and policy:
        try:
            policy_enum = RetentionPolicy(policy)
            retention_manager.retention_configs[filename].policy = policy_enum
            print(f"✅ Set policy for {filename} to {policy}")
        except ValueError:
            print(f"❌ Invalid policy: {policy}")
            print(f"Available policies: {[p.value for p in RetentionPolicy]}")


async def main():
    parser = argparse.ArgumentParser(
        description="Event Store Retention Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show current status
  python scripts/retention_cleanup.py status

  # Dry run cleanup
  python scripts/retention_cleanup.py cleanup --dry-run

  # Run cleanup
  python scripts/retention_cleanup.py cleanup --execute

  # Force cleanup without confirmation
  python scripts/retention_cleanup.py cleanup --execute --force

  # Manage Redis retention
  python scripts/retention_cleanup.py redis --max-length 5000

  # Show configuration
  python scripts/retention_cleanup.py config

  # Modify configuration
  python scripts/retention_cleanup.py config --file application_events.jsonl --retention-days 60
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show retention status')
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Run retention cleanup')
    cleanup_parser.add_argument('--dry-run', action='store_true', 
                               help='Show what would be done without making changes')
    cleanup_parser.add_argument('--execute', action='store_true',
                               help='Actually perform the cleanup')
    cleanup_parser.add_argument('--force', action='store_true',
                               help='Skip confirmation prompts')
    
    # Redis command
    redis_parser = subparsers.add_parser('redis', help='Manage Redis retention')
    redis_parser.add_argument('--max-length', type=int, default=10000,
                             help='Maximum stream length (default: 10000)')
    
    # Config command
    config_parser = subparsers.add_parser('config', help='Show/modify configuration')
    config_parser.add_argument('--file', type=str, help='Event file to configure')
    config_parser.add_argument('--retention-days', type=int, help='Retention period in days')
    config_parser.add_argument('--policy', type=str, choices=[p.value for p in RetentionPolicy],
                              help='Retention policy')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'status':
            await status_command()
        elif args.command == 'cleanup':
            if args.execute or args.dry_run:
                await cleanup_command(dry_run=args.dry_run, force=args.force)
            else:
                print("❌ Must specify --dry-run or --execute")
                cleanup_parser.print_help()
        elif args.command == 'redis':
            await redis_command(max_length=args.max_length)
        elif args.command == 'config':
            await config_command(
                filename=args.file,
                retention_days=args.retention_days,
                policy=args.policy
            )
    except KeyboardInterrupt:
        print("\n❌ Interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)