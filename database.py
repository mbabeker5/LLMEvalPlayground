"""
Database operations for LLM Eval Playground.
Supports both Supabase (production) and in-memory storage (demo mode).
"""

import os
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

# Check if Supabase is configured
_supabase_configured = bool(SUPABASE_URL and SUPABASE_SERVICE_KEY)
_supabase_verified = False
USE_SUPABASE = False  # Will be set to True after successful connection test

# In-memory storage for demo mode
_memory_store = {
    "prompt_versions": [],
    "schemas": [],
    "documents": [],
    "judges": [],
    "runs": [],
    "run_results": [],
    "judge_results": [],
    "files": {}
}

# Supabase client (lazy initialized)
_supabase_client = None


def get_supabase():
    """Get or create Supabase client with service role key."""
    global _supabase_client, USE_SUPABASE, _supabase_verified
    
    if not _supabase_configured:
        return None
    
    if _supabase_client is None:
        try:
            from supabase import create_client
            _supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
            
            # Test the connection only once
            if not _supabase_verified:
                # Quick test query to verify connection works
                _supabase_client.table("prompt_versions").select("id").limit(1).execute()
                _supabase_verified = True
                USE_SUPABASE = True
                print("✅ Supabase connection verified - using database mode")
        except Exception as e:
            print(f"⚠️ Supabase connection failed: {e}")
            print("📦 Falling back to in-memory demo mode")
            _supabase_client = None
            USE_SUPABASE = False
            return None
    
    return _supabase_client


def _check_supabase():
    """Check if Supabase is available, attempt connection if not yet verified."""
    global USE_SUPABASE
    if _supabase_configured and not _supabase_verified:
        get_supabase()  # This will verify and set USE_SUPABASE
    return USE_SUPABASE


def _generate_id() -> str:
    """Generate a UUID string."""
    return str(uuid.uuid4())


def _now() -> str:
    """Get current timestamp as ISO string."""
    return datetime.utcnow().isoformat() + "Z"


# ==================== Prompt Versions ====================

def create_prompt_version(user_id: str, name: str, content: str, is_active: bool = False) -> Dict[str, Any]:
    """Create a new prompt version."""
    supabase = get_supabase()
    if supabase and USE_SUPABASE:
        try:
            existing = supabase.table("prompt_versions").select("version_number").eq("user_id", user_id).eq("name", name).order("version_number", desc=True).limit(1).execute()
            next_version = (existing.data[0]["version_number"] + 1) if existing.data else 1
            if is_active:
                supabase.table("prompt_versions").update({"is_active": False}).eq("user_id", user_id).eq("name", name).execute()
            result = supabase.table("prompt_versions").insert({
                "user_id": user_id, "name": name, "version_number": next_version,
                "content": content, "is_active": is_active
            }).execute()
            return result.data[0] if result.data else {}
        except Exception as e:
            print(f"Supabase error in create_prompt_version: {e}")
            # Fall through to in-memory mode
    # In-memory mode
        # In-memory mode
        existing = [p for p in _memory_store["prompt_versions"] if p["user_id"] == user_id and p["name"] == name]
        next_version = max([p["version_number"] for p in existing], default=0) + 1
        if is_active:
            for p in existing:
                p["is_active"] = False
        prompt = {
            "id": _generate_id(), "user_id": user_id, "name": name,
            "version_number": next_version, "content": content,
            "is_active": is_active, "created_at": _now()
        }
        _memory_store["prompt_versions"].append(prompt)
        return prompt


