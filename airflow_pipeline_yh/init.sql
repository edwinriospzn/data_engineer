-- Tabla 1min
CREATE TABLE IF NOT EXISTS raw_intraday_1min (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    open DECIMAL(12,4),
    high DECIMAL(12,4),
    low DECIMAL(12,4),
    close DECIMAL(12,4),
    volume BIGINT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(ticker, timestamp)
);

-- Tabla 5min
CREATE TABLE IF NOT EXISTS raw_intraday_5min (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    open DECIMAL(12,4),
    high DECIMAL(12,4),
    low DECIMAL(12,4),
    close DECIMAL(12,4),
    volume BIGINT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(ticker, timestamp)
);

-- Tabla fundamental
CREATE TABLE IF NOT EXISTS raw_fundamental (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(20) NOT NULL,
    fetch_timestamp TIMESTAMP NOT NULL,
    market_cap BIGINT,
    trailing_pe DECIMAL(10,2),
    dividend_yield DECIMAL(8,4),
    sector VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(ticker, fetch_timestamp)
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_1min_ticker_time ON raw_intraday_1min(ticker, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_5min_ticker_time ON raw_intraday_5min(ticker, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_fundamental_ticker_time ON raw_fundamental(ticker, fetch_timestamp DESC);