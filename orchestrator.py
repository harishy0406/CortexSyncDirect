"""
Autonomous Provider Directory Management - Master Orchestrator
A LangGraph-based cyclic workflow for validating healthcare provider data.
"""

from typing import TypedDict, Literal

try:
    from langgraph.graph import StateGraph, END
except ImportError:
    # Fallback for different langgraph versions
    try:
        from langgraph import StateGraph, END
    except ImportError:
        raise ImportError(
            "Could not import StateGraph and END from langgraph. "
            "Please install langgraph: pip install langgraph>=0.0.20"
        )


# ============================================================================
# State Management
# ============================================================================

class AgentState(TypedDict):
    """State object that tracks the workflow progress and data."""
    provider_id: int
    current_db_data: dict
    scraped_data: dict
    discrepancies: list
    confidence_score: int  # 0-100
    status: Literal['pending', 'verified', 'flagged']


# ============================================================================
# Mock Data Providers (Indian Healthcare Providers)
# ============================================================================

def get_mock_provider_data(provider_id: int) -> dict:
    """
    Returns mock provider data based on provider_id.
    Different IDs return different scenarios for testing.
    """
    providers = {
        # High confidence scenarios (>80) - Will be verified
        1001: {
            "db": {
                "id": 1001,
                "name": "Dr. Rajesh Kumar",
                "specialty": "Cardiology",
                "phone": "+91-11-2658-3456",
                "address": "A-123, Green Park",
                "city": "New Delhi",
                "state": "Delhi",
                "zip": "110016",
                "license_number": "MCI/DEL/12345/2010",
                "npi": "9876543210"
            },
            "scraped": {
                "id": 1001,
                "name": "Dr. Rajesh Kumar",
                "specialty": "Cardiology",
                "phone": "+91-11-2658-3456",
                "address": "A-123, Green Park",
                "city": "New Delhi",
                "state": "Delhi",
                "zip": "110016",
                "license_number": "MCI/DEL/12345/2010",
                "npi": "9876543210"
            },
            "confidence": 85  # Perfect match
        },
        1002: {
            "db": {
                "id": 1002,
                "name": "Dr. Priya Sharma",
                "specialty": "Pediatrics",
                "phone": "+91-22-2645-7890",
                "address": "B-456, Bandra West",
                "city": "Mumbai",
                "state": "Maharashtra",
                "zip": "400050",
                "license_number": "MCI/MAH/23456/2012",
                "npi": "8765432109"
            },
            "scraped": {
                "id": 1002,
                "name": "Dr. Priya Sharma",
                "specialty": "Pediatrics",
                "phone": "+91-22-2645-7890",
                "address": "B-456, Bandra West",
                "city": "Mumbai",
                "state": "Maharashtra",
                "zip": "400050",
                "license_number": "MCI/MAH/23456/2012",
                "npi": "8765432109"
            },
            "confidence": 92  # Perfect match
        },
        1003: {
            "db": {
                "id": 1003,
                "name": "Dr. Amit Patel",
                "specialty": "Orthopedics",
                "phone": "+91-79-2658-1234",
                "address": "C-789, Satellite",
                "city": "Ahmedabad",
                "state": "Gujarat",
                "zip": "380015",
                "license_number": "MCI/GUJ/34567/2015",
                "npi": "7654321098"
            },
            "scraped": {
                "id": 1003,
                "name": "Dr. Amit Patel",
                "specialty": "Orthopedics",
                "phone": "+91-79-2658-1234",
                "address": "C-789, Satellite Area",
                "city": "Ahmedabad",
                "state": "Gujarat",
                "zip": "380015",
                "license_number": "MCI/GUJ/34567/2015",
                "npi": "7654321098"
            },
            "confidence": 88  # Minor address variation (Area added)
        },
        # Medium confidence scenarios (70-80) - Will be flagged
        2001: {
            "db": {
                "id": 2001,
                "name": "Dr. Anjali Reddy",
                "specialty": "Dermatology",
                "phone": "+91-40-2789-4567",
                "address": "D-321, Banjara Hills",
                "city": "Hyderabad",
                "state": "Telangana",
                "zip": "500034",
                "license_number": "MCI/TEL/45678/2011",
                "npi": "6543210987"
            },
            "scraped": {
                "id": 2001,
                "name": "Dr. Anjali Reddy",
                "specialty": "Dermatology",
                "phone": "+91-40-2789-4568",  # Different phone
                "address": "D-321, Banjara Hills",
                "city": "Hyderabad",
                "state": "Telangana",
                "zip": "500034",
                "license_number": "MCI/TEL/45678/2011",
                "npi": "6543210987"
            },
            "confidence": 78  # Phone mismatch
        },
        2002: {
            "db": {
                "id": 2002,
                "name": "Dr. Vikram Singh",
                "specialty": "Neurology",
                "phone": "+91-80-2558-9876",
                "address": "E-654, Koramangala",
                "city": "Bangalore",
                "state": "Karnataka",
                "zip": "560095",
                "license_number": "MCI/KAR/56789/2013",
                "npi": "5432109876"
            },
            "scraped": {
                "id": 2002,
                "name": "Dr. Vikram Singh",
                "specialty": "Neurology",
                "phone": "+91-80-2558-9876",
                "address": "E-654, Koramangala 5th Block",  # Different address
                "city": "Bangalore",
                "state": "Karnataka",
                "zip": "560095",
                "license_number": "MCI/KAR/56789/2013",
                "npi": "5432109876"
            },
            "confidence": 75  # Address variation
        },
        # Low confidence scenarios (<70) - Will be flagged
        3001: {
            "db": {
                "id": 3001,
                "name": "Dr. Meera Nair",
                "specialty": "Gynecology",
                "phone": "+91-44-2845-2345",
                "address": "F-987, T. Nagar",
                "city": "Chennai",
                "state": "Tamil Nadu",
                "zip": "600017",
                "license_number": "MCI/TN/67890/2014",
                "npi": "4321098765"
            },
            "scraped": {
                "id": 3001,
                "name": "Dr. Meera Nair",
                "specialty": "Gynecology",
                "phone": "+91-44-2845-2346",  # Different phone
                "address": "F-987, Thyagaraya Nagar",  # Different address format
                "city": "Chennai",
                "state": "Tamil Nadu",
                "zip": "600017",
                "license_number": "MCI/TN/67890/2014",
                "npi": "4321098765"
            },
            "confidence": 65  # Multiple discrepancies
        },
        3002: {
            "db": {
                "id": 3002,
                "name": "Dr. Ravi Iyer",
                "specialty": "Oncology",
                "phone": "+91-33-2445-6789",
                "address": "G-147, Salt Lake",
                "city": "Kolkata",
                "state": "West Bengal",
                "zip": "700064",
                "license_number": "MCI/WB/78901/2016",
                "npi": "3210987654"
            },
            "scraped": {
                "id": 3002,
                "name": "Dr. Ravi Iyer",
                "specialty": "Oncology",
                "phone": "+91-33-2445-6790",  # Different phone
                "address": "G-147, Salt Lake City",  # Different address
                "city": "Kolkata",
                "state": "West Bengal",
                "zip": "700064",
                "license_number": "MCI/WB/78901/2016",
                "npi": "3210987654"
            },
            "confidence": 68  # Multiple discrepancies
        },
        # Edge case: Very high confidence with minor formatting difference
        4001: {
            "db": {
                "id": 4001,
                "name": "Dr. Kavita Desai",
                "specialty": "Endocrinology",
                "phone": "+91-20-2558-3456",
                "address": "H-258, Koregaon Park",
                "city": "Pune",
                "state": "Maharashtra",
                "zip": "411001",
                "license_number": "MCI/MAH/89012/2017",
                "npi": "2109876543"
            },
            "scraped": {
                "id": 4001,
                "name": "Dr. Kavita Desai",
                "specialty": "Endocrinology",
                "phone": "+91-20-2558-3456",
                "address": "H-258, Koregaon Park",
                "city": "Pune",
                "state": "Maharashtra",
                "zip": "411001",
                "license_number": "MCI/MAH/89012/2017",
                "npi": "2109876543"
            },
            "confidence": 90  # Perfect match
        }
    }
    
    # Return specific provider or default
    if provider_id in providers:
        return providers[provider_id]
    
    # Default provider (original) - medium confidence
    return {
        "db": {
            "id": provider_id,
            "name": "Dr. Arjun Mehta",
            "specialty": "General Medicine",
            "phone": "+91-11-2658-3456",
            "address": "I-369, Connaught Place",
            "city": "New Delhi",
            "state": "Delhi",
            "zip": "110001",
            "license_number": "MCI/DEL/90123/2018",
            "npi": "1098765432"
        },
        "scraped": {
            "id": provider_id,
            "name": "Dr. Arjun Mehta",
            "specialty": "General Medicine",
            "phone": "+91-11-2658-3457",  # Different phone
            "address": "I-369, Connaught Place",
            "city": "New Delhi",
            "state": "Delhi",
            "zip": "110001",
            "license_number": "MCI/DEL/90123/2018",
            "npi": "1098765432"
        },
        "confidence": 75  # Phone mismatch
    }


