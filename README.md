# Financial Report Analyzer

An AI-powered financial analysis tool built with Streamlit and CrewAI that analyzes CSV, PDF, and DOCX files.

## Setup Instructions

### Local Development

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Create a `.env` file:**
```bash
GROQ_API_KEY=your_groq_api_key_here
```

3. **Run the app:**
```bash
streamlit run streamlit_financial_report_analyzer.py
```

### Streamlit Cloud Deployment

1. **Push to GitHub** with these files:
   - `streamlit_financial_report_analyzer.py`
   - `requirements.txt`
   - `packages.txt`
   - `.streamlit/config.toml`

2. **Set up Secrets:**
   - Go to your Streamlit Cloud app settings
   - Click "Manage Secrets"
   - Add your GROQ API key:
   ```
   GROQ_API_KEY = "your_groq_api_key_here"
   ```

3. **Deploy** - Streamlit will automatically install dependencies

## Features

- ✅ **CSV Analysis** - Income/expense reports with KPI cards and visualizations
- ✅ **PDF Support** - Extract and analyze financial documents
- ✅ **DOCX Support** - Process Word documents
- ✅ **AI-Powered Analysis** - CrewAI orchestrates Analyzer & Reporter agents
- ✅ **Report Generation** - Automatic financial summary reports
- ✅ **Download Reports** - Export analysis results as text files

## Required Files

- `requirements.txt` - Python package dependencies
- `packages.txt` - System-level dependencies (for Streamlit Cloud)
- `.streamlit/config.toml` - Streamlit configuration
- `.env` - Environment variables (local development only)

## Supported File Formats

- **CSV** - Comma-separated financial data
- **PDF** - PDF financial documents
- **DOCX** - Microsoft Word documents

## API Requirements

- **GROQ API Key** - Required for LLM (Llama 3.1 8B Instant)

Get your free API key at: https://console.groq.com/

## Troubleshooting

### "ModuleNotFoundError: No module named 'crewai'"
Run: `pip install -r requirements.txt`

### "GROQ_API_KEY not found"
- **Local**: Add to `.env` file
- **Streamlit Cloud**: Add to Secrets management

### Installation fails on Streamlit Cloud
- Check `packages.txt` is present
- Ensure `requirements.txt` has no version conflicts
- Try removing version pinning from problematic packages

## Architecture

- **Analyzer Agent** - Analyzes financial data and identifies trends
- **Reporter Agent** - Creates polished financial reports
- **CrewAI Orchestration** - Manages agent workflow sequentially
- **Groq LLM** - Powers the AI agents (Llama 3.1 8B Instant)
