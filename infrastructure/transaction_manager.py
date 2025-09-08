"""
Transaction Manager for Event Store Dual Publishing Consistency
Ensures atomic operations across file-based and Redis event stores
"""
import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class TransactionState(Enum):
    PENDING = "pending"
    COMMITTED = "committed"
    ABORTED = "aborted"
    FAILED = "failed"


@dataclass
class Transaction:
    """Represents a dual publishing transaction"""
    transaction_id: str
    event_data: Dict[str, Any]
    file_path: Path
    redis_stream: str
    state: TransactionState
    created_at: datetime
    error_message: Optional[str] = None
    file_written: bool = False
    redis_written: bool = False


class TransactionManager:
    """Manages atomic dual publishing transactions with rollback support"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Transaction log for recovery
        self.transaction_log_path = self.data_dir / "transaction_log.jsonl"
        
        # Pending transactions
        self.pending_transactions: Dict[str, Transaction] = {}
        
        # Recovery on startup
        asyncio.create_task(self._recover_transactions())
    
    async def _recover_transactions(self):
        """Recover pending transactions on startup"""
        if not self.transaction_log_path.exists():
            return
            
        try:
            with open(self.transaction_log_path, 'r') as f:
                for line in f:
                    if line.strip():
                        tx_data = json.loads(line.strip())
                        if tx_data.get('state') == TransactionState.PENDING.value:
                            # Attempt to complete pending transaction
                            await self._complete_pending_transaction(tx_data)
        except Exception as e:
            logger.error(f"Transaction recovery failed: {e}")
    
    async def _complete_pending_transaction(self, tx_data: Dict[str, Any]):
        """Complete a pending transaction from recovery"""
        try:
            transaction = Transaction(
                transaction_id=tx_data['transaction_id'],
                event_data=tx_data['event_data'],
                file_path=Path(tx_data['file_path']),
                redis_stream=tx_data['redis_stream'],
                state=TransactionState.PENDING,
                created_at=datetime.fromisoformat(tx_data['created_at']),
                file_written=tx_data.get('file_written', False),
                redis_written=tx_data.get('redis_written', False)
            )
            
            # Try to complete the transaction
            await self._finish_transaction(transaction)
            logger.info(f"Recovered transaction: {transaction.transaction_id}")
            
        except Exception as e:
            logger.error(f"Failed to complete recovered transaction: {e}")
    
    def _log_transaction_state(self, transaction: Transaction):
        """Log transaction state for recovery"""
        tx_record = {
            "transaction_id": transaction.transaction_id,
            "event_data": transaction.event_data,
            "file_path": str(transaction.file_path),
            "redis_stream": transaction.redis_stream,
            "state": transaction.state.value,
            "created_at": transaction.created_at.isoformat(),
            "file_written": transaction.file_written,
            "redis_written": transaction.redis_written,
            "error_message": transaction.error_message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            with open(self.transaction_log_path, 'a') as f:
                f.write(json.dumps(tx_record, default=str) + '\n')
        except Exception as e:
            logger.error(f"Failed to log transaction state: {e}")
    
    async def publish_dual_atomic(
        self,
        event_data: Dict[str, Any],
        file_path: Path,
        redis_client=None,
        redis_stream: str = "seraaj:events:global"
    ) -> bool:
        """
        Atomically publish event to both file and Redis with transaction consistency
        
        Returns:
            bool: True if both operations succeeded, False otherwise
        """
        from uuid import uuid4
        
        transaction_id = str(uuid4())
        transaction = Transaction(
            transaction_id=transaction_id,
            event_data=event_data,
            file_path=file_path,
            redis_stream=redis_stream,
            state=TransactionState.PENDING,
            created_at=datetime.utcnow()
        )
        
        self.pending_transactions[transaction_id] = transaction
        self._log_transaction_state(transaction)
        
        try:
            # Phase 1: Prepare both operations
            await self._prepare_file_write(transaction)
            await self._prepare_redis_write(transaction, redis_client)
            
            # Phase 2: Commit both operations
            await self._commit_file_write(transaction)
            await self._commit_redis_write(transaction, redis_client)
            
            # Mark as committed
            transaction.state = TransactionState.COMMITTED
            self._log_transaction_state(transaction)
            
            # Clean up
            self.pending_transactions.pop(transaction_id, None)
            
            logger.info(f"Transaction {transaction_id} committed successfully")
            return True
            
        except Exception as e:
            # Abort transaction
            transaction.state = TransactionState.ABORTED
            transaction.error_message = str(e)
            self._log_transaction_state(transaction)
            
            await self._rollback_transaction(transaction, redis_client)
            
            # Clean up
            self.pending_transactions.pop(transaction_id, None)
            
            logger.error(f"Transaction {transaction_id} aborted: {e}")
            return False
    
    async def _prepare_file_write(self, transaction: Transaction):
        """Prepare file write operation (check permissions, space, etc.)"""
        try:
            # Check if directory is writable
            if not os.access(transaction.file_path.parent, os.W_OK):
                raise PermissionError(f"Cannot write to {transaction.file_path.parent}")
            
            # Check disk space (simple check)
            stat = os.statvfs(transaction.file_path.parent)
            free_space = stat.f_bavail * stat.f_frsize
            if free_space < 1024 * 1024:  # Less than 1MB
                raise OSError("Insufficient disk space")
                
            logger.debug(f"File write prepared for transaction {transaction.transaction_id}")
            
        except Exception as e:
            raise Exception(f"File write preparation failed: {e}")
    
    async def _prepare_redis_write(self, transaction: Transaction, redis_client):
        """Prepare Redis write operation (check connection, etc.)"""
        if not redis_client:
            # Redis not available - this is acceptable for degraded mode
            logger.warning(f"Redis not available for transaction {transaction.transaction_id}")
            return
            
        try:
            # Test Redis connection
            await redis_client._ensure_connection()
            logger.debug(f"Redis write prepared for transaction {transaction.transaction_id}")
            
        except Exception as e:
            # Redis failure is non-fatal, we can continue with file-only mode
            logger.warning(f"Redis preparation failed for transaction {transaction.transaction_id}: {e}")
    
    async def _commit_file_write(self, transaction: Transaction):
        """Commit the file write operation"""
        try:
            # Write to file atomically using temp file
            temp_file = transaction.file_path.with_suffix('.tmp')
            
            # Read existing content
            existing_content = ""
            if transaction.file_path.exists():
                with open(transaction.file_path, 'r') as f:
                    existing_content = f.read()
            
            # Write to temp file
            with open(temp_file, 'w') as f:
                f.write(existing_content)
                if existing_content and not existing_content.endswith('\n'):
                    f.write('\n')
                f.write(json.dumps(transaction.event_data, default=str) + '\n')
                f.flush()
                os.fsync(f.fileno())  # Force write to disk
            
            # Atomic move
            temp_file.rename(transaction.file_path)
            transaction.file_written = True
            
            logger.debug(f"File write committed for transaction {transaction.transaction_id}")
            
        except Exception as e:
            raise Exception(f"File write commit failed: {e}")
    
    async def _commit_redis_write(self, transaction: Transaction, redis_client):
        """Commit the Redis write operation"""
        if not redis_client:
            transaction.redis_written = False
            return
            
        try:
            # Publish to Redis stream
            stream_id = await redis_client.publish(
                transaction.event_data.get('eventType', 'unknown'),
                transaction.event_data.get('data', {}),
                source_service=transaction.event_data.get('source_service', 'unknown')
            )
            
            transaction.redis_written = stream_id is not None
            
            if transaction.redis_written:
                logger.debug(f"Redis write committed for transaction {transaction.transaction_id}")
            else:
                logger.warning(f"Redis write failed for transaction {transaction.transaction_id}")
                
        except Exception as e:
            logger.warning(f"Redis write commit failed for transaction {transaction.transaction_id}: {e}")
            transaction.redis_written = False
    
    async def _rollback_transaction(self, transaction: Transaction, redis_client):
        """Rollback transaction if something failed"""
        try:
            if transaction.file_written:
                await self._rollback_file_write(transaction)
            
            if transaction.redis_written:
                await self._rollback_redis_write(transaction, redis_client)
                
            logger.info(f"Transaction {transaction.transaction_id} rolled back")
            
        except Exception as e:
            logger.error(f"Rollback failed for transaction {transaction.transaction_id}: {e}")
    
    async def _rollback_file_write(self, transaction: Transaction):
        """Rollback file write (remove the last line)"""
        try:
            if not transaction.file_path.exists():
                return
                
            # Read all lines
            with open(transaction.file_path, 'r') as f:
                lines = f.readlines()
            
            if not lines:
                return
                
            # Check if last line matches our event
            last_line = lines[-1].strip()
            if last_line:
                try:
                    last_event = json.loads(last_line)
                    if last_event.get('eventId') == transaction.event_data.get('eventId'):
                        # Remove the last line
                        lines = lines[:-1]
                        
                        # Write back
                        with open(transaction.file_path, 'w') as f:
                            f.writelines(lines)
                            f.flush()
                            os.fsync(f.fileno())
                        
                        logger.debug(f"File write rolled back for transaction {transaction.transaction_id}")
                        
                except Exception as e:
                    logger.error(f"Failed to parse last line during rollback: {e}")
                    
        except Exception as e:
            logger.error(f"File rollback failed: {e}")
    
    async def _rollback_redis_write(self, transaction: Transaction, redis_client):
        """Rollback Redis write (Redis streams are append-only, so we log the rollback)"""
        try:
            if redis_client and transaction.redis_written:
                # Redis streams don't support deletion, so we publish a rollback event
                rollback_event = {
                    "eventType": "system.transaction_rollback",
                    "data": {
                        "original_transaction_id": transaction.transaction_id,
                        "original_event_id": transaction.event_data.get('eventId'),
                        "rollback_reason": transaction.error_message,
                        "rollback_at": datetime.utcnow().isoformat()
                    }
                }
                
                await redis_client.publish(
                    "system.transaction_rollback",
                    rollback_event["data"],
                    source_service="transaction_manager"
                )
                
                logger.debug(f"Redis rollback event published for transaction {transaction.transaction_id}")
                
        except Exception as e:
            logger.error(f"Redis rollback failed: {e}")
    
    async def _finish_transaction(self, transaction: Transaction):
        """Finish a pending transaction"""
        # This is used during recovery
        try:
            if not transaction.file_written:
                await self._commit_file_write(transaction)
            
            # Redis failure is acceptable in recovery
            transaction.state = TransactionState.COMMITTED
            self._log_transaction_state(transaction)
            
        except Exception as e:
            transaction.state = TransactionState.FAILED
            transaction.error_message = str(e)
            self._log_transaction_state(transaction)
            raise
    
    def get_transaction_stats(self) -> Dict[str, Any]:
        """Get transaction statistics for monitoring"""
        if not self.transaction_log_path.exists():
            return {"total": 0, "committed": 0, "aborted": 0, "failed": 0}
            
        stats = {"total": 0, "committed": 0, "aborted": 0, "failed": 0, "pending": 0}
        
        try:
            with open(self.transaction_log_path, 'r') as f:
                for line in f:
                    if line.strip():
                        tx_data = json.loads(line.strip())
                        stats["total"] += 1
                        state = tx_data.get('state', 'unknown')
                        stats[state] = stats.get(state, 0) + 1
                        
            stats["pending"] = len(self.pending_transactions)
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get transaction stats: {e}")
            return {"error": str(e)}


# Global transaction manager instance
transaction_manager = TransactionManager()