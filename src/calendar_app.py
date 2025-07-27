import streamlit as st
import datetime
import os
import pickle
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import openai
import json
from prompt_generator import generate_founder_identification_prompt, generate_research_prompt
from dotenv import load_dotenv
import requests
from openai import OpenAI

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
CREDENTIALS_FILE = 'credentials.json'  # You must provide this from Google Cloud Console
TOKEN_FILE = 'token.pickle'

# Check if we're in a deployed environment
IS_DEPLOYED = os.getenv('STREAMLIT_SERVER_RUNNING', False)

# Load environment variables - supports both .env file and deployment environment variables
load_dotenv(dotenv_path=os.path.join('config', '.env'))
PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Support for multiple OAuth configurations
def get_oauth_config():
    """Get OAuth configuration - always use the main credentials"""
    # Use the main OAuth credentials for everyone
    # Each user will authenticate with their own Google account
    client_id = os.getenv('GOOGLE_CLIENT_ID')
    client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
    
    return client_id, client_secret

def admin_oauth_setup():
    """Admin interface for managing team OAuth credentials"""
    st.markdown("### 🔧 Admin: Team OAuth Setup")
    st.info("Add team members' Google OAuth credentials here. They only need to do this once.")
    
    # Load existing team config
    team_config = st.session_state.get('team_oauth_config', {})
    
    with st.form("add_team_member"):
        member_name = st.text_input("Team Member Name:", placeholder="e.g., John Doe")
        client_id = st.text_input("Google Client ID:", placeholder="xxx.apps.googleusercontent.com")
        client_secret = st.text_input("Google Client Secret:", placeholder="GOCSPX-...", type="password")
        
        if st.form_submit_button("Add Team Member"):
            if member_name and client_id and client_secret:
                team_config[member_name] = {
                    'client_id': client_id,
                    'client_secret': client_secret
                }
                st.session_state.team_oauth_config = team_config
                st.success(f"Added {member_name} to team configuration!")
                st.rerun()
            else:
                st.error("Please fill in all fields")
    
    # Display current team members
    if team_config:
        st.markdown("#### Current Team Members:")
        for name, config in team_config.items():
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.write(f"**{name}**")
            with col2:
                st.write("✅ Configured")
            with col3:
                if st.button(f"Remove {name}", key=f"remove_{name}"):
                    del team_config[name]
                    st.session_state.team_oauth_config = team_config
                    st.rerun()
    
    # Instructions for team members
    st.markdown("---")
    st.markdown("#### 📋 Instructions for Team Members:")
    st.markdown("""
    1. **Ask each team member for their Google OAuth credentials**
    2. **Add them above using the form**
    3. **Team members just need to:**
       - Enter their name in the sidebar
       - Complete Google OAuth once
       - Start using the app!
    """)



EXCLUDE_EMAILS = ['96aadith@gmail.com']
EXCLUDE_DOMAINS = ['@peakxv.com']

