# ResearchBot Deployment Guide

## Quick Deploy to Streamlit Cloud

### 1. Prepare Your Repository
- Ensure all files are committed to GitHub
- Make sure `requirements.txt` is in the root directory
- Verify `.streamlit/config.toml` exists

### 2. Set Up Google OAuth for Production

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to your project's OAuth 2.0 credentials
3. Add your deployment URL to authorized redirect URIs:
   - For Streamlit Cloud: `https://your-app-name.streamlit.app`
   - For Railway: `https://your-app-name.railway.app`
   - For Render: `https://your-app-name.onrender.com`

### 3. Deploy to Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click "New app"
4. Select your repository
5. Set the path to your app: `src/calendar_app.py`
6. Click "Deploy"

### 4. Configure Environment Variables

In your Streamlit Cloud dashboard, add these secrets:

```
OPENAI_API_KEY = sk-your-openai-api-key-here
```

### 5. Share with Your Team

1. Share the deployment URL with your team
2. Each team member needs to:
   - Set their user ID in the sidebar
   - Complete Google OAuth authentication
   - Start using the app!

## Alternative Deployment Options

### Railway (Recommended for Production)

1. Go to [railway.app](https://railway.app)
2. Connect your GitHub repository
3. Add environment variables in Railway dashboard
4. Deploy automatically

### Render

1. Go to [render.com](https://render.com)
2. Create a new Web Service
3. Connect your GitHub repository
4. Set build command: `pip install -r requirements.txt`
5. Set start command: `streamlit run src/calendar_app.py --server.port $PORT --server.address 0.0.0.0`

## Team Usage Instructions

### For Team Members:

1. **First Time Setup:**
   - Enter your name/ID in the sidebar
   - Click "Set User ID"
   - Complete Google OAuth authentication
   - Start using the app!

2. **Daily Usage:**
   - Your user ID will be remembered
   - Google authentication will persist
   - All your research data is saved per session

### For Administrators:

1. **Monitor Usage:**
   - Check Streamlit Cloud analytics
   - Monitor OpenAI API usage
   - Review team research outputs

2. **Update the App:**
   - Push changes to GitHub
   - Streamlit Cloud will auto-deploy
   - No downtime for users

## Troubleshooting

### Common Issues:

1. **Google OAuth Error:**
   - Ensure redirect URI is correct in Google Cloud Console
   - Clear browser cache and try again

2. **OpenAI API Error:**
   - Check environment variables are set correctly
   - Verify API key has sufficient credits

3. **App Not Loading:**
   - Check Streamlit Cloud status
   - Verify all dependencies are in requirements.txt

### Support:

- Check Streamlit Cloud logs for errors
- Monitor OpenAI API usage and limits
- Contact team admin for issues

## Security Notes

- Each user's Google authentication is separate
- Research data is not shared between users
- API keys are stored securely in environment variables
- No sensitive data is logged or stored permanently 