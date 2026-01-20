# ------------------------------ IMPORTS ------------------------------
from typing import Dict, Any

# ------------------------------ EMAIL TEMPLATES ------------------------------

def get_waitlist_confirmation_template(email: str, context: Dict[str, Any] = None) -> Dict[str, str]:
    """
    Generate waitlist confirmation email template.
    
    Args:
        email: Recipient email address
        context: Optional context data for personalization (can include vehicle_count, tracking_product, etc.)
    
    Returns:
        Dictionary with 'subject' and 'html_content' keys
    """
    subject = "You're on the Turolytics waitlist"
    
    has_fleet_details = context and (
        context.get("vehicle_count") or 
        context.get("tracking_product") or 
        context.get("would_use") or 
        context.get("feedback")
    )
    
    position = context.get("position") if context else None
    total = context.get("total") if context else None
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Welcome to Turolytics Waitlist</title>
    </head>
    <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f5f5f5;">
        <table role="presentation" style="width: 100%; border-collapse: collapse;">
            <tr>
                <td style="padding: 40px 20px; text-align: center;">
                    <table role="presentation" style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <!-- Header -->
                        <tr>
                            <td style="padding: 40px 40px 30px; text-align: left;">
                                <div style="display: inline-block; width: 40px; height: 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 8px; margin-bottom: 20px;">
                                    <span style="display: flex; align-items: center; justify-content: center; height: 100%; color: #ffffff; font-weight: 700; font-size: 20px;">T</span>
                                </div>
                                <h1 style="margin: 0 0 8px; color: #1a1a1a; font-size: 24px; font-weight: 600;">Turolytics</h1>
                            </td>
                        </tr>
                        
                        <!-- Content -->
                        <tr>
                            <td style="padding: 0 40px 40px;">
                                <p style="margin: 0 0 20px; color: #1a1a1a; font-size: 16px; line-height: 1.6;">
                                    Hi there,
                                </p>
                                
                                <p style="margin: 0 0 20px; color: #1a1a1a; font-size: 16px; line-height: 1.6;">
                                    Thanks for signing up for the <strong>Turolytics waitlist</strong> — you're officially in.
                                </p>
                                
                                {f'<p style="margin: 0 0 20px; color: #667eea; font-size: 16px; line-height: 1.6; font-weight: 600;">You\'re #{position} on the waitlist{f" of {total} people" if total else ""}.</p>' if position else ''}
                                
                                <p style="margin: 0 0 20px; color: #1a1a1a; font-size: 16px; line-height: 1.6;">
                                    Turolytics is being built to help Turo hosts track fleet performance, earnings, utilization, and key insights in one place. We're currently onboarding early users in phases to make sure everything is stable, accurate, and genuinely useful.
                                </p>
                                
                                <h3 style="margin: 24px 0 12px; color: #1a1a1a; font-size: 18px; font-weight: 600;">
                                    What happens next:
                                </h3>
                                
                                <ul style="margin: 0 0 20px; padding-left: 24px; color: #1a1a1a; font-size: 16px; line-height: 1.8;">
                                    <li style="margin-bottom: 8px;">You'll receive updates as new features roll out</li>
                                    <li style="margin-bottom: 8px;">Early users will get <strong>priority access</strong> and the ability to give direct feedback</li>
                                    <li style="margin-bottom: 8px;">We'll notify you as soon as your spot opens up</li>
                                </ul>
                                
                                {f'<p style="margin: 0 0 20px; color: #1a1a1a; font-size: 16px; line-height: 1.6;">If you shared any details about your fleet or tools, those are already noted and will help shape upcoming features.</p>' if has_fleet_details else ''}
                                
                                <p style="margin: 0; color: #1a1a1a; font-size: 16px; line-height: 1.6;">
                                    Thanks again for your interest — we're excited to have you early.
                                </p>
                                
                                <p style="margin: 24px 0 0; color: #1a1a1a; font-size: 16px; line-height: 1.6;">
                                    Best,<br>
                                    <strong>Turolytics Team</strong>
                                </p>
                            </td>
                        </tr>
                        
                        <!-- Footer -->
                        <tr>
                            <td style="padding: 30px 40px; border-top: 1px solid #e5e7eb; background-color: #f9fafb; border-radius: 0 0 8px 8px;">
                                <p style="margin: 0; color: #6b7280; font-size: 12px; line-height: 1.5;">
                                    © 2025 Turolytics. All rights reserved.
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    position_text = f"\nYou're #{position} on the waitlist{f' of {total} people' if total else ''}.\n" if position else ""
    
    text_content = f"""Hi there,

Thanks for signing up for the Turolytics waitlist — you're officially in.{position_text}

Turolytics is being built to help Turo hosts track fleet performance, earnings, utilization, and key insights in one place. We're currently onboarding early users in phases to make sure everything is stable, accurate, and genuinely useful.

What happens next:

* You'll receive updates as new features roll out
* Early users will get priority access and the ability to give direct feedback
* We'll notify you as soon as your spot opens up

{f'If you shared any details about your fleet or tools, those are already noted and will help shape upcoming features.\n\n' if has_fleet_details else ''}Thanks again for your interest — we're excited to have you early.

Best,
Turolytics Team

© 2026 Turolytics. All rights reserved.
"""
    
    return {
        "subject": subject,
        "html_content": html_content,
        "text_content": text_content
    }