# --- Google Calendar and OpenAI logic (unchanged) ---
def get_google_credentials():
    st.write("=== get_google_credentials() called ===")
    # Check for token in session state first (for deployed environments)
    st.write("Checking session state for credentials...")
    if 'google_creds' in st.session_state:
        st.write("Found credentials in session state")
        creds = st.session_state.google_creds
        if creds and creds.valid:
            st.write("Session state credentials are valid")
            return creds
        else:
            st.write("Session state credentials are invalid")
    else:
        st.write("No credentials found in session state")
    
    # Check for token file (for local development)
    st.write(f"Checking for token file: {TOKEN_FILE}")
    st.write(f"Token file exists: {os.path.exists(TOKEN_FILE)}")
    
    creds = None
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, 'rb') as token:
                creds = pickle.load(token)
            st.write(f"Token file found and loaded: {TOKEN_FILE}")
        except Exception as e:
            st.error(f"Error loading token file: {e}")
            if os.path.exists(TOKEN_FILE):
                os.remove(TOKEN_FILE)
            creds = None
    else:
        st.write("No token file found, will need to authenticate")
    
    if not creds or not creds.valid:
        if creds:
            st.write(f"Token found but invalid. Expired: {creds.expired}, Has refresh token: {creds.refresh_token}")
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                st.success("Token refreshed successfully!")
            except Exception as e:
                st.error(f"Token refresh failed: {e}")
                # Remove invalid token file
                if os.path.exists(TOKEN_FILE):
                    os.remove(TOKEN_FILE)
                creds = None
        
        if not creds:
            try:
                # Determine redirect URI based on environment
                # Always use the deployed URL for Streamlit Cloud
                redirect_uri = "https://vcresearchbot.streamlit.app/"
                
                # Check if credentials file exists
                if not os.path.exists(CREDENTIALS_FILE):
                    st.error("Google OAuth credentials not found.")
                    st.info("For deployment, credentials need to be configured as environment variables.")
                    
                    # Try to get credentials from environment variables
                    client_id, client_secret = get_oauth_config()
                    
                    if client_id and client_secret:
                        st.success("Found Google OAuth credentials in environment variables!")
                        
                        # Create temporary credentials file
                        import tempfile
                        import json
                        
                        credentials_dict = {
                            "web": {
                                "client_id": client_id,
                                "client_secret": client_secret,
                                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                                "token_uri": "https://oauth2.googleapis.com/token",
                                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                                "redirect_uris": ["http://localhost", "https://vcresearchbot.streamlit.app/"]
                            }
                        }
                        
                        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                            json.dump(credentials_dict, f)
                            temp_credentials_file = f.name
                        
                        # Use temporary file
                        credentials_file_to_use = temp_credentials_file
                    else:
                        st.error("Google OAuth credentials not configured.")
                        st.info("""
                        **For Team Usage:**
                        - Contact your administrator to set up Google OAuth
                        - Once configured, team members just need to:
                          - Enter their name
                          - Login with their Google account
                          - Start using the app!
                        """)
                        return None
                else:
                    # Use regular credentials file
                    credentials_file_to_use = CREDENTIALS_FILE
                    temp_credentials_file = None
                
                # Create OAuth flow
                try:
                    flow = Flow.from_client_secrets_file(
                        credentials_file_to_use, SCOPES,
                        redirect_uri=redirect_uri)
                except Exception as e:
                    st.error(f"Failed to create OAuth flow: {e}")
                    # Clean up temp file if it exists
                    if 'temp_credentials_file' in locals() and temp_credentials_file and os.path.exists(temp_credentials_file):
                        os.unlink(temp_credentials_file)
                    return None
                
                # Show authorization URL
                auth_url, _ = flow.authorization_url(prompt='consent')
                st.info(f"Please go to the following URL to authorize the application:")
                st.markdown(f"[**Click here to authorize**]({auth_url})")
                st.info("After authorization, you'll be redirected back. If you see an error page, copy the 'code' parameter from the URL and paste it below.")
                
                # Try to extract code from URL parameters automatically
                import urllib.parse
                query_params = st.experimental_get_query_params()
                code = query_params.get('code', [None])[0]
                
                if not code:
                    code = st.text_input("Enter the authorization code from the URL (if needed):")
                else:
                    st.success("Authorization code found in URL!")
                if code:
                    try:
                        st.write("Processing authorization code...")
                        flow.fetch_token(code=code)
                        creds = flow.credentials
                        st.write("Token fetched successfully, saving to session state...")
                        
                        # Save to session state (for deployed environments)
                        st.session_state.google_creds = creds
                        st.write("Token saved to session state")
                        
                        # Try to save to file as well (for local development)
                        try:
                            with open(TOKEN_FILE, 'wb') as token:
                                pickle.dump(creds, token)
                            st.write(f"Token also saved to file: {TOKEN_FILE}")
                        except Exception as file_error:
                            st.write(f"Could not save to file (expected in deployment): {file_error}")
                        
                        st.success("Authentication successful! Token saved to session.")
                        # Clean up temp file if it exists
                        if 'temp_credentials_file' in locals() and temp_credentials_file and os.path.exists(temp_credentials_file):
                            os.unlink(temp_credentials_file)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error saving token: {e}")
                        st.write(f"Current working directory: {os.getcwd()}")
                        st.write(f"Can write to current directory: {os.access('.', os.W_OK)}")
                        return None
                else:
                    st.warning("Please complete the authorization process first.")
                    # Clean up temp file if it exists
                    if 'temp_credentials_file' in locals() and temp_credentials_file and os.path.exists(temp_credentials_file):
                        os.unlink(temp_credentials_file)
                    return None
            except Exception as e:
                st.error(f"Authentication failed: {e}")
                # Clean up temp file if it exists
                if 'temp_credentials_file' in locals() and temp_credentials_file and os.path.exists(temp_credentials_file):
                    os.unlink(temp_credentials_file)
                return None
    return creds

