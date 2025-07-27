# Simple Team Setup Guide

## For You (Admin)

### 1. Set up Google OAuth (One Time)
1. **Go to [Google Cloud Console](https://console.cloud.google.com/)**
2. **Create OAuth 2.0 Client ID** (Web application)
3. **Add redirect URIs:**
   ```
   http://localhost
   https://vcresearchbot.streamlit.app
   ```
4. **Download credentials.json**

### 2. Add to Streamlit Cloud Secrets
In your Streamlit Cloud app settings → Secrets, add:
```toml
OPENAI_API_KEY = "sk-your-openai-api-key"
GOOGLE_CLIENT_ID = "your-client-id.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "your-client-secret"
```

### 3. Add Team Members to Google OAuth
1. **Go to Google Cloud Console → OAuth consent screen**
2. **Add all team members as "Test users"**
3. **Save changes**

## For Your Team Members

### Super Simple Process:
1. **Visit your app**: `https://vcresearchbot.streamlit.app`
2. **Enter their name** in the sidebar (can be anything - John, Sarah, Alex, etc.)
3. **Click "Start"**
4. **Click "Fetch Meetings"**
5. **Login with their Google account** (normal Gmail login)
6. **Authorize the app** (one-time process)
7. **Start using the app!**

## How It Works

- ✅ **One OAuth setup** for everyone
- ✅ **Each person authenticates** with their own Google account
- ✅ **Each person sees** their own calendar
- ✅ **Each person's data** is separate
- ✅ **No technical setup** required for team members

## Security

- Each user's Google authentication is separate
- Research data is not shared between users
- API keys are stored securely
- No sensitive data is logged permanently

## That's It!

Your team members just need to:
1. **Enter their name** (anything they want)
2. **Login with Google**
3. **Start researching!**

No technical setup, no OAuth credentials, no complicated processes. 