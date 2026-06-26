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

;