def fetch_events(service, calendar_id, date):
    start = datetime.datetime.combine(date, datetime.time.min).isoformat() + 'Z'
    end = datetime.datetime.combine(date, datetime.time.max).isoformat() + 'Z'
    events_result = service.events().list(
        calendarId=calendar_id, timeMin=start, timeMax=end,
        singleEvents=True, orderBy='startTime').execute()
    return events_result.get('items', [])

def filter_attendees(attendees):
    filtered = []
    for a in attendees:
        email = a.get('email', '').lower()
        if email in EXCLUDE_EMAILS:
            continue
        if any(email.endswith(domain) for domain in EXCLUDE_DOMAINS):
            continue
        filtered.append(a)
    return filtered

def analyze_founders(event):
    attendees = filter_attendees(event.get('attendees', []))
    if not attendees:
        return []
    
    attendees_for_prompt = [
        {'name': a.get('displayName', ''), 'email': a.get('email', '')}
        for a in attendees
    ]
    organizer = event.get('organizer', {})
    organizer_info = {
        'name': organizer.get('displayName', ''),
        'email': organizer.get('email', '')
    } if organizer else None
    
    prompt = generate_founder_identification_prompt(
        event_title=event.get('summary', '(No Title)'),
        attendees=attendees_for_prompt,
        organizer=organizer_info,
        description=event.get('description', '')
    )
    
    try:
        # Debug: Show what we're sending to OpenAI
        st.write(f"Calling OpenAI with {len(attendees_for_prompt)} attendees...")
        
        # Use the same client instance as the research function
        import httpx
        client = OpenAI(
            api_key=OPENAI_API_KEY,
            http_client=httpx.Client(
                verify=False,  # Disable SSL verification to bypass certificate issues
                timeout=30.0
            )
        )
        
        # Add timeout to prevent hanging
        import time
        start_time = time.time()
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
            temperature=0.2
        )
        
        elapsed_time = time.time() - start_time
        st.write(f"OpenAI response received in {elapsed_time:.2f} seconds")
        
        content = response.choices[0].message.content
        st.write(f"OpenAI response: {content[:200]}...")  # Show first 200 chars
        
        # Try to extract JSON from the response
        json_start = content.find('[')
        json_end = content.rfind(']') + 1
        if json_start != -1 and json_end != -1:
            json_str = content[json_start:json_end]
            result = json.loads(json_str)
            st.write(f"Successfully parsed {len(result)} founder entries")
            return result
        else:
            st.warning("Could not find JSON array in OpenAI response")
            return []
    except Exception as e:
        st.error(f"OpenAI API error: {str(e)}")
        return [{"error": str(e)}]

