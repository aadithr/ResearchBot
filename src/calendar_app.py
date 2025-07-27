import streamlit as st
import os
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle
import tempfile
import json
from openai import OpenAI
import httpx

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configuration
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Check if deployed
IS_DEPLOYED = os.getenv('STREAMLIT_SERVER_RUNNING_ON_PORT') is not None

def get_google_credentials():
    """Get Google OAuth credentials, handling both local and deployed environments."""
    # Check session state first (for deployed environments)
    if 'google_credentials' in st.session_state:
        try:
            creds = st.session_state['google_credentials']
            if creds and not creds.expired:
                return creds
            elif creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                st.session_state['google_credentials'] = creds
                return creds
        except Exception as e:
            pass
    
    # Check for token file (for local development)
    token_file = 'token.pickle'
    if os.path.exists(token_file):
        with open(token_file, 'rb') as token:
            creds = pickle.load(token)
        
        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                with open(token_file, 'wb') as token:
                    pickle.dump(creds, token)
                return creds
            except Exception as e:
                os.remove(token_file)
    
    # Get OAuth credentials
    creds = None
    if IS_DEPLOYED:
        client_id = os.getenv('GOOGLE_CLIENT_ID')
        client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
        
        if client_id and client_secret:
            credentials_data = {
                "installed": {
                    "client_id": client_id,
                    "project_id": "researchbot",
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "client_secret": client_secret,
                    "redirect_uris": ["https://vcresearchbot.streamlit.app/"]
                }
            }
            
            temp_credentials_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
            json.dump(credentials_data, temp_credentials_file)
            temp_credentials_file.close()
            
            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    temp_credentials_file.name, SCOPES
                )
                
                auth_url, _ = flow.authorization_url(prompt='consent')
                
                st.write("Please go to the following URL to authorize the application:")
                st.markdown(f"[Click here to authorize]({auth_url})")
                
                st.write("After authorization, you'll be redirected back. If you see an error page, copy the 'code' parameter from the URL and paste it below.")
                
                query_params = st.experimental_get_query_params()
                code = query_params.get('code', [None])[0]
                
                if not code:
                    code = st.text_input("Enter the authorization code from the URL (if needed):")
                
                if code:
                    try:
                        flow.fetch_token(code=code)
                        creds = flow.credentials
                        st.session_state['google_credentials'] = creds
                        st.success("✅ Google authentication successful!")
                        return creds
                    except Exception as e:
                        st.error(f"Failed to exchange code for credentials: {e}")
                        return None
                else:
                    st.warning("Please complete the authorization process first.")
                    return None
                    
            finally:
                try:
                    os.unlink(temp_credentials_file.name)
                except:
                    pass
        else:
            st.error("Google OAuth credentials not found in environment variables.")
            return None
    else:
        if os.path.exists('credentials.json'):
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
            
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
            
            return creds
        else:
            st.error("credentials.json not found. Please download it from Google Cloud Console.")
            return None

