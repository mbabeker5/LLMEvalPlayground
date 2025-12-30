"""
LLM Eval Playground API
A prompt engineering platform with run history, versioning, and LLM-as-Judge evaluation.
"""

import os
import base64
import tempfile
import time
import asyncio
import json
from typing import Optional, List, Dict, Any
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv

# Google Gemini imports
from google import genai
from google.genai import types
from google.api_core.exceptions import ResourceExhausted, GoogleAPIError

# OpenAI imports
from openai import OpenAI

# Local imports
from auth import get_current_user_or_demo, get_current_user, get_optional_user
from models import (
    ModelResult, EvalResponse, PromptVersionCreate, PromptVersionUpdate,
    PromptVersionResponse, JudgeCreate, JudgeUpdate, JudgeResponse,
    JudgeRunRequest, JudgeResultResponse, RunListItem, RunWithResultsResponse,
    SchemaCreate, SchemaResponse, DocumentResponse, ModelsResponse, AvailableModel
)
import database as db

# Load environment variables
load_dotenv()

app = FastAPI(
    title="LLM Eval Playground",
    description="A prompt engineering platform with run history, versioning, and LLM-as-Judge evaluation",
    version="2.0.0"
)

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
                    "effort": "medium"
                },
                text={
                    "verbosity": "low"
                }
            )
            
            duration_ms = int((time.time() - start_time) * 1000)
            result_text = response.output_text
            
        else:
            # Use Chat Completions API for older models
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


async def run_judge_evaluation(
    judge: Dict[str, Any],
    model_output: Dict[str, Any],
    target_schema: Dict[str, Any],
    original_prompt: str
) -> Dict[str, Any]:
    """
    Run a judge evaluation on a model output.
    Returns evaluation result with reasoning, pass/fail, and optional score.
    """
    judge_prompt_template = judge["judge_prompt"]
    judge_model = judge["judge_model"]
    golden_set = judge.get("golden_set")
    
    # Build the judge prompt with variables
    judge_prompt = judge_prompt_template.replace("{{model_output}}", json.dumps(model_output, indent=2))
    judge_prompt = judge_prompt.replace("{{schema}}", json.dumps(target_schema, indent=2))
    judge_prompt = judge_prompt.replace("{{original_prompt}}", original_prompt)
    
    if golden_set:
        judge_prompt = judge_prompt.replace("{{golden_set}}", json.dumps(golden_set, indent=2))
    else:
        judge_prompt = judge_prompt.replace("{{golden_set}}", "Not provided")
    
    # Determine provider and call appropriate API
    model_info = next((m for m in AVAILABLE_MODELS if m["id"] == judge_model), None)
    if not model_info:
        return {
            "evaluation": {},
            "reasoning": f"Judge model {judge_model} not found",
            "passed": False,
            "score": None
        }
    
    provider = model_info["provider"]
    
    judge_system_prompt = """You are an LLM output evaluator. Analyze the model output and provide your evaluation.

Your response MUST be a valid JSON object with the following structure:
{
    "passed": true/false,
    "score": 0-100 (optional, include if appropriate),
    "reasoning": "Your detailed reasoning",
    "issues": ["list", "of", "specific", "issues"] (optional)
}

Be thorough but concise in your reasoning."""

    try:
        if provider == "google":
            if not GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY not configured")
            
            client = genai.Client(api_key=GEMINI_API_KEY)
            response = client.models.generate_content(
                model=judge_model,
                contents=[f"{judge_system_prompt}\n\n{judge_prompt}"]
            )
            result_text = response.text
            
        elif provider == "openai":
            if not OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY not configured")
            
            client = OpenAI(api_key=OPENAI_API_KEY)
            
            if judge_model.startswith("gpt-5"):
                response = client.responses.create(
                    model=judge_model,
                    input=[
                        {"role": "system", "content": judge_system_prompt},
                        {"role": "user", "content": judge_prompt}
                    ]
                )
                result_text = response.output_text
            else:
                response = client.chat.completions.create(
                    model=judge_model,
                    messages=[
                        {"role": "system", "content": judge_system_prompt},
                        {"role": "user", "content": judge_prompt}
                    ],
                    temperature=0.3
                )
                result_text = response.choices[0].message.content
        else:
            raise ValueError(f"Unknown provider: {provider}")
        
        # Parse the judge response
        evaluation = parse_json_response(result_text)
        
        return {
            "evaluation": evaluation,
            "reasoning": evaluation.get("reasoning", result_text),
            "passed": evaluation.get("passed", False),
            "score": evaluation.get("score")
        }
        
    except Exception as e:
        return {
            "evaluation": {},
            "reasoning": f"Judge evaluation failed: {str(e)}",
            "passed": False,
            "score": None
        }


