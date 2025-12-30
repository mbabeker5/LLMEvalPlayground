"""
Pydantic models for API request/response validation.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ==================== Auth ====================

class UserInfo(BaseModel):
    user_id: str
    email: Optional[str] = None
    role: str = "authenticated"


# ==================== Prompt Versions ====================

class PromptVersionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    content: str = Field(..., min_length=1)
    is_active: bool = False


class PromptVersionUpdate(BaseModel):
    content: Optional[str] = None
    is_active: Optional[bool] = None


class PromptVersionResponse(BaseModel):
    id: str
    user_id: str
    name: str
    version_number: int
    content: str
    is_active: bool
    created_at: datetime


# ==================== Schemas ====================

class SchemaCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    schema_content: Dict[str, Any]
    parent_schema_id: Optional[str] = None  # For versioning - ID of the schema being edited
    is_active: Optional[bool] = False  # Set as active/default version


class SchemaResponse(BaseModel):
    id: str
    user_id: str
    name: str
    schema_content: Dict[str, Any]
    version_number: int = 1
    parent_schema_id: Optional[str] = None
    created_at: datetime


# ==================== Documents ====================

class DocumentResponse(BaseModel):
    id: str
    user_id: str
    filename: str
    storage_path: str
    created_at: datetime


# ==================== Judges ====================

class JudgeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = ""
    judge_prompt: str = Field(..., min_length=1)
    judge_model: str = Field(..., min_length=1)
    golden_set: Optional[Dict[str, Any]] = None
    input_variables: List[str] = Field(default_factory=list)
    parent_judge_id: Optional[str] = None  # For versioning - ID of the judge being edited


class JudgeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    judge_prompt: Optional[str] = None
    judge_model: Optional[str] = None
    golden_set: Optional[Dict[str, Any]] = None
    input_variables: Optional[List[str]] = None


class JudgeResponse(BaseModel):
    id: str
    user_id: str
    name: str
    description: str
    judge_prompt: str
    judge_model: str
    golden_set: Optional[Dict[str, Any]] = None
    input_variables: List[str] = Field(default_factory=list)
    created_at: datetime


# ==================== Runs ====================

class RunCreate(BaseModel):
    prompt_version_id: str
    schema_id: Optional[str] = None
    schema_content: Optional[Dict[str, Any]] = None  # Inline schema if no schema_id
    selected_models: List[str]


class ModelResult(BaseModel):
    model_id: str
    model_name: str
    provider: str
    success: bool
    json_data: Optional[Dict[str, Any]] = None
    raw_response: Optional[str] = None
    error: Optional[str] = None
    duration_ms: int = 0


class RunResultResponse(BaseModel):
    id: str
    run_id: str
    model_id: str
    provider: str
    output_json: Optional[Dict[str, Any]] = None
    raw_response: Optional[str] = None
    duration_ms: int
    success: bool
    error: Optional[str] = None


class RunResponse(BaseModel):
    id: str
    user_id: str
    prompt_version_id: str
    schema_id: Optional[str] = None
    document_id: str
    selected_models: List[str]
    created_at: datetime
    # Nested relations (optional)
    prompt_versions: Optional[Dict[str, Any]] = None
    schemas: Optional[Dict[str, Any]] = None
    documents: Optional[Dict[str, Any]] = None


class RunWithResultsResponse(BaseModel):
    run: RunResponse
    results: List[RunResultResponse]


class RunListItem(BaseModel):
    id: str
    created_at: datetime
    selected_models: List[str]
    prompt_name: Optional[str] = None
    prompt_version: Optional[int] = None
    document_name: Optional[str] = None
    success_count: int = 0
    total_count: int = 0


# ==================== Judge Results ====================

class JudgeRunRequest(BaseModel):
    judge_id: str


class JudgeResultResponse(BaseModel):
    id: str
    run_result_id: str
    judge_id: str
    judge_model_used: str
    evaluation: Dict[str, Any]
    reasoning: str
    passed: bool
    score: Optional[int] = None
    created_at: datetime
    # Nested
    judges: Optional[Dict[str, Any]] = None


# ==================== Eval Request/Response ====================

class EvalRequest(BaseModel):
    prompt_version_id: str
    schema_content: Dict[str, Any]
    selected_models: List[str]


class EvalResponse(BaseModel):
    success: bool
    run_id: Optional[str] = None
    results: List[ModelResult] = []
    error: Optional[str] = None


# ==================== Available Models ====================

class AvailableModel(BaseModel):
    id: str
    name: str
    provider: str


class ModelsResponse(BaseModel):
    models: List[AvailableModel]



