PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS digest_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    triggered_by TEXT NOT NULL CHECK (triggered_by IN ('scheduler', 'manual')),
    started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at TEXT NULL,
    fetched_count INTEGER NOT NULL DEFAULT 0,
    selected_count INTEGER NOT NULL DEFAULT 0,
    summarized_count INTEGER NOT NULL DEFAULT 0,
    email_status TEXT NOT NULL DEFAULT 'skipped'
        CHECK (email_status IN ('success', 'skipped', 'failed')),
    error_message TEXT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    description TEXT NULL,
    source_name TEXT NULL,
    published_at TEXT NOT NULL,
    category TEXT NOT NULL,
    summary TEXT NULL,
    summary_status TEXT NOT NULL DEFAULT 'pending'
        CHECK (summary_status IN ('pending', 'success', 'failed')),
    fetched_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_sent_run_id INTEGER NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (last_sent_run_id) REFERENCES digest_runs(id)
        ON DELETE SET NULL
        ON UPDATE NO ACTION
);

CREATE INDEX IF NOT EXISTS idx_articles_category_published_at
    ON articles (category, published_at DESC);

CREATE INDEX IF NOT EXISTS idx_articles_last_sent_run_id
    ON articles (last_sent_run_id);

CREATE INDEX IF NOT EXISTS idx_digest_runs_started_at
    ON digest_runs (started_at DESC);
