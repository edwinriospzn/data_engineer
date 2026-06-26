SELECT a.* FROM actor a;
--## Module 1 — Querying (SQL Fundamentals & Analytics)

-- Exercise 1.1 — Explore the Data
/*
List:

film title
rental rate
replacement cost

for the first 20 films. 
*/
select
title,
rental_rate,
replacement_cost 
from film
limit 20
;
-- Exercise 1.2 — Joins
/*
Return:
film title
category name

One row per film-category combination.

Tables involved:
film
film_category
category
*/

select
f.title as film_title,
c.name as category
from 
film as f
left join 
film_category as fc
on f.film_id = fc.film_id
left join 
category as c
on fc.category_id =c.category_id 
order by f.title , c.name
;

--Exercise 1.3 — Aggregation
/*
For each category:

Return:

category name
number of films

Sort descending.
*/
with filmcate as (
select
f.title as film_title,
c.name as category
from 
film as f
left join 
film_category as fc
on f.film_id = fc.film_id
left join 
category as c
on fc.category_id =c.category_id 
order by f.title , c.name
)

select category,
count(film_title) as films
from filmcate
group by category
order by category
;

select
c.name as category,
count(f.title) as films
from 
film as f
left join 
film_category as fc
on f.film_id = fc.film_id
left join 
category as c
on fc.category_id =c.category_id 
group by c.name
order by c.name
;
--Exercise 1.4 — Multi-table Analytics
/*
Find the top 10 customers by total amount spent.

Return:

customer id
full name
total spent
*/
select
c.customer_id,
c.first_name ,
c.last_name ,
sum(p.amount) total_amount
from customer c 
left join payment p
on c.customer_id =p.customer_id 
group by 1,2,3
order by 4 desc
limit 10
;
--Exercise 1.5 — Window Functions
/*
Rank customers by total spending.

Return:

customer id
full name
total spent
rank

Use: rank()
*/
select
c.customer_id,
c.first_name ,
c.last_name ,
rank()  over (order by sum(p.amount) desc ) rank,
sum(p.amount) total_amount
from customer c 
left join payment p
on c.customer_id =p.customer_id 
group by 1,2,3
order by 4 asc
limit 10
;
--## Module 2 — Views
--Exercise 2.1
/*
Create:

vw_customer_spending

Columns:

customer_id
customer_name
total_spent
*/
create view vw_customer_spending as
select
c.customer_id,
concat(c.first_name,' ',c.last_name) customer_name,
sum(p.amount) total_spent
from customer c 
left join payment p
on c.customer_id =p.customer_id 
group by 1,2
order by 3 desc
;
select * from vw_customer_spending limit 20
;
--Exercise 2.2
/*
Create:

vw_film_popularity

Columns:

film_id
title
rental_count
*/
create view  vw_film_popularity as
select 
f.film_id,
f.title,
count(r.rental_id) rental_count
from film f
left join inventory i
on f.film_id = i.inventory_id 
left join rental r
on i.inventory_id  = r.inventory_id 
group by 1,2
order by 3 desc
;
select * from vw_film_popularity
;
--Exercise 2.3
/*
Query your view and find:

Top 10 customers.

Use the view only.
*/
select * from vw_customer_spending order by 3 desc limit 10
;
--## Module 3 — Materialized Views
--Exercise 3.1
/*
Create:

mv_monthly_revenue

Columns:

year
month
revenue
*/
select 
extract(YEAR from p.payment_date) as year,
extract(MONTH from p.payment_date) as month,
sum(p.amount) as revenue
from payment p
group by
extract(YEAR from p.payment_date),extract(MONTH from p.payment_date)
order by 3 desc
limit 20
;
create materialized view mv_monthly_revenue as 
select 
extract(YEAR from p.payment_date) as year,
extract(MONTH from p.payment_date) as month,
sum(p.amount) as revenue
from payment p
group by
extract(YEAR from p.payment_date),extract(MONTH from p.payment_date)
order by 3 desc
;
SELECT * FROM mv_monthly_revenue 
;
--Exercise 3.2
/*
Refresh the materialized view manually.

REFRESH MATERIALIZED VIEW ...
*/

