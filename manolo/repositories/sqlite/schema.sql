CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    title TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    tool_call_id TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (conversation_id) REFERENCES conversations (id)
);

CREATE TABLE IF NOT EXISTS runs (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    status TEXT NOT NULL,
    final_answer TEXT,
    last_error TEXT,
    started_at TEXT NOT NULL,
    ended_at TEXT,
    FOREIGN KEY (conversation_id) REFERENCES conversations (id)
);

CREATE TABLE IF NOT EXISTS run_steps (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    idx INTEGER NOT NULL,
    kind TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (run_id) REFERENCES runs (id)
);

CREATE TABLE IF NOT EXISTS calendar_events (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    starts_at TEXT NOT NULL,
    ends_at TEXT,
    description TEXT,
    location TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS fx_cache (
    pair TEXT PRIMARY KEY,
    rate REAL NOT NULL,
    fetched_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS memory_items (
    id TEXT PRIMARY KEY,
    key TEXT NOT NULL,
    tags TEXT,
    value_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_messages_conv ON messages (conversation_id, created_at);
CREATE INDEX IF NOT EXISTS idx_runsteps_run ON run_steps (run_id, idx);
CREATE INDEX IF NOT EXISTS idx_memory_key ON memory_items (key);
