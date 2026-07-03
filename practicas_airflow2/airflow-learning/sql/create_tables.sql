CREATE TABLE IF NOT EXISTS customers (
  customer_id INT PRIMARY KEY,
  name TEXT,
  city TEXT
);

CREATE TABLE IF NOT EXISTS orders (
  order_id INT PRIMARY KEY,
  customer_id INT,
  amount INT
);
