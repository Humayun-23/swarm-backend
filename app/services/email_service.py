"""
Email Service
"""
from typing import List, Optional, Dict, Any
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Template
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.models import Email, EmailStatus
from app.utils.logger import logger
from app.utils.helpers import validate_email


class EmailService:
    """Service for sending and managing emails"""
    
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.SMTP_FROM_EMAIL
        self.from_name = settings.SMTP_FROM_NAME
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
        to_name: Optional[str] = None
    ) -> bool:
        """
        Send email to recipient
        
        Args:
            to_email: Recipient email
            subject: Email subject
            body_text: Plain text body
            body_html: HTML body (optional)
            to_name: Recipient name (optional)
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not validate_email(to_email):
            logger.error(f"Invalid email address: {to_email}")
            return False
        
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.from_name} <{self.from_email}>"
            message["To"] = f"{to_name} <{to_email}>" if to_name else to_email
            
            # Add text part
            text_part = MIMEText(body_text, "plain")
            message.attach(text_part)
            
            # Add HTML part if provided
            if body_html:
                html_part = MIMEText(body_html, "html")
                message.attach(html_part)
            
            # Send email
            async with aiosmtplib.SMTP(
                hostname=self.smtp_host,
                port=self.smtp_port,
                use_tls=False,
                start_tls=True
            ) as smtp:
                await smtp.login(self.smtp_username, self.smtp_password)
                await smtp.send_message(message)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    async def send_bulk_emails(
        self,
        recipients: List[Dict[str, str]],
        subject: str,
        body_template: str,
        use_html: bool = True
    ) -> Dict[str, int]:
        """
        Send bulk emails to multiple recipients
        
        Args:
            recipients: List of recipient dictionaries with 'email', 'name', and template variables
            subject: Email subject
            body_template: Email body template (Jinja2 format)
            use_html: Whether to send HTML email
            
        Returns:
            Dictionary with counts of sent, failed emails
        """
        sent_count = 0
        failed_count = 0
        
        template = Template(body_template)
        
        for recipient in recipients:
            try:
                # Render template with recipient data
                body = template.render(**recipient)
                
                # Send email
                success = await self.send_email(
                    to_email=recipient.get("email"),
                    subject=subject,
                    body_text=body,
                    body_html=body if use_html else None,
                    to_name=recipient.get("name")
                )
                
                if success:
                    sent_count += 1
                else:
                    failed_count += 1
                    
            except Exception as e:
                logger.error(f"Failed to send email to {recipient.get('email')}: {e}")
                failed_count += 1
        
        logger.info(f"Bulk email send complete: {sent_count} sent, {failed_count} failed")
        return {"sent": sent_count, "failed": failed_count}
    
    def personalize_email(
        self,
        template: str,
        participant_data: Dict[str, Any]
    ) -> str:
        """
        Personalize email template with participant data
        
        Args:
            template: Email template string
            participant_data: Dictionary with participant information
            
        Returns:
            Personalized email content
        """
        try:
            jinja_template = Template(template)
            return jinja_template.render(**participant_data)
        except Exception as e:
            logger.error(f"Failed to personalize email: {e}")
            return template
    
    async def log_email(
        self,
        db: AsyncSession,
        event_id: str,
        recipient_email: str,
        subject: str,
        body_text: str,
        status: EmailStatus,
        recipient_name: Optional[str] = None,
        body_html: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> Email:
        """
        Log email to database
        
        Args:
            db: Database session
            event_id: Event ID
            recipient_email: Recipient email
            subject: Email subject
            body_text: Email body text
            status: Email status
            recipient_name: Recipient name (optional)
            body_html: Email HTML body (optional)
            error_message: Error message if failed (optional)
            
        Returns:
            Created Email instance
        """
        from datetime import datetime
        
        email = Email(
            event_id=event_id,
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            status=status,
            sent_at=datetime.utcnow() if status == EmailStatus.SENT else None,
            error_message=error_message
        )
        
        db.add(email)
        await db.commit()
        await db.refresh(email)
        
        return email
    
    def validate_email_list(self, emails: List[str]) -> Dict[str, List[str]]:
        """
        Validate list of email addresses
        
        Args:
            emails: List of email addresses
            
        Returns:
            Dictionary with 'valid' and 'invalid' email lists
        """
        valid_emails = []
        invalid_emails = []
        
        for email in emails:
            if validate_email(email):
                valid_emails.append(email)
            else:
                invalid_emails.append(email)
        
        return {
            "valid": valid_emails,
            "invalid": invalid_emails
        }
    
    def segment_recipients(
        self,
        participants: List[Dict[str, Any]],
        criteria: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Segment recipients based on criteria
        
        Args:
            participants: List of participant dictionaries
            criteria: Segmentation criteria
            
        Returns:
            Filtered list of participants
        """
        filtered = participants.copy()
        
        # Filter by speaker status
        if "is_speaker" in criteria:
            filtered = [p for p in filtered if p.get("is_speaker") == criteria["is_speaker"]]
        
        # Filter by sponsor status
        if "is_sponsor" in criteria:
            filtered = [p for p in filtered if p.get("is_sponsor") == criteria["is_sponsor"]]
        
        # Filter by organization
        if "organization" in criteria:
            filtered = [
                p for p in filtered 
                if p.get("organization") == criteria["organization"]
            ]
        
        # Filter by role
        if "role" in criteria:
            filtered = [p for p in filtered if p.get("role") == criteria["role"]]
        
        return filtered


# Create singleton instance
email_service = EmailService()