"""
Communication/Mailing Agent
Manages participant communication and email campaigns
"""
from typing import Dict, Any, List
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.agents.base_agent import BaseAgent
from app.orchestration.state_schema import AgentState
from app.services.email_service import email_service
from app.database.models import Participant, EmailStatus
from app.utils.logger import logger


class CommunicationAgent(BaseAgent):
    """Agent responsible for participant communication and emails"""
    
    def __init__(self):
        super().__init__("CommunicationAgent")
    
    async def execute(self, state: AgentState) -> AgentState:
        """
        Execute email communication workflow
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with email results
        """
        self.start_execution()
        
        try:
            # Get participants from state
            participants = state.get("participants", [])
            
            if not participants:
                logger.warning("No participants found in state")
                return self._log_warning(state, "No participants to email")
            
            # Validate and segment participants
            validated_participants = self._validate_participants(participants)
            segments = self._segment_participants(validated_participants)
            
            # Generate personalized email templates
            email_templates = await self._generate_email_templates(state, segments)
            
            # Prepare email messages (don't send yet unless configured)
            email_messages = self._prepare_email_messages(
                validated_participants,
                email_templates,
                state
            )
            
            # Update state
            updated_state = self._update_state(state, {
                "email_templates": email_templates,
                "email_segments": segments,
                "emails_sent": email_messages
            })
            
            # Save output
            updated_state = await self._save_output(
                updated_state,
                "emails_prepared",
                {
                    "total_participants": len(participants),
                    "validated_participants": len(validated_participants),
                    "segments": list(segments.keys()),
                    "emails_prepared": len(email_messages)
                }
            )
            
            logger.info(f"Prepared {len(email_messages)} email messages")
            
        except Exception as e:
            logger.error(f"Communication agent execution failed: {e}")
            updated_state = self._log_error(state, str(e))
        
        finally:
            self.end_execution()
        
        return updated_state
    
    def _validate_participants(
        self,
        participants: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Validate participant email addresses"""
        
        validated = []
        
        for participant in participants:
            email = participant.get("email", "")
            
            if email_service.validate_email_list([email])["valid"]:
                validated.append(participant)
            else:
                logger.warning(f"Invalid email address: {email}")
        
        return validated
    
    def _segment_participants(
        self,
        participants: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Segment participants for targeted communication"""
        
        segments = {
            "all": participants,
            "speakers": [],
            "sponsors": [],
            "general_attendees": []
        }
        
        for participant in participants:
            if participant.get("is_speaker"):
                segments["speakers"].append(participant)
            elif participant.get("is_sponsor"):
                segments["sponsors"].append(participant)
            else:
                segments["general_attendees"].append(participant)
        
        return segments
    
    async def _generate_email_templates(
        self,
        state: AgentState,
        segments: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, str]:
        """Generate personalized email templates for each segment"""
        
        context = self._get_context(state)
        templates = {}
        
        # Generate template for general attendees
        if segments.get("general_attendees"):
            templates["general_welcome"] = await self._generate_template(
                context,
                "general attendee",
                "welcome and event information"
            )
        
        # Generate template for speakers
        if segments.get("speakers"):
            templates["speaker_briefing"] = await self._generate_template(
                context,
                "speaker",
                "speaker briefing and logistics"
            )
        
        # Generate template for sponsors
        if segments.get("sponsors"):
            templates["sponsor_welcome"] = await self._generate_template(
                context,
                "sponsor",
                "sponsorship details and benefits"
            )
        
        return templates
    
    async def _generate_template(
        self,
        context: str,
        recipient_type: str,
        template_purpose: str
    ) -> str:
        """Generate a single email template"""
        
        prompt = f"""Create a professional email template for {recipient_type} regarding {template_purpose}.

Event Context:
{context}

The email should:
1. Be warm and professional
2. Include personalization placeholders: {{{{full_name}}}}, {{{{event_name}}}}
3. Provide relevant information for {recipient_type}
4. Include a clear call-to-action
5. Be concise (200-300 words)

Generate the email body (plain text format):
"""
        
        response = await self._invoke_llm(prompt, {})
        return response.strip()
    
    def _prepare_email_messages(
        self,
        participants: List[Dict[str, Any]],
        templates: Dict[str, str],
        state: AgentState
    ) -> List[Dict[str, Any]]:
        """Prepare email messages with personalization"""
        
        messages = []
        
        for participant in participants:
            # Determine which template to use
            if participant.get("is_speaker"):
                template_key = "speaker_briefing"
            elif participant.get("is_sponsor"):
                template_key = "sponsor_welcome"
            else:
                template_key = "general_welcome"
            
            template = templates.get(
                template_key,
                f"Welcome to {state.get('event_name')}! We're excited to have you join us."
            )
            
            # Personalize template
            personalized_body = email_service.personalize_email(
                template,
                {
                    "full_name": participant.get("full_name", ""),
                    "event_name": state.get("event_name", ""),
                    "organization": participant.get("organization", "")
                }
            )
            
            messages.append({
                "recipient_email": participant["email"],
                "recipient_name": participant.get("full_name"),
                "subject": f"Welcome to {state.get('event_name')}!",
                "body_text": personalized_body,
                "segment": template_key,
                "status": "prepared"
            })
        
        return messages
    
    async def send_emails(
        self,
        state: AgentState,
        db: AsyncSession
    ) -> Dict[str, int]:
        """
        Actually send the prepared emails
        
        Args:
            state: Current state with prepared emails
            db: Database session
            
        Returns:
            Dictionary with send statistics
        """
        email_messages = state.get("emails_sent", [])
        
        sent_count = 0
        failed_count = 0
        
        for message in email_messages:
            try:
                success = await email_service.send_email(
                    to_email=message["recipient_email"],
                    subject=message["subject"],
                    body_text=message["body_text"],
                    to_name=message.get("recipient_name")
                )
                
                # Log to database
                await email_service.log_email(
                    db=db,
                    event_id=state["event_id"],
                    recipient_email=message["recipient_email"],
                    subject=message["subject"],
                    body_text=message["body_text"],
                    status=EmailStatus.SENT if success else EmailStatus.FAILED,
                    recipient_name=message.get("recipient_name")
                )
                
                if success:
                    sent_count += 1
                else:
                    failed_count += 1
                    
            except Exception as e:
                logger.error(f"Failed to send email to {message['recipient_email']}: {e}")
                failed_count += 1
        
        return {"sent": sent_count, "failed": failed_count}


# Create singleton instance
communication_agent = CommunicationAgent()