# ============================================================================
# Workflow Nodes
# ============================================================================

def fetch_provider_node(state: AgentState) -> AgentState:
    """
    Fetches provider data from Supabase database.
    TODO: Insert Supabase Client here
    """
    provider_id = state["provider_id"]
    
    # Mock Supabase fetch - simulate database record
    # TODO: Replace with actual Supabase query
    # Example: result = supabase_client.table('providers').select('*').eq('id', provider_id).execute()
    
    # Get mock provider data
    provider_data = get_mock_provider_data(provider_id)
    mock_db_data = provider_data["db"]
    
    # Store the expected confidence score for later use
    state["_expected_confidence"] = provider_data.get("confidence", 75)
    
    state["current_db_data"] = mock_db_data
    state["status"] = "pending"
    
    print(f"[FETCH] Retrieved provider {provider_id} from database")
    return state


def scrape_web_node(state: AgentState) -> AgentState:
    """
    Scrapes provider data from web sources using Firecrawl/Playwright.
    TODO: Insert Firecrawl/Playwright scraper here
    """
    # Mock web scraping - return slightly different data to test logic
    # TODO: Replace with actual Firecrawl/Playwright scraping
    # Example: scraped = firecrawl_client.scrape(url) or playwright_scraper.scrape(url)
    
    provider_id = state["provider_id"]
    
    # Get mock provider data with scraped version
    provider_data = get_mock_provider_data(provider_id)
    mock_scraped_data = provider_data["scraped"]
    
    state["scraped_data"] = mock_scraped_data
    state["discrepancies"] = []  # Will be populated by QA node
    
    print(f"[SCRAPE] Scraped web data for provider {provider_id}")
    return state