REFRESH MATERIALIZED VIEW mv_monthly_revenue
;
--Exercise 3.3
/*
Create:

mv_top_films

Containing:

film title
rentals
revenue
*/
create materialized view mv_top_films as 
select 
f.title,
count(r.rental_id) rentals,
sum(p.amount) as revenue
from film f
left join inventory i
on f.film_id = i.inventory_id 
left join rental r
on i.inventory_id  = r.inventory_id
left join payment p
on p.rental_id =r.rental_id 
group by 1
order by 3 desc
;
--Exercise 3.4
/*
Compare:

EXPLAIN ANALYZE

on:

base query
materialized view

Observe performance differences.
*/

EXPLAIN analyze select * from mv_top_films
;
--## Module 4 — Functions
--Exercise 4.1
/*
Create:

get_customer_spending(customer_id)

Returns:

NUMERIC
*/
create or replace function get_customer_spending(p_customer_id integer)
returns numeric
language plpgsql
as $$
declare
total_spent numeric;
begin
select sum(p.amount) into total_spent
from payment p
where p.customer_id=p_customer_id;

return total_spent;
end;
$$;

select get_customer_spending(7);

select sum(amount)
from payment
where customer_id =7
;

--Exercise 4.2
/*
Create:

get_total_rentals(customer_id)

Returns:

INTEGER
*/
create or replace function get_total_rentals(r_customer_id integer)
returns integer
language plpgsql
as $$
declare
total_rentals numeric;
begin
select count(r.rental_id) into total_rentals
from rental r
where r.customer_id=r_customer_id;

return total_rentals;
end;
$$;

select get_total_rentals(7);

select count(rental_id)
from rental
where customer_id=7
;
--Exercise 4.3
/*
Create:

get_customer_tier(customer_id)

Rules:
< 50      Bronze
50-100    Silver
>100      Gold

Returns:
TEXT

Use:
IF
ELSIF
ELSE
*/
create or replace function get_customer_tier(p_customer_id integer)
returns text
language plpgsql
as $$
declare
total_spent numeric;
customer_tier text;
begin
--get total spent by specific customer
select coalesce(sum(p.amount),0) into total_spent
from payment p
where p.customer_id=p_customer_id;
--get tier case when
if total_spent < 50 then
	customer_tier:='Bronze';
ELSIF total_spent>=50 and total_spent <= 100 then
	customer_tier:='Silver';
else 
	customer_tier :='Gold';
end if;
return customer_tier;
end;
$$;

-- Testing
SELECT 
    customer_id,
    first_name,
    last_name,
    get_customer_spending(customer_id) AS total_spent,
    get_customer_tier(customer_id) AS tier
FROM customer
ORDER BY get_customer_spending(customer_id) DESC
LIMIT 10;


--## Module 5 — Table Functions
--Exercise 5.1
/*
Create:

top_customers(limit_value)

Returns:

TABLE
(
 customer_id,
 customer_name,
 total_spent
)
*/
create or replace function top_customers(limit_value integer)
returns table (
customer_id integer,
customer_name text,
total_spent numeric
)
language plpgsql
as $$
begin
	return query
	select
	c.customer_id,
	concat(c.first_name, ' ', c.last_name) as customer_name,
	coalesce(sum(p.amount),0) as total_spent
	from customer c
	left join payment p on
	c.customer_id=p.customer_id
	group by c.customer_id, c.first_name, c.last_name
	order by total_spent desc
	limit limit_value;
end;
$$;

SELECT * FROM top_customers(6);
--Exercise 5.2
/*
Create:

films_by_category(category_name)

Returns all films belonging to that category.
*/
create or replace function films_by_category(f_category_name text)
returns table(
category_name text,
title text,
description text,
film_id integer
)
language plpgsql
as $$
begin
	return query
	select
	c.name as category_name,
	f.title,
	f.description,
	f.film_id
	from film f
	left join film_category fc
	on f.film_id = fc.film_id
	left join category c
	on fc.category_id=c.category_id
	where c.name=f_category_name
	order by f.title asc;
end;
$$;
-- testing categories
SELECT * FROM films_by_category('Animation');

