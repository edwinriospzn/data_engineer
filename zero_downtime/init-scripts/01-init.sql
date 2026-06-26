-- Create the orders table
CREATE TABLE IF NOT EXISTS orders (
    order_id SERIAL PRIMARY KEY,
    customer_name TEXT,
    amount NUMERIC(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for performance
CREATE INDEX idx_orders_created ON orders(created_at);
CREATE INDEX idx_orders_customer ON orders(customer_name);
CREATE INDEX idx_orders_amount ON orders(amount);

-- Insert 10,000 sample rows
INSERT INTO orders (customer_name, amount)
SELECT
    'Customer ' || g,
    ROUND((random()*1000)::numeric, 2)
FROM generate_series(1,10000) g;

-- Insert some recent orders for performance testing
INSERT INTO orders (customer_name, amount, created_at)
SELECT
    'Recent Customer ' || g,
    ROUND((random()*1000)::numeric, 2),
    NOW() - (random() * interval '12 hours')
FROM generate_series(1,100) g;

-- Analyze the table for query planner
ANALYZE orders;

-- Verify data
SELECT 'Data loaded successfully' as status, 
       COUNT(*) as total_orders,
       MIN(created_at) as oldest_order,
       MAX(created_at) as newest_order
FROM orders;

-- Create a view for monitoring
CREATE OR REPLACE VIEW order_stats AS
SELECT 
    DATE(created_at) as order_date,
    COUNT(*) as order_count,
    SUM(amount) as total_amount,
    AVG(amount) as avg_amount
FROM orders
GROUP BY DATE(created_at)
ORDER BY order_date DESC;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;