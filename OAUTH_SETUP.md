# OAuth Setup Guide for Study Buddy

## Overview
Study Buddy now supports OAuth login with Google and Apple. Follow these steps to set up OAuth credentials for both providers.

For phone sign-in, your deployed app must use a public `https://` URL and open Google sign-in in a normal browser window. Google can block OAuth inside embedded webviews or iframe-only flows.

---

## Google Sign-In Setup

### Step 1: Create a Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click on the project dropdown and select "New Project"
3. Enter "Study Buddy" as the project name
4. Click "Create"

### Step 2: Configure OAuth Consent Screen
1. In the Cloud Console, go to "APIs & Services" > "OAuth consent screen"
2. Choose the appropriate user type
3. Fill in your app name, support email, and developer contact email
4. If this is a production app, add your home page, privacy policy, and terms of service URLs

### Step 3: Create OAuth 2.0 Credentials
1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. Select "Web application"
4. Add these Authorized JavaScript origins:
   - `http://localhost:8501`
   - `http://127.0.0.1:8501`
5. Add these Authorized redirect URIs (exact match required):
   - `http://localhost:8501`
   - `http://127.0.0.1:8501`
6. If you are deploying publicly, also add your real HTTPS app URL:
   - Authorized JavaScript origin example: `https://your-app-name.streamlit.app`
   - Authorized redirect URI example: `https://your-app-name.streamlit.app`
7. Click "Create"
8. Copy your **Client ID** and **Client Secret**

### Step 4: Add to Environment
Create a `.env` file in the project root:

```bash
GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret
APP_BASE_URL=https://your-app-name.streamlit.app

# Optional:
# Leave GOOGLE_REDIRECT_URI blank to reuse APP_BASE_URL.
# For local development, set GOOGLE_REDIRECT_URI=http://localhost:8501
GOOGLE_REDIRECT_URI=
```

Or add to Streamlit secrets in `.streamlit/secrets.toml`:

```toml
GOOGLE_CLIENT_ID = "your_client_id.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "your_client_secret"
APP_BASE_URL = "https://your-app-name.streamlit.app"
GOOGLE_REDIRECT_URI = ""
```

### Step 5: Test in a Secure Browser
1. Open the deployed app directly in Safari or Chrome
2. Tap **Continue with Google**
3. If the app is embedded in another site, the OAuth flow must open in the top-level browser window
4. If Google still shows `access blocked`, verify that the exact HTTPS redirect URI in Google Cloud matches your deployed app URL

---

## Apple Sign-In Setup

