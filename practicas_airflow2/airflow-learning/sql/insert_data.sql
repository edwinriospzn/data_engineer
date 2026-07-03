INSERT INTO customers (customer_id, name, city) VALUES (1, 'Ana', 'Barcelona') ON CONFLICT DO NOTHING;
INSERT INTO customers (customer_id, name, city) VALUES (2, 'Beto', 'Madrid') ON CONFLICT DO NOTHING;

INSERT INTO orders (order_id, customer_id, amount) VALUES (100, 1, 50) ON CONFLICT DO NOTHING;
INSERT INTO orders (order_id, customer_id, amount) VALUES (101, 2, 75) ON CONFLICT DO NOTHING;