def get_prompt_versions(user_id: str, name: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get all prompt versions for a user, optionally filtered by name."""
    supabase = get_supabase()
    if supabase and USE_SUPABASE:
        try:
            query = supabase.table("prompt_versions").select("*").eq("user_id", user_id)
            if name:
                query = query.eq("name", name)
            result = query.order("created_at", desc=True).execute()
            return result.data or []
        except Exception as e:
            print(f"Supabase error in get_prompt_versions: {e}")
    # In-memory mode
        prompts = [p for p in _memory_store["prompt_versions"] if p["user_id"] == user_id]
        if name:
            prompts = [p for p in prompts if p["name"] == name]
        return sorted(prompts, key=lambda x: x["created_at"], reverse=True)


def get_prompt_version_by_id(prompt_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific prompt version by ID."""
    supabase = get_supabase()
    if supabase and USE_SUPABASE:
        try:
            result = supabase.table("prompt_versions").select("*").eq("id", prompt_id).limit(1).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Supabase error in get_prompt_version_by_id: {e}")
    # In-memory mode
        for p in _memory_store["prompt_versions"]:
            if p["id"] == prompt_id:
                return p
        return None


def update_prompt_version(prompt_id: str, user_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update a prompt version."""
    supabase = get_supabase()
    if supabase and USE_SUPABASE:
        try:
            if updates.get("is_active"):
                prompt = get_prompt_version_by_id(prompt_id)
                if prompt:
                    supabase.table("prompt_versions").update({"is_active": False}).eq("user_id", user_id).eq("name", prompt["name"]).execute()
            result = supabase.table("prompt_versions").update(updates).eq("id", prompt_id).eq("user_id", user_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Supabase error in update_prompt_version: {e}")
    # In-memory mode
        for p in _memory_store["prompt_versions"]:
            if p["id"] == prompt_id and p["user_id"] == user_id:
                if updates.get("is_active"):
                    for other in _memory_store["prompt_versions"]:
                        if other["user_id"] == user_id and other["name"] == p["name"]:
                            other["is_active"] = False
                p.update(updates)
                return p
        return None


def delete_prompt_version(prompt_id: str, user_id: str) -> bool:
    """Delete a prompt version."""
    supabase = get_supabase()
    if supabase and USE_SUPABASE:
        try:
            result = supabase.table("prompt_versions").delete().eq("id", prompt_id).eq("user_id", user_id).execute()
            return len(result.data) > 0 if result.data else False
        except Exception as e:
            print(f"Supabase error in delete_prompt_version: {e}")
    # In-memory mode
        for i, p in enumerate(_memory_store["prompt_versions"]):
            if p["id"] == prompt_id and p["user_id"] == user_id:
                _memory_store["prompt_versions"].pop(i)
                return True
        return False


def get_active_prompt(user_id: str, name: str) -> Optional[Dict[str, Any]]:
    """Get the active prompt version for a given name."""
    supabase = get_supabase()
    if supabase and USE_SUPABASE:
        try:
            result = supabase.table("prompt_versions").select("*").eq("user_id", user_id).eq("name", name).eq("is_active", True).limit(1).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Supabase error in get_active_prompt: {e}")
    # In-memory mode
        for p in _memory_store["prompt_versions"]:
            if p["user_id"] == user_id and p["name"] == name and p["is_active"]:
                return p
        return None


# ==================== Schemas ====================

def create_schema(
    user_id: str,
    name: str,
    schema_content: Dict[str, Any],
    parent_schema_id: Optional[str] = None,
    is_active: bool = False
) -> Dict[str, Any]:
    """Create a new schema. If parent_schema_id is provided, this is a new version."""
    # Calculate version number
    version_number = 1
    if parent_schema_id:
        root_id = get_schema_root_id(parent_schema_id, user_id)
        versions = get_schema_versions(root_id, user_id)
        version_number = len(versions) + 1
    
    supabase = get_supabase()
    if supabase and USE_SUPABASE:
        try:
            # If setting as active, deactivate other schemas with the same name
            if is_active:
                supabase.table("schemas").update({"is_active": False}).eq("user_id", user_id).eq("name", name).execute()
            
            insert_data = {
                "user_id": user_id,
                "name": name,
                "schema_content": schema_content,
                "version_number": version_number,
                "is_active": is_active
            }
            if parent_schema_id:
                insert_data["parent_schema_id"] = parent_schema_id
            result = supabase.table("schemas").insert(insert_data).execute()
            return result.data[0] if result.data else {}
        except Exception as e:
            # IMPORTANT: don't silently fall back here; it makes UI claim success while data isn't persisted.
            raise Exception(f"Supabase error in create_schema: {e}")
    # In-memory mode (only used when Supabase is not available)
    if is_active:
        # Deactivate other schemas with the same name
        for s in _memory_store["schemas"]:
            if s["user_id"] == user_id and s["name"] == name:
                s["is_active"] = False
    
    schema = {
        "id": _generate_id(),
        "user_id": user_id,
        "name": name,
        "schema_content": schema_content,
        "version_number": version_number,
        "parent_schema_id": parent_schema_id,
        "is_active": is_active,
        "created_at": _now()
    }
    _memory_store["schemas"].append(schema)
    return schema


def get_schema_root_id(schema_id: str, user_id: str) -> str:
    """Get the root schema ID by traversing parent_schema_id."""
    current_id = schema_id
    while True:
        schema = get_schema_by_id(current_id)
        if not schema or schema.get("user_id") != user_id:
            return current_id
        parent_id = schema.get("parent_schema_id")
        if not parent_id:
            return current_id
        current_id = parent_id


def get_schema_versions(root_schema_id: str, user_id: str) -> List[Dict[str, Any]]:
    """Get all versions of a schema by root id."""
    supabase = get_supabase()
    if supabase and USE_SUPABASE:
        try:
            result = supabase.table("schemas").select("*").eq("user_id", user_id).execute()
            all_schemas = result.data or []
        except Exception as e:
            print(f"Supabase error in get_schema_versions: {e}")
            all_schemas = []
    else:
        all_schemas = [s for s in _memory_store["schemas"] if s["user_id"] == user_id]

    schema_map = {s["id"]: s for s in all_schemas if "id" in s}
    versions: List[Dict[str, Any]] = []
    ids_to_check = {root_schema_id}
    checked_ids = set()

    while ids_to_check:
        current_id = ids_to_check.pop()
        checked_ids.add(current_id)
        s = schema_map.get(current_id)
        if s:
            versions.append(s)
        for candidate in all_schemas:
            if candidate.get("parent_schema_id") == current_id and candidate.get("id") not in checked_ids:
                ids_to_check.add(candidate["id"])

    return sorted(versions, key=lambda x: x.get("version_number", 1))


def get_schemas(user_id: str) -> List[Dict[str, Any]]:
    """Get all schemas for a user."""
    supabase = get_supabase()
    if supabase and USE_SUPABASE:
        try:
            result = supabase.table("schemas").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
            return result.data or []
        except Exception as e:
            print(f"Supabase error in get_schemas: {e}")
    # In-memory mode
        schemas = [s for s in _memory_store["schemas"] if s["user_id"] == user_id]
        return sorted(schemas, key=lambda x: x["created_at"], reverse=True)


def get_schema_by_id(schema_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific schema by ID."""
    supabase = get_supabase()
    if supabase and USE_SUPABASE:
        try:
            result = supabase.table("schemas").select("*").eq("id", schema_id).limit(1).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Supabase error in get_schema_by_id: {e}")
    # In-memory mode
        for s in _memory_store["schemas"]:
            if s["id"] == schema_id:
                return s
        return None


def delete_schema(schema_id: str, user_id: str) -> bool:
    """Delete a schema."""
    supabase = get_supabase()
    if supabase and USE_SUPABASE:
        try:
            result = supabase.table("schemas").delete().eq("id", schema_id).eq("user_id", user_id).execute()
            return len(result.data) > 0 if result.data else False
        except Exception as e:
            print(f"Supabase error in delete_schema: {e}")
    # In-memory mode
        for i, s in enumerate(_memory_store["schemas"]):
            if s["id"] == schema_id and s["user_id"] == user_id:
                _memory_store["schemas"].pop(i)
                return True
        return False


# ==================== Documents ====================

def create_document(user_id: str, filename: str, storage_path: str) -> Dict[str, Any]:
    """Create a document record."""
    supabase = get_supabase()
    if supabase and USE_SUPABASE:
        try:
            result = supabase.table("documents").insert({
                "user_id": user_id, "filename": filename, "storage_path": storage_path
            }).execute()
            return result.data[0] if result.data else {}
        except Exception as e:
            print(f"Supabase error in create_document: {e}")
    # In-memory mode
        doc = {
            "id": _generate_id(), "user_id": user_id, "filename": filename,
            "storage_path": storage_path, "created_at": _now()
        }
        _memory_store["documents"].append(doc)
        return doc


def get_documents(user_id: str) -> List[Dict[str, Any]]:
    """Get all documents for a user."""
    supabase = get_supabase()
    if supabase and USE_SUPABASE:
        try:
            result = supabase.table("documents").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
            return result.data or []
        except Exception as e:
            print(f"Supabase error in get_documents: {e}")
    # In-memory mode
        docs = [d for d in _memory_store["documents"] if d["user_id"] == user_id]
        return sorted(docs, key=lambda x: x["created_at"], reverse=True)


def get_document_by_id(document_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific document by ID."""
    supabase = get_supabase()
    if supabase and USE_SUPABASE:
        try:
            result = supabase.table("documents").select("*").eq("id", document_id).limit(1).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Supabase error in get_document_by_id: {e}")
    # In-memory mode
        for d in _memory_store["documents"]:
            if d["id"] == document_id:
                return d
        return None


# ==================== Judges ====================

def create_judge(
    user_id: str,
    name: str,
    description: str,
    judge_prompt: str,
    judge_model: str,
    golden_set: Optional[Dict[str, Any]] = None,
    input_variables: Optional[List[str]] = None,
    parent_judge_id: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new judge template. If parent_judge_id is provided, this is a new version."""
    # Calculate version number
    version_number = 1
    if parent_judge_id:
        # Find the root judge and count all versions
        root_id = get_judge_root_id(parent_judge_id, user_id)
        all_versions = get_judge_versions(root_id, user_id)
        version_number = len(all_versions) + 1
    
    supabase = get_supabase()
    if supabase and USE_SUPABASE:
        try:
            data = {
                "user_id": user_id, "name": name, "description": description,
                "judge_prompt": judge_prompt, "judge_model": judge_model,
                "golden_set": golden_set, "input_variables": input_variables or [],
                "version_number": version_number
            }
            if parent_judge_id:
                data["parent_judge_id"] = parent_judge_id
            result = supabase.table("judges").insert(data).execute()
            return result.data[0] if result.data else {}
        except Exception as e:
            print(f"Supabase error in create_judge: {e}")
    # In-memory mode
    judge = {
        "id": _generate_id(), "user_id": user_id, "name": name,
        "description": description, "judge_prompt": judge_prompt,
        "judge_model": judge_model, "golden_set": golden_set,
        "input_variables": input_variables or [], "created_at": _now(),
        "version_number": version_number, "parent_judge_id": parent_judge_id
    }
    _memory_store["judges"].append(judge)
    return judge


def get_judge_root_id(judge_id: str, user_id: str) -> str:
    """Get the root judge ID by traversing the parent chain."""
    current_id = judge_id
    while True:
        judge = get_judge_by_id(current_id)
        if not judge or judge.get("user_id") != user_id:
            return current_id
        parent_id = judge.get("parent_judge_id")
        if not parent_id:
            return current_id
        current_id = parent_id


def get_judge_versions(root_judge_id: str, user_id: str) -> List[Dict[str, Any]]:
    """Get all versions of a judge by root ID."""
    supabase = get_supabase()
    if supabase and USE_SUPABASE:
        try:
            # Get the root judge and all judges that have it as parent (direct or indirect)
            result = supabase.table("judges").select("*").eq("user_id", user_id).execute()
            all_judges = result.data or []
            
            # Build version chain
            versions = []
            ids_to_check = {root_judge_id}
            checked_ids = set()
            
            while ids_to_check:
                current_id = ids_to_check.pop()
                checked_ids.add(current_id)
                for j in all_judges:
                    if j["id"] == current_id:
                        versions.append(j)
                    if j.get("parent_judge_id") == current_id and j["id"] not in checked_ids:
                        ids_to_check.add(j["id"])
            
            return sorted(versions, key=lambda x: x.get("version_number", 1))
        except Exception as e:
            print(f"Supabase error in get_judge_versions: {e}")
    # In-memory mode
    all_judges = [j for j in _memory_store["judges"] if j["user_id"] == user_id]
    versions = []
    ids_to_check = {root_judge_id}
    checked_ids = set()
    
    while ids_to_check:
        current_id = ids_to_check.pop()
        checked_ids.add(current_id)
        for j in all_judges:
            if j["id"] == current_id:
                versions.append(j)
            if j.get("parent_judge_id") == current_id and j["id"] not in checked_ids:
                ids_to_check.add(j["id"])
    
    return sorted(versions, key=lambda x: x.get("version_number", 1))


def get_judges(user_id: str) -> List[Dict[str, Any]]:
    """Get all judges for a user."""
    supabase = get_supabase()
    if supabase and USE_SUPABASE:
        try:
            result = supabase.table("judges").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
            return result.data or []
        except Exception as e:
            print(f"Supabase error in get_judges: {e}")
    # In-memory mode
        judges = [j for j in _memory_store["judges"] if j["user_id"] == user_id]
        return sorted(judges, key=lambda x: x["created_at"], reverse=True)


def get_judge_by_id(judge_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific judge by ID."""
    supabase = get_supabase()
    if supabase and USE_SUPABASE:
        try:
            result = supabase.table("judges").select("*").eq("id", judge_id).limit(1).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Supabase error in get_judge_by_id: {e}")
    # In-memory mode
        for j in _memory_store["judges"]:
            if j["id"] == judge_id:
                return j
        return None


def update_judge(judge_id: str, user_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update a judge."""
    supabase = get_supabase()
    if supabase and USE_SUPABASE:
        try:
            result = supabase.table("judges").update(updates).eq("id", judge_id).eq("user_id", user_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Supabase error in update_judge: {e}")
    # In-memory mode
        for j in _memory_store["judges"]:
            if j["id"] == judge_id and j["user_id"] == user_id:
                j.update(updates)
                return j
        return None


def delete_judge(judge_id: str, user_id: str) -> bool:
    """Delete a judge."""
    supabase = get_supabase()
    if supabase and USE_SUPABASE:
        try:
            result = supabase.table("judges").delete().eq("id", judge_id).eq("user_id", user_id).execute()
            return len(result.data) > 0 if result.data else False
        except Exception as e:
            print(f"Supabase error in delete_judge: {e}")
    # In-memory mode
        for i, j in enumerate(_memory_store["judges"]):
            if j["id"] == judge_id and j["user_id"] == user_id:
                _memory_store["judges"].pop(i)
                return True
        return False


# ==================== Runs ====================

def create_run(
    user_id: str,
    prompt_version_id: str,
    schema_id: Optional[str],
    document_id: str,
    selected_models: List[str],
    schema_content: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create a new evaluation run."""
    supabase = get_supabase()
    if supabase and USE_SUPABASE:
        try:
            result = supabase.table("runs").insert({
                "user_id": user_id, "prompt_version_id": prompt_version_id,
                "schema_id": schema_id, "document_id": document_id,
                "selected_models": selected_models, "schema_content": schema_content
            }).execute()
            return result.data[0] if result.data else {}
        except Exception as e:
            print(f"Supabase error in create_run: {e}")
    # In-memory mode
        run = {
            "id": _generate_id(), "user_id": user_id,
            "prompt_version_id": prompt_version_id, "schema_id": schema_id,
            "document_id": document_id, "selected_models": selected_models,
            "schema_content": schema_content, "created_at": _now()
        }
        _memory_store["runs"].append(run)
        return run


def get_runs(user_id: str, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    """Get all runs for a user with pagination."""
    supabase = get_supabase()
    if supabase and USE_SUPABASE:
        try:
            result = supabase.table("runs").select(
                "*, prompt_versions(name, version_number), documents(filename)"
            ).eq("user_id", user_id).order("created_at", desc=True).range(offset, offset + limit - 1).execute()
            return result.data or []
        except Exception as e:
            print(f"Supabase error in get_runs: {e}")
    # In-memory mode
        runs = [r for r in _memory_store["runs"] if r["user_id"] == user_id]
        runs = sorted(runs, key=lambda x: x["created_at"], reverse=True)[offset:offset+limit]
        # Enrich with related data
        for run in runs:
            prompt = get_prompt_version_by_id(run["prompt_version_id"])
            doc = get_document_by_id(run["document_id"])
            run["prompt_versions"] = {"name": prompt["name"], "version_number": prompt["version_number"]} if prompt else None
            run["documents"] = {"filename": doc["filename"]} if doc else None
        return runs


def get_run_by_id(run_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific run by ID with full details."""
    supabase = get_supabase()
    if supabase and USE_SUPABASE:
        try:
            result = supabase.table("runs").select(
                "*, prompt_versions(*), schemas(*), documents(*)"
            ).eq("id", run_id).limit(1).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Supabase error in get_run_by_id: {e}")
    # In-memory mode
        for r in _memory_store["runs"]:
            if r["id"] == run_id:
                run = r.copy()
                run["prompt_versions"] = get_prompt_version_by_id(r["prompt_version_id"])
                run["schemas"] = get_schema_by_id(r["schema_id"]) if r["schema_id"] else None
                run["documents"] = get_document_by_id(r["document_id"])
                return run
        return None


def get_runs_by_prompt(user_id: str, prompt_version_id: str) -> List[Dict[str, Any]]:
    """Get all runs for a specific prompt version."""
    supabase = get_supabase()
    if supabase and USE_SUPABASE:
        try:
            result = supabase.table("runs").select(
                "*, documents(filename)"
            ).eq("user_id", user_id).eq("prompt_version_id", prompt_version_id).order("created_at", desc=True).execute()
            return result.data or []
        except Exception as e:
            print(f"Supabase error in get_runs_by_prompt: {e}")
    # In-memory mode
        runs = [r for r in _memory_store["runs"] if r["user_id"] == user_id and r["prompt_version_id"] == prompt_version_id]
        for run in runs:
            doc = get_document_by_id(run["document_id"])
            run["documents"] = {"filename": doc["filename"]} if doc else None
        return sorted(runs, key=lambda x: x["created_at"], reverse=True)


# ==================== Run Results ====================

def create_run_result(
    run_id: str,
    model_id: str,
    provider: str,
    output_json: Optional[Dict[str, Any]] = None,
    raw_response: Optional[str] = None,
    duration_ms: int = 0,
    success: bool = True,
    error: Optional[str] = None
) -> Dict[str, Any]:
    """Create a run result for a specific model."""
    supabase = get_supabase()
    if supabase and USE_SUPABASE:
        try:
            result = supabase.table("run_results").insert({
                "run_id": run_id, "model_id": model_id, "provider": provider,
                "output_json": output_json, "raw_response": raw_response,
                "duration_ms": duration_ms, "success": success, "error": error
            }).execute()
            return result.data[0] if result.data else {}
        except Exception as e:
            print(f"Supabase error in create_run_result: {e}")
    # In-memory mode
        result = {
            "id": _generate_id(), "run_id": run_id, "model_id": model_id,
            "provider": provider, "output_json": output_json,
            "raw_response": raw_response, "duration_ms": duration_ms,
            "success": success, "error": error, "created_at": _now()
        }
        _memory_store["run_results"].append(result)
        return result


def get_run_results(run_id: str) -> List[Dict[str, Any]]:
    """Get all results for a run."""
    supabase = get_supabase()
    if supabase and USE_SUPABASE:
        try:
            result = supabase.table("run_results").select("*").eq("run_id", run_id).execute()
            return result.data or []
        except Exception as e:
            print(f"Supabase error in get_run_results: {e}")
    # In-memory mode
        return [r for r in _memory_store["run_results"] if r["run_id"] == run_id]


def get_run_result_by_id(result_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific run result by ID."""
    supabase = get_supabase()
    if supabase and USE_SUPABASE:
        try:
            result = supabase.table("run_results").select("*").eq("id", result_id).limit(1).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Supabase error in get_run_result_by_id: {e}")
    # In-memory mode
        for r in _memory_store["run_results"]:
            if r["id"] == result_id:
                return r
        return None


# ==================== Judge Results ====================

def create_judge_result(
    run_result_id: str,
    judge_id: str,
    judge_model_used: str,
    evaluation: Dict[str, Any],
    reasoning: str,
    passed: bool,
    score: Optional[int] = None
) -> Dict[str, Any]:
    """Create a judge result for a run result."""
    supabase = get_supabase()
    if supabase and USE_SUPABASE:
        try:
            result = supabase.table("judge_results").insert({
                "run_result_id": run_result_id, "judge_id": judge_id,
                "judge_model_used": judge_model_used, "evaluation": evaluation,
                "reasoning": reasoning, "passed": passed, "score": score
            }).execute()
            return result.data[0] if result.data else {}
        except Exception as e:
            print(f"Supabase error in create_judge_result: {e}")
    # In-memory mode
        result = {
            "id": _generate_id(), "run_result_id": run_result_id,
            "judge_id": judge_id, "judge_model_used": judge_model_used,
            "evaluation": evaluation, "reasoning": reasoning,
            "passed": passed, "score": score, "created_at": _now()
        }
        _memory_store["judge_results"].append(result)
        return result


def get_judge_results_for_run_result(run_result_id: str) -> List[Dict[str, Any]]:
    """Get all judge results for a specific run result."""
    supabase = get_supabase()
    if supabase and USE_SUPABASE:
        try:
            result = supabase.table("judge_results").select(
                "*, judges(name, description)"
            ).eq("run_result_id", run_result_id).order("created_at", desc=True).execute()
            return result.data or []
        except Exception as e:
            print(f"Supabase error in get_judge_results_for_run_result: {e}")
    # In-memory mode
        results = [jr for jr in _memory_store["judge_results"] if jr["run_result_id"] == run_result_id]
        for jr in results:
            judge = get_judge_by_id(jr["judge_id"])
            jr["judges"] = {"name": judge["name"], "description": judge["description"]} if judge else None
        return sorted(results, key=lambda x: x["created_at"], reverse=True)


def get_judge_results_for_run(run_id: str) -> List[Dict[str, Any]]:
    """Get all judge results for all results in a run."""
    run_results = get_run_results(run_id)
    result_ids = [r["id"] for r in run_results]
    
    if not result_ids:
        return []
    
    supabase = get_supabase()
    if supabase and USE_SUPABASE:
        try:
            result = supabase.table("judge_results").select(
                "*, judges(name, description), run_results(model_id, provider)"
            ).in_("run_result_id", result_ids).order("created_at", desc=True).execute()
            return result.data or []
        except Exception as e:
            print(f"Supabase error in get_judge_results_for_run: {e}")
    # In-memory mode
        all_results = []
        for result_id in result_ids:
            all_results.extend(get_judge_results_for_run_result(result_id))
        return all_results


# ==================== File Storage ====================

def upload_file_to_storage(user_id: str, file_content: bytes, filename: str) -> str:
    """Upload a file to storage and return the path."""
    file_ext = filename.split('.')[-1] if '.' in filename else ''
    storage_path = f"{user_id}/{_generate_id()}.{file_ext}"
    
    supabase = get_supabase()
    if supabase and USE_SUPABASE:
        try:
            supabase.storage.from_("documents").upload(
                storage_path, file_content, {"content-type": "application/pdf"}
            )
            return storage_path
        except Exception as e:
            print(f"Supabase storage error: {e}")
    
    # In-memory storage
    _memory_store["files"][storage_path] = file_content
    return storage_path


def get_file_from_storage(storage_path: str) -> bytes:
    """Download a file from storage."""
    supabase = get_supabase()
    if supabase and USE_SUPABASE:
        try:
            return supabase.storage.from_("documents").download(storage_path)
        except Exception as e:
            print(f"Supabase storage download error: {e}")
    # In-memory storage
    return _memory_store["files"].get(storage_path, b"")

