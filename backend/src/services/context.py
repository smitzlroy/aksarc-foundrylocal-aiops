"""
Context buffer for storing cluster state history.

This module provides a circular buffer for storing cluster status snapshots
with time-based retention and efficient querying.
"""

from collections import deque
from datetime import datetime, timedelta, timezone
from typing import Optional

import structlog

from src.models.cluster import ClusterStatus, Event, PodStatus

logger = structlog.get_logger(__name__)


class ContextBuffer:
    """Circular buffer for cluster state with time-based retention."""

    def __init__(self, retention_hours: int = 24, max_snapshots: int = 1000):
        """Initialize context buffer.
        
        Args:
            retention_hours: Hours to retain data (default: 24)
            max_snapshots: Maximum number of snapshots to store (default: 1000)
        """
        self.retention_hours = retention_hours
        self.max_snapshots = max_snapshots
        self._snapshots: deque[ClusterStatus] = deque(maxlen=max_snapshots)
        
        logger.info(
            "context_buffer_initialized",
            retention_hours=retention_hours,
            max_snapshots=max_snapshots,
        )

    def add(self, status: ClusterStatus) -> None:
        """Add a cluster status snapshot to the buffer.
        
        Args:
            status: ClusterStatus snapshot to add
        """
        # Automatically prune old data before adding
        self._prune_old_data()
        
        self._snapshots.append(status)
        
        logger.debug(
            "snapshot_added",
            timestamp=status.timestamp,
            pod_count=len(status.pods),
            event_count=len(status.events),
            buffer_size=len(self._snapshots),
        )

    def get_recent(self, hours: Optional[int] = None) -> list[ClusterStatus]:
        """Get recent snapshots within specified hours.
        
        Args:
            hours: Number of hours to look back (default: retention_hours)
            
        Returns:
            List of ClusterStatus snapshots in chronological order
        """
        hours = hours or self.retention_hours
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        recent = [s for s in self._snapshots if s.timestamp >= cutoff]
        
        logger.debug(
            "retrieved_recent_snapshots",
            hours=hours,
            snapshot_count=len(recent),
        )
        
        return recent

    def get_range(
        self,
        start: datetime,
        end: Optional[datetime] = None,
    ) -> list[ClusterStatus]:
        """Get snapshots within a specific time range.
        
        Args:
            start: Start timestamp
            end: End timestamp (default: now)
            
        Returns:
            List of ClusterStatus snapshots in chronological order
        """
        end = end or datetime.now(timezone.utc)
        
        in_range = [
            s for s in self._snapshots
            if start <= s.timestamp <= end
        ]
        
        logger.debug(
            "retrieved_range_snapshots",
            start=start,
            end=end,
            snapshot_count=len(in_range),
        )
        
        return in_range

    def get_latest(self) -> Optional[ClusterStatus]:
        """Get the most recent snapshot.
        
        Returns:
            Latest ClusterStatus or None if buffer is empty
        """
        if not self._snapshots:
            return None
        return self._snapshots[-1]

    def get_pod_history(
        self,
        pod_name: str,
        namespace: str,
        hours: int = 1,
    ) -> list[PodStatus]:
        """Get history of a specific pod.
        
        Args:
            pod_name: Name of the pod
            namespace: Namespace of the pod
            hours: Hours to look back
            
        Returns:
            List of PodStatus snapshots for the specified pod
        """
        recent_snapshots = self.get_recent(hours)
        
        pod_history = []
        for snapshot in recent_snapshots:
            for pod in snapshot.pods:
                if pod.name == pod_name and pod.namespace == namespace:
                    pod_history.append(pod)
                    break
        
        logger.debug(
            "retrieved_pod_history",
            pod=pod_name,
            namespace=namespace,
            history_count=len(pod_history),
        )
        
        return pod_history

    def get_events_by_type(
        self,
        event_type: str,
        hours: Optional[int] = None,
    ) -> list[Event]:
        """Get events of a specific type.
        
        Args:
            event_type: Event type (e.g., "Warning", "Normal")
            hours: Hours to look back (default: retention_hours)
            
        Returns:
            List of matching events
        """
        recent_snapshots = self.get_recent(hours)
        
        events = []
        for snapshot in recent_snapshots:
            events.extend(
                event for event in snapshot.events
                if event.type == event_type
            )
        
        # Deduplicate by name and sort by timestamp descending
        seen = set()
        unique_events = []
        for event in sorted(events, key=lambda e: e.timestamp, reverse=True):
            if event.name not in seen:
                seen.add(event.name)
                unique_events.append(event)
        
        logger.debug(
            "retrieved_events_by_type",
            event_type=event_type,
            event_count=len(unique_events),
        )
        
        return unique_events

    def get_events_for_object(
        self,
        involved_object: str,
        hours: Optional[int] = None,
    ) -> list[Event]:
        """Get events related to a specific object.
        
        Args:
            involved_object: Object identifier (e.g., "Pod/my-pod")
            hours: Hours to look back (default: retention_hours)
            
        Returns:
            List of matching events
        """
        recent_snapshots = self.get_recent(hours)
        
        events = []
        for snapshot in recent_snapshots:
            events.extend(
                event for event in snapshot.events
                if involved_object in event.involved_object
            )
        
        # Sort by timestamp descending
        events.sort(key=lambda e: e.timestamp, reverse=True)
        
        logger.debug(
            "retrieved_events_for_object",
            involved_object=involved_object,
            event_count=len(events),
        )
        
        return events

    def get_statistics(self) -> dict:
        """Get buffer statistics.
        
        Returns:
            Dictionary with buffer statistics
        """
        if not self._snapshots:
            return {
                "snapshot_count": 0,
                "oldest_timestamp": None,
                "newest_timestamp": None,
                "total_pods_tracked": 0,
                "total_events_tracked": 0,
            }
        
        oldest = self._snapshots[0]
        newest = self._snapshots[-1]
        
        total_pods = sum(len(s.pods) for s in self._snapshots)
        total_events = sum(len(s.events) for s in self._snapshots)
        
        return {
            "snapshot_count": len(self._snapshots),
            "oldest_timestamp": oldest.timestamp,
            "newest_timestamp": newest.timestamp,
            "total_pods_tracked": total_pods,
            "total_events_tracked": total_events,
        }

    def clear(self) -> None:
        """Clear all data from the buffer."""
        self._snapshots.clear()
        logger.info("context_buffer_cleared")

    def _prune_old_data(self) -> None:
        """Remove snapshots older than retention period."""
        if not self._snapshots:
            return
        
        cutoff = datetime.now(timezone.utc) - timedelta(hours=self.retention_hours)
        
        # Remove from left (oldest) until we hit something recent
        removed_count = 0
        while self._snapshots and self._snapshots[0].timestamp < cutoff:
            self._snapshots.popleft()
            removed_count += 1
        
        if removed_count > 0:
            logger.debug(
                "pruned_old_snapshots",
                removed_count=removed_count,
                remaining_count=len(self._snapshots),
            )
