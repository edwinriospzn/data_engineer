-- ============================================
-- PHYSICAL REPLICATION INITIALIZATION
-- ============================================

-- Create replication user
CREATE ROLE replica_user WITH LOGIN REPLICATION PASSWORD 'replica_password';

-- Create test table
CREATE TABLE IF NOT EXISTS employees (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    department VARCHAR(50),
    salary NUMERIC(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample data
INSERT INTO employees (name, department, salary) VALUES
    ('Alice Johnson', 'Engineering', 85000.00),
    ('Bob Smith', 'Marketing', 65000.00),
    ('Carol White', 'Sales', 72000.00),
    ('David Brown', 'Engineering', 92000.00),
    ('Eve Davis', 'HR', 58000.00),
    ('Frank Wilson', 'Finance', 78000.00),
    ('Grace Lee', 'Engineering', 88000.00),
    ('Henry Taylor', 'Marketing', 69000.00),
    ('Ivy Martinez', 'Sales', 75000.00),
    ('Jack Anderson', 'IT', 95000.00);

-- Insert more data for testing
INSERT INTO employees (name, department, salary)
SELECT 
    'Employee ' || g,
    (ARRAY['Engineering', 'Marketing', 'Sales', 'HR', 'Finance', 'IT'])[floor(random() * 6 + 1)],
    ROUND((random() * 50000 + 40000)::numeric, 2)
FROM generate_series(11, 1000) g;

-- Create indexes
CREATE INDEX idx_employees_department ON employees(department);
CREATE INDEX idx_employees_salary ON employees(salary);
CREATE INDEX idx_employees_created ON employees(created_at);

-- Analyze for query planner
ANALYZE employees;

-- Create view for monitoring
CREATE OR REPLACE VIEW employee_stats AS
SELECT 
    department,
    COUNT(*) as employee_count,
    ROUND(AVG(salary), 2) as avg_salary,
    ROUND(MIN(salary), 2) as min_salary,
    ROUND(MAX(salary), 2) as max_salary
FROM employees
GROUP BY department
ORDER BY avg_salary DESC;

-- Create function to simulate activity
CREATE OR REPLACE FUNCTION add_random_employee()
RETURNS VOID AS $$
DECLARE
    depts TEXT[] := ARRAY['Engineering', 'Marketing', 'Sales', 'HR', 'Finance', 'IT'];
    names TEXT[] := ARRAY['John', 'Mary', 'James', 'Patricia', 'Robert', 'Jennifer', 'Michael', 'Linda', 'William', 'Elizabeth'];
BEGIN
    INSERT INTO employees (name, department, salary)
    VALUES (
        names[floor(random() * array_length(names, 1) + 1)] || ' ' || names[floor(random() * array_length(names, 1) + 1)],
        depts[floor(random() * array_length(depts, 1) + 1)],
        ROUND((random() * 50000 + 40000)::numeric, 2)
    );
END;
$$ LANGUAGE plpgsql;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;

-- Allow replica_user to monitor
GRANT SELECT ON ALL TABLES IN SCHEMA public TO replica_user;

-- Show status
SELECT 
    'Physical DB initialized' as status,
    COUNT(*) as total_employees,
    MIN(created_at) as oldest_record,
    MAX(created_at) as newest_record
FROM employees;

-- Show replication user exists
SELECT 
    rolname as replication_user,
    rolreplication as has_replication_privilege
FROM pg_roles
WHERE rolname = 'replica_user';