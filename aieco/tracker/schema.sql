-- aieco tracker DB schema
-- 경로추적 + 예측모형 시스템

-- 뉴스 이벤트
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    headline TEXT NOT NULL,
    source TEXT,
    my_judgment TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

-- 리스크 팩터
CREATE TABLE IF NOT EXISTS risk_factors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    category TEXT NOT NULL  -- 'macro', 'financial', 'sector', 'geopolitical'
);

-- 경로 매핑: 이벤트 -> 팩터 -> 시장 영향
CREATE TABLE IF NOT EXISTS impact_paths (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER REFERENCES events(id),
    factor_id INTEGER REFERENCES risk_factors(id),
    path_description TEXT,
    expected_direction TEXT CHECK(expected_direction IN ('positive','negative','neutral')),
    actual_outcome TEXT,
    confidence REAL CHECK(confidence BETWEEN 0.0 AND 1.0),
    created_at TEXT DEFAULT (datetime('now')),
    reviewed_at TEXT
);

-- 베이스라인 예측
CREATE TABLE IF NOT EXISTS baseline (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    variable TEXT NOT NULL,
    forecast_value TEXT NOT NULL,
    reasoning TEXT,
    set_date TEXT NOT NULL,
    review_date TEXT,
    was_correct INTEGER,
    notes TEXT
);

-- 기본 리스크 팩터 시드 데이터
INSERT OR IGNORE INTO risk_factors (name, category) VALUES
    ('us_rate', 'macro'),
    ('inflation', 'macro'),
    ('oil_price', 'macro'),
    ('usdkrw', 'macro'),
    ('geopolitical', 'geopolitical'),
    ('liquidity', 'financial'),
    ('credit_spread', 'financial'),
    ('vix', 'financial'),
    ('china_growth', 'macro'),
    ('trade_policy', 'geopolitical');