def get_calendar_events(service, date):
    """Fetch calendar events for a specific date."""
    start_time = datetime.combine(date, datetime.min.time()).isoformat() + 'Z'
    end_time = datetime.combine(date, datetime.max.time()).isoformat() + 'Z'
    
    events_result = service.events().list(
        calendarId='primary',
        timeMin=start_time,
        timeMax=end_time,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    
    return events_result.get('items', [])

def analyze_founders(attendees, event_title):
    """Analyze attendees to identify founders using OpenAI."""
    if not attendees:
        return []
    
    client = OpenAI(
        api_key=OPENAI_API_KEY,
        http_client=httpx.Client(
            verify=False,
            timeout=30.0
        )
    )
    
    attendee_info = []
    for attendee in attendees:
        name = attendee.get('displayName', attendee.get('email', 'Unknown'))
        email = attendee.get('email', '')
        attendee_info.append(f"Name: {name}, Email: {email}")
    
    attendee_text = "\n".join(attendee_info)
    
    prompt = f"""
    Analyze the following meeting attendees and identify if any are founders, CEOs, or key executives of companies.
    
    Meeting: {event_title}
    Attendees:
    {attendee_text}
    
    For each person who appears to be a founder/executive, provide:
    1. Their name
    2. Their company name (if identifiable from email domain or context)
    3. Their role (Founder, CEO, CTO, etc.)
    4. Confidence level (High/Medium/Low)
    
    If no founders/executives are identified, respond with "No founders identified."
    
    Format your response as a clear list.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.3
        )
        
        result = response.choices[0].message.content
        return result
    except Exception as e:
        st.error(f"OpenAI API error: {e}")
        return f"Error analyzing event: {e}"

def check_available_models():
    """Check which models are available with the current API key."""
    client = OpenAI(
        api_key=OPENAI_API_KEY,
        http_client=httpx.Client(
            verify=False,
            timeout=30.0
        )
    )
    
    try:
        models = client.models.list()
        available_models = [model.id for model in models.data]
        
        deep_research_available = any('deep-research' in model for model in available_models)
        o4_mini_deep_research_available = any('o4-mini-deep-research' in model for model in available_models)
        o4_mini_available = 'o4-mini' in available_models
        o4_available = any('o4' in model for model in available_models)
        
        return deep_research_available, o4_mini_deep_research_available, o4_mini_available, o4_available
        
    except Exception as e:
        return False, False, False, False

def run_openai_deep_research(company_name, website, linkedin, founder_linkedin, key_questions):
    """Run deep research using OpenAI's models with web search capabilities."""
    client = OpenAI(
        api_key=OPENAI_API_KEY,
        http_client=httpx.Client(
            verify=False,
            timeout=120.0
        )
    )
    
    deep_research_available, o4_mini_deep_research_available, o4_mini_available, o4_available = check_available_models()
    
    system_message = """You are a senior technical VC analyst conducting deep due diligence on early-stage companies. 
    
    Formatting re-enabled
    
    Provide a comprehensive, data-driven analysis in markdown format with the following structure:
    
    1. **Depth and Nature of Pain Point** - Quantify the problem with specific data
    2. **Market Headwinds & Tailwinds** - Industry trends and external factors
    3. **Competitive Landscape** - Direct and indirect competitors with funding/valuation data
    4. **Product Deep-Dive** - Technical capabilities and differentiation
    5. **Market Size & Dynamics** - TAM/SAM/SOM with growth projections
    6. **Go-To-Market (GTM) Strategy** - Sales motion, partnerships, pricing
    7. **Key Questions for Management** - Critical due diligence questions
    8. **Key Risks** - Technology, market, execution, competitive risks
    9. **Long-Term Moat** - Sustainable competitive advantages
    
    Use specific data points, citations, and market research. Include funding rounds, valuations, customer testimonials, and competitive analysis.
    
    Format as clean markdown with proper headers, bullet points, and citations."""
    
    user_message = f"""
    Company: {company_name}
    Website: {website}
    Company LinkedIn: {linkedin}
    Founder LinkedIn: {founder_linkedin}
    Key Questions: {key_questions}
    
    Conduct comprehensive due diligence research on this company. Use web search to find the most current and accurate information about their business model, market position, funding, team, and competitive landscape.
    """
    
    models_to_try = []
    
    if o4_mini_deep_research_available:
        o4_mini_deep_research_models = [model for model in client.models.list().data if 'o4-mini-deep-research' in model.id]
        if o4_mini_deep_research_models:
            models_to_try.append((o4_mini_deep_research_models[0].id, "o4-mini-deep-research"))
    
    if deep_research_available:
        models_to_try.append(("gpt-4o-deep-research", "Deep Research API"))
    
    if o4_mini_available:
        models_to_try.append(("o4-mini", "o4-mini"))
    
    if o4_available and not o4_mini_available:
        o4_models = [model for model in client.models.list().data if 'o4' in model.id]
        if o4_models:
            models_to_try.append((o4_models[0].id, f"o4 model: {o4_models[0].id}"))
    
    if not models_to_try:
        st.error("❌ No suitable models available with your API key")
        return None
    
    for model_id, model_name in models_to_try:
        try:
            st.write(f"Trying {model_name} for {company_name}...")
            
            if 'deep-research' in model_id:
                response = client.beta.chat.completions.create(
                    model=model_id,
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": user_message}
                    ],
                    max_completion_tokens=20000
                )
            else:
                response = client.chat.completions.create(
                    model=model_id,
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": user_message}
                    ],
                    max_completion_tokens=20000
                )
            
            result = response.choices[0].message.content
            st.success(f"✅ {model_name} call succeeded for {company_name}")
            return result
            
        except Exception as e:
            st.warning(f"⚠️ {model_name} failed: {str(e)}")
            continue
    
    st.error("❌ All available models failed")
    return None

