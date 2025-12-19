import os
import base64
import tempfile
import time
import asyncio
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
from dotenv import load_dotenv

# Google Gemini imports
from google import genai
from google.genai import types
from google.api_core.exceptions import ResourceExhausted, GoogleAPIError

# OpenAI imports
from openai import OpenAI

# Load environment variables
load_dotenv()

app = FastAPI(title="LLM Prompt Engineering Playground")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
SYSTEM_PROMPT_FILE = "System_Prompt.md"

# Available models for evaluation
AVAILABLE_MODELS = [
    # Google Gemini Models
    {"id": "gemini-3-flash-preview", "name": "Gemini 3 Flash (Preview)", "provider": "google"},
    {"id": "gemini-3-pro-preview", "name": "Gemini 3 Pro (Preview)", "provider": "google"},
    {"id": "gemini-2.0-flash-exp", "name": "Gemini 2.0 Flash (Exp)", "provider": "google"},
    {"id": "gemini-1.5-flash", "name": "Gemini 1.5 Flash", "provider": "google"},
    {"id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro", "provider": "google"},
    # OpenAI GPT-5 Family (Latest)
    {"id": "gpt-5.2", "name": "GPT-5.2", "provider": "openai"},
    {"id": "gpt-5.2-pro", "name": "GPT-5.2 Pro", "provider": "openai"},
    {"id": "gpt-5.1-codex-max", "name": "GPT-5.1 Codex Max", "provider": "openai"},
    {"id": "gpt-5-mini", "name": "GPT-5 Mini", "provider": "openai"},
    {"id": "gpt-5-nano", "name": "GPT-5 Nano", "provider": "openai"},
    # OpenAI GPT-4 Family
    {"id": "gpt-4.1", "name": "GPT-4.1", "provider": "openai"},
    {"id": "gpt-4.1-mini", "name": "GPT-4.1 Mini", "provider": "openai"},
    {"id": "gpt-4o", "name": "GPT-4o", "provider": "openai"},
    {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "provider": "openai"},
    # OpenAI Reasoning Models
    {"id": "o3", "name": "o3 (Reasoning)", "provider": "openai"},
    {"id": "o3-mini", "name": "o3 Mini (Reasoning)", "provider": "openai"},
    {"id": "o1", "name": "o1 (Reasoning)", "provider": "openai"},
    {"id": "o1-mini", "name": "o1 Mini (Reasoning)", "provider": "openai"},
]

# User prompt template
USER_PROMPT_TEMPLATE = """Extract information from the following document into the exact JSON structure provided.

Document text:
{document_text}

Target JSON schema (populate all keys; leave unknowns as empty strings or empty arrays as appropriate):
{target_schema_json}"""


class ModelResult(BaseModel):
    model_id: str
    model_name: str
    provider: str
    success: bool
    json_data: Optional[Dict[str, Any]] = None
    raw_response: Optional[str] = None
    error: Optional[str] = None
    duration_ms: int = 0


class EvalResponse(BaseModel):
    success: bool
    results: List[ModelResult] = []
    error: Optional[str] = None


