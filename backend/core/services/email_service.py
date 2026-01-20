# ------------------------------ IMPORTS ------------------------------
import logging
import os
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

from core.config.settings import settings

logger = logging.getLogger(__name__)

# ------------------------------ EMAIL SERVICE INTERFACE ------------------------------

class EmailServiceInterface(ABC):
    """Abstract interface for email services. Makes it easy to swap implementations."""
    
    @abstractmethod
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send an email.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email content
            text_content: Plain text email content (optional)
            from_email: Sender email (optional, uses default if not provided)
            from_name: Sender name (optional, uses default if not provided)
        
        Returns:
            Dictionary with 'success' (bool) and 'message' (str) keys
        """
        pass

# ------------------------------ SENDGRID EMAIL SERVICE ------------------------------

class SendGridEmailService(EmailServiceInterface):
    """SendGrid email service implementation."""
    
    def __init__(self, api_key: str, from_email: str, from_name: str):
        """
        Initialize SendGrid email service.
        
        Args:
            api_key: SendGrid API key
            from_email: Default sender email
            from_name: Default sender name
        """
        try:
            import sendgrid
            from sendgrid.helpers.mail import Mail, Email, Content
            self.sendgrid = sendgrid
            self.Mail = Mail
            self.Email = Email
            self.Content = Content
        except ImportError:
            raise ImportError(
                "sendgrid package is required. Install it with: pip install sendgrid"
            )
        
        self.api_key = api_key
        self.from_email = from_email
        self.from_name = from_name
        self.client = sendgrid.SendGridAPIClient(api_key=api_key)
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send email via SendGrid."""
        try:
            from_email = from_email or self.from_email
            from_name = from_name or self.from_name
            
            message = self.Mail(
                from_email=self.Email(from_email, from_name),
                to_emails=to_email,
                subject=subject,
                html_content=html_content
            )
            
            if text_content:
                message.add_content(self.Content("text/plain", text_content))
            
            response = self.client.send(message)
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"Email sent successfully to {to_email}")
                return {
                    "success": True,
                    "message": "Email sent successfully",
                    "status_code": response.status_code
                }
            else:
                logger.error(f"SendGrid API error: {response.status_code} - {response.body}")
                return {
                    "success": False,
                    "message": f"Failed to send email: {response.status_code}",
                    "status_code": response.status_code
                }
        
        except Exception as e:
            logger.error(f"Error sending email via SendGrid: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Error sending email: {str(e)}"
            }

# ------------------------------ LAMBDA EMAIL SERVICE ------------------------------

class LambdaEmailService(EmailServiceInterface):
    """AWS Lambda email service implementation."""
    
    def __init__(self, function_name: str, from_email: str, from_name: str):
        """
        Initialize Lambda email service.
        
        Args:
            function_name: AWS Lambda function name
            from_email: Default sender email
            from_name: Default sender name
        """
        try:
            import boto3
            self.boto3 = boto3
        except ImportError:
            raise ImportError(
                "boto3 package is required. Install it with: pip install boto3"
            )
        
        self.function_name = function_name
        self.from_email = from_email
        self.from_name = from_name
        self.lambda_client = boto3.client('lambda')
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send email via AWS Lambda."""
        try:
            import json
            
            payload = {
                "to_email": to_email,
                "subject": subject,
                "html_content": html_content,
                "text_content": text_content,
                "from_email": from_email or self.from_email,
                "from_name": from_name or self.from_name
            }
            
            response = self.lambda_client.invoke(
                FunctionName=self.function_name,
                InvocationType='Event',  # Async invocation
                Payload=json.dumps(payload)
            )
            
            if response['StatusCode'] in [200, 202]:
                logger.info(f"Lambda invoked successfully for email to {to_email}")
                return {
                    "success": True,
                    "message": "Email queued for sending",
                    "request_id": response.get('RequestId')
                }
            else:
                logger.error(f"Lambda invocation error: {response['StatusCode']}")
                return {
                    "success": False,
                    "message": f"Failed to invoke Lambda: {response['StatusCode']}"
                }
        
        except Exception as e:
            logger.error(f"Error invoking Lambda for email: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Error invoking Lambda: {str(e)}"
            }

# ------------------------------ EMAIL SERVICE FACTORY ------------------------------

class EmailService:
    """
    Email service factory that provides the appropriate implementation.
    Easy to switch between direct sending and Lambda.
    """
    
    _instance: Optional[EmailServiceInterface] = None
    
    @classmethod
    def get_instance(cls) -> EmailServiceInterface:
        """
        Get email service instance (singleton pattern).
        Automatically selects implementation based on configuration.
        """
        if cls._instance is None:
            config = settings.email
            
            if config.use_lambda and config.lambda_function_name:
                logger.info("Using Lambda email service")
                cls._instance = LambdaEmailService(
                    function_name=config.lambda_function_name,
                    from_email=config.from_email,
                    from_name=config.from_name
                )
            elif config.provider == "sendgrid":
                if not config.sendgrid_api_key:
                    raise ValueError("SENDGRID_API_KEY is required when using SendGrid")
                logger.info("Using SendGrid email service")
                cls._instance = SendGridEmailService(
                    api_key=config.sendgrid_api_key,
                    from_email=config.from_email,
                    from_name=config.from_name
                )
            else:
                raise ValueError(f"Unsupported email provider: {config.provider}")
        
        return cls._instance
    
    @classmethod
    def send_waitlist_confirmation(cls, email: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Send waitlist confirmation email.
        
        Args:
            email: Recipient email address
            context: Optional context data for personalization (vehicle_count, tracking_product, etc.)
        
        Returns:
            Dictionary with 'success' (bool) and 'message' (str) keys
        """
        from core.services.email_templates import get_waitlist_confirmation_template
        
        try:
            template = get_waitlist_confirmation_template(email, context or {})
            service = cls.get_instance()
            
            result = service.send_email(
                to_email=email,
                subject=template["subject"],
                html_content=template["html_content"],
                text_content=template["text_content"]
            )
            
            return result
        
        except Exception as e:
            logger.error(f"Error sending waitlist confirmation email: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Error sending email: {str(e)}"
            }
