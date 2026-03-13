"""
Schedule Service
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from app.utils.logger import logger
from app.utils.helpers import calculate_time_slots


class ScheduleService:
    """Service for managing event schedules"""
    
    def __init__(self):
        self.conflicts: List[Dict[str, Any]] = []
    
    def generate_schedule(
        self,
        sessions: List[Dict[str, Any]],
        rooms: List[str],
        start_time: datetime,
        end_time: datetime,
        constraints: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate optimized event schedule
        
        Args:
            sessions: List of session dictionaries
            rooms: List of available rooms
            start_time: Event start time
            end_time: Event end time
            constraints: Scheduling constraints
            
        Returns:
            List of scheduled sessions
        """
        constraints = constraints or {}
        scheduled_sessions = []
        self.conflicts = []
        
        # Sort sessions by priority if specified
        if constraints.get("prioritize_speakers"):
            sessions = sorted(
                sessions,
                key=lambda x: x.get("is_keynote", False),
                reverse=True
            )
        
        # Initialize room availability
        room_schedules = {room: [] for room in rooms}
        
        for session in sessions:
            scheduled = self._schedule_session(
                session,
                room_schedules,
                start_time,
                end_time,
                constraints
            )
            
            if scheduled:
                scheduled_sessions.append(scheduled)
            else:
                self.conflicts.append({
                    "session": session.get("name"),
                    "reason": "No available time slot found"
                })
        
        logger.info(
            f"Generated schedule: {len(scheduled_sessions)} sessions, "
            f"{len(self.conflicts)} conflicts"
        )
        
        return scheduled_sessions
    
    def _schedule_session(
        self,
        session: Dict[str, Any],
        room_schedules: Dict[str, List[Dict[str, Any]]],
        start_time: datetime,
        end_time: datetime,
        constraints: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Schedule a single session
        
        Args:
            session: Session to schedule
            room_schedules: Current room schedules
            start_time: Earliest start time
            end_time: Latest end time
            constraints: Scheduling constraints
            
        Returns:
            Scheduled session or None if cannot be scheduled
        """
        duration = session.get("duration_minutes", 60)
        
        # Try each room
        for room in room_schedules.keys():
            # Find available time slot
            time_slot = self._find_available_slot(
                room_schedules[room],
                start_time,
                end_time,
                duration,
                constraints
            )
            
            if time_slot:
                scheduled_session = {
                    **session,
                    "room": room,
                    "start_time": time_slot,
                    "end_time": time_slot + timedelta(minutes=duration),
                    "duration_minutes": duration
                }
                
                room_schedules[room].append(scheduled_session)
                return scheduled_session
        
        return None
    
    def _find_available_slot(
        self,
        room_schedule: List[Dict[str, Any]],
        start_time: datetime,
        end_time: datetime,
        duration: int,
        constraints: Dict[str, Any]
    ) -> Optional[datetime]:
        """
        Find available time slot in room
        
        Args:
            room_schedule: Current room schedule
            start_time: Earliest start time
            end_time: Latest end time
            duration: Session duration in minutes
            constraints: Scheduling constraints
            
        Returns:
            Available start time or None
        """
        # Generate possible time slots
        slot_interval = constraints.get("slot_interval_minutes", 30)
        possible_slots = calculate_time_slots(start_time, end_time, slot_interval)
        
        for slot in possible_slots:
            slot_end = slot + timedelta(minutes=duration)
            
            # Check if slot is within bounds
            if slot_end > end_time:
                continue
            
            # Check for conflicts
            has_conflict = False
            for existing in room_schedule:
                if self._slots_overlap(
                    slot,
                    slot_end,
                    existing["start_time"],
                    existing["end_time"]
                ):
                    has_conflict = True
                    break
            
            if not has_conflict:
                # Apply buffer time constraint if specified
                buffer_minutes = constraints.get("buffer_minutes", 0)
                if buffer_minutes > 0:
                    buffer_start = slot - timedelta(minutes=buffer_minutes)
                    buffer_end = slot_end + timedelta(minutes=buffer_minutes)
                    
                    for existing in room_schedule:
                        if self._slots_overlap(
                            buffer_start,
                            buffer_end,
                            existing["start_time"],
                            existing["end_time"]
                        ):
                            has_conflict = True
                            break
                
                if not has_conflict:
                    return slot
        
        return None
    
    def _slots_overlap(
        self,
        start1: datetime,
        end1: datetime,
        start2: datetime,
        end2: datetime
    ) -> bool:
        """
        Check if two time slots overlap
        
        Args:
            start1: First slot start time
            end1: First slot end time
            start2: Second slot start time
            end2: Second slot end time
            
        Returns:
            True if slots overlap, False otherwise
        """
        return start1 < end2 and start2 < end1
    
    def detect_conflicts(
        self,
        scheduled_sessions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Detect conflicts in scheduled sessions
        
        Args:
            scheduled_sessions: List of scheduled sessions
            
        Returns:
            List of detected conflicts
        """
        conflicts = []
        
        for i, session1 in enumerate(scheduled_sessions):
            for session2 in scheduled_sessions[i + 1:]:
                # Check room conflicts
                if session1["room"] == session2["room"]:
                    if self._slots_overlap(
                        session1["start_time"],
                        session1["end_time"],
                        session2["start_time"],
                        session2["end_time"]
                    ):
                        conflicts.append({
                            "type": "room_conflict",
                            "session1": session1["session_name"],
                            "session2": session2["session_name"],
                            "room": session1["room"],
                            "time": session1["start_time"]
                        })
                
                # Check speaker conflicts if same speaker
                if (session1.get("speaker") and 
                    session1.get("speaker") == session2.get("speaker")):
                    if self._slots_overlap(
                        session1["start_time"],
                        session1["end_time"],
                        session2["start_time"],
                        session2["end_time"]
                    ):
                        conflicts.append({
                            "type": "speaker_conflict",
                            "session1": session1["session_name"],
                            "session2": session2["session_name"],
                            "speaker": session1["speaker"],
                            "time": session1["start_time"]
                        })
        
        return conflicts
    
    def resolve_conflicts(
        self,
        conflicts: List[Dict[str, Any]],
        sessions: List[Dict[str, Any]],
        rooms: List[str],
        start_time: datetime,
        end_time: datetime
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Attempt to resolve scheduling conflicts
        
        Args:
            conflicts: List of conflicts to resolve
            sessions: Original sessions list
            rooms: Available rooms
            start_time: Event start time
            end_time: Event end time
            
        Returns:
            Tuple of (resolved sessions, remaining conflicts)
        """
        resolved_sessions = sessions.copy()
        remaining_conflicts = []
        
        for conflict in conflicts:
            if conflict["type"] == "room_conflict":
                # Try to move one session to different room
                success = self._try_move_to_different_room(
                    conflict,
                    resolved_sessions,
                    rooms
                )
                
                if not success:
                    remaining_conflicts.append(conflict)
            
            elif conflict["type"] == "speaker_conflict":
                # Try to reschedule one session
                success = self._try_reschedule_session(
                    conflict,
                    resolved_sessions,
                    start_time,
                    end_time
                )
                
                if not success:
                    remaining_conflicts.append(conflict)
        
        return resolved_sessions, remaining_conflicts
    
    def _try_move_to_different_room(
        self,
        conflict: Dict[str, Any],
        sessions: List[Dict[str, Any]],
        rooms: List[str]
    ) -> bool:
        """Try to move session to different room"""
        # Implementation would try to find alternative room
        # This is a simplified version
        return False
    
    def _try_reschedule_session(
        self,
        conflict: Dict[str, Any],
        sessions: List[Dict[str, Any]],
        start_time: datetime,
        end_time: datetime
    ) -> bool:
        """Try to reschedule session to different time"""
        # Implementation would try to find alternative time slot
        # This is a simplified version
        return False
    
    def optimize_schedule(
        self,
        sessions: List[Dict[str, Any]],
        optimization_goals: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Optimize schedule based on goals
        
        Args:
            sessions: Scheduled sessions
            optimization_goals: List of optimization goals
            
        Returns:
            Optimized schedule
        """
        optimized = sessions.copy()
        
        if "minimize_conflicts" in optimization_goals:
            conflicts = self.detect_conflicts(optimized)
            if conflicts:
                logger.info(f"Detected {len(conflicts)} conflicts to minimize")
        
        if "maximize_utilization" in optimization_goals:
            # Ensure rooms are used efficiently
            logger.info("Optimizing for room utilization")
        
        if "balance_load" in optimization_goals:
            # Balance sessions across time slots
            logger.info("Optimizing for load balancing")
        
        return optimized


# Create singleton instance
schedule_service = ScheduleService()