def read_system_prompt() -> str:
    """Read the system prompt from markdown file"""
    try:
        with open(SYSTEM_PROMPT_FILE, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "You are an expert document information extractor. Extract structured data from the provided document."


def parse_json_response(result_text: str) -> Dict[str, Any]:
    """Parse JSON from model response, handling various formats."""
    import re
    
    # First try direct JSON parsing
    try:
        return json.loads(result_text)
    except json.JSONDecodeError:
        pass
    
    # Try to extract JSON from markdown code blocks
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', result_text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass
    
    # Look for JSON object directly
    json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
    
    # Return raw response wrapped in dict
    return {"raw_response": result_text}


async def run_gemini_eval(
    client: genai.Client,
    model_id: str,
    model_name: str,
    uploaded_file,
    user_prompt: str,
    system_prompt: str
) -> ModelResult:
    """Run evaluation on a Gemini model."""
    start_time = time.time()
    
    try:
        response = client.models.generate_content(
            model=model_id,
            contents=[
                types.Part.from_uri(file_uri=uploaded_file.uri, mime_type="application/pdf"),
                f"{system_prompt}\n\n{user_prompt}"
            ],
        )
        
        duration_ms = int((time.time() - start_time) * 1000)
        result_text = response.text
        
        json_data = parse_json_response(result_text)
        is_raw = "raw_response" in json_data and len(json_data) == 1
        
        return ModelResult(
            model_id=model_id,
            model_name=model_name,
            provider="google",
            success=True,
            json_data=json_data if not is_raw else None,
            raw_response=result_text if is_raw else None,
            duration_ms=duration_ms
        )
    
    except ResourceExhausted as e:
        duration_ms = int((time.time() - start_time) * 1000)
        return ModelResult(
            model_id=model_id,
            model_name=model_name,
            provider="google",
            success=False,
            error=f"Quota exceeded: {str(e)}",
            duration_ms=duration_ms
        )
    except GoogleAPIError as e:
        duration_ms = int((time.time() - start_time) * 1000)
        return ModelResult(
            model_id=model_id,
            model_name=model_name,
            provider="google",
            success=False,
            error=f"API error: {str(e)}",
            duration_ms=duration_ms
        )
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        return ModelResult(
            model_id=model_id,
            model_name=model_name,
            provider="google",
            success=False,
            error=str(e),
            duration_ms=duration_ms
        )


async def run_openai_eval(
    client: OpenAI,
    model_id: str,
    model_name: str,
    pdf_base64: str,
    full_prompt: str,
    system_prompt: str
) -> ModelResult:
    """
    Run evaluation on an OpenAI model using the Responses API for GPT-5.x
    or Chat Completions for older models.
    """
    start_time = time.time()
    
    try:
        # Check if this is a GPT-5.x model (uses Responses API)
        is_gpt5 = model_id.startswith("gpt-5")
        
        if is_gpt5:
            # Use the new Responses API for GPT-5.x models
            # GPT-5.2 has native multimodal/vision support for PDFs
            response = client.responses.create(
                model=model_id,
                input=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_file",
                                "filename": "document.pdf",
                                "file_data": f"data:application/pdf;base64,{pdf_base64}"
                            },
                            {
                                "type": "input_text",
                                "text": full_prompt
                            }
                        ]
                    }
                ],
                reasoning={
                    "effort": "medium"  # Balanced reasoning for extraction tasks
                },
                text={
                    "verbosity": "low"  # Concise JSON output
                }
            )
            
            duration_ms = int((time.time() - start_time) * 1000)
            result_text = response.output_text
            
        else:
            # Use Chat Completions API for older models (GPT-4.x, o1, o3, etc.)
            # These models support vision with base64 images, but for PDFs we need text
            # Try vision API with PDF as image pages or fallback to text
            
            messages = [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:application/pdf;base64,{pdf_base64}",
                                "detail": "high"
                            }
                        },
                        {
                            "type": "text",
                            "text": full_prompt
                        }
                    ]
                }
            ]
            
            response = client.chat.completions.create(
                model=model_id,
                messages=messages,
                temperature=1.0,
            )
            
            duration_ms = int((time.time() - start_time) * 1000)
            result_text = response.choices[0].message.content
        
        json_data = parse_json_response(result_text)
        is_raw = "raw_response" in json_data and len(json_data) == 1
        
        return ModelResult(
            model_id=model_id,
            model_name=model_name,
            provider="openai",
            success=True,
            json_data=json_data if not is_raw else None,
            raw_response=result_text if is_raw else None,
            duration_ms=duration_ms
        )
    
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        error_msg = str(e)
        
        # Handle common OpenAI errors
        if "rate_limit" in error_msg.lower():
            error_msg = f"Rate limit exceeded: {error_msg}"
        elif "invalid_api_key" in error_msg.lower():
            error_msg = "Invalid OpenAI API key"
        elif "model_not_found" in error_msg.lower() or "does not exist" in error_msg.lower():
            error_msg = f"Model not available: {model_id}"
        
        return ModelResult(
            model_id=model_id,
            model_name=model_name,
            provider="openai",
            success=False,
            error=error_msg,
            duration_ms=duration_ms
        )


@app.get("/")
async def root():
    return {"message": "LLM Prompt Engineering Playground API is running"}


@app.get("/models")
async def get_models():
    """Return list of available models for evaluation"""
    return {"models": AVAILABLE_MODELS}


@app.get("/system-prompt")
async def get_system_prompt():
    """Return the current system prompt"""
    return {"system_prompt": read_system_prompt()}


@app.post("/eval", response_model=EvalResponse)
async def evaluate_models(
    file: UploadFile = File(...),
    models: str = Form(...),  # JSON array of model IDs
    target_schema: str = Form(...)  # JSON schema string
):
    """
    Run evaluation across multiple models with the same document and schema.
    Supports both Google Gemini and OpenAI models.
    """
    try:
        # Parse models list
        model_ids = json.loads(models)
        if not model_ids:
            return EvalResponse(success=False, error="No models selected")
        
        # Validate file type
        if not file.filename.endswith('.pdf'):
            return EvalResponse(success=False, error="File must be a PDF")
        
        # Validate target schema is valid JSON
        try:
            target_schema_obj = json.loads(target_schema)
            target_schema_formatted = json.dumps(target_schema_obj, indent=2)
        except json.JSONDecodeError:
            return EvalResponse(success=False, error="Target schema must be valid JSON")
        
        # Read PDF file
        contents = await file.read()
        pdf_base64 = base64.b64encode(contents).decode('utf-8')
        
        # Separate models by provider
        google_models = [m for m in model_ids if next((x for x in AVAILABLE_MODELS if x["id"] == m and x["provider"] == "google"), None)]
        openai_models = [m for m in model_ids if next((x for x in AVAILABLE_MODELS if x["id"] == m and x["provider"] == "openai"), None)]
        
        # Check API keys
        if google_models and not GEMINI_API_KEY:
            return EvalResponse(success=False, error="GEMINI_API_KEY not configured for Google models")
        if openai_models and not OPENAI_API_KEY:
            return EvalResponse(success=False, error="OPENAI_API_KEY not configured for OpenAI models")
        
        # Read system prompt
        system_prompt = read_system_prompt()
        
        # Build user prompt
        user_prompt = USER_PROMPT_TEMPLATE.format(
            document_text="[See attached PDF document]",
            target_schema_json=target_schema_formatted
        )
        
        results = []
        
        # Process Google Gemini models
        if google_models:
            gemini_client = genai.Client(api_key=GEMINI_API_KEY)
            
            # Create temporary file for PDF
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(contents)
                tmp_file_path = tmp_file.name
            
            try:
                # Upload the PDF file to Gemini
                uploaded_file = gemini_client.files.upload(path=tmp_file_path)
                
                # Wait for file to be processed
                while getattr(uploaded_file, "state", None) == "PROCESSING":
                    time.sleep(2)
                    uploaded_file = gemini_client.files.get(name=uploaded_file.name)
                
                if getattr(uploaded_file, "state", None) == "FAILED":
                    for model_id in google_models:
                        model_info = next((m for m in AVAILABLE_MODELS if m["id"] == model_id), None)
                        results.append(ModelResult(
                            model_id=model_id,
                            model_name=model_info["name"] if model_info else model_id,
                            provider="google",
                            success=False,
                            error="File upload to Gemini failed"
                        ))
                else:
                    # Run evaluations for each Google model
                    for model_id in google_models:
                        model_info = next((m for m in AVAILABLE_MODELS if m["id"] == model_id), None)
                        model_name = model_info["name"] if model_info else model_id
                        
                        result = await run_gemini_eval(
                            client=gemini_client,
                            model_id=model_id,
                            model_name=model_name,
                            uploaded_file=uploaded_file,
                            user_prompt=user_prompt,
                            system_prompt=system_prompt
                        )
                        results.append(result)
                
                # Clean up uploaded file
                try:
                    if uploaded_file and hasattr(uploaded_file, 'name'):
                        gemini_client.files.delete(name=uploaded_file.name)
                except:
                    pass
            
            finally:
                try:
                    os.unlink(tmp_file_path)
                except:
                    pass
        
        # Process OpenAI models
        if openai_models:
            openai_client = OpenAI(api_key=OPENAI_API_KEY)
            
            # Build full prompt for OpenAI
            openai_prompt = USER_PROMPT_TEMPLATE.format(
                document_text="[See attached PDF document - analyze the visual content]",
                target_schema_json=target_schema_formatted
            )
            
            # Run evaluations for each OpenAI model
            for model_id in openai_models:
                model_info = next((m for m in AVAILABLE_MODELS if m["id"] == model_id), None)
                model_name = model_info["name"] if model_info else model_id
                
                result = await run_openai_eval(
                    client=openai_client,
                    model_id=model_id,
                    model_name=model_name,
                    pdf_base64=pdf_base64,
                    full_prompt=openai_prompt,
                    system_prompt=system_prompt
                )
                results.append(result)
        
        return EvalResponse(success=True, results=results)
    
    except Exception as e:
        return EvalResponse(success=False, error=f"Error: {str(e)}")


# Keep legacy endpoint for backwards compatibility
@app.post("/parse")
async def parse_pdf(file: UploadFile = File(...)):
    """Legacy endpoint - redirects to eval with default model"""
    return {"message": "Please use the new /eval endpoint for model evaluation"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
