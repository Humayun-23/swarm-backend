"""
Dynamic Scheduler Agent
Generates optimized event schedules and resolves conflicts
"""
from typing import Dict, Any, List
import json
from datetime import datetime, timedelta

from app.agents.base_agent import BaseAgent
from app.orchestration.state_schema import AgentState
from app.services.schedule_service import schedule_service
from app.utils.logger import logger


class SchedulerAgent(BaseAgent):
    """Agent responsible for generating and optimizing event schedules"""
    
    def __init__(self):
        super().__init__("SchedulerAgent")
    
    async def execute(self, state: AgentState) -> AgentState:
        """
        Execute schedule generation workflow
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with schedule
        """
        self.start_execution()
        
        try:
            # Extract scheduling parameters
            sessions = await self._generate_sessions(state)
            rooms = await self._get_rooms(state)
            
            # Generate schedule
            scheduled_sessions = schedule_service.generate_schedule(
                sessions=sessions,
                rooms=rooms,
                start_time=state.get("start_date"),
                end_time=state.get("end_date"),
                constraints={
                    "buffer_minutes": 15,
                    "slot_interval_minutes": 30,
                    "prioritize_speakers": True
                }
            )
            
            # Detect conflicts
            conflicts = schedule_service.detect_conflicts(scheduled_sessions)
            
            # Auto-resolve if enabled
            if conflicts:
                logger.info(f"Detected {len(conflicts)} scheduling conflicts")
                scheduled_sessions, remaining_conflicts = schedule_service.resolve_conflicts(
                    conflicts=conflicts,
                    sessions=scheduled_sessions,
                    rooms=rooms,
                    start_time=state.get("start_date"),
                    end_time=state.get("end_date")
                )
                conflicts = remaining_conflicts
            
            # Create schedule summary
            schedule_summary = self._create_schedule_summary(scheduled_sessions)
            
            # Update state
            updated_state = self._update_state(state, {
                "scheduled_sessions": scheduled_sessions,
                "schedule": schedule_summary,
                "schedule_conflicts": conflicts,
                "rooms": rooms
            })
            
            # Save output
            updated_state = await self._save_output(
                updated_state,
                "schedule_generated",
                {
                    "total_sessions": len(scheduled_sessions),
                    "rooms_used": len(rooms),
                    "conflicts_remaining": len(conflicts),
                    "schedule_efficiency": self._calculate_efficiency(
                        scheduled_sessions,
                        state.get("start_date"),
                        state.get("end_date")
                    )
                }
            )
            
            logger.info(
                f"Generated schedule with {len(scheduled_sessions)} sessions, "
                f"{len(conflicts)} unresolved conflicts"
            )
            
        except Exception as e:
            logger.error(f"Scheduler agent execution failed: {e}")
            updated_state = self._log_error(state, str(e))
        
        finally:
            self.end_execution()
        
        return updated_state
    
    async def _generate_sessions(self, state: AgentState) -> List[Dict[str, Any]]:
        """Generate session list using LLM based on event context"""
        
        context = self._get_context(state)
        speakers = state.get("speakers", [])
        
        prompt = f"""Generate a list of sessions for this event:

{context}

Available Speakers:
{json.dumps([s.get('full_name', 'TBD') for s in speakers], indent=2)}

Create 5-10 diverse sessions including:
- Keynotes
- Technical sessions
- Workshops
- Panel discussions
- Networking sessions

Return as JSON array:
[
  {{
    "session_name": "Session title",
    "session_type": "keynote|technical|workshop|panel|networking",
    "description": "Brief description",
    "speaker": "Speaker name or TBD",
    "duration_minutes": 60,
    "max_capacity": 100,
    "is_keynote": false,
    "tags": ["tag1", "tag2"]
  }}
]
"""
        
        response = await self._invoke_llm(prompt, {})
        
        try:
            json_start = response.find("[")
            json_end = response.rfind("]") + 1
            json_str = response[json_start:json_end]
            sessions = json.loads(json_str)
            return sessions
        except json.JSONDecodeError:
            logger.warning("Failed to parse sessions JSON, using fallback")
            return self._create_fallback_sessions(state)
    
    async def _get_rooms(self, state: AgentState) -> List[str]:
        """Get or generate room list"""
        
        # Check if rooms are in state
        if state.get("rooms"):
            return state["rooms"]
        
        # Generate default rooms based on venue
        venue = state.get("venue", "Conference Center")
        
        prompt = f"""List 3-5 suitable rooms/venues for this event at {venue}.

Event Type: {state.get('event_type', 'Conference')}
Expected Participants: {state.get('participant_count', 100)}

Return as JSON array of room names:
["Room 1", "Room 2", "Room 3"]
"""
        
        response = await self._invoke_llm(prompt, {})
        
        try:
            json_start = response.find("[")
            json_end = response.rfind("]") + 1
            json_str = response[json_start:json_end]
            rooms = json.loads(json_str)
            return rooms
        except json.JSONDecodeError:
            return ["Main Hall", "Conference Room A", "Conference Room B", "Workshop Space"]
    
    def _create_schedule_summary(
        self,
        scheduled_sessions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create high-level schedule summary"""
        
        if not scheduled_sessions:
            return {}
        
        # Group sessions by day
        sessions_by_day = {}
        
        for session in scheduled_sessions:
            start_time = session["start_time"]
            day_key = start_time.strftime("%Y-%m-%d")
            
            if day_key not in sessions_by_day:
                sessions_by_day[day_key] = []
            
            sessions_by_day[day_key].append({
                "session_name": session["session_name"],
                "start_time": start_time.strftime("%H:%M"),
                "end_time": session["end_time"].strftime("%H:%M"),
                "room": session["room"],
                "speaker": session.get("speaker", "TBD")
            })
        
        return {
            "total_sessions": len(scheduled_sessions),
            "total_days": len(sessions_by_day),
            "sessions_by_day": sessions_by_day
        }
    
    def _calculate_efficiency(
        self,
        scheduled_sessions: List[Dict[str, Any]],
        start_date: datetime,
        end_date: datetime
    ) -> float:
        """Calculate schedule efficiency percentage"""
        
        if not scheduled_sessions:
            return 0.0
        
        # Calculate total scheduled time
        total_scheduled_minutes = sum(
            session.get("duration_minutes", 60)
            for session in scheduled_sessions
        )
        
        # Calculate total available time
        total_available_minutes = (end_date - start_date).total_seconds() / 60
        
        # Efficiency = scheduled time / available time
        efficiency = (total_scheduled_minutes / total_available_minutes) * 100
        
        return min(efficiency, 100.0)  # Cap at 100%
    
    def _create_fallback_sessions(self, state: AgentState) -> List[Dict[str, Any]]:
        """Create fallback sessions if LLM fails"""
        
        return [
            {
                "session_name": "Opening Keynote",
                "session_type": "keynote",
                "description": "Event kickoff and introduction",
                "speaker": "TBD",
                "duration_minutes": 60,
                "max_capacity": 200,
                "is_keynote": True,
                "tags": ["keynote", "opening"]
            },
            {
                "session_name": "Technical Workshop",
                "session_type": "workshop",
                "description": "Hands-on technical session",
                "speaker": "TBD",
                "duration_minutes": 90,
                "max_capacity": 50,
                "is_keynote": False,
                "tags": ["workshop", "technical"]
            },
            {
                "session_name": "Panel Discussion",
                "session_type": "panel",
                "description": "Expert panel discussion",
                "speaker": "Multiple Speakers",
                "duration_minutes": 60,
                "max_capacity": 150,
                "is_keynote": False,
                "tags": ["panel", "discussion"]
            },
            {
                "session_name": "Networking Break",
                "session_type": "networking",
                "description": "Networking and refreshments",
                "speaker": "N/A",
                "duration_minutes": 30,
                "max_capacity": 200,
                "is_keynote": False,
                "tags": ["networking", "break"]
            }
        ]


# Create singleton instance
scheduler_agent = SchedulerAgent()