def run_openai_deep_research(prompt, model="o4-mini"):
    system_message = (
        "Formatting re-enabled\n"
        "You are a professional researcher preparing a structured, data-driven report on behalf of a venture capital team. "
        "Please answer in markdown format with clear headings, bullet points, and tables where appropriate. "
        "Your task is to analyze the company and founder(s) described in the prompt. "
        "Focus on data-rich insights, include specific figures, trends, statistics, and measurable outcomes. "
        "Prioritize reliable, up-to-date sources and include inline citations and return all source metadata. "
        "Be analytical, avoid generalities, and ensure that each section supports data-backed reasoning that could inform investment decisions."
    )
    
    import httpx
    client = OpenAI(
        api_key=OPENAI_API_KEY,
        http_client=httpx.Client(
            verify=False,  # Disable SSL verification to bypass certificate issues
            timeout=120.0  # Increased timeout for deep research
        )
    )
    
    try:
        # Try the deep research API first
        response = client.responses.create(
            model=model,
            input=[
                {
                    "role": "developer",
                    "content": [
                        {"type": "input_text", "text": system_message}
                    ]
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt}
                    ]
                }
            ],
            reasoning={"summary": "auto"},
            tools=[{"type": "web_search_preview"}]
        )
        # Return the main text output
        return response.output[-1].content[0].text
    except Exception as e:
        # Fallback to o4-mini chat completion if deep research fails
        try:
            fallback_prompt = f"{system_message}\n\nResearch Request:\n{prompt}"
            response = client.chat.completions.create(
                model="o4-mini",
                messages=[{"role": "user", "content": fallback_prompt}],
                max_completion_tokens=40000
            )
            return f"⚠️ Deep Research API failed, using o4-mini fallback.\n\n{response.choices[0].message.content}"
        except Exception as fallback_error:
            return f"❌ Both Deep Research API and fallback failed.\n\nDeep Research Error: {str(e)}\nFallback Error: {str(fallback_error)}"

