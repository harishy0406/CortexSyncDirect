# Autonomous Provider Directory Management: An Agentic AI Solution
- Building Autonomous, Goal-Driven Systems to Solve Healthcare's Data Inaccuracy Crisis

## 🚀 Quick Start

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the FastAPI server:
```bash
python app.py
```

3. Open your browser and navigate to:
```
http://localhost:8000
```

## 📋 Features

- **Web Interface**: Modern, responsive UI for provider validation
- **LangGraph Workflow**: Cyclic validation workflow with conditional routing
- **Real-time Results**: Visual display of data comparison and discrepancies
- **Confidence Scoring**: AI-powered confidence assessment (0-100%)
- **Automated Actions**: Auto-updates database or flags for review based on confidence

## 🏗️ Architecture

### Components

1. **orchestrator.py**: Core LangGraph workflow engine
   - State management with `AgentState` TypedDict
   - Workflow nodes: fetch → scrape → QA → (update_db | flag_review)
   - Conditional routing based on confidence score

2. **app.py**: FastAPI backend
   - REST API endpoints
   - Workflow execution
   - CORS-enabled for frontend

3. **index.html**: Modern web interface
   - Provider ID input
   - Workflow visualization
   - Data comparison display
   - Discrepancy highlighting

## 🔄 Workflow

1. **Fetch Provider**: Retrieves provider data from Supabase (mocked)
2. **Scrape Web**: Scrapes provider data from web sources (mocked)
3. **Quality Assurance**: LLM compares datasets and calculates confidence score
4. **Decision**:
   - If confidence > 80% → Update Database
   - If confidence ≤ 80% → Flag for Human Review

## 🛠️ Tech Stack

- **LangGraph**: Workflow orchestration
- **LangChain Core**: AI framework
- **FastAPI**: Backend API
- **Python 3.8+**: Runtime

## 🧪 Test Provider IDs

The system includes multiple Indian healthcare provider samples for testing:

### High Confidence (>80%) - Will be Verified ✅
- **1001**: Dr. Rajesh Kumar (Cardiology, New Delhi) - Perfect match (95%)
- **1002**: Dr. Priya Sharma (Pediatrics, Mumbai) - Perfect match (92%)
- **1003**: Dr. Amit Patel (Orthopedics, Ahmedabad) - Minor variation (88%)
- **4001**: Dr. Kavita Desai (Endocrinology, Pune) - Perfect match (90%)

### Medium Confidence (70-80%) - Will be Flagged ⚠️
- **2001**: Dr. Anjali Reddy (Dermatology, Hyderabad) - Phone mismatch (78%)
- **2002**: Dr. Vikram Singh (Neurology, Bangalore) - Address variation (75%)

### Low Confidence (<70%) - Will be Flagged 🚨
- **3001**: Dr. Meera Nair (Gynecology, Chennai) - Multiple discrepancies (65%)
- **3002**: Dr. Ravi Iyer (Oncology, Kolkata) - Multiple discrepancies (68%)

All providers use authentic Indian names, addresses, phone numbers (+91 format), and MCI license numbers.

## 📝 TODO Integration Points

The code includes placeholder comments for:
- Supabase client integration
- Firecrawl/Playwright web scraping
- LLM client (Anthropic/OpenAI) for QA comparison