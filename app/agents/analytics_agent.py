"""
Analytics Agent
Analyzes engagement data and generates insights
"""
from typing import Dict, Any, List
import json
from datetime import datetime

from app.agents.base_agent import BaseAgent
from app.orchestration.state_schema import AgentState
from app.utils.logger import logger


class AnalyticsAgent(BaseAgent):
    """Agent responsible for analyzing engagement and generating insights"""
    
    def __init__(self):
        super().__init__("AnalyticsAgent")
    
    async def execute(self, state: AgentState) -> AgentState:
        """
        Execute analytics workflow
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with analytics and insights
        """
        self.start_execution()
        
        try:
            # Analyze participant demographics
            demographics = self._analyze_demographics(state)
            
            # Analyze schedule metrics
            schedule_metrics = self._analyze_schedule(state)
            
            # Analyze marketing performance (simulated for now)
            marketing_metrics = self._analyze_marketing(state)
            
            # Generate insights using LLM
            insights = await self._generate_insights(
                state,
                demographics,
                schedule_metrics,
                marketing_metrics
            )
            
            # Generate recommendations
            recommendations = await self._generate_recommendations(
                state,
                insights
            )
            
            # Compile analytics report
            analytics_report = {
                "demographics": demographics,
                "schedule_metrics": schedule_metrics,
                "marketing_metrics": marketing_metrics,
                "generated_at": datetime.utcnow().isoformat()
            }
            
            # Update state
            updated_state = self._update_state(state, {
                "analytics": analytics_report,
                "insights": insights,
                "recommendations": recommendations,
                "engagement_metrics": {
                    "participant_engagement_score": self._calculate_engagement_score(state),
                    "schedule_utilization": schedule_metrics.get("utilization_rate", 0),
                    "marketing_reach": marketing_metrics.get("estimated_reach", 0)
                }
            })
            
            # Save output
            updated_state = await self._save_output(
                updated_state,
                "analytics_generated",
                {
                    "insights_count": len(insights),
                    "recommendations_count": len(recommendations),
                    "metrics_analyzed": list(analytics_report.keys())
                }
            )
            
            logger.info(
                f"Generated {len(insights)} insights and "
                f"{len(recommendations)} recommendations"
            )
            
        except Exception as e:
            logger.error(f"Analytics agent execution failed: {e}")
            updated_state = self._log_error(state, str(e))
        
        finally:
            self.end_execution()
        
        return updated_state
    
    def _analyze_demographics(self, state: AgentState) -> Dict[str, Any]:
        """Analyze participant demographics"""
        
        participants = state.get("participants", [])
        
        if not participants:
            return {
                "total_participants": 0,
                "speakers_count": 0,
                "sponsors_count": 0,
                "organizations": []
            }
        
        # Count categories
        speakers = [p for p in participants if p.get("is_speaker")]
        sponsors = [p for p in participants if p.get("is_sponsor")]
        
        # Extract organizations
        organizations = {}
        for p in participants:
            org = p.get("organization", "Independent")
            organizations[org] = organizations.get(org, 0) + 1
        
        # Extract roles
        roles = {}
        for p in participants:
            role = p.get("role", "Attendee")
            roles[role] = roles.get(role, 0) + 1
        
        return {
            "total_participants": len(participants),
            "speakers_count": len(speakers),
            "sponsors_count": len(sponsors),
            "general_attendees": len(participants) - len(speakers) - len(sponsors),
            "organizations": dict(sorted(
                organizations.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]),  # Top 10 organizations
            "roles": dict(sorted(
                roles.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10])  # Top 10 roles
        }
    
    def _analyze_schedule(self, state: AgentState) -> Dict[str, Any]:
        """Analyze schedule metrics"""
        
        scheduled_sessions = state.get("scheduled_sessions", [])
        
        if not scheduled_sessions:
            return {
                "total_sessions": 0,
                "session_types": {},
                "utilization_rate": 0
            }
        
        # Count session types
        session_types = {}
        total_duration = 0
        
        for session in scheduled_sessions:
            session_type = session.get("session_type", "other")
            session_types[session_type] = session_types.get(session_type, 0) + 1
            total_duration += session.get("duration_minutes", 60)
        
        # Calculate utilization
        start_date = state.get("start_date")
        end_date = state.get("end_date")
        
        if start_date and end_date:
            total_available_minutes = (end_date - start_date).total_seconds() / 60
            utilization_rate = (total_duration / total_available_minutes) * 100 if total_available_minutes > 0 else 0
        else:
            utilization_rate = 0
        
        return {
            "total_sessions": len(scheduled_sessions),
            "session_types": session_types,
            "total_duration_minutes": total_duration,
            "average_session_duration": total_duration / len(scheduled_sessions) if scheduled_sessions else 0,
            "utilization_rate": round(utilization_rate, 2),
            "conflicts": len(state.get("schedule_conflicts", []))
        }
    
    def _analyze_marketing(self, state: AgentState) -> Dict[str, Any]:
        """Analyze marketing metrics"""
        
        marketing_posts = state.get("marketing_posts", [])
        
        # Count by platform
        platform_distribution = {}
        for post in marketing_posts:
            platform = post.get("platform", "unknown")
            platform_distribution[platform] = platform_distribution.get(platform, 0) + 1
        
        # Simulate engagement metrics (in real scenario, would fetch from APIs)
        estimated_reach = len(marketing_posts) * 500  # Rough estimate
        
        return {
            "total_posts": len(marketing_posts),
            "platform_distribution": platform_distribution,
            "estimated_reach": estimated_reach,
            "campaigns_created": len(state.get("marketing_timeline", []))
        }
    
    async def _generate_insights(
        self,
        state: AgentState,
        demographics: Dict[str, Any],
        schedule_metrics: Dict[str, Any],
        marketing_metrics: Dict[str, Any]
    ) -> List[str]:
        """Generate insights using LLM"""
        
        context = self._get_context(state)
        
        prompt = f"""Analyze this event data and generate 5-7 key insights:

Event Context:
{context}

Demographics:
{json.dumps(demographics, indent=2)}

Schedule Metrics:
{json.dumps(schedule_metrics, indent=2)}

Marketing Metrics:
{json.dumps(marketing_metrics, indent=2)}

Provide actionable insights about:
- Participant engagement and diversity
- Schedule optimization
- Marketing effectiveness
- Potential improvements

Return as JSON array of insight strings:
["Insight 1", "Insight 2", ...]
"""
        
        response = await self._invoke_llm(prompt, {})
        
        try:
            json_start = response.find("[")
            json_end = response.rfind("]") + 1
            json_str = response[json_start:json_end]
            insights = json.loads(json_str)
            return insights
        except json.JSONDecodeError:
            return [
                f"Total of {demographics.get('total_participants', 0)} participants registered",
                f"Schedule utilization rate: {schedule_metrics.get('utilization_rate', 0)}%",
                f"Marketing reach estimated at {marketing_metrics.get('estimated_reach', 0)} people",
                f"{demographics.get('speakers_count', 0)} speakers confirmed for the event"
            ]
    
    async def _generate_recommendations(
        self,
        state: AgentState,
        insights: List[str]
    ) -> List[str]:
        """Generate recommendations based on insights"""
        
        context = self._get_context(state)
        
        prompt = f"""Based on these insights, provide 5 specific recommendations to improve the event:

Event Context:
{context}

Insights:
{json.dumps(insights, indent=2)}

Provide actionable recommendations for:
- Participant engagement
- Schedule improvements
- Marketing strategies
- Logistics optimization

Return as JSON array of recommendation strings:
["Recommendation 1", "Recommendation 2", ...]
"""
        
        response = await self._invoke_llm(prompt, {})
        
        try:
            json_start = response.find("[")
            json_end = response.rfind("]") + 1
            json_str = response[json_start:json_end]
            recommendations = json.loads(json_str)
            return recommendations
        except json.JSONDecodeError:
            return [
                "Increase social media promotion to reach more attendees",
                "Add more networking sessions to improve participant interaction",
                "Consider adding buffer time between sessions",
                "Send follow-up emails to participants who haven't confirmed"
            ]
    
    def _calculate_engagement_score(self, state: AgentState) -> float:
        """Calculate overall engagement score (0-100)"""
        
        score = 0.0
        max_score = 100.0
        
        # Participant registration (30 points)
        participant_count = state.get("participant_count", 0)
        max_participants = state.get("metadata", {}).get("expected_participants", 100)
        if max_participants > 0:
            score += min(30, (participant_count / max_participants) * 30)
        
        # Marketing activity (25 points)
        marketing_posts = len(state.get("marketing_posts", []))
        score += min(25, (marketing_posts / 10) * 25)
        
        # Schedule completeness (25 points)
        scheduled_sessions = len(state.get("scheduled_sessions", []))
        score += min(25, (scheduled_sessions / 10) * 25)
        
        # Email communication (20 points)
        emails_sent = len(state.get("emails_sent", []))
        if participant_count > 0:
            score += min(20, (emails_sent / participant_count) * 20)
        
        return round(min(score, max_score), 2)


# Create singleton instance
analytics_agent = AnalyticsAgent()