def main():
    st.title("Google Calendar Meeting Research Assistant")
    st.write("Authenticate with Google, pick a date, and see your meetings and attendees. Founders will be identified automatically using OpenAI.")
    st.info("After reviewing and editing all enrichment fields, press 'Run Deep Research' to start research. You can edit all details before running research.")
    
    # Test OpenAI API key
    st.write(f"OPENAI_API_KEY loaded: {OPENAI_API_KEY is not None}")
    
    # Try multiple ways to get the API key
    api_key_from_env = os.getenv('OPENAI_API_KEY')
    st.write(f"API key from os.getenv: {api_key_from_env is not None}")
    
    if OPENAI_API_KEY:
        st.write(f"API key length: {len(OPENAI_API_KEY)}")
        st.write(f"API key starts with: {OPENAI_API_KEY[:10]}...")
        st.write(f"API key ends with: ...{OPENAI_API_KEY[-10:]}")
        st.write(f"API key contains spaces: {' ' in OPENAI_API_KEY}")
        st.write(f"API key contains newlines: {'\\n' in OPENAI_API_KEY}")
        st.write(f"API key contains tabs: {'\\t' in OPENAI_API_KEY}")
        
        # Try cleaning the API key
        cleaned_key = OPENAI_API_KEY.strip()
        st.write(f"Cleaned key length: {len(cleaned_key)}")
        
        try:
            import httpx
            test_client = OpenAI(
                api_key=cleaned_key,  # Use cleaned key
                http_client=httpx.Client(
                    verify=False,  # Disable SSL verification
                    timeout=30.0
                )
            )
            # First try to list available models
            try:
                models = test_client.models.list()
                st.write(f"Available models: {len(models.data)} models")
                for model in models.data[:5]:  # Show first 5 models
                    st.write(f"- {model.id}")
            except Exception as model_error:
                st.write(f"Could not list models: {model_error}")
            
            # Try with gpt-4o-mini which should work with most API keys
            response = test_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            st.success("✅ OpenAI API key is valid!")
        except Exception as e:
            error_msg = str(e)
            st.error(f"❌ OpenAI API key error: {error_msg}")
            
            if "401" in error_msg:
                st.info("401 error: API key might be invalid or expired")
            elif "429" in error_msg:
                st.info("429 error: Rate limit exceeded")
            elif "500" in error_msg:
                st.info("500 error: OpenAI server issue")
            else:
                st.info("Please check your API key in Streamlit Cloud secrets")
    else:
        st.error("❌ OPENAI_API_KEY not found in environment variables")

    # User identification for team usage
    if 'user_id' not in st.session_state:
        with st.sidebar:
            st.markdown("### 👋 Welcome!")
            st.info("Enter your name to get started. This helps track your research sessions.")
            user_id = st.text_input("Your name:", placeholder="e.g., John, Sarah, Alex")
            if st.button("Start"):
                if user_id.strip():
                    st.session_state.user_id = user_id.strip()
                    st.rerun()
                else:
                    st.error("Please enter your name")
    
    if 'user_id' not in st.session_state:
        st.warning("Please enter your name in the sidebar to continue.")
        st.stop()

    if not OPENAI_API_KEY:
        st.error("OPENAI_API_KEY environment variable not set.")
        st.stop()

    # Display user info
    with st.sidebar:
        st.markdown(f"**Welcome, {st.session_state.user_id}!**")
        if st.button("Change Name"):
            del st.session_state.user_id
            st.rerun()
        


    creds = get_google_credentials()
    if not creds:
        st.warning("Please complete Google authentication first.")
        st.stop()
    elif not creds.valid:
        st.error("Google credentials are invalid. Please re-authenticate.")
        st.stop()

    service = build('calendar', 'v3', credentials=creds)
    calendar_id = 'primary'

    today = datetime.date.today()
    date = st.date_input("Select a date", value=today)

    # Use session_state to persist enrichment data
    if 'enrichment_data' not in st.session_state:
        st.session_state['enrichment_data'] = []
    
    col1, col2 = st.columns([1,1])
    with col1:
        if st.button("Fetch Meetings and Analyze Founders"):
            try:
                with st.spinner("Fetching meetings and analyzing founders..."):
                    # Logic to fetch and analyze
                    calendar_enrichment_data = []
                    
                    # Debug: Check if service is working
                    st.info("Testing Google Calendar connection...")
                    events = fetch_events(service, calendar_id, date)
                    st.success(f"Found {len(events)} events for {date}")
                    
                    if not events:
                        st.write("No meetings found for this date.")
                    else:
                        st.info("Analyzing founders with OpenAI...")
                        for event_idx, event in enumerate(events):
                            st.write(f"Processing event: {event.get('summary', '(No Title)')}")
                            results = analyze_founders(event)
                            if results:
                                for founder_idx, r in enumerate(results):
                                    if 'error' in r:
                                        st.error(f"Error analyzing event: {r['error']}")
                                        continue
                                    
                                    enrich = {
                                        'event_title': event.get('summary', '(No Title)'),
                                        'event_time': event.get('start', {}).get('dateTime', event.get('start', {}).get('date', '')),
                                        'name': r.get('name', ''),
                                        'email': r.get('email', ''),
                                        'company': r.get('company', ''),
                                        'is_founder': r.get('is_founder', ''),
                                        'reasoning': r.get('reasoning', ''),
                                        'company_website': '', 'company_linkedin': '', 'founders_linkedin': [],
                                        'key_questions': [], 'deck_url': '', 'deck_file': None, 'notes': '',
                                        'exclude': False, 'key': f"event{event_idx}_founder{founder_idx}"
                                    }
                                    calendar_enrichment_data.append(enrich)
                    st.session_state['enrichment_data'] = calendar_enrichment_data
                    st.success("Analysis complete!")
            except Exception as e:
                st.error(f"Error fetching meetings: {str(e)}")
                st.exception(e)
            st.rerun()

    with col2:
        if st.button("Add Manual Research Target"):
            manual_key = f"manual_{datetime.datetime.now().timestamp()}"
            new_entry = {
                'key': manual_key, 'name': '', 'company': '', 'reasoning': 'Manually added.',
                'company_website': '', 'company_linkedin': '', 'founders_linkedin': [],
                'key_questions': [], 'deck_url': '', 'deck_file': None, 'notes': '', 'exclude': False
            }
            st.session_state.enrichment_data.insert(0, new_entry)
            st.rerun()

    # --- UI Rendering Section ---
    if st.session_state['enrichment_data']:
        updated_enrichment_data = []
        for r in st.session_state['enrichment_data']:
            founder_key = r['key']
            
            expander_title = f"Enrich: {r.get('name') or 'New Founder'} | Company: {r.get('company') or 'New Company'}"

            with st.expander(expander_title, expanded=(not r.get('company'))):
                # Create a mutable copy to update
                updated_entry = r.copy()
                
                if r.get('reasoning') != 'Manually added.':
                    st.write(f"Reasoning: {r.get('reasoning', '')}")

                updated_entry['company'] = st.text_input("Company Name", value=r.get('company', ''), key=f"company_{founder_key}")
                updated_entry['name'] = st.text_input("Founder(s) Name(s)", value=r.get('name', ''), key=f"name_{founder_key}")
                
                updated_entry['company_website'] = st.text_input(f"Company Website", value=r.get('company_website', ''), key=f"website_{founder_key}")
                updated_entry['company_linkedin'] = st.text_input(f"Company LinkedIn", value=r.get('company_linkedin', ''), key=f"clinkedin_{founder_key}")
                
                founder_linkedins_str = "\n".join(r.get('founders_linkedin', []))
                founder_linkedins_area = st.text_area(f"Founder(s) LinkedIn (one per line)", value=founder_linkedins_str, key=f"flinkedin_{founder_key}")
                updated_entry['founders_linkedin'] = [l.strip() for l in founder_linkedins_area.splitlines() if l.strip()]
                
                key_questions_str = "\n".join(r.get('key_questions', []))
                key_questions_area = st.text_area(f"Key Research Questions (one per line)", value=key_questions_str, key=f"questions_{founder_key}")
                updated_entry['key_questions'] = [q.strip() for q in key_questions_area.splitlines() if q.strip()]

                updated_entry['deck_url'] = st.text_input(f"Deck URL (optional)", value=r.get('deck_url', ''), key=f"deckurl_{founder_key}")
                
                deck_file = st.file_uploader(f"Upload Deck (optional)", key=f"deckfile_{founder_key}")
                updated_entry['deck_file'] = deck_file.name if deck_file else r.get('deck_file')

                updated_entry['notes'] = st.text_area(f"Notes (optional)", value=r.get('notes', ''), key=f"notes_{founder_key}")
                updated_entry['exclude'] = st.checkbox(f"Exclude from research", value=r.get('exclude', False), key=f"exclude_{founder_key}")
                
                updated_enrichment_data.append(updated_entry)

        st.session_state['enrichment_data'] = updated_enrichment_data

    # --- Review and Research Section ---
    enrichment_data = st.session_state.get('enrichment_data', [])
    included = [e for e in enrichment_data if not e.get('exclude')]

    if enrichment_data:
        if included:
            st.success(f"{len(included)} founders/companies ready for deep research.")
            
            with st.container(border=True):
                st.markdown("#### Review Your Selections:")
                for entry in included:
                    st.markdown(f"**Company:** {entry.get('company', 'N/A')}")
                    st.markdown(f"**Name:** {entry.get('name', 'N/A')}")
                    st.markdown(f"**Website:** {entry.get('company_website', 'N/A')}")
                    st.markdown(f"**Company LinkedIn:** {entry.get('company_linkedin', 'N/A')}")
                    st.markdown(f"**Founder(s) LinkedIn:** {', '.join(entry.get('founders_linkedin', [])) or 'N/A'}")
                    st.markdown(f"**Key Questions:** {', '.join(entry.get('key_questions', [])) or 'N/A'}")
                    st.markdown("---")
                st.info("Review details in the expanders above. When ready, click below.")

            if st.button("Run Deep Research"):
                for entry in included:
                    research_params = {
                        'company_name': entry.get('company', ''),
                        'details': {
                            'company_website': entry.get('company_website', ''),
                            'company_linkedin': entry.get('company_linkedin', ''),
                            'founders_linkedin': entry.get('founders_linkedin', [])
                        },
                        'key_questions': entry.get('key_questions', [])
                    }
                    prompt = generate_research_prompt(research_params)
                    st.info(f"Calling OpenAI Deep Research API for {entry.get('company', '')}...")
                    with st.spinner(f"Running Deep Research for {entry.get('company', '')}..."):
                        try:
                            result = run_openai_deep_research(prompt)
                            st.success(f"OpenAI Deep Research API call succeeded for {entry.get('company', '')}")
                            st.markdown(result, unsafe_allow_html=True)
                        except Exception as e:
                            st.error(f"OpenAI Deep Research API error for {entry.get('company', '')}: {e}")
        else:
            st.warning("No founders/companies selected for research. (All are currently excluded or none were found.)")
    else:
        st.info("Click 'Fetch Meetings' to begin.")

if __name__ == "__main__":
    main() 