def quality_assurance_node(state: AgentState) -> AgentState:
    """
    Uses LLM (Claude/GPT-4) to compare database and scraped data.
    Outputs a confidence_score based on the comparison.
    TODO: Insert LLM client (Anthropic/OpenAI) here
    """
    db_data = state["current_db_data"]
    scraped_data = state["scraped_data"]
    
    # TODO: Replace with actual LLM comparison
    # Example:
    # prompt = f"Compare these two provider records:\nDB: {db_data}\nScraped: {scraped_data}"
    # response = llm_client.chat.completions.create(
    #     model="gpt-4",
    #     messages=[{"role": "user", "content": prompt}]
    # )
    # Parse response to extract confidence_score and discrepancies
    
    # Mock LLM comparison logic
    discrepancies = []
    
    # Compare all fields and identify discrepancies
    fields_to_compare = ["name", "specialty", "phone", "address", "city", "state", "zip", "license_number", "npi"]
    
    for field in fields_to_compare:
        db_value = db_data.get(field, "")
        scraped_value = scraped_data.get(field, "")
        
        # Normalize for comparison (case-insensitive, strip whitespace)
        db_normalized = str(db_value).lower().strip()
        scraped_normalized = str(scraped_value).lower().strip()
        
        # Check for discrepancies (allowing minor variations)
        if db_normalized != scraped_normalized:
            # Check if it's just a minor variation (e.g., "Dr" vs "Drive", "Area" added)
            is_minor_variation = (
                db_normalized in scraped_normalized or 
                scraped_normalized in db_normalized or
                field == "address" and (len(db_normalized.split()) == len(scraped_normalized.split()) - 1)
            )
            
            if not is_minor_variation:
                discrepancies.append({
                    "field": field,
                    "db_value": str(db_value),
                    "scraped_value": str(scraped_value)
                })
    
    # Use pre-defined confidence score if available, otherwise calculate
    if "_expected_confidence" in state:
        confidence_score = state["_expected_confidence"]
        # Adjust slightly based on actual discrepancies found
        if len(discrepancies) > 0:
            confidence_score = max(0, confidence_score - (len(discrepancies) * 5))
    else:
        # Fallback calculation
        discrepancy_count = len(discrepancies)
        if discrepancy_count == 0:
            confidence_score = 95
        elif discrepancy_count == 1:
            confidence_score = 75
        else:
            confidence_score = max(0, 100 - (discrepancy_count * 20))
    
    state["discrepancies"] = discrepancies
    state["confidence_score"] = confidence_score
    
    print(f"[QA] Confidence score: {confidence_score}% | Discrepancies: {len(discrepancies)}")
    if discrepancies:
        for disc in discrepancies:
            print(f"  - {disc['field']}: DB='{disc['db_value']}' vs Scraped='{disc['scraped_value']}'")
    
    return state


