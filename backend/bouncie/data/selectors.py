# ------------------------------ BOUNCIE SELECTORS ------------------------------

# ------------------------------ URLS ------------------------------
BOUNCIE_LOGIN_URL = "https://auth.bouncie.com/login"
BOUNCIE_AUTH_URL = "https://auth.bouncie.com/dialog/authorize"

# ------------------------------ LOGIN SELECTORS ------------------------------
EMAIL_SELECTOR = '#email, input[type="email"][name="email"], input[name="email"]'
PASSWORD_SELECTOR = '#password, input[type="password"][name="password"], input[name="password"]'
SIGN_IN_BUTTON_SELECTOR = 'button[type="submit"]:has-text("SIGN IN"), button:has-text("SIGN IN")'

# ------------------------------ OAUTH AUTHORIZATION SELECTORS ------------------------------
AUTHORIZE_BUTTON_SELECTOR = 'button:has-text("Authorize Access"), button.authorize-button, .css-r60df2'

# ------------------------------ SUCCESS INDICATORS ------------------------------
# After authorization, Bouncie redirects to callback URL with code parameter
AUTHORIZATION_SUCCESS_URL_PATTERN = "**/auth/bouncie/callback**"
AUTHORIZATION_SUCCESS_SELECTORS = [
    '[data-authorization="success"]',
    '.authorization-success'
]

# ------------------------------ ERROR SELECTORS ------------------------------
ERROR_SELECTOR = '.error-message, .alert-error, [role="alert"]'



