-- Event Store and Projections Schema for Seraaj
-- PostgreSQL 14+ required for gen_random_uuid()

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Event Store Table
CREATE TABLE IF NOT EXISTS events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    aggregate_type TEXT NOT NULL,
    aggregate_id UUID NOT NULL,
    event_type TEXT NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    version INTEGER NOT NULL,
    payload JSONB NOT NULL,
    contracts_version TEXT NOT NULL DEFAULT '1.0.0',
    
    CONSTRAINT events_aggregate_version_unique UNIQUE (aggregate_id, version)
);

-- Indexes for event store queries
CREATE INDEX IF NOT EXISTS idx_events_aggregate ON events (aggregate_type, aggregate_id);
CREATE INDEX IF NOT EXISTS idx_events_type ON events (event_type);
CREATE INDEX IF NOT EXISTS idx_events_occurred ON events (occurred_at);
CREATE INDEX IF NOT EXISTS idx_events_aggregate_id ON events (aggregate_id);

-- Application Projections Table
CREATE TABLE IF NOT EXISTS applications (
    id UUID PRIMARY KEY,
    volunteer_id UUID NOT NULL,
    opportunity_id UUID NOT NULL,
    organization_id UUID,
    status TEXT NOT NULL,
    cover_letter TEXT,
    submitted_at TIMESTAMPTZ,
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    version INTEGER NOT NULL DEFAULT 0,
    
    CONSTRAINT applications_volunteer_opportunity_unique UNIQUE (volunteer_id, opportunity_id)
);

-- Indexes for application queries
CREATE INDEX IF NOT EXISTS idx_applications_volunteer ON applications (volunteer_id);
CREATE INDEX IF NOT EXISTS idx_applications_opportunity ON applications (opportunity_id);
CREATE INDEX IF NOT EXISTS idx_applications_status ON applications (status);
CREATE INDEX IF NOT EXISTS idx_applications_created ON applications (created_at);

-- Match Suggestions Projections Table
CREATE TABLE IF NOT EXISTS match_suggestions (
    id UUID PRIMARY KEY,
    volunteer_id UUID NOT NULL,
    opportunity_id UUID NOT NULL,
    organization_id UUID NOT NULL,
    score DECIMAL(5,2) NOT NULL,
    score_components JSONB NOT NULL,
    explanation JSONB NOT NULL,
    generated_at TIMESTAMPTZ NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for match suggestion queries
CREATE INDEX IF NOT EXISTS idx_match_suggestions_volunteer ON match_suggestions (volunteer_id);
CREATE INDEX IF NOT EXISTS idx_match_suggestions_opportunity ON match_suggestions (opportunity_id);
CREATE INDEX IF NOT EXISTS idx_match_suggestions_score ON match_suggestions (score DESC);
CREATE INDEX IF NOT EXISTS idx_match_suggestions_generated ON match_suggestions (generated_at);
CREATE INDEX IF NOT EXISTS idx_match_suggestions_status ON match_suggestions (status);

-- View for active match suggestions
CREATE OR REPLACE VIEW active_match_suggestions AS
SELECT * FROM match_suggestions WHERE status = 'active';

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for automatic updated_at
CREATE TRIGGER update_applications_updated_at 
    BEFORE UPDATE ON applications 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_match_suggestions_updated_at 
    BEFORE UPDATE ON match_suggestions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();