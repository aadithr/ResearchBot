import json
from typing import List, Dict, Optional

def generate_founder_identification_prompt(event_title: str, attendees: List[Dict[str, str]], organizer: Optional[Dict[str, str]] = None, description: Optional[str] = None) -> str:
    """
    Generates a detailed prompt for OpenAI to deeply reason about which attendees are founders and what companies they are building, using all available event context.
    Args:
        event_title: The title of the calendar event.
        attendees: List of dicts with keys 'name' and 'email' for each attendee.
        organizer: Optional dict with keys 'name' and 'email' for the organizer.
        description: Optional event description.
    Returns:
        A string prompt for OpenAI.
    """
    attendees_str = "\n".join([
        f"- {a.get('name', '')} <{a.get('email', '')}>" for a in attendees
    ])
    organizer_str = f"{organizer.get('name', '')} <{organizer.get('email', '')}>" if organizer else "(not specified)"
    description_str = description if description else "(none)"
    
    prompt = f"""
You are an expert at analyzing meeting context to identify startup founders and the companies they are building. Please use all available information and think step by step. For each attendee, tell me:
- Are they a founder? (Y/N)
- What company are they building (if any)?
- Your reasoning for each answer.

Here is the meeting context:
- Title: {event_title}
- Organizer: {organizer_str}
- Attendees:\n{attendees_str}
- Description: {description_str}

Please output a JSON array, one object per attendee, with keys: name, email, is_founder (Y/N), company (if any), reasoning.
"""
    return prompt.strip()

def generate_research_prompt(research_params):
    """
    Generates the final research prompt based on the collected user input.

    :param research_params: A dictionary containing company_name, details, and key_questions.
    :return: A string containing the fully formatted research prompt.
    """
    company_name = research_params['company_name']
    details = research_params['details']
    key_questions = research_params['key_questions']

    # Build the initial information block
    info_block = f"Company Name: {company_name}\n"
    if details.get('company_website'):
        info_block += f"Company Website: {details['company_website']}\n"
    if details.get('company_linkedin'):
        info_block += f"Company LinkedIn: {details['company_linkedin']}\n"
    if details.get('founders_linkedin'):
        info_block += "Founder(s) LinkedIn:\n" + "\n".join([f"- {url}" for url in details['founders_linkedin']]) + "\n"

    # Build the user's key questions block
    questions_block = ""
    if key_questions:
        questions_block = "Also, please specifically address the following key questions:\n"
        questions_block += "\n".join([f"- {q}" for q in key_questions])

    # The main prompt template
    prompt = f"""
You are the world's best early-stage technical VC conducting deep research on {company_name}. Your task is to gather concrete, factual information about this specific company and provide actionable insights for investment decision-making.

IMPORTANT: Use web search to find current, factual information about {company_name}. Do not provide generic frameworks or theoretical approaches. Instead, find and analyze real data about this specific company.

Here is the information I have on the company:
---
{info_block.strip()}
---

Please conduct a deep and comprehensive research analysis covering the following areas. For each section, provide specific facts, data, and insights about {company_name}:

1.  **Depth and Nature of Painpoint:** What specific, critical pain point does {company_name}'s product solve? How severe is this pain for its target customers? Find concrete evidence and customer testimonials.

2.  **Market Headwinds and Tailwinds:** What broader market trends are helping or hurting {company_name} specifically? Find recent news, market reports, and industry analysis.

3.  **Competitive Landscape:**
    *   Identify {company_name}'s direct and indirect competitors with specific company names.
    *   Find their funding amounts, scale, and key investors. What is the overall sentiment around them?
    *   Are there any open-source competitors in {company_name}'s space?
    *   If {company_name} or its competitors have open-source offerings, compare their GitHub activity (stars, forks, contributor velocity).

4.  **Product Deep-Dive:**
    *   What does {company_name}'s product do exactly? Find product descriptions, demos, and feature lists.
    *   What is their key differentiation compared to competitors? What is their unique value proposition?

5.  **Market Size and Dynamics:** What is the estimated Total Addressable Market (TAM) for {company_name}'s specific market? Is this market growing, shrinking, or consolidating?

6.  **Go-To-Market (GTM) Strategy:** How is {company_name} acquiring customers? Find evidence of their marketing, sales, and growth strategies.

7.  **Key Questions for Management:** What are the most important questions one should ask {company_name}'s founders to better understand the business and its growth prospects?

8.  **Key Risks:** What are the primary risks associated with {company_name} specifically? Consider technology risk, market risk, execution risk, and competitive risk.

{questions_block}

CRITICAL: Provide specific, factual information about {company_name}. Include company names, funding amounts, dates, and concrete data. Do not give generic advice or frameworks. Use web search to find current information about this specific company.
"""
    return prompt.strip()

if __name__ == '__main__':
    # For testing purposes
    test_params = {
        'company_name': 'SuperStellar AI',
        'details': {
            'company_website': 'https://superstellar.ai',
            'company_linkedin': 'https://linkedin.com/company/superstellar-ai',
            'founders_linkedin': ['https://linkedin.com/in/founder-one', 'https://linkedin.com/in/founder-two']
        },
        'key_questions': [
            'How defensible is their technology?',
            'What is their pricing model and how does it compare to others?'
        ]
    }
    generated_prompt = generate_research_prompt(test_params)
    print("--- Generated Prompt ---")
    print(generated_prompt) 