def main():
    st.title("Google Calendar Meeting Research Assistant")
    st.write("Authenticate with Google, pick a date, and see your meetings and attendees. Founders will be identified automatically using OpenAI.")
    st.write("After reviewing and editing all enrichment fields, press 'Run Deep Research' to start research. You can edit all details before running research.")
    
    with st.sidebar:
        st.header("User Setup")
        user_id = st.text_input(
            "Enter your name:",
            placeholder="e.g., John, Sarah, Alex",
            help="This helps track your research sessions"
        )
        
        if user_id:
            st.success(f"Welcome, {user_id}!")
            st.button("Start", help="Click to begin using the app")
        else:
            st.info("Please enter your name in the sidebar to continue.")
            return
        
        st.markdown("---")
        st.header("Authentication")
        
        if st.button("🔄 Re-authenticate with Google", help="Clear stored credentials and login again"):
            if 'google_credentials' in st.session_state:
                del st.session_state['google_credentials']
            
            if os.path.exists('token.pickle'):
                os.remove('token.pickle')
            
            st.success("✅ Credentials cleared! Please refresh the page to login again.")
            st.info("💡 Tip: This is perfect for recording demo videos!")
            st.stop()
    
    creds = get_google_credentials()
    if not creds:
        st.error("Please complete Google authentication first.")
        return
    
    service = build('calendar', 'v3', credentials=creds)
    
    selected_date = st.date_input("Select a date", value=datetime.now())
    
    if st.button("Fetch Meetings and Analyze Founders"):
        st.info("Fetching meetings and analyzing founders...")
        
        events = get_calendar_events(service, selected_date)
        st.write(f"Found {len(events)} events for {selected_date}")
        
        if not events:
            st.info("No events found for this date.")
            return
        
        st.write("Analyzing founders with OpenAI...")
        all_founders = []
        
        for event in events:
            event_title = event.get('summary', 'Untitled Event')
            attendees = event.get('attendees', [])
            
            st.write(f"Processing event: {event_title}")
            
            if attendees:
                analysis = analyze_founders(attendees, event_title)
                st.write(analysis)
                
                if "founder" in analysis.lower() or "ceo" in analysis.lower():
                    all_founders.append({
                        'name': event_title,
                        'analysis': analysis
                    })
        
        st.success("Analysis complete!")
    
    st.header("Deep Research")
    st.write("Review and edit the information below, then run deep research.")
    
    research_data = {
        'company_name': 'Witness.ai',
        'website': 'https://witness.ai/',
        'linkedin': '',
        'founder_linkedin': 'N/A',
        'key_questions': "What's the long term moat of this company"
    }
    
    with st.expander("Company Information", expanded=True):
        company_name = st.text_input("Company Name", value=research_data['company_name'])
        website = st.text_input("Website", value=research_data['website'])
        linkedin = st.text_input("Company LinkedIn", value=research_data['linkedin'])
        founder_linkedin = st.text_input("Founder(s) LinkedIn", value=research_data['founder_linkedin'])
        key_questions = st.text_area("Key Questions", value=research_data['key_questions'])
    
    st.subheader("Review Your Selections:")
    st.write(f"**Company:** {company_name}")
    st.write(f"**Name:** {company_name}")
    st.write(f"**Website:** {website}")
    st.write(f"**Company LinkedIn:** {linkedin}")
    st.write(f"**Founder(s) LinkedIn:** {founder_linkedin}")
    st.write(f"**Key Questions:** {key_questions}")
    
    st.write("Review details in the expanders above. When ready, click below.")
    
    if st.button("Run Deep Research"):
        if company_name and website:
            result = run_openai_deep_research(
                company_name, website, linkedin, founder_linkedin, key_questions
            )
            
            if result:
                st.markdown("## Deep Research Result")
                st.markdown(result, unsafe_allow_html=True)
            else:
                st.error("Failed to complete deep research. Please try again.")
        else:
            st.warning("Please provide at least a company name and website.")

if __name__ == "__main__":
    main() 