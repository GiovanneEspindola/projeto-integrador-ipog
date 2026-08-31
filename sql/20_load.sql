-- =============================================================================
-- 20_load.sql — carga public -> nw
-- =============================================================================
-- Migra 3311 das 3362 linhas de public para o modelo do projeto. As 51 que
-- ficam de fora são a tabela us_states, excluída do modelo por decisão
-- declarada (docs/02 §4.3). A validação está em 21_validacao_carga.sql.
--
-- Idempotente: TRUNCATE antes de inserir, então pode rodar quantas vezes quiser.
--   docker compose exec -T postgres psql -U pi -d northwind -f /sql/20_load.sql
--
-- QUATRO transformações, cada uma com motivo:
--   1. real -> numeric      nos valores monetários (docs/01 §4.1)
--   2. integer -> boolean   em products.discontinued (docs/01 §4.7)
--   3. btrim DEFENSIVO      nas chaves e nomes de texto. No dump usado aqui não
--      altera nenhuma linha — foi verificado, as 11 colunas dão zero. Fica
--      porque outras versões do Northwind usam bpchar e trazem espaço à direita.
--   4. renomes              ship_via -> shipper_id e *_description -> *_name,
--      porque o nome antigo descrevia o tipo do dado, não o significado.
--
-- TRÊS COLUNAS DE public FICAM DE FORA, e é decisão, não esquecimento:
--   categories.picture e employees.photo — são bytea de comprimento ZERO no
--     dump (8 e 9 linhas não nulas, 0 bytes cada). Coluna sem conteúdo.
--   employees.photo_path — caminho de rede de 1996 que não existe mais.
--   Nenhuma outra coluna é descartada; 21_validacao_carga.sql §8 confere isso
--   comparando as colunas das duas pontas contra esta lista.
-- =============================================================================

SET search_path TO nw;

-- As 11 tabelas estão listadas, então CASCADE é desnecessário.
-- RESTART IDENTITY zera as sequences; o setval no fim do arquivo as reposiciona.
TRUNCATE regions, territories, categories, suppliers, shippers,
         customers, employees, employee_territories, products,
         orders, order_items
    RESTART IDENTITY;

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
                       title_of_courtesy, birth_date, hire_date, address,
                       city, region, postal_code, country, home_phone,
                       extension, notes, reports_to)
SELECT employee_id, last_name, first_name, title,
       title_of_courtesy, birth_date, hire_date, address,
       city, region, postal_code, country, home_phone,
       extension, notes, reports_to
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

-- As chaves vieram prontas da origem, então as sequences de IDENTITY ainda
-- estão em 1 e o próximo INSERT sem id colidiria com uma linha existente.
-- setval reposiciona cada uma no maior id já usado.
SELECT setval(pg_get_serial_sequence('nw.regions',   'region_id'),   max(region_id))   FROM regions;
SELECT setval(pg_get_serial_sequence('nw.categories','category_id'), max(category_id)) FROM categories;
SELECT setval(pg_get_serial_sequence('nw.suppliers', 'supplier_id'), max(supplier_id)) FROM suppliers;
SELECT setval(pg_get_serial_sequence('nw.shippers',  'shipper_id'),  max(shipper_id))  FROM shippers;
SELECT setval(pg_get_serial_sequence('nw.employees', 'employee_id'), max(employee_id)) FROM employees;
SELECT setval(pg_get_serial_sequence('nw.products',  'product_id'),  max(product_id))  FROM products;
SELECT setval(pg_get_serial_sequence('nw.orders',    'order_id'),    max(order_id))    FROM orders;

ANALYZE regions, territories, categories, suppliers, shippers, customers,
        employees, employee_territories, products, orders, order_items;
