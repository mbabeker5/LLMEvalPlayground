-- LLM Eval Playground Database Schema
-- Run this in Supabase SQL Editor to create all tables

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==================== Prompt Versions ====================
CREATE TABLE IF NOT EXISTS prompt_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    version_number INTEGER NOT NULL DEFAULT 1,
    content TEXT NOT NULL,
    is_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Unique constraint: only one active version per prompt name per user
    CONSTRAINT unique_prompt_version UNIQUE (user_id, name, version_number)
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_prompt_versions_user ON prompt_versions(user_id);
CREATE INDEX IF NOT EXISTS idx_prompt_versions_active ON prompt_versions(user_id, name, is_active) WHERE is_active = TRUE;

-- ==================== Schemas ====================
CREATE TABLE IF NOT EXISTS schemas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    version_number INTEGER NOT NULL DEFAULT 1,
    parent_schema_id UUID REFERENCES schemas(id) ON DELETE SET NULL,
    schema_content JSON NOT NULL,
    is_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_schemas_user ON schemas(user_id);
CREATE INDEX IF NOT EXISTS idx_schemas_parent ON schemas(parent_schema_id);
CREATE INDEX IF NOT EXISTS idx_schemas_active ON schemas(user_id, name, is_active) WHERE is_active = TRUE;

-- ==================== Documents ====================
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    storage_path TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_documents_user ON documents(user_id);

-- ==================== Judges ====================
CREATE TABLE IF NOT EXISTS judges (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
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
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    prompt_version_id UUID NOT NULL REFERENCES prompt_versions(id) ON DELETE SET NULL,
    schema_id UUID REFERENCES schemas(id) ON DELETE SET NULL,
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    selected_models JSONB NOT NULL DEFAULT '[]'::jsonb,
    schema_content JSON, -- Inline schema snapshot at time of run
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

-- ==================== Row Level Security (RLS) ====================

-- Enable RLS on all tables
ALTER TABLE prompt_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE schemas ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE judges ENABLE ROW LEVEL SECURITY;
ALTER TABLE runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE run_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE judge_results ENABLE ROW LEVEL SECURITY;

-- Policies for prompt_versions
CREATE POLICY "Users can view their own prompts" ON prompt_versions
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can create their own prompts" ON prompt_versions
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update their own prompts" ON prompt_versions
    FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete their own prompts" ON prompt_versions
    FOR DELETE USING (auth.uid() = user_id);

-- Policies for schemas
CREATE POLICY "Users can view their own schemas" ON schemas
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can create their own schemas" ON schemas
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update their own schemas" ON schemas
    FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete their own schemas" ON schemas
    FOR DELETE USING (auth.uid() = user_id);

-- Policies for documents
CREATE POLICY "Users can view their own documents" ON documents
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can create their own documents" ON documents
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can delete their own documents" ON documents
    FOR DELETE USING (auth.uid() = user_id);

-- Policies for judges
CREATE POLICY "Users can view their own judges" ON judges
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can create their own judges" ON judges
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update their own judges" ON judges
    FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete their own judges" ON judges
    FOR DELETE USING (auth.uid() = user_id);

-- Policies for runs
CREATE POLICY "Users can view their own runs" ON runs
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can create their own runs" ON runs
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can delete their own runs" ON runs
    FOR DELETE USING (auth.uid() = user_id);

-- Policies for run_results (linked through runs)
CREATE POLICY "Users can view their own run results" ON run_results
    FOR SELECT USING (
        EXISTS (SELECT 1 FROM runs WHERE runs.id = run_results.run_id AND runs.user_id = auth.uid())
    );
CREATE POLICY "Users can create run results for their runs" ON run_results
    FOR INSERT WITH CHECK (
        EXISTS (SELECT 1 FROM runs WHERE runs.id = run_results.run_id AND runs.user_id = auth.uid())
    );

-- Policies for judge_results (linked through run_results -> runs)
CREATE POLICY "Users can view their own judge results" ON judge_results
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM run_results 
            JOIN runs ON runs.id = run_results.run_id 
            WHERE run_results.id = judge_results.run_result_id 
            AND runs.user_id = auth.uid()
        )
    );
CREATE POLICY "Users can create judge results for their run results" ON judge_results
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM run_results 
            JOIN runs ON runs.id = run_results.run_id 
            WHERE run_results.id = judge_results.run_result_id 
            AND runs.user_id = auth.uid()
        )
    );

-- ==================== Storage Bucket ====================
-- Run this separately or in Supabase dashboard:
-- INSERT INTO storage.buckets (id, name, public) VALUES ('documents', 'documents', false);

-- Storage policies for documents bucket
-- CREATE POLICY "Users can upload documents" ON storage.objects
--     FOR INSERT WITH CHECK (bucket_id = 'documents' AND auth.uid()::text = (storage.foldername(name))[1]);
-- CREATE POLICY "Users can view their documents" ON storage.objects
--     FOR SELECT USING (bucket_id = 'documents' AND auth.uid()::text = (storage.foldername(name))[1]);
-- CREATE POLICY "Users can delete their documents" ON storage.objects
--     FOR DELETE USING (bucket_id = 'documents' AND auth.uid()::text = (storage.foldername(name))[1]);



