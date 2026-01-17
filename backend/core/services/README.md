# Email Service

Clean, modular email service that can easily be converted to Lambda.

## Structure

- `email_service.py` - Main email service with SendGrid and Lambda implementations
- `email_templates.py` - Email templates (HTML and plain text)

## Setup

### 1. Install Dependencies

For SendGrid:
```bash
pip install sendgrid
```

For Lambda (when converting):
```bash
pip install boto3
```

### 2. Environment Variables

Add to your `.env` file:

```env
# Email Configuration
EMAIL_PROVIDER=sendgrid
SENDGRID_API_KEY=your_sendgrid_api_key_here
EMAIL_FROM=noreply@turolytics.com
EMAIL_FROM_NAME=Turolytics

# For Lambda (when converting):
# EMAIL_USE_LAMBDA=true
# EMAIL_LAMBDA_FUNCTION=your-lambda-function-name
```

### 3. Get SendGrid API Key

1. Sign up at https://sendgrid.com
2. Go to Settings > API Keys
3. Create a new API key with "Mail Send" permissions
4. Copy the key to your `.env` file

## Usage

```python
from core.services.email_service import EmailService

# Send waitlist confirmation
result = EmailService.send_waitlist_confirmation("user@example.com")
if result["success"]:
    print("Email sent!")
```

## Converting to Lambda

To convert to Lambda, simply:

1. Set environment variables:
   ```env
   EMAIL_USE_LAMBDA=true
   EMAIL_LAMBDA_FUNCTION=your-lambda-function-name
   ```

2. Deploy the email service code to Lambda (same code works!)

3. No code changes needed - the service automatically switches to Lambda mode.

## Architecture

- **EmailServiceInterface** - Abstract base class for all email implementations
- **SendGridEmailService** - Direct SendGrid implementation
- **LambdaEmailService** - AWS Lambda implementation
- **EmailService** - Factory that selects the right implementation

This structure makes it easy to:
- Switch between implementations
- Add new email providers
- Test with mocks
- Convert to Lambda without code changes
