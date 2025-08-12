-- Seraaj Event Store Database Schema
-- This schema supports event sourcing with projections for optimized queries

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Event Store Table - core of the event sourcing system
CREATE TABLE events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    aggregate_type TEXT NOT NULL,
    aggregate_id UUID NOT NULL,
    event_type TEXT NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    version INTEGER NOT NULL,
    payload JSONB NOT NULL,
    contracts_version TEXT NOT NULL DEFAULT '1.0.0',
    
    -- Ensure no duplicate versions per aggregate
    CONSTRAINT events_aggregate_version_unique UNIQUE (aggregate_id, version)
);

-- Indexes for efficient event retrieval
CREATE INDEX idx_events_aggregate ON events (aggregate_type, aggregate_id);
CREATE INDEX idx_events_type ON events (event_type);
CREATE INDEX idx_events_occurred ON events (occurred_at);
CREATE INDEX idx_events_version ON events (aggregate_id, version);

-- Application Projections - optimized read model for applications
CREATE TABLE applications (
    id UUID PRIMARY KEY,
    volunteer_id UUID NOT NULL,
    opportunity_id UUID NOT NULL,
    organization_id UUID,
    status TEXT NOT NULL,
    cover_letter TEXT,
    submitted_at TIMESTAMPTZ,
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    version INTEGER NOT NULL DEFAULT 0,
    
    -- Ensure one application per volunteer-opportunity pair
    CONSTRAINT applications_volunteer_opportunity_unique UNIQUE (volunteer_id, opportunity_id)
);

-- Indexes for application projections
CREATE INDEX idx_applications_volunteer ON applications (volunteer_id);
CREATE INDEX idx_applications_opportunity ON applications (opportunity_id);
CREATE INDEX idx_applications_status ON applications (status);
CREATE INDEX idx_applications_created ON applications (created_at);

-- Match Suggestions Projections - optimized read model for matching
CREATE TABLE match_suggestions (
    id UUID PRIMARY KEY,
    volunteer_id UUID NOT NULL,
    opportunity_id UUID NOT NULL,
    organization_id UUID NOT NULL,
    score DECIMAL(3,2) NOT NULL CHECK (score >= 0 AND score <= 1),
    score_components JSONB NOT NULL,
    explanation JSONB NOT NULL,
    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Ensure reasonable score range
    CONSTRAINT match_suggestions_score_range CHECK (score BETWEEN 0.0 AND 1.0)
);

-- Indexes for match suggestion projections
CREATE INDEX idx_match_suggestions_volunteer ON match_suggestions (volunteer_id);
CREATE INDEX idx_match_suggestions_opportunity ON match_suggestions (opportunity_id);
CREATE INDEX idx_match_suggestions_score ON match_suggestions (score DESC);
CREATE INDEX idx_match_suggestions_generated ON match_suggestions (generated_at);
CREATE INDEX idx_match_suggestions_status ON match_suggestions (status);

-- Event Store Statistics View (for monitoring)
CREATE VIEW event_store_stats AS
SELECT 
    aggregate_type,
    COUNT(*) as event_count,
    COUNT(DISTINCT aggregate_id) as aggregate_count,
    MIN(occurred_at) as first_event,
    MAX(occurred_at) as last_event
FROM events 
GROUP BY aggregate_type;

-- Application Statistics View 
CREATE VIEW application_stats AS
SELECT 
    status,
    COUNT(*) as count,
    MIN(created_at) as first_created,
    MAX(created_at) as last_created
FROM applications 
GROUP BY status;

-- Match Suggestion Statistics View
CREATE VIEW match_suggestion_stats AS  
SELECT 
    status,
    COUNT(*) as count,
    AVG(score) as avg_score,
    MIN(score) as min_score,
    MAX(score) as max_score
FROM match_suggestions 
GROUP BY status;