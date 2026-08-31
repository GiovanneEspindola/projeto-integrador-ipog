-- =============================================================================
-- 20_load.sql — carga public -> nw
-- =============================================================================
-- Migra as 3362 linhas do Northwind original para o modelo do projeto,
-- aplicando as conversões que o schema nw exige. A validação da carga está
-- em 21_validacao_carga.sql e roda separado.
--
-- Idempotente: TRUNCATE antes de inserir, então pode rodar quantas vezes quiser.
--   docker compose exec -T postgres psql -U pi -d northwind -f /sql/20_load.sql
--
-- Três transformações acontecem aqui, e cada uma tem motivo:
--   1. real -> numeric      nos valores monetários (docs/01 §4.1)
--   2. integer -> boolean   em products.discontinued (docs/01 §4.7)
--   3. btrim                nas chaves e nomes de texto, contra espaço à direita
-- Duas colunas mudam de nome: ship_via -> shipper_id e *_description -> *_name,
-- porque o nome antigo descrevia o tipo do dado, não o que ele significa.
-- =============================================================================

SET search_path TO nw;

TRUNCATE regions, territories, categories, suppliers, shippers,
         customers, employees, employee_territories, products,
         orders, order_items
    RESTART IDENTITY CASCADE;

-- Ordem ditada pelas chaves estrangeiras: pai antes de filho.

INSERT INTO regions (region_id, region_name)
SELECT region_id, btrim(region_description)
FROM public.region;

INSERT INTO territories (territory_id, territory_name, region_id)
SELECT btrim(territory_id), btrim(territory_description), region_id
FROM public.territories;

INSERT INTO categories (category_id, category_name, description)
SELECT category_id, btrim(category_name), description
FROM public.categories;

INSERT INTO suppliers (supplier_id, company_name, contact_name, contact_title,
                       address, city, region, postal_code, country,
                       phone, fax, homepage)
SELECT supplier_id, btrim(company_name), contact_name, contact_title,
       address, city, region, postal_code, country, phone, fax, homepage
FROM public.suppliers;

INSERT INTO shippers (shipper_id, company_name, phone)
SELECT shipper_id, btrim(company_name), phone
FROM public.shippers;

INSERT INTO customers (customer_id, company_name, contact_name, contact_title,
                       address, city, region, postal_code, country, phone, fax)
SELECT btrim(customer_id), btrim(company_name), contact_name, contact_title,
       address, city, region, postal_code, country, phone, fax
FROM public.customers;

-- A auto-referência reports_to funciona numa única instrução porque o
-- PostgreSQL só verifica chave estrangeira no fim do comando, quando todas
-- as linhas já entraram.
INSERT INTO employees (employee_id, last_name, first_name, title,
                       birth_date, hire_date, address, city, region,
                       postal_code, country, home_phone, extension,
                       notes, reports_to)
SELECT employee_id, last_name, first_name, title,
       birth_date, hire_date, address, city, region,
       postal_code, country, home_phone, extension, notes, reports_to
FROM public.employees;

INSERT INTO employee_territories (employee_id, territory_id)
SELECT employee_id, btrim(territory_id)
FROM public.employee_territories;

INSERT INTO products (product_id, product_name, supplier_id, category_id,
                      quantity_per_unit, unit_price, units_in_stock,
                      units_on_order, reorder_level, discontinued)
SELECT product_id, btrim(product_name), supplier_id, category_id,
       quantity_per_unit,
       unit_price::numeric(10,2),
       units_in_stock, units_on_order, reorder_level,
       (discontinued = 1)
FROM public.products;

INSERT INTO orders (order_id, customer_id, employee_id, shipper_id,
                    order_date, required_date, shipped_date, freight,
                    ship_name, ship_address, ship_city, ship_region,
                    ship_postal_code, ship_country)
SELECT order_id, btrim(customer_id), employee_id, ship_via,
       order_date, required_date, shipped_date,
       freight::numeric(10,2),
       ship_name, ship_address, ship_city, ship_region,
       ship_postal_code, ship_country
FROM public.orders;

INSERT INTO order_items (order_id, product_id, unit_price, quantity, discount)
SELECT order_id, product_id,
       unit_price::numeric(10,2),
       quantity,
       discount::numeric(4,3)
FROM public.order_details;

ANALYZE;