# ==================== API Routes ====================

# Static files directory
STATIC_DIR = Path(__file__).parent


@app.get("/")
async def root():
    """Serve the main HTML page."""
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "LLM Eval Playground API v2.0"}


@app.get("/styles.css")
async def get_styles():
    """Serve CSS file."""
    return FileResponse(STATIC_DIR / "styles.css", media_type="text/css")


@app.get("/script.js")
async def get_script():
    """Serve JavaScript file."""
    return FileResponse(STATIC_DIR / "script.js", media_type="application/javascript")


@app.get("/api")
async def api_info():
    """API info endpoint."""
    return {"message": "LLM Eval Playground API v2.0"}


@app.get("/models")
async def get_models():
    """Return list of available models for evaluation"""
    return {"models": AVAILABLE_MODELS}


@app.get("/system-prompt")
async def get_system_prompt():
    """Return the current system prompt from file"""
    return {"system_prompt": read_system_prompt()}


# ==================== Prompt Versions ====================

@app.get("/prompts")
async def list_prompts(
    name: Optional[str] = None,
    user: dict = Depends(get_current_user_or_demo)
):
    """List all prompt versions for the current user."""
    prompts = db.get_prompt_versions(user["user_id"], name)
    return {"prompts": prompts}


@app.post("/prompts")
async def create_prompt(
    data: PromptVersionCreate,
    user: dict = Depends(get_current_user_or_demo)
):
    """Create a new prompt version."""
    prompt = db.create_prompt_version(
        user_id=user["user_id"],
        name=data.name,
        content=data.content,
        is_active=data.is_active
    )
    return {"prompt": prompt}


@app.get("/prompts/{prompt_id}")
async def get_prompt(
    prompt_id: str,
    user: dict = Depends(get_current_user_or_demo)
):
    """Get a specific prompt version."""
    prompt = db.get_prompt_version_by_id(prompt_id)
    if not prompt or prompt["user_id"] != user["user_id"]:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return {"prompt": prompt}


@app.put("/prompts/{prompt_id}")
async def update_prompt(
    prompt_id: str,
    data: PromptVersionUpdate,
    user: dict = Depends(get_current_user_or_demo)
):
    """Update a prompt version."""
    updates = {k: v for k, v in data.dict().items() if v is not None}
    prompt = db.update_prompt_version(prompt_id, user["user_id"], updates)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return {"prompt": prompt}


@app.delete("/prompts/{prompt_id}")
async def delete_prompt(
    prompt_id: str,
    user: dict = Depends(get_current_user_or_demo)
):
    """Delete a prompt version."""
    success = db.delete_prompt_version(prompt_id, user["user_id"])
    if not success:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return {"success": True}


@app.post("/prompts/{prompt_id}/versions")
async def create_new_version(
    prompt_id: str,
    content: str = Form(...),
    user: dict = Depends(get_current_user_or_demo)
):
    """Create a new version of an existing prompt."""
    existing = db.get_prompt_version_by_id(prompt_id)
    if not existing or existing["user_id"] != user["user_id"]:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    new_version = db.create_prompt_version(
        user_id=user["user_id"],
        name=existing["name"],
        content=content,
        is_active=False
    )
    return {"prompt": new_version}


# ==================== Schemas ====================

@app.get("/schemas")
async def list_schemas(user: dict = Depends(get_current_user_or_demo)):
    """List all saved schemas."""
    schemas = db.get_schemas(user["user_id"])
    return {"schemas": schemas}


@app.post("/schemas")
async def create_schema(
    data: SchemaCreate,
    user: dict = Depends(get_current_user_or_demo)
):
    """Save a new schema."""
    schema = db.create_schema(
        user_id=user["user_id"],
        name=data.name,
        schema_content=data.schema_content,
        parent_schema_id=data.parent_schema_id,
        is_active=data.is_active or False
    )
    return {"schema": schema}


