-- LLM Eval Playground Database Schema (Simplified - No Auth Required)
-- Run this in Supabase SQL Editor to create all tables

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==================== Prompt Versions ====================
CREATE TABLE IF NOT EXISTS prompt_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL DEFAULT '00000000-0000-0000-0000-000000000001',
    name VARCHAR(100) NOT NULL,
    version_number INTEGER NOT NULL DEFAULT 1,
    content TEXT NOT NULL,
    is_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT unique_prompt_version UNIQUE (user_id, name, version_number)
);

CREATE INDEX IF NOT EXISTS idx_prompt_versions_user ON prompt_versions(user_id);

-- ==================== Schemas ====================
CREATE TABLE IF NOT EXISTS schemas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL DEFAULT '00000000-0000-0000-0000-000000000001',
    name VARCHAR(100) NOT NULL,
    version_number INTEGER NOT NULL DEFAULT 1,
    parent_schema_id UUID REFERENCES schemas(id) ON DELETE SET NULL,
    schema_content JSON NOT NULL,
    is_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_schemas_user ON schemas(user_id);
CREATE INDEX IF NOT EXISTS idx_schemas_name ON schemas(user_id, name);
CREATE INDEX IF NOT EXISTS idx_schemas_parent ON schemas(parent_schema_id);
CREATE INDEX IF NOT EXISTS idx_schemas_active ON schemas(user_id, name, is_active) WHERE is_active = TRUE;

-- ==================== Documents ====================
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL DEFAULT '00000000-0000-0000-0000-000000000001',
    filename VARCHAR(255) NOT NULL,
    storage_path TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_documents_user ON documents(user_id);

-- ==================== Judges ====================
CREATE TABLE IF NOT EXISTS judges (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL DEFAULT '00000000-0000-0000-0000-000000000001',
    name VARCHAR(100) NOT NULL,
    description TEXT DEFAULT '',
    judge_prompt TEXT NOT NULL,
    judge_model VARCHAR(100) NOT NULL,
    golden_set JSON,
    input_variables JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_judges_user ON judges(user_id);

-- ==================== Runs ====================
CREATE TABLE IF NOT EXISTS runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL DEFAULT '00000000-0000-0000-0000-000000000001',
    prompt_version_id UUID REFERENCES prompt_versions(id) ON DELETE SET NULL,
    schema_id UUID REFERENCES schemas(id) ON DELETE SET NULL,
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    selected_models JSONB NOT NULL DEFAULT '[]'::jsonb,
    schema_content JSON,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_runs_user ON runs(user_id);
CREATE INDEX IF NOT EXISTS idx_runs_prompt ON runs(prompt_version_id);
CREATE INDEX IF NOT EXISTS idx_runs_created ON runs(created_at DESC);

-- ==================== Run Results ====================
CREATE TABLE IF NOT EXISTS run_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id UUID NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    model_id VARCHAR(100) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    output_json JSON,
    raw_response TEXT,
    duration_ms INTEGER DEFAULT 0,
    success BOOLEAN DEFAULT TRUE,
    error TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_run_results_run ON run_results(run_id);

-- ==================== Judge Results ====================
CREATE TABLE IF NOT EXISTS judge_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_result_id UUID NOT NULL REFERENCES run_results(id) ON DELETE CASCADE,
    judge_id UUID NOT NULL REFERENCES judges(id) ON DELETE CASCADE,
    judge_model_used VARCHAR(100) NOT NULL,
    evaluation JSON NOT NULL DEFAULT '{}'::json,
    reasoning TEXT DEFAULT '',
    passed BOOLEAN DEFAULT FALSE,
    score INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_judge_results_run_result ON judge_results(run_result_id);
CREATE INDEX IF NOT EXISTS idx_judge_results_judge ON judge_results(judge_id);

-- ==================== Storage Bucket ====================
-- Create a storage bucket for documents (run in Supabase Dashboard -> Storage)
-- Or uncomment and run:
-- INSERT INTO storage.buckets (id, name, public) VALUES ('documents', 'documents', false) ON CONFLICT DO NOTHING;