### Step 1: Sign Up for Apple Developer Program
1. Go to [Apple Developer Program](https://developer.apple.com/)
2. Sign in with your Apple ID
3. Enroll in the program (requires subscription)

### Step 2: Create an App ID
1. Go to "Certificates, Identifiers & Profiles"
2. Click "Identifiers"
3. Click the "+" button to create a new identifier
4. Select "App IDs" and click "Continue"
5. Register as:
   - App Type: App
   - App ID Prefix: Select your team
   - App ID Description: "Study Buddy"
   - Bundle ID: `com.studybuddy.app`
6. Enable "Sign in with Apple" capability
7. Click "Continue" and then "Register"

### Step 3: Create a Service ID
1. Go to "Identifiers"
2. Click the "+" button
3. Select "Services IDs" and click "Continue"
4. Enter:
   - Description: "Study Buddy Web"
   - Identifier: `com.studybuddy.app.web`
5. Check "Sign in with Apple"
6. Click "Configure"
7. Add these domains:
   - `localhost`
   - `127.0.0.1`
8. Add these Return URLs:
   - `http://localhost:8501/auth/apple/callback`
9. Click "Save"
10. Click "Continue" and then "Register"

### Step 4: Create a Private Key
1. Go to "Keys"
2. Click the "+" button
3. Enter key name: "Study Buddy Key"
4. Check "Sign in with Apple"
5. Click "Configure"
6. Select the Service ID you just created
7. Click "Save"
8. Click "Continue" and then "Register"
9. **Download the key file** - you'll need this
10. Copy your **Key ID** from the page

### Step 5: Get Your Team ID
1. In the top right, click on your profile
2. Go to "Membership"
3. Your Team ID is listed there

### Step 6: Add to Environment
Add to `.env`:

```bash
APPLE_TEAM_ID=your_team_id
APPLE_CLIENT_ID=com.studybuddy.app.web
APPLE_KEY_ID=your_key_id
APPLE_PRIVATE_KEY=-----BEGIN EC PRIVATE KEY-----\nYour key content here\n-----END EC PRIVATE KEY-----
APPLE_REDIRECT_URI=http://localhost:8501/auth/apple/callback
```

Or add to `.streamlit/secrets.toml`:

```toml
APPLE_TEAM_ID = "your_team_id"
APPLE_CLIENT_ID = "com.studybuddy.app.web"
APPLE_KEY_ID = "your_key_id"
APPLE_PRIVATE_KEY = "-----BEGIN EC PRIVATE KEY-----\nYour key content here\n-----END EC PRIVATE KEY-----"
APPLE_REDIRECT_URI = "http://localhost:8501/auth/apple/callback"
```

---

## Testing OAuth Locally

### For Google:
1. Click the 🔵 Google button on login/signup page
2. You'll be redirected to Google's login page
3. Sign in with your Google account
4. You'll be asked to consent to share your profile
5. You'll be redirected back to the app with your user info

### For Apple:
1. Click the 🍎 Apple button on login/signup page
2. You'll be redirected to Apple's Sign in page
3. Sign in with your Apple ID
4. You may be asked to verify with Face ID or passcode
5. You'll be redirected back with your user info

---

## Production Setup

For production deployment, you'll need to:

1. **Set a public app URL**:
   - Example: `APP_BASE_URL=https://studybuddy.example.com`
   - For Streamlit Community Cloud, this is usually your `https://<subdomain>.streamlit.app` URL

2. **Use HTTPS**: OAuth requires secure connections in production

3. **Store Secrets Securely**:
   - Use environment variables or secret management tools
   - Never commit `.env` file to git

4. **Update OAuth providers**:
   - Add your production domain to Google Cloud Console as both an Authorized JavaScript origin and Authorized redirect URI
   - Add your production domain to Apple Developer account

5. **Set up OAuth callback handler** in `app.py` to handle redirect and create/login user automatically

6. **Avoid embedded browsers**:
   - Test on phone from Safari or Chrome
   - Avoid opening Google sign-in from in-app browsers like Instagram, Facebook, or Gmail

---

## Troubleshooting

### "Invalid client ID" error
- Make sure your Client ID is correct
- Check that domains are registered in provider settings

### "Redirect URI mismatch" error
- Ensure the redirect URI in code matches exactly what's registered
- Check for trailing slashes and case sensitivity
- If you use `APP_BASE_URL`, make sure it exactly matches the deployed HTTPS URL

### Apple key not loading
- Verify the private key is properly formatted (with \n for newlines)
- Make sure you're using EC private key, not RSA

### Google says "Access blocked" or mentions "Use secure browsers"
- Open the app in Safari or Chrome, not an in-app browser
- Make sure the sign-in flow opens in the top-level browser window
- Verify the deployed app URL is HTTPS and registered in Google Cloud Console
- Check that your OAuth consent screen and app URLs are configured for production use

### User info not being retrieved
- Check that scopes are correct (`openid email profile` for Google, `name email` for Apple)
- Verify your credentials are valid and not expired

---

## Files Modified

- `oauth_handler.py` - New OAuth handler with Google and Apple integration
- `landing.py` - Updated with OAuth redirect buttons
- `auth.py` - Will be updated to handle OAuth user creation (coming next)

---

## Next Steps

1. Get OAuth credentials from Google and Apple
2. Add them to your `.env` file or Streamlit secrets
3. Restart the app
4. Test the OAuth login flow
5. Update `auth.py` to auto-create/login users from OAuth data