--Exercise 5.3
/*
Create:

customer_rental_history(customer_id)

Returns:

rental date
title
amount
*/
create or replace function customer_rental_history(f_customer_id integer)
returns table (
rental_date timestamptz,
title text,
amount numeric
)
language plpgsql
as $$
begin
	return query
	select
	r.rental_date,
	f.title,
	p.amount
	from rental r
	left join inventory i 
	on r.inventory_id =i.inventory_id
	left join film f
	on i.film_id = f.film_id
	left join payment p
	on r.rental_id = p.rental_id
	where r.customer_id=f_customer_id
	order by r.rental_date desc;
end;
$$;
-- test function
SELECT * FROM customer_rental_history(1);
;
drop function customer_rental_history;

--## Module 6 — Procedures
--Exercise 6.1
/*
Create:

refresh_reporting_views()

Refreshes:

mv_monthly_revenue
mv_top_films
*/
-- Create índex for better performance
CREATE UNIQUE INDEX idx_mv_top_films ON mv_top_films (title);

create or replace procedure refresh_reporting_views()
language plpgsql
as $$
begin
refresh materialized view mv_monthly_revenue;
refresh materialized view mv_top_films;
raise notice 'materialized views updated in %', now();
end;
$$;
call refresh_reporting_views()
;
--Exercise 6.2
/*
Create:

log_database_stats()

Insert into a custom table:

analytics_log

Store:

timestamp
total customers
total rentals
total payments
*/

create table if not exists analytics_log (
    id SERIAL primary key,
    log_timestamp timestamptz default now(),
    total_customers integer,
    total_rentals integer,
    total_payments integer
);
create or replace procedure log_database_stats()
language plpgsql
as $$
declare
v_total_customers integer;
v_total_rentals integer;
v_total_payments integer;
begin
	select count(*) into v_total_customers from customer;
	select count(*) into v_total_rentals from rental;
	select count(*) into v_total_payments from payment;
	insert into 
	analytics_log 
	(log_timestamp, total_customers, total_rentals, total_payments)
	values (current_timestamp, v_total_customers, v_total_rentals, v_total_payments);
	raise notice 'Log inserted in %: Customers=%, Rentals=%, Payments=%', 
        current_timestamp, v_total_customers, v_total_rentals, v_total_payments;
	exception
    when others then
        raise warning 'Error insertando log: %', sqlerrm;
end;
$$;
--Exercise 6.3
/*
Call the procedure.

CALL log_database_stats();

Verify rows were inserted.
*/
-- run procedure
CALL log_database_stats();

-- test log
SELECT * FROM analytics_log;


--## Module 7 — Loops
--Exercise 7.1
/*
Create a procedure that:

Loops through all categories.

For each category:

calculate film count
insert result into
category_summary

Use:

FOR rec IN
*/
create table if not exists category_summary (
id serial primary key,
category_name text,
film_count integer,
calculated_at timestamptz default now()
)
;
create or replace procedure process_category_summary()
language plpgsql
as $$
declare
	rec record;
	v_film_count integer;
begin
	for rec in 
		select category_id, name
		from category
		order by name
	loop
		select count(*) into v_film_count
		from film f
		join film_category fc on f.film_id=fc.film_id
		where fc.category_id = rec.category_id;
	
		insert into category_summary (category_name, film_count)
		values (rec.name, v_film_count);
		
		raise notice 'Categoría: %, Películas: %', rec.name, v_film_count;

	end loop;

		raise notice 'Proceso completado. Total categorías procesadas: %', 
        (SELECT COUNT(*) FROM category);

end;
$$;
CALL process_category_summary()
;
select * from category_summary;

;
--Exercise 7.2
/*
Loop through all customers.

Calculate:

total rentals

Store results in:

customer_metrics
*/
create table if not exists customer_metrics(
    id serial primary key,
    customer_id integer,
    customer_name text,
    total_rentals integer,
    total_spent numeric(10,2),
    calculated_at timestamptz default now()
)
;
create or replace procedure process_customer_metrics()
language plpgsql
as $$
declare
	rec record;
    v_total_rentals integer;
    v_total_spent numeric(10,2);
    v_counter integer := 0;
    v_total_customers integer;