@app.get("/schemas/{schema_id}")
async def get_schema(
    schema_id: str,
    user: dict = Depends(get_current_user_or_demo)
):
    """Get a specific schema by ID."""
    schema = db.get_schema_by_id(schema_id)
    if not schema or schema.get("user_id") != user["user_id"]:
        raise HTTPException(status_code=404, detail="Schema not found")
    return {"schema": schema}


@app.delete("/schemas/{schema_id}")
async def delete_schema(
    schema_id: str,
    user: dict = Depends(get_current_user_or_demo)
):
    """Delete a schema."""
    success = db.delete_schema(schema_id, user["user_id"])
    if not success:
        raise HTTPException(status_code=404, detail="Schema not found")
    return {"success": True}


# ==================== Judges ====================

@app.get("/judges")
async def list_judges(user: dict = Depends(get_current_user_or_demo)):
    """List all judge templates."""
    judges = db.get_judges(user["user_id"])
    return {"judges": judges}


@app.post("/judges")
async def create_judge(
    data: JudgeCreate,
    user: dict = Depends(get_current_user_or_demo)
):
    """Create a new judge template. If parent_judge_id is provided, creates a new version."""
    judge = db.create_judge(
        user_id=user["user_id"],
        name=data.name,
        description=data.description,
        judge_prompt=data.judge_prompt,
        judge_model=data.judge_model,
        golden_set=data.golden_set,
        input_variables=data.input_variables,
        parent_judge_id=data.parent_judge_id
    )
    return {"judge": judge}


@app.get("/judges/{judge_id}")
async def get_judge(
    judge_id: str,
    user: dict = Depends(get_current_user_or_demo)
):
    """Get a specific judge."""
    judge = db.get_judge_by_id(judge_id)
    if not judge or judge["user_id"] != user["user_id"]:
        raise HTTPException(status_code=404, detail="Judge not found")
    return {"judge": judge}


@app.put("/judges/{judge_id}")
async def update_judge(
    judge_id: str,
    data: JudgeUpdate,
    user: dict = Depends(get_current_user_or_demo)
):
    """Update a judge template."""
    updates = {k: v for k, v in data.dict().items() if v is not None}
    judge = db.update_judge(judge_id, user["user_id"], updates)
    if not judge:
        raise HTTPException(status_code=404, detail="Judge not found")
    return {"judge": judge}


@app.delete("/judges/{judge_id}")
async def delete_judge(
    judge_id: str,
    user: dict = Depends(get_current_user_or_demo)
):
    """Delete a judge template."""
    success = db.delete_judge(judge_id, user["user_id"])
    if not success:
        raise HTTPException(status_code=404, detail="Judge not found")
    return {"success": True}


# ==================== Runs ====================

@app.get("/runs")
async def list_runs(
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    user: dict = Depends(get_current_user_or_demo)
):
    """List all evaluation runs with pagination."""
    runs = db.get_runs(user["user_id"], limit, offset)
    
    # Transform to list items with aggregated info
    items = []
    for run in runs:
        results = db.get_run_results(run["id"])
        success_count = sum(1 for r in results if r["success"])
        
        items.append({
            "id": run["id"],
            "created_at": run["created_at"],
            "selected_models": run["selected_models"],
            "prompt_name": run.get("prompt_versions", {}).get("name") if run.get("prompt_versions") else None,
            "prompt_version": run.get("prompt_versions", {}).get("version_number") if run.get("prompt_versions") else None,
            "document_name": run.get("documents", {}).get("filename") if run.get("documents") else None,
            "success_count": success_count,
            "total_count": len(results)
        })
    
    return {"runs": items}


@app.get("/runs/{run_id}")
async def get_run(
    run_id: str,
    user: dict = Depends(get_current_user_or_demo)
):
    """Get a specific run with all results."""
    run = db.get_run_by_id(run_id)
    if not run or run["user_id"] != user["user_id"]:
        raise HTTPException(status_code=404, detail="Run not found")
    
    results = db.get_run_results(run_id)
    
    # Get judge results for each run result
    for result in results:
        result["judge_results"] = db.get_judge_results_for_run_result(result["id"])
    
    return {"run": run, "results": results}


@app.get("/runs/by-prompt/{prompt_version_id}")
async def get_runs_by_prompt(
    prompt_version_id: str,
    user: dict = Depends(get_current_user_or_demo)
):
    """Get all runs for a specific prompt version."""
    runs = db.get_runs_by_prompt(user["user_id"], prompt_version_id)
    return {"runs": runs}


