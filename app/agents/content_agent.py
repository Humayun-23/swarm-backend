"""
Content Strategist Agent
Generates promotional content and marketing plans
"""
from typing import Dict, Any, List
import json
from app.agents.base_agent import BaseAgent
from app.orchestration.state_schema import AgentState
from app.memory.vector_store import vector_store
from app.utils.logger import logger


class ContentStrategistAgent(BaseAgent):
    """Agent responsible for generating marketing content and plans"""
    
    def __init__(self):
        super().__init__("ContentStrategistAgent")
        self.platforms = ["twitter", "linkedin", "facebook", "instagram"]
    
    async def execute(self, state: AgentState) -> AgentState:
        """
        Execute content generation workflow
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with marketing content
        """
        self.start_execution()
        
        try:
            # Retrieve relevant marketing examples from memory
            marketing_examples = vector_store.get_marketing_examples(
                event_type=state.get("event_type"),
                k=3
            )
            
            # Generate marketing posts
            marketing_posts = await self._generate_marketing_posts(state, marketing_examples)
            
            # Generate marketing plan and timeline
            marketing_plan = await self._generate_marketing_plan(state)
            marketing_timeline = await self._generate_marketing_timeline(state, marketing_plan)
            
            # Update state
            updated_state = self._update_state(state, {
                "marketing_posts": marketing_posts,
                "marketing_plan": marketing_plan,
                "marketing_timeline": marketing_timeline
            })
            
            # Save output
            updated_state = await self._save_output(
                updated_state,
                "content_generated",
                {
                    "posts_count": len(marketing_posts),
                    "platforms": list(set([p["platform"] for p in marketing_posts])),
                    "timeline_phases": len(marketing_timeline)
                }
            )
            
            # Store successful content in vector memory
            for post in marketing_posts[:3]:  # Store top posts as examples
                vector_store.add_marketing_template(
                    template_name=f"{state['event_id']}_{post['platform']}",
                    content=post["content"],
                    metadata={
                        "event_type": state.get("event_type"),
                        "platform": post["platform"]
                    }
                )
            
            logger.info(f"Generated {len(marketing_posts)} marketing posts")
            
        except Exception as e:
            logger.error(f"Content agent execution failed: {e}")
            updated_state = self._log_error(state, str(e))
        
        finally:
            self.end_execution()
        
        return updated_state
    
    async def _generate_marketing_posts(
        self,
        state: AgentState,
        examples: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate platform-specific marketing posts"""
        
        context = self._get_context(state)
        examples_text = "\n\n".join([
            f"Example {i+1}:\n{ex.get('content', '')}"
            for i, ex in enumerate(examples[:2])
        ]) if examples else "No examples available"
        
        prompt = f"""You are a marketing content strategist creating promotional posts for an event.

{context}

Example posts from similar events:
{examples_text}

Generate 3 engaging social media posts for each platform: Twitter, LinkedIn, and Facebook.

For each post, consider:
- Platform-specific best practices (character limits, tone, hashtags)
- Target audience engagement
- Call-to-action
- Event unique selling points

Return your response as a JSON array with this structure:
[
  {{
    "platform": "twitter",
    "content": "post content...",
    "hashtags": ["hashtag1", "hashtag2"],
    "post_type": "announcement|teaser|countdown|recap"
  }}
]

Generate exactly 9 posts total (3 per platform).
"""
        
        response = await self._invoke_llm(prompt, {})
        
        try:
            # Extract JSON from response
            json_start = response.find("[")
            json_end = response.rfind("]") + 1
            json_str = response[json_start:json_end]
            posts = json.loads(json_str)
            
            return posts
            
        except json.JSONDecodeError:
            logger.warning("Failed to parse marketing posts JSON, using fallback")
            return self._create_fallback_posts(state)
    
    async def _generate_marketing_plan(self, state: AgentState) -> Dict[str, Any]:
        """Generate comprehensive marketing plan"""
        
        context = self._get_context(state)
        
        prompt = f"""Create a comprehensive marketing plan for this event:

{context}

Include:
1. Marketing objectives
2. Target audience segments
3. Key messages
4. Channel strategy
5. Budget recommendations
6. Success metrics

Return as JSON:
{{
  "objectives": ["objective1", "objective2"],
  "audience_segments": ["segment1", "segment2"],
  "key_messages": ["message1", "message2"],
  "channels": ["channel1", "channel2"],
  "budget_recommendations": {{}},
  "success_metrics": ["metric1", "metric2"]
}}
"""
        
        response = await self._invoke_llm(prompt, {})
        
        try:
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            json_str = response[json_start:json_end]
            plan = json.loads(json_str)
            return plan
        except json.JSONDecodeError:
            logger.warning("Failed to parse marketing plan, using fallback")
            return {
                "objectives": ["Increase awareness", "Drive registrations"],
                "audience_segments": [state.get("target_audience", "General")],
                "key_messages": [f"Join {state.get('event_name')}"],
                "channels": ["social_media", "email", "website"],
                "success_metrics": ["registrations", "engagement_rate"]
            }
    
    async def _generate_marketing_timeline(
        self,
        state: AgentState,
        marketing_plan: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate marketing campaign timeline"""
        
        context = self._get_context(state)
        
        prompt = f"""Create a marketing campaign timeline for this event:

{context}

Marketing Plan:
{json.dumps(marketing_plan, indent=2)}

Create a phased timeline with specific activities, dates, and channels.

Return as JSON array:
[
  {{
    "phase": "Pre-launch|Launch|Mid-campaign|Final push|Post-event",
    "days_before_event": 30,
    "activities": ["activity1", "activity2"],
    "channels": ["channel1", "channel2"],
    "goals": ["goal1"]
  }}
]
"""
        
        response = await self._invoke_llm(prompt, {})
        
        try:
            json_start = response.find("[")
            json_end = response.rfind("]") + 1
            json_str = response[json_start:json_end]
            timeline = json.loads(json_str)
            return timeline
        except json.JSONDecodeError:
            return [
                {
                    "phase": "Pre-launch",
                    "days_before_event": 30,
                    "activities": ["Announce event", "Open registrations"],
                    "channels": ["social_media", "email"],
                    "goals": ["Build awareness"]
                },
                {
                    "phase": "Launch",
                    "days_before_event": 14,
                    "activities": ["Share speaker lineup", "Post testimonials"],
                    "channels": ["social_media", "website"],
                    "goals": ["Drive registrations"]
                }
            ]
    
    def _create_fallback_posts(self, state: AgentState) -> List[Dict[str, Any]]:
        """Create fallback marketing posts if LLM fails"""
        
        event_name = state.get("event_name", "Our Event")
        
        return [
            {
                "platform": "twitter",
                "content": f"🎉 Excited to announce {event_name}! Join us for an amazing experience. #Event #TechCommunity",
                "hashtags": ["Event", "TechCommunity"],
                "post_type": "announcement"
            },
            {
                "platform": "linkedin",
                "content": f"We're thrilled to invite you to {event_name}. Connect with industry leaders and innovators.",
                "hashtags": ["Networking", "ProfessionalDevelopment"],
                "post_type": "announcement"
            },
            {
                "platform": "facebook",
                "content": f"Mark your calendars! {event_name} is coming soon. Don't miss this opportunity!",
                "hashtags": ["Event", "Community"],
                "post_type": "announcement"
            }
        ]


# Create singleton instance
content_agent = ContentStrategistAgent()