begin
	select count(*) into v_total_customers from customer;

	truncate customer_metrics;

	for rec in
		select customer_id, first_name, last_name
		from customer
		order by customer_id
	loop
		v_counter := v_counter + 1;

		select
			count(r.rental_id),
			coalesce(sum(p.amount),0)
		into
			v_total_rentals,
			v_total_spent
		from rental r
		left join payment p on r.rental_id = p.rental_id
		where r.customer_id =rec.customer_id;

		insert into customer_metrics(
			customer_id,
			customer_name,
			total_rentals,
			total_spent
		) values (
            rec.customer_id,
            rec.first_name || ' ' || rec.last_name,
            v_total_rentals,
            v_total_spent
        );

		if v_counter % 100 = 0 OR v_counter = v_total_customers THEN
            RAISE NOTICE 'Progreso: %/% clientes procesados', v_counter, v_total_customers;
        END IF;
		END LOOP;

		RAISE NOTICE 'Proceso completado. % clientes procesados.', v_counter;
end;
$$;
call process_customer_metrics()
;
select * from customer_metrics
;
--## Module 8 — Triggers
--Exercise 8.1
/*
Create table:

customer_audit
*/
CREATE TABLE IF NOT EXISTS customer_audit (
    audit_id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    operation_type TEXT NOT NULL,
    changed_at TIMESTAMPTZ DEFAULT NOW(),
    changed_by TEXT DEFAULT CURRENT_USER,
    old_data JSONB,
    new_data JSONB
);
CREATE OR REPLACE FUNCTION audit_customer_changes()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    -- Para operación INSERT
    IF TG_OP = 'INSERT' THEN
        INSERT INTO customer_audit (
            customer_id,
            operation_type,
            new_data
        ) VALUES (
            NEW.customer_id,
            'INSERT',
            row_to_json(NEW)
        );
        RETURN NEW;
    
    -- Para operación UPDATE
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO customer_audit (
            customer_id,
            operation_type,
            old_data,
            new_data
        ) VALUES (
            NEW.customer_id,
            'UPDATE',
            row_to_json(OLD),
            row_to_json(NEW)
        );
        RETURN NEW;
    
    -- Para operación DELETE
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO customer_audit (
            customer_id,
            operation_type,
            old_data
        ) VALUES (
            OLD.customer_id,
            'DELETE',
            row_to_json(OLD)
        );
        RETURN OLD;
    END IF;
    
    RETURN NULL;
END;
$$;
--Exercise 8.2
/*
Create table:
Create trigger:

Whenever customer data changes.

Store:

customer id
timestamp
operation type

Examples:

INSERT
UPDATE
DELETE
*/
CREATE TRIGGER trg_customer_audit
AFTER INSERT OR UPDATE OR DELETE ON customer
FOR EACH ROW
EXECUTE FUNCTION audit_customer_changes();

-- testing
SELECT COUNT(*) AS total_customers FROM customer;

-- Insertar un nuevo cliente de prueba
INSERT INTO customer (
    store_id,
    first_name,
    last_name,
    email,
    address_id,
    active,
    create_date
) VALUES (
    1,                           -- store_id
    'Trigger',                   -- first_name
    'Test',                      -- last_name
    'trigger.test@example.com',  -- email
    1,                           -- address_id
    1,                           -- active (1 = activo)
    NOW()                        -- create_date
);

-- Obtener el ID del cliente recién creado
SELECT customer_id, first_name, last_name, email 
FROM customer 
WHERE email = 'trigger.test@example.com';

-- Ver el registro de auditoría del INSERT
SELECT 
    audit_id,
    customer_id,
    operation_type,
    changed_at,
    changed_by
FROM customer_audit
WHERE customer_id = (
    SELECT customer_id 
    FROM customer 
    WHERE email = 'trigger.test@example.com'
)
ORDER BY changed_at DESC;

-- Actualizar el cliente recién creado
UPDATE customer 
SET 
    first_name = 'TriggerUpdated',
    last_name = 'TestUpdated',
    email = 'trigger.updated@example.com',
    active = 0
WHERE email = 'trigger.test@example.com';

-- Verificar que se actualizó correctamente
SELECT customer_id, first_name, last_name, email, active
FROM customer 
WHERE email = 'trigger.updated@example.com';
-- Ver todos los registros de auditoría para este cliente
SELECT 
    audit_id,
    customer_id,
    operation_type,
    changed_at,
    changed_by,
    old_data,
    new_data
FROM customer_audit
WHERE customer_id = (
    SELECT customer_id 
    FROM customer 
    WHERE email = 'trigger.updated@example.com'
)
ORDER BY changed_at DESC;
