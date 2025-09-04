
<h1 align="center">GenAI SMS Chatbot</h1>

<p align="center">
  A multi-agent conversational AI system for job candidate interactions<br>
  <a href="#demo">View Demo</a>
  ·
  <a href="#demo">Report Bug</a>
  ·
  <a href="#demo">Request Feature</a>
</p>

---
<br></br>

## Quick Guide (TL:DR)
### Download and run your matching OS  **install_and_run** script (.sh / .bat) to fully setup the project
#### Then set your Open AI API key and trained model ID in the designated files under the secrets folder and run the project:
```bash
streamlit run streamlit/streamlit_main.py
```

<br></br>
## Table of Contents

- [About The Project](#about-the-project)
- [Features](#features)
- [Getting Started](#getting-started)
- [Usage](#usage)
- [Screenshots](#screenshots)
- [Code Examples](#code-examples)
- [Project Structure](#project-structure)
- [To-Do List](#to-do-list)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)
- [Acknowledgments](#acknowledgments)

---
<br></br>


## About The Project

> This project demonstrates a sophisticated multi-agent conversational AI system for job candidate interactions, featuring intelligent conversation management, interview scheduling, and persistent user context.<br>

<div style="background: #272822; color: #f8f8f2; padding: 10px; border-radius: 8px;">
  <b> Technologies:</b> Python, OpenAI API, Streamlit, MongoDB, SQL Server, ChromaDB, Docker
</div>

---
<br></br>


## Features

- [x] 🤖 **Multi-Agent Architecture**: Main Agent orchestrates Info Advisor, Scheduling Advisor, and Exit Advisor
- [x] 📱 **User Registration**: Phone number-based user identification and conversation persistence
- [x] 🗄️ **MongoDB Integration**: Conversation history and user data storage
- [x] 🧠 **AI-Powered Responses**: OpenAI GPT-4 integration for intelligent conversations
- [x] 📊 **Vector Database**: ChromaDB for job description embeddings and semantic search
- [x] 🎨 **Streamlit Interface**: Beautiful web-based chat interface
- [x] 📅 **Interview Scheduling**: Automated interview slot management with SQL Server
- [x] 📝 **Conversation Summarization**: AI-generated conversation summaries
- [x] <span style="color: green; font-weight: bold;">Context-Aware Conversations</span>
- [ ] Cloud deployment _(coming soon!)_  

---
<br></br>


## Getting Started

### Prerequisites

- Python >= 3.11
- OpenAI API key
- MongoDB (optional - system works in fallback mode)
- Docker (for local database setup)

### Installation
You can set up the project in one of two ways:

#### Option 1: Download and run the helper script only (Windows / Other OS)
These scripts will do the following:

- Auto detect whether they run from an already cloned directory (so you don’t need to worry about the current directory).
- Clone the repository if it doesn’t exist.
- Enter the repository folder if needed.
- Create a virtual environment (if it doesn’t exist).
- Activate the virtual environment.
- Upgrade pip and install all dependencies.
- Create a secrets directory with the following files:
	- openai_api_key.txt → Set your Open AI API key (sk-XXXX) in this file
	- openai_fine_tune_model.txt →  Set your trained model id () in this file

✅ After running the script, edit the secret files and replace the placeholders with your actual OpenAI API key and fine-tuned model ID.

* Linux / macOS / Git Bash (Windows):
	```bash
	./install_and_run.sh
	```

* Windows Command Prompt:
	```cmd
	install_and_run.bat
	```


#### Option 2: Manual setup
*  On Linux / macOS / Git Bash (Windows)
	```bash
	git clone https://github.com/LiamNomad/GenAIFinalProject.git
	cd GenAIFinalProject
	python3 -m venv .venv
	source .venv/bin/activate
	python -m pip install --upgrade pip
	python -m pip install -r requirements.txt

	# Create secrets folder and files manually
	mkdir -p secrets
	echo "sk-XXXX" > secrets/openai_api_key.txt
	echo "ft:gpt-3.5-turbo-1106:personal::XXXXXXXX" > secrets/openai_fine_tune_model.txt
	```

*  On Windows Command Prompt
	```cmd
	git clone https://github.com/LiamNomad/GenAIFinalProject.git
	cd GenAIFinalProject
	python -m venv .venv
	.venv\Scripts\activate
	python -m pip install --upgrade pip
	python -m pip install -r requirements.txt

	REM Create secrets folder and files manually
	mkdir secrets
	echo sk-XXXX > secrets\openai_api_key.txt
	echo ft:gpt-3.5-turbo-1106:personal::XXXXXXXX > secrets\openai_fine_tune_model.txt
	```
s
### Environment Setup

#### 🔐 **Required: OpenAI API Key Setup**

**⚠️ IMPORTANT**: You must set up your OpenAI API key before running the application, or you'll get the error: `"Mandatory directory 'secrets' is missing"`

**Step 1: Create the secrets directory**
```bash
mkdir -p secrets
```

**Step 2: Get your OpenAI API key**
- Visit: https://platform.openai.com/api-keys
- Create a new API key (starts with `sk-`)
- Copy the full API key

**Step 3: Create the API key file**
```bash
# Create the file
touch secrets/openai_api_key.txt

# Edit the file and paste your API key
# The file should contain ONLY your API key, nothing else
```

**Step 4: Create the fine-tuned model file (Optional)**
```bash
# Create the file
touch secrets/openai_fine_tune_model.txt

# Edit the file and add your model ID, or use the default:
echo "gpt-4-turbo-preview" > secrets/openai_fine_tune_model.txt
```

**📁 Required File Structure:**
```
GenAIFinalProject/
├── secrets/
│   ├── openai_api_key.txt          # Your OpenAI API key (sk-...)
│   └── openai_fine_tune_model.txt  # Model ID or "gpt-4-turbo-preview"
└── ... (other files)
```

**🔒 Security Note**: The `secrets/` directory is automatically ignored by git, so your API key will never be committed to version control.

**✅ Verification**: After setup, you should be able to run:
```bash
streamlit run streamlit/streamlit_main.py
```
Without getting the `"Mandatory directory 'secrets' is missing"` error.

### Quick Start (Zero Configuration!)

```bash
# Start the application - database setup is automatic!
streamlit run streamlit/streamlit_main.py
```

**🎯 What happens automatically:**
- **MSSQL**: Automatically falls back to SQLite if unavailable
- **SQLite**: Auto-initializes with sample data (future dates only)
- **MongoDB**: Optional (conversation history only)
- **Works on all platforms**: Windows, macOS, Linux

**No database configuration required!** The system handles everything automatically.

### Database Setup

The application uses two databases:
- **MongoDB**: For conversation history and user management
- **MSSQL/SQLite**: For interview scheduling and availability

#### MongoDB Setup

**Option A: Docker (Recommended for both Windows & Mac)**
```bash
docker-compose up -d mongodb
```

**Option B: MongoDB Atlas (Cloud)**
- Create account at [MongoDB Atlas](https://www.mongodb.com/atlas)
- Update `MONGODB_URI` in `.env`

#### Interview Scheduling Database

The system automatically handles database setup with intelligent fallback:

**Windows (Recommended Setup):**
- **Primary**: MSSQL Server with Windows Authentication
- **Fallback**: SQLite (if MSSQL unavailable)
- **Setup**: Install SQL Server Express or use Docker

**macOS/Linux:**
- **Primary**: MSSQL Server with username/password authentication
- **Fallback**: SQLite (automatic when MSSQL fails)
- **Note**: ODBC drivers have compatibility issues on macOS ARM64

**Automatic Fallback System:**
1. **Attempts MSSQL connection** first
2. **If MSSQL fails** → Automatically switches to SQLite
3. **Populates SQLite** with sample data (future dates only)
4. **Continues operation** seamlessly

**SQLite Fallback Features:**
- ✅ **Automatic initialization** when MSSQL unavailable
- ✅ **Sample data population** (next 5 available dates)
- ✅ **Full functionality** (scheduling, booking, queries)
- ✅ **Data persistence** (stored in `data/tech_interviews.db`)
- ✅ **No configuration required** - works out of the box

**Environment Variables:**
```bash
# MSSQL Configuration (optional - fallback works without these)
MSSQL_SERVER=localhost
MSSQL_DATABASE=Tech
MSSQL_USERNAME=sa
MSSQL_PASSWORD=YourPassword
MSSQL_PORT=1433

# MongoDB Configuration (optional - for conversation history)
MONGODB_URI=mongodb://admin:password123@localhost:27017/sms_chatbot?authSource=admin
MONGODB_DATABASE=sms_chatbot
```

---
<br></br>

## Troubleshooting

### 🔐 **Secrets Setup Issues**

**Error: `"Mandatory directory 'secrets' is missing"`**
- ❌ **Problem**: Missing or incorrectly configured secrets directory
- 🔧 **Solution**: Follow the [Environment Setup](#environment-setup) steps above
- ✅ **Verify**: Check that `secrets/openai_api_key.txt` contains your actual API key

**Error: `"Secret key file 'secrets/openai_api_key.txt' not found"`**
- ❌ **Problem**: API key file doesn't exist
- 🔧 **Solution**: Create the file and add your OpenAI API key
- ✅ **Verify**: File should contain only the API key (starts with `sk-`)

**Error: `"Secret key is empty"`**
- ❌ **Problem**: API key file exists but is empty
- 🔧 **Solution**: Add your actual OpenAI API key to the file
- ✅ **Verify**: No extra spaces, newlines, or placeholder text

### Database Connection Issues

**MSSQL Connection Fails:**
- ✅ **Normal behavior** - SQLite fallback will activate automatically
- ✅ **No action required** - application continues working
- ✅ **Check logs** for "SQLite fallback database initialized successfully"

**MongoDB Connection Fails:**
- ❌ **Action required** - conversation history won't be saved
- 🔧 **Solution**: Start MongoDB container with `docker-compose up -d mongodb`
- 🔧 **Alternative**: Use MongoDB Atlas cloud service

**Common macOS ARM64 Issues:**
- **ODBC Driver Problems**: Expected on Apple Silicon Macs
- **Solution**: SQLite fallback handles this automatically
- **No configuration needed** - system works out of the box

### Performance Notes

**SQLite vs MSSQL:**
- **SQLite**: Faster for development, sufficient for small-medium deployments
- **MSSQL**: Better for production, concurrent users, and complex queries
- **Automatic switching**: No performance impact during fallback

**Sample Data:**
- **Generated automatically** when SQLite is initialized
- **Future dates only** (no past dates shown to users)
- **Limited to 5 dates** for better user experience
- **Realistic availability** (50% chance of being available)

---
<br></br>

## Usage

### Start the Application

```bash
# Run the Streamlit web interface
streamlit run streamlit/streamlit_main.py

# Or test the system directly
python -m app.agents.main_agent
```

### Conversation Flow

1. **Registration**: User provides phone number
2. **Job Interest**: User specifies job type (Python Developer, etc.)
3. **Interaction**: AI-powered conversation with context awareness
4. **Scheduling**: Automated interview slot booking
5. **Summary**: AI-generated conversation summary



## Code Examples

### Multi-Agent System

```python
from app.agents.main_agent import MainAgent
from app.agents.info_advisor import InfoAdvisor
from app.agents.scheduler import Scheduler

# Initialize the main agent
main_agent = MainAgent()

# Process user message
response = main_agent.process_message("I'm interested in Python development", "1234567890")
```

### Database Operations

```python
from app.mongodb_manager import MongoDBManager
from app.database import DatabaseManager

# MongoDB for conversation history
mongo_manager = MongoDBManager()
conversation_history = mongo_manager.get_conversation_history("1234567890")

# SQL Server for interview scheduling
db_manager = DatabaseManager()
available_slots = db_manager.get_available_slots("Python Developer")
```

---
<br></br>


## Project Structure

```text
GenAIFinalProject/
├── app/
│   ├── agents/           # Multi-agent system
│   │   ├── main_agent.py      # Main conversation orchestrator
│   │   ├── info_advisor.py    # Job information and Q&A
│   │   ├── scheduler_advisor.py # Interview scheduling (MSSQL/SQLite)
│   │   ├── exit_advisor.py    # Conversation ending and summaries
│   │   └── prompts/           # AI prompts for all agents
│   │       ├── main_agent_prompts.py
│   │       ├── scheduler_advisor_prompts.py
│   │       └── info_advisor_prompts.py
│   ├── embedding.py           # Vector database (ChromaDB) management
│   ├── mongodb_manager.py     # MongoDB operations (conversation history)
│   ├── database.py            # Database manager (MSSQL/SQLite fallback)
│   ├── fine_tuning.py         # Model fine-tuning utilities
│   └── logger.py              # Logging configuration
├── config/
│   └── project_config.py      # Project configuration bootstrap and validation
├── data/                      # Job descriptions, SQLite DB, ChromaDB
│   ├── *.pdf                  # Job description PDFs
│   ├── tech_interviews.db     # SQLite database (auto-generated)
│   └── chroma_db/             # Vector database (auto-generated)
├── fine_tune/                 # Fine-tuning scripts and utilities
├── logs/                 	   # Project logs
├── secrets/                   # api keys and other secrets
├── streamlit/
│   └── streamlit_main.py      # Web interface for testing
├── tests/                     # Test files
├── docker-compose.yml         # MongoDB and MSSQL Docker setup
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

---
<br></br>

## Prompts System

The application uses a centralized prompts system for better organization and maintainability.

### Prompts Directory

The `app/agents/prompts/` directory contains text files with prompts used by various agents in the GenAI SMS Chatbot system.

### Files

- `main_agent_prompts.py` - Main agent prompts including system prompt, time slot selection, and conversation summary
- `scheduler_advisor_prompts.py` - Scheduler advisor prompts for interview scheduling
- `info_advisor_prompts.py` - Info advisor prompts for job information, candidate interaction, and AI-based intent analysis

### Usage

Prompts are imported as Python constants by the agents. This allows for easy modification of prompts without changing the code and provides better type safety and IDE support.

### Adding New Prompts

1. Add the new prompt constant to the appropriate prompts file (e.g., `main_agent_prompts.py`)
2. Update the corresponding agent to import and use the new prompt
3. Update the `prompts/__init__.py` file to export the new prompt

### Benefits

- **Readability**: Prompts are separated from code for better readability
- **Maintainability**: Easy to modify prompts without touching code
- **Version Control**: Prompts can be versioned separately from code
- **Collaboration**: Non-developers can easily edit prompts

---
<br></br>

## To-Do List

- [x] Initial project setup
- [x] Multi-agent architecture implementation
- [x] MongoDB integration
- [x] SQL Server scheduling database
- [x] Streamlit web interface
- [x] Vector database for job descriptions
- [x] Performance optimization


---
<br></br>




## License

Distributed under the MIT License. See `LICENSE` for more information.

---
<br></br>


## Contact

- **Liam Nomad** **Id: 302841234** - [@liam.nomad34@gmail.com](yourmail@gmail.com) 
- **Yossi Yacov** **Id: 032292799** - [@yossiy@gmail.com](yourmail@gmail.com)

Project Link: [https://github.com/LiamNomad/GenAIFinalProject](https://github.com/LiamNomad/GenAIFinalProject)

---
<br></br>


## Acknowledgments

- [Python](https://www.python.org/)
- [OpenAI API](https://platform.openai.com/docs/overview)
- [Streamlit](https://streamlit.io/)
- [MongoDB](https://www.mongodb.com/)
- [ChromaDB](https://www.trychroma.com/)
- [Docker](https://www.docker.com/)


--- 