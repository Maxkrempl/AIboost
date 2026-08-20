-- AI Authority Foundation — SQLite Schema
-- Database: /home/hdwebd88/data/ai-authority.db

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stripe_session_id TEXT UNIQUE,
    stripe_subscription_id TEXT,
    stripe_customer_email TEXT,
    customer_name TEXT,
    customer_url TEXT,
    customer_notes TEXT,
    product TEXT DEFAULT 'ai_authority', -- 'ai_authority' or 'ai_authority_monthly'
    amount INTEGER, -- in cents
    status TEXT DEFAULT 'pending', -- pending, active, shield_expired, cancelled
    shield_start TEXT, -- ISO date when 3-month shield started
    shield_end TEXT, -- ISO date when shield ends
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS audits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER REFERENCES orders(id),
    url TEXT NOT NULL,
    score INTEGER, -- 0-100 GEO score
    has_llms_txt INTEGER DEFAULT 0, -- boolean
    has_schema_org INTEGER DEFAULT 0,
    has_open_graph INTEGER DEFAULT 0,
    has_meta_description INTEGER DEFAULT 0,
    has_structured_data INTEGER DEFAULT 0,
    has_robots_txt INTEGER DEFAULT 0,
    has_sitemap INTEGER DEFAULT 0,
    schema_types TEXT, -- JSON array of found Schema.org types
    missing_items TEXT, -- JSON array of missing items
    recommendations TEXT, -- JSON array of recommendations
    raw_report TEXT, -- full JSON report
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS generated_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER REFERENCES orders(id),
    audit_id INTEGER REFERENCES audits(id),
    file_type TEXT, -- 'llms_txt', 'schema_org', 'report'
    content TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS monthly_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER REFERENCES orders(id),
    report_month TEXT, -- YYYY-MM
    score_before INTEGER,
    score_after INTEGER,
    changes TEXT, -- JSON: what changed
    sent_at TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_orders_stripe ON orders(stripe_session_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_audits_order ON audits(order_id);
