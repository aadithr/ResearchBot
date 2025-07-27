# Team Setup Guide - Individual Google OAuth

## For Each Team Member

### Step 1: Create Your Own Google Cloud Project

1. **Go to [Google Cloud Console](https://console.cloud.google.com/)**
2. **Create a new project** (or use your existing one)
3. **Enable Google Calendar API:**
   - Go to "APIs & Services" → "Library"
   - Search for "Google Calendar API"
   - Click "Enable"

### Step 2: Create OAuth 2.0 Credentials

1. **Go to "APIs & Services" → "Credentials"**
2. **Click "Create Credentials" → "OAuth 2.0 Client ID"**
3. **Choose "Web application"**
4. **Add these redirect URIs:**
   ```
   http://localhost
   https://vcresearchbot.streamlit.app
   ```
5. **Download the credentials.json file**

### Step 3: Add Your Credentials to Streamlit Cloud

1. **Go to your Streamlit Cloud app**
2. **Settings → Secrets**
3. **Add your credentials:**
   ```toml
   OPENAI_API_KEY = "sk-your-openai-api-key"
   GOOGLE_CLIENT_ID = "your-client-id.apps.googleusercontent.com"
   GOOGLE_CLIENT_SECRET = "your-client-secret"
   ```

### Step 4: Use the App

1. **Open the app**
2. **Set your user ID in the sidebar**
3. **Complete Google OAuth authentication**
4. **Start using with your own calendar!**

## Alternative: Shared OAuth (Not Recommended)

If you want to use the same OAuth credentials for everyone:
- Add all team members as "test users" in your OAuth consent screen
- Everyone uses the same client ID/secret
- Each person still authenticates with their own Google account

## Security Notes

- Each person's Google authentication is separate
- Research data is not shared between users
- API keys are stored securely
- No sensitive data is logged permanently

## Support

Contact your team administrator if you need help setting up your credentials. 