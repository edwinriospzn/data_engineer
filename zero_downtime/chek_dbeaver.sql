-- On target database
SELECT subname, subenabled, subslotname FROM pg_subscription;

-- Check row counts
SELECT COUNT(*) FROM orders

SELECT * FROM orders ORDER BY order_id DESC LIMIT 10;

-- Check replication lag
SELECT 
    subname,
    subenabled,
    subslotname,
    pg_wal_lsn_diff(pg_current_wal_lsn(), confirmed_flush_lsn) as lag_bytes
FROM pg_subscription s
JOIN pg_replication_slots rs ON s.subslotname = rs.slot_name;