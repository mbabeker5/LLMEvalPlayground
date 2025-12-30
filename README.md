# LLM Prompt Engineering Playground

A prompt engineering evaluation tool for comparing multiple LLM model outputs side-by-side. Upload a document, define your target JSON schema, and run evaluations across different models to compare their extraction capabilities.

## Features

- 🧪 **Multi-Model Evaluation**: Run the same prompt across multiple LLM models simultaneously
- 📊 **Side-by-Side Comparison**: View model outputs in a responsive grid layout
- 📄 **PDF Document Support**: Upload PDF documents for information extraction
- 🎯 **Target Schema Definition**: Paste your target JSON schema to guide extraction
- ⏱️ **Performance Metrics**: See response times for each model
- 📋 **One-Click Copy**: Copy individual model outputs to clipboard

## Available Models

- Gemini 3 Flash (Preview)
- Gemini 3 Pro (Preview)
- Gemini 2.0 Flash (Exp)
- Gemini 1.5 Flash
- Gemini 1.5 Pro

## Setup Instructions

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Credentials

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and add your Gemini API key:

```
GEMINI_API_KEY=your_api_key_here
```

### 3. Customize System Prompt

Edit `System_Prompt.md` to customize the system prompt that will be sent to the LLM.

### 4. Run the Application

```bash
# Using the run script
./run.sh

# Or manually
source venv/bin/activate
python app.py
```

The API will be available at `http://localhost:8000`

### 5. Open the Frontend

Open `index.html` in your browser, or serve it:

```bash
python -m http.server 8080
```

Then navigate to `http://localhost:8080`

## Project Structure

```
.
├── app.py                 # FastAPI backend server
├── index.html             # Frontend HTML (Eval Playground)
├── styles.css             # Frontend styles (Dark theme)
├── script.js              # Frontend JavaScript
├── System_Prompt.md       # System prompt for LLM
├── Parsing_Prompt.md      # Legacy parsing prompt
├── requirements.txt       # Python dependencies
├── .env.example           # Example environment variables
└── README.md              # This file
```

## API Endpoints

### GET /

Health check endpoint.

### GET /models

Returns list of available models for evaluation.

**Response:**
```json
{
  "models": [
    {"id": "gemini-3-flash-preview", "name": "Gemini 3 Flash (Preview)", "provider": "google"},
    ...
  ]
}
```

### GET /system-prompt

Returns the current system prompt.

### POST /eval

Run evaluation across selected models.

**Request:**
- Content-Type: `multipart/form-data`
- Body:
  - `file`: PDF file
  - `models`: JSON array of model IDs
  - `target_schema`: JSON schema string

**Response:**
```json
{
  "success": true,
  "results": [
    {
      "model_id": "gemini-3-flash-preview",
      "model_name": "Gemini 3 Flash (Preview)",
  "success": true,
  "json_data": { ... },
      "duration_ms": 2500
    },
    ...
  ]
}
```

## User Prompt Template

The user prompt sent to each model follows this template:

```
Extract information from the following document into the exact JSON structure provided.

Document text:
{{ document_text }}

Target JSON schema (populate all keys; leave unknowns as empty strings or empty arrays as appropriate):
{{ target_schema_json }}
```

## Usage Tips

1. **Select Models**: Choose one or more models to compare
2. **Upload Document**: Drag and drop or click to upload a PDF
3. **Define Schema**: Paste your target JSON structure
4. **Run Evaluation**: Click "Run Evaluation" to process
5. **Compare Results**: View outputs side-by-side and copy as needed

## License

MIT