def update_db_node(state: AgentState) -> AgentState:
    """
    Updates the database with verified data.
    Runs when confidence_score > 80.
    TODO: Insert Supabase update logic here
    """
    provider_id = state["provider_id"]
    confidence_score = state["confidence_score"]
    
    # TODO: Replace with actual Supabase update
    # Example:
    # supabase_client.table('providers').update({
    #     'verified_at': datetime.now(),
    #     'confidence_score': confidence_score,
    #     'status': 'verified'
    # }).eq('id', provider_id).execute()
    
    print("Updating Database...")
    print(f"  Provider {provider_id} verified with confidence {confidence_score}%")
    
    state["status"] = "verified"
    return state


def flag_review_node(state: AgentState) -> AgentState:
    """
    Flags the provider record for human review.
    Runs when confidence_score <= 80.
    TODO: Insert flagging logic here (e.g., create review ticket, send notification)
    """
    provider_id = state["provider_id"]
    confidence_score = state["confidence_score"]
    discrepancies = state["discrepancies"]
    
    # TODO: Replace with actual flagging logic
    # Example:
    # supabase_client.table('review_queue').insert({
    #     'provider_id': provider_id,
    #     'confidence_score': confidence_score,
    #     'discrepancies': discrepancies,
    #     'created_at': datetime.now()
    # }).execute()
    # Or send notification to review team
    
    print("Flagging for Human Review...")
    print(f"  Provider {provider_id} flagged (confidence: {confidence_score}%)")
    print(f"  Discrepancies found: {len(discrepancies)}")
    
    state["status"] = "flagged"
    return state


# ============================================================================
# Conditional Edge Logic
# ============================================================================

def should_update_db(state: AgentState) -> Literal["update_db", "flag_review"]:
    """
    Conditional edge function that routes based on confidence_score.
    """
    confidence_score = state["confidence_score"]
    
    if confidence_score > 80:
        return "update_db"
    else:
        return "flag_review"


# ============================================================================
# Graph Construction
# ============================================================================

def create_workflow_graph() -> StateGraph:
    """
    Creates and configures the LangGraph workflow.
    """
    # Initialize the StateGraph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("fetch_provider", fetch_provider_node)
    workflow.add_node("scrape_web", scrape_web_node)
    workflow.add_node("quality_assurance", quality_assurance_node)
    workflow.add_node("update_db", update_db_node)
    workflow.add_node("flag_review", flag_review_node)
    
    # Set entry point
    workflow.set_entry_point("fetch_provider")
    
    # Add edges: fetch -> scrape -> qa
    workflow.add_edge("fetch_provider", "scrape_web")
    workflow.add_edge("scrape_web", "quality_assurance")
    
    # Add conditional edge after QA: routes based on confidence_score
    workflow.add_conditional_edges(
        "quality_assurance",
        should_update_db,
        {
            "update_db": "update_db",
            "flag_review": "flag_review"
        }
    )
    
    # Both end nodes lead to END
    workflow.add_edge("update_db", END)
    workflow.add_edge("flag_review", END)
    
    return workflow.compile()


# ============================================================================
# Main Execution
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Autonomous Provider Directory Management - Orchestrator")
    print("=" * 60)
    print()
    
    # Create the workflow graph
    graph = create_workflow_graph()
    
    # Example provider IDs to test:
    # High confidence (>80): 1001, 1002, 1003, 4001
    # Medium confidence (70-80): 2001, 2002
    # Low confidence (<70): 3001, 3002
    
    # Initialize state with dummy provider_id
    initial_state: AgentState = {
        "provider_id": 1001,  # High confidence example
        "current_db_data": {},
        "scraped_data": {},
        "discrepancies": [],
        "confidence_score": 0,
        "status": "pending"
    }
    
    print(f"Starting workflow for provider_id: {initial_state['provider_id']}")
    print("-" * 60)
    print()
    
    # Run the graph
    try:
        final_state = graph.invoke(initial_state)
        
        print()
        print("-" * 60)
        print("Workflow completed!")
        print(f"Final status: {final_state['status']}")
        print(f"Final confidence score: {final_state['confidence_score']}%")
        print("=" * 60)
        print("\nTry these provider IDs in the web interface:")
        print("  High confidence (>80): 1001, 1002, 1003, 4001")
        print("  Medium confidence (70-80): 2001, 2002")
        print("  Low confidence (<70): 3001, 3002")
        
    except Exception as e:
        print(f"Error during workflow execution: {e}")
        raise

