Certainly! Here’s a **detailed, step-by-step plan** for your new app, with a focus on deep, context-aware founder identification using OpenAI, and a modern, user-friendly workflow.

---

# **Detailed Plan: Founder/Company Research Assistant from Google Calendar**

---

## **1. Google Calendar Integration**

### 1.1. User Authentication
- Use **Google OAuth2** to authenticate the user.
- Request permissions for read-only access to the user’s calendar events.

### 1.2. Date Selection
- Provide a **calendar picker UI** (default: today).
- User can select any date to view meetings for that day.

### 1.3. Fetch Events
- Use the **Google Calendar API** to fetch all events for the selected date.
- For each event, extract:
  - Event title
  - Start/end time
  - Description (if any)
  - Organizer info
  - Attendee emails and names (if available)
  - Location/meeting link

---

## **2. Deep Founder & Company Identification (OpenAI Reasoning)**

### 2.1. Gather Context for Each Event
- For each event, collect:
  - Event title
  - Attendee emails and names
  - Organizer info
  - Description
  - Any other metadata

### 2.2. OpenAI Prompting for Founder/Company Identification
- For each event, **construct a detailed prompt** for OpenAI:
  - Instruct the model to “think step by step” and use all available context.
  - Ask the model to:
    - Identify which attendee(s) are likely founders.
    - Identify the company each founder is building.
    - Justify its reasoning for each identification.
    - Output a structured JSON or table with:
      - Attendee name/email
      - Is founder? (Y/N)
      - Company name (if identified)
      - Reasoning/explanation

#### **Sample Prompt:**
> Here is a meeting from my calendar:
> - Title: "Catch up with John Doe (AcmeAI)"
> - Attendees: John Doe (john@acmeai.com), Jane Smith (jane@vcfirm.com)
> - Organizer: Jane Smith
> - Description: "Intro to AcmeAI, John is the founder"
>
> Please think step by step and, for each attendee, tell me:
> - Are they a founder? (Y/N)
> - What company are they building (if any)?
> - Your reasoning for each answer.

### 2.3. Parse and Store Results
- Parse OpenAI’s response for each event.
- Store:
  - Attendee info
  - Founder/company status
  - Reasoning

---

## **3. Interim Review & Enrichment UI**

### 3.1. Display Meetings and Attendees
- Show a **dashboard/table** for the selected date:
  - Each meeting as a row/card
  - For each attendee: name, email, founder/company status, reasoning

### 3.2. User Enrichment
- For each attendee/company, allow the user to:
  - **Edit/add:**
    - LinkedIn URL
    - Decks (file upload or link)
    - Notes (free text)
- Optionally, allow the user to **exclude** certain meetings/attendees from research.

### 3.3. Save Enriched Data
- Store all user-provided enrichment for use in the next step.

---

## **4. Deep Research Automation (Perplexity)**

### 4.1. Generate Research Prompts
- For each identified founder/company, use your **existing prompt generator** to create a deep research prompt.
- Incorporate all available info (name, company, LinkedIn, notes, etc.).

### 4.2. Perplexity Automation
- For each prompt:
  - Use Playwright/browser-use to automate Perplexity (Deep Research mode).
  - Submit the prompt, handle any CAPTCHAs or login as needed.
  - Scrape and store the research results.

### 4.3. Track Progress
- Show progress/status for each research job in the UI.

---

## **5. Results & Export**

### 5.1. Results Dashboard
- Display a **summary dashboard** for the selected date:
  - Meetings, founders, companies, research results, notes, decks, etc.
  - Allow user to review all information in one place.

### 5.2. Export/Share
- Allow user to **export** results as:
  - PDF (nicely formatted report)
  - CSV/Excel (for further analysis)
  - Copy to clipboard

---

## **6. Tech Stack & Architecture**

- **Frontend:** Streamlit (for rapid UI, file uploads, calendar picker, etc.)
- **Backend:** Python (FastAPI or Flask, if needed for async/background jobs)
- **APIs:**  
  - Google Calendar API (for events)
  - OpenAI API (for founder/company reasoning)
  - Perplexity (via browser automation)
- **Storage:** Local files or lightweight DB (for user enrichment, session, and results)
- **Authentication:** Google OAuth2

---

## **7. Optional Enhancements**

- **Multi-calendar support** (if user has several Google accounts/calendars)
- **Recurring meeting handling**
- **Automatic LinkedIn lookup for attendees**
- **Integration with other research sources (Crunchbase, LinkedIn, etc.)**
- **Team sharing/collaboration features**

---

## **Summary Flow**

1. **User logs in with Google**
2. **User selects a date**
3. **App fetches meetings and attendees**
4. **OpenAI deeply reasons about founders/companies**
5. **User reviews and enriches data**
6. **App runs Perplexity deep research for each**
7. **Results are displayed and can be exported**

---

**Ready to start with Google Calendar authentication and event fetching? Or would you like a sample OpenAI prompt for the founder identification step?**