# ==================== Eval (Main Evaluation Endpoint) ====================

@app.post("/eval", response_model=EvalResponse)
async def evaluate_models(
    file: UploadFile = File(...),
    models: str = Form(...),
    target_schema: str = Form(...),
    prompt_version_id: Optional[str] = Form(None),
    user: dict = Depends(get_current_user_or_demo)
):
    """
    Run evaluation across multiple models with the same document and schema.
    Now persists the run and results to the database.
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
        
        # Get or create prompt version
        if prompt_version_id:
            prompt_version = db.get_prompt_version_by_id(prompt_version_id)
            if not prompt_version:
                return EvalResponse(success=False, error="Prompt version not found")
            system_prompt = prompt_version["content"]
        else:
            # Use default system prompt and create a version for tracking
            system_prompt = read_system_prompt()
            prompt_version = db.create_prompt_version(
                user_id=user["user_id"],
                name="Default System Prompt",
                content=system_prompt,
                is_active=False
            )
            prompt_version_id = prompt_version["id"]
        
        # Upload document and create record
        try:
            storage_path = db.upload_file_to_storage(user["user_id"], contents, file.filename)
            document = db.create_document(
                user_id=user["user_id"],
                filename=file.filename,
                storage_path=storage_path
            )
            document_id = document["id"]
        except Exception as e:
            # If storage fails, continue without persisting document
            document_id = None
            print(f"Document storage failed: {e}")
        
        # Create run record
        run = None
        if document_id:
            try:
                run = db.create_run(
                    user_id=user["user_id"],
                    prompt_version_id=prompt_version_id,
                    schema_id=None,
                    document_id=document_id,
                    selected_models=model_ids,
                    schema_content=target_schema_obj
                )
            except Exception as e:
                print(f"Run creation failed: {e}")
        
        # Separate models by provider
        google_models = [m for m in model_ids if next((x for x in AVAILABLE_MODELS if x["id"] == m and x["provider"] == "google"), None)]
        openai_models = [m for m in model_ids if next((x for x in AVAILABLE_MODELS if x["id"] == m and x["provider"] == "openai"), None)]
        
        # Check API keys
        if google_models and not GEMINI_API_KEY:
            return EvalResponse(success=False, error="GEMINI_API_KEY not configured for Google models")
        if openai_models and not OPENAI_API_KEY:
            return EvalResponse(success=False, error="OPENAI_API_KEY not configured for OpenAI models")
        
        # Build user prompt
        user_prompt = USER_PROMPT_TEMPLATE.format(
            document_text="[See attached PDF document]",
            target_schema_json=target_schema_formatted
        )
        
        results = []
        
        # Process Google Gemini models
        if google_models:
            gemini_client = genai.Client(api_key=GEMINI_API_KEY)
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(contents)
                tmp_file_path = tmp_file.name
            
            try:
                uploaded_file = gemini_client.files.upload(path=tmp_file_path)
                
                while getattr(uploaded_file, "state", None) == "PROCESSING":
                    time.sleep(2)
                    uploaded_file = gemini_client.files.get(name=uploaded_file.name)
                
                if getattr(uploaded_file, "state", None) == "FAILED":
                    for model_id in google_models:
                        model_info = next((m for m in AVAILABLE_MODELS if m["id"] == model_id), None)
                        result = ModelResult(
                            model_id=model_id,
                            model_name=model_info["name"] if model_info else model_id,
                            provider="google",
                            success=False,
                            error="File upload to Gemini failed"
                        )
                        results.append(result)
                else:
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
                        
                        # Save result to database
                        if run:
                            try:
                                db.create_run_result(
                                    run_id=run["id"],
                                    model_id=result.model_id,
                                    provider=result.provider,
                                    output_json=result.json_data,
                                    raw_response=result.raw_response,
                                    duration_ms=result.duration_ms,
                                    success=result.success,
                                    error=result.error
                                )
                            except Exception as e:
                                print(f"Failed to save run result: {e}")
                
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
            
            openai_prompt = USER_PROMPT_TEMPLATE.format(
                document_text="[See attached PDF document - analyze the visual content]",
                target_schema_json=target_schema_formatted
            )
            
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
                
                # Save result to database
                if run:
                    try:
                        db.create_run_result(
                            run_id=run["id"],
                            model_id=result.model_id,
                            provider=result.provider,
                            output_json=result.json_data,
                            raw_response=result.raw_response,
                            duration_ms=result.duration_ms,
                            success=result.success,
                            error=result.error
                        )
                    except Exception as e:
                        print(f"Failed to save run result: {e}")
        
        return EvalResponse(
            success=True,
            run_id=run["id"] if run else None,
            results=results
        )
    
    except Exception as e:
        return EvalResponse(success=False, error=f"Error: {str(e)}")


# ==================== Judge Evaluation ====================

@app.post("/runs/{run_id}/results/{result_id}/judge")
async def judge_run_result(
    run_id: str,
    result_id: str,
    data: JudgeRunRequest,
    user: dict = Depends(get_current_user_or_demo)
):
    """Apply a judge to a specific run result."""
    # Verify run belongs to user
    run = db.get_run_by_id(run_id)
    if not run or run["user_id"] != user["user_id"]:
        raise HTTPException(status_code=404, detail="Run not found")
    
    # Get the run result
    result = db.get_run_result_by_id(result_id)
    if not result or result["run_id"] != run_id:
        raise HTTPException(status_code=404, detail="Run result not found")
    
    # Get the judge
    judge = db.get_judge_by_id(data.judge_id)
    if not judge or judge["user_id"] != user["user_id"]:
        raise HTTPException(status_code=404, detail="Judge not found")
    
    # Run the judge evaluation
    model_output = result.get("output_json") or {"raw_response": result.get("raw_response", "")}
    target_schema = run.get("schema_content", {})
    
    # Get the original prompt
    prompt_version = db.get_prompt_version_by_id(run["prompt_version_id"])
    original_prompt = prompt_version["content"] if prompt_version else ""
    
    evaluation_result = await run_judge_evaluation(
        judge=judge,
        model_output=model_output,
        target_schema=target_schema,
        original_prompt=original_prompt
    )
    
    # Save judge result
    judge_result = db.create_judge_result(
        run_result_id=result_id,
        judge_id=data.judge_id,
        judge_model_used=judge["judge_model"],
        evaluation=evaluation_result["evaluation"],
        reasoning=evaluation_result["reasoning"],
        passed=evaluation_result["passed"],
        score=evaluation_result["score"]
    )
    
    return {"judge_result": judge_result}


@app.post("/runs/{run_id}/judge-all")
async def judge_all_run_results(
    run_id: str,
    data: JudgeRunRequest,
    user: dict = Depends(get_current_user_or_demo)
):
    """Apply a judge to all results in a run."""
    # Verify run belongs to user
    run = db.get_run_by_id(run_id)
    if not run or run["user_id"] != user["user_id"]:
        raise HTTPException(status_code=404, detail="Run not found")
    
    # Get the judge
    judge = db.get_judge_by_id(data.judge_id)
    if not judge or judge["user_id"] != user["user_id"]:
        raise HTTPException(status_code=404, detail="Judge not found")
    
    # Get all run results
    results = db.get_run_results(run_id)
    
    # Get the original prompt
    prompt_version = db.get_prompt_version_by_id(run["prompt_version_id"])
    original_prompt = prompt_version["content"] if prompt_version else ""
    target_schema = run.get("schema_content", {})
    
    judge_results = []
    
    for result in results:
        if not result["success"]:
            continue
        
        model_output = result.get("output_json") or {"raw_response": result.get("raw_response", "")}
        
        evaluation_result = await run_judge_evaluation(
            judge=judge,
            model_output=model_output,
            target_schema=target_schema,
            original_prompt=original_prompt
        )
        
        judge_result = db.create_judge_result(
            run_result_id=result["id"],
            judge_id=data.judge_id,
            judge_model_used=judge["judge_model"],
            evaluation=evaluation_result["evaluation"],
            reasoning=evaluation_result["reasoning"],
            passed=evaluation_result["passed"],
            score=evaluation_result["score"]
        )
        
        judge_results.append(judge_result)
    
    return {"judge_results": judge_results}


# ==================== Add Models to Existing Run ====================

class AddModelsRequest(BaseModel):
    models: List[str]


@app.post("/runs/{run_id}/add-models")
async def add_models_to_run(
    run_id: str,
    data: AddModelsRequest,
    user: dict = Depends(get_current_user_or_demo)
):
    """Add additional models to an existing run."""
    # Verify run belongs to user
    run = db.get_run_by_id(run_id)
    if not run or run.get("user_id") != user["user_id"]:
        raise HTTPException(status_code=404, detail="Run not found")
    
    model_ids = data.models
    if not model_ids:
        return {"success": False, "error": "No models specified"}
    
    # Get existing results to avoid duplicates
    existing_results = db.get_run_results(run_id)
    existing_models = {r["model_id"] for r in existing_results}
    
    # Filter out models that already have results
    new_model_ids = [m for m in model_ids if m not in existing_models]
    if not new_model_ids:
        return {"success": False, "error": "All specified models already have results for this run"}
    
    # Get the document content
    document = run.get("documents") or db.get_document_by_id(run.get("document_id"))
    if not document:
        return {"success": False, "error": "Document not found for this run"}
    
    # Get the PDF content
    try:
        contents = db.get_file_from_storage(document.get("storage_path"))
        if not contents:
            return {"success": False, "error": "Could not retrieve document file"}
    except Exception as e:
        return {"success": False, "error": f"Failed to retrieve document: {str(e)}"}
    
    pdf_base64 = base64.b64encode(contents).decode('utf-8')
    
    # Get prompt content
    prompt_version = run.get("prompt_versions") or db.get_prompt_version_by_id(run.get("prompt_version_id"))
    system_prompt = prompt_version.get("content") if prompt_version else read_system_prompt()
    
    # Get schema
    target_schema_obj = run.get("schema_content") or {}
    target_schema_formatted = json.dumps(target_schema_obj, indent=2)
    
    # Build user prompt
    user_prompt = USER_PROMPT_TEMPLATE.format(
        document_text="[See attached PDF document]",
        target_schema_json=target_schema_formatted
    )
    
    # Separate models by provider
    google_models = [m for m in new_model_ids if next((x for x in AVAILABLE_MODELS if x["id"] == m and x["provider"] == "google"), None)]
    openai_models = [m for m in new_model_ids if next((x for x in AVAILABLE_MODELS if x["id"] == m and x["provider"] == "openai"), None)]
    
    # Check API keys
    if google_models and not GEMINI_API_KEY:
        return {"success": False, "error": "GEMINI_API_KEY not configured for Google models"}
    if openai_models and not OPENAI_API_KEY:
        return {"success": False, "error": "OPENAI_API_KEY not configured for OpenAI models"}
    
    results = []
    
    # Process Google Gemini models
    if google_models:
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(contents)
            tmp_file_path = tmp_file.name
        
        try:
            uploaded_file = gemini_client.files.upload(path=tmp_file_path)
            
            while getattr(uploaded_file, "state", None) == "PROCESSING":
                time.sleep(2)
                uploaded_file = gemini_client.files.get(name=uploaded_file.name)
            
            if getattr(uploaded_file, "state", None) != "FAILED":
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
                    
                    # Save result to database
                    try:
                        db.create_run_result(
                            run_id=run_id,
                            model_id=result.model_id,
                            provider=result.provider,
                            output_json=result.json_data,
                            raw_response=result.raw_response,
                            duration_ms=result.duration_ms,
                            success=result.success,
                            error=result.error
                        )
                    except Exception as e:
                        print(f"Failed to save run result: {e}")
            
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
        
        for model_id in openai_models:
            model_info = next((m for m in AVAILABLE_MODELS if m["id"] == model_id), None)
            model_name = model_info["name"] if model_info else model_id
            
            result = await run_openai_eval(
                client=openai_client,
                model_id=model_id,
                model_name=model_name,
                pdf_base64=pdf_base64,
                user_prompt=user_prompt,
                system_prompt=system_prompt
            )
            results.append(result)
            
            # Save result to database
            try:
                db.create_run_result(
                    run_id=run_id,
                    model_id=result.model_id,
                    provider=result.provider,
                    output_json=result.json_data,
                    raw_response=result.raw_response,
                    duration_ms=result.duration_ms,
                    success=result.success,
                    error=result.error
                )
            except Exception as e:
                print(f"Failed to save run result: {e}")
    
    return {
        "success": True,
        "results": [r.model_dump() for r in results],
        "run_id": run_id
    }


# ==================== Legacy Endpoint ====================

@app.post("/parse")
async def parse_pdf(file: UploadFile = File(...)):
    """Legacy endpoint - redirects to eval with default model"""
    return {"message": "Please use the new /eval endpoint for model evaluation"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
