CREATE TABLE IF NOT EXISTS dataset_samples (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    label VARCHAR(64) NOT NULL,
    source_type VARCHAR(64) NOT NULL DEFAULT 'text',
    split VARCHAR(16) NOT NULL DEFAULT 'unsplit',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_dataset_samples_label ON dataset_samples(label);
CREATE INDEX IF NOT EXISTS idx_dataset_samples_split ON dataset_samples(split);

CREATE TABLE IF NOT EXISTS analysis_logs (
    id SERIAL PRIMARY KEY,
    input_text TEXT NOT NULL,
    classification VARCHAR(64) NOT NULL,
    confidence INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
