# Conferência da Entrega 1

Consultas executadas em uma transação somente leitura.

Dump SHA-256: `0ee30c01ba282f7194f38bf7f99cd6be0470b7ee5f67d0f7ca41fb058d735e0c`

## ambiente

```sql
SELECT current_database() AS banco, version() AS versao, current_timestamp AS verificado_em
```

| banco     | versao                                                                                                               | verificado_em                    |
|-----------|----------------------------------------------------------------------------------------------------------------------|----------------------------------|
| northwind | PostgreSQL 16.15 (Debian 16.15-1.pgdg13+2) on x86_64-pc-linux-gnu, compiled by gcc (Debian 14.2.0-19) 14.2.0, 64-bit | 2026-09-06 01:28:59.057986+00:00 |

## resumo

```sql
SELECT min(order_date) AS primeiro_pedido,
       max(order_date) AS ultimo_pedido,
       count(*) AS pedidos,
       count(DISTINCT customer_id) AS clientes_com_pedido
FROM public.orders;
```

| primeiro_pedido   | ultimo_pedido   | pedidos   | clientes_com_pedido   |
|-------------------|-----------------|-----------|-----------------------|
| 1996-07-04        | 1998-05-06      | 830       | 89                    |

## anos

```sql
SELECT extract(year FROM o.order_date)::int AS ano,
       count(DISTINCT o.order_id) AS pedidos,
       round(sum(d.unit_price::numeric * d.quantity *
                 (1 - d.discount::numeric)), 2) AS valor
FROM public.orders o
JOIN public.order_details d ON d.order_id = o.order_id
GROUP BY 1 ORDER BY 1;
```

| ano   | pedidos   | valor     |
|-------|-----------|-----------|
| 1996  | 152       | 208083.97 |
| 1997  | 408       | 617085.20 |
| 1998  | 270       | 440623.87 |

## valores

```sql
WITH totais AS (
  SELECT order_id,
         sum(unit_price::numeric * quantity *
             (1 - discount::numeric)) AS valor
  FROM public.order_details GROUP BY order_id
)
SELECT round(sum(valor), 2) AS total,
       round(avg(valor), 2) AS media,
       round(percentile_cont(0.5) WITHIN GROUP
             (ORDER BY valor)::numeric, 2) AS mediana,
       round(min(valor), 2) AS minimo,
       round(max(valor), 2) AS maximo
FROM totais;
```

| total      | media   | mediana   | minimo   | maximo   |
|------------|---------|-----------|----------|----------|
| 1265793.04 | 1525.05 | 943.25    | 12.50    | 16387.50 |

## categorias

```sql
SELECT c.category_name AS categoria,
       round(sum(d.unit_price::numeric * d.quantity *
                 (1 - d.discount::numeric)), 2) AS valor
FROM public.order_details d
JOIN public.products p ON p.product_id = d.product_id
JOIN public.categories c ON c.category_id = p.category_id
GROUP BY c.category_name ORDER BY valor DESC;
```

| categoria      | valor     |
|----------------|-----------|
| Beverages      | 267868.18 |
| Dairy Products | 234507.29 |
| Confections    | 167357.23 |
| Meat/Poultry   | 163022.36 |
| Seafood        | 131261.74 |
| Condiments     | 106047.09 |
| Produce        | 99984.58  |
| Grains/Cereals | 95744.59  |

## envio

```sql
SELECT count(*) AS pedidos,
       count(*) FILTER (WHERE shipped_date IS NULL) AS sem_data,
       round(100.0 * count(*) FILTER
         (WHERE shipped_date IS NULL) / count(*), 2) AS pct_sem_data,
       round(avg(shipped_date - order_date), 2) AS dias_ate_envio
FROM public.orders;
```

| pedidos   | sem_data   | pct_sem_data   | dias_ate_envio   |
|-----------|------------|----------------|------------------|
| 830       | 21         | 2.53           | 8.49             |

## integridade

```sql
SELECT 'pedido sem cliente válido' AS verificacao, count(*) AS casos
FROM public.orders o WHERE NOT EXISTS (
  SELECT 1 FROM public.customers c WHERE c.customer_id = o.customer_id)
UNION ALL
SELECT 'item sem pedido válido', count(*)
FROM public.order_details d WHERE NOT EXISTS (
  SELECT 1 FROM public.orders o WHERE o.order_id = d.order_id)
UNION ALL
SELECT 'pedido sem item', count(*)
FROM public.orders o WHERE NOT EXISTS (
  SELECT 1 FROM public.order_details d WHERE d.order_id = o.order_id);
```

| verificacao               | casos   |
|---------------------------|---------|
| pedido sem cliente válido | 0       |
| item sem pedido válido    | 0       |
| pedido sem item           | 0       |

## dominios

```sql
SELECT 'quantidade <= 0' AS verificacao, count(*) AS casos
FROM public.order_details WHERE quantity <= 0
UNION ALL
SELECT 'preço < 0', count(*) FROM public.order_details WHERE unit_price < 0
UNION ALL
SELECT 'desconto fora de [0, 1)', count(*)
FROM public.order_details WHERE discount < 0 OR discount >= 1
UNION ALL
SELECT 'envio anterior ao pedido', count(*)
FROM public.orders WHERE shipped_date < order_date;
```

| verificacao              | casos   |
|--------------------------|---------|
| quantidade <= 0          | 0       |
| preço < 0                | 0       |
| desconto fora de [0, 1)  | 0       |
| envio anterior ao pedido | 0       |

## precos

```sql
SELECT count(*) AS itens,
       count(*) FILTER
         (WHERE d.unit_price <> p.unit_price) AS precos_diferentes
FROM public.order_details d
JOIN public.products p ON p.product_id = d.product_id;
```

| itens   | precos_diferentes   |
|---------|---------------------|
| 2155    | 662                 |

## arredondamento

```sql
SELECT round(sum(unit_price::numeric * quantity *
                 (1 - discount::numeric)), 2) AS arredondar_total,
       sum(round(unit_price::numeric * quantity *
                 (1 - discount::numeric), 2)) AS arredondar_itens
FROM public.order_details;
```

| arredondar_total   | arredondar_itens   |
|--------------------|--------------------|
| 1265793.04         | 1265793.29         |

## contagem_categories

```sql
SELECT count(*) AS linhas FROM public."categories"
```

| linhas   |
|----------|
| 8        |

## nulos_categories_category_id

```sql
SELECT count(*) AS linhas, count(*) - count("category_id") AS nulos FROM public."categories"
```

| linhas   | nulos   |
|----------|---------|
| 8        | 0       |

## nulos_categories_category_name

```sql
SELECT count(*) AS linhas, count(*) - count("category_name") AS nulos FROM public."categories"
```

| linhas   | nulos   |
|----------|---------|
| 8        | 0       |

## nulos_categories_description

```sql
SELECT count(*) AS linhas, count(*) - count("description") AS nulos FROM public."categories"
```

| linhas   | nulos   |
|----------|---------|
| 8        | 0       |

## nulos_categories_picture

```sql
SELECT count(*) AS linhas, count(*) - count("picture") AS nulos FROM public."categories"
```

| linhas   | nulos   |
|----------|---------|
| 8        | 0       |

## contagem_customer_customer_demo

```sql
SELECT count(*) AS linhas FROM public."customer_customer_demo"
```

| linhas   |
|----------|
| 0        |

## nulos_customer_customer_demo_customer_id

```sql
SELECT count(*) AS linhas, count(*) - count("customer_id") AS nulos FROM public."customer_customer_demo"
```

| linhas   | nulos   |
|----------|---------|
| 0        | 0       |

## nulos_customer_customer_demo_customer_type_id

```sql
SELECT count(*) AS linhas, count(*) - count("customer_type_id") AS nulos FROM public."customer_customer_demo"
```

| linhas   | nulos   |
|----------|---------|
| 0        | 0       |

## contagem_customer_demographics

```sql
SELECT count(*) AS linhas FROM public."customer_demographics"
```

| linhas   |
|----------|
| 0        |

## nulos_customer_demographics_customer_type_id

```sql
SELECT count(*) AS linhas, count(*) - count("customer_type_id") AS nulos FROM public."customer_demographics"
```

| linhas   | nulos   |
|----------|---------|
| 0        | 0       |

## nulos_customer_demographics_customer_desc

```sql
SELECT count(*) AS linhas, count(*) - count("customer_desc") AS nulos FROM public."customer_demographics"
```

| linhas   | nulos   |
|----------|---------|
| 0        | 0       |

## contagem_customers

```sql
SELECT count(*) AS linhas FROM public."customers"
```

| linhas   |
|----------|
| 91       |

## nulos_customers_customer_id

```sql
SELECT count(*) AS linhas, count(*) - count("customer_id") AS nulos FROM public."customers"
```

| linhas   | nulos   |
|----------|---------|
| 91       | 0       |

## nulos_customers_company_name

```sql
SELECT count(*) AS linhas, count(*) - count("company_name") AS nulos FROM public."customers"
```

| linhas   | nulos   |
|----------|---------|
| 91       | 0       |

## nulos_customers_contact_name

```sql
SELECT count(*) AS linhas, count(*) - count("contact_name") AS nulos FROM public."customers"
```

| linhas   | nulos   |
|----------|---------|
| 91       | 0       |

## nulos_customers_contact_title

```sql
SELECT count(*) AS linhas, count(*) - count("contact_title") AS nulos FROM public."customers"
```

| linhas   | nulos   |
|----------|---------|
| 91       | 0       |

## nulos_customers_address

```sql
SELECT count(*) AS linhas, count(*) - count("address") AS nulos FROM public."customers"
```

| linhas   | nulos   |
|----------|---------|
| 91       | 0       |

## nulos_customers_city

```sql
SELECT count(*) AS linhas, count(*) - count("city") AS nulos FROM public."customers"
```

| linhas   | nulos   |
|----------|---------|
| 91       | 0       |

## nulos_customers_region

```sql
SELECT count(*) AS linhas, count(*) - count("region") AS nulos FROM public."customers"
```

| linhas   | nulos   |
|----------|---------|
| 91       | 60      |

## nulos_customers_postal_code

```sql
SELECT count(*) AS linhas, count(*) - count("postal_code") AS nulos FROM public."customers"
```

| linhas   | nulos   |
|----------|---------|
| 91       | 1       |

## nulos_customers_country

```sql
SELECT count(*) AS linhas, count(*) - count("country") AS nulos FROM public."customers"
```

| linhas   | nulos   |
|----------|---------|
| 91       | 0       |

## nulos_customers_phone

```sql
SELECT count(*) AS linhas, count(*) - count("phone") AS nulos FROM public."customers"
```

| linhas   | nulos   |
|----------|---------|
| 91       | 0       |

## nulos_customers_fax

```sql
SELECT count(*) AS linhas, count(*) - count("fax") AS nulos FROM public."customers"
```

| linhas   | nulos   |
|----------|---------|
| 91       | 22      |

## contagem_employee_territories

```sql
SELECT count(*) AS linhas FROM public."employee_territories"
```

| linhas   |
|----------|
| 49       |

## nulos_employee_territories_employee_id

```sql
SELECT count(*) AS linhas, count(*) - count("employee_id") AS nulos FROM public."employee_territories"
```

| linhas   | nulos   |
|----------|---------|
| 49       | 0       |

## nulos_employee_territories_territory_id

```sql
SELECT count(*) AS linhas, count(*) - count("territory_id") AS nulos FROM public."employee_territories"
```

| linhas   | nulos   |
|----------|---------|
| 49       | 0       |

## contagem_employees

```sql
SELECT count(*) AS linhas FROM public."employees"
```

| linhas   |
|----------|
| 9        |

## nulos_employees_employee_id

```sql
SELECT count(*) AS linhas, count(*) - count("employee_id") AS nulos FROM public."employees"
```

| linhas   | nulos   |
|----------|---------|
| 9        | 0       |

## nulos_employees_last_name

```sql
SELECT count(*) AS linhas, count(*) - count("last_name") AS nulos FROM public."employees"
```

| linhas   | nulos   |
|----------|---------|
| 9        | 0       |

## nulos_employees_first_name

```sql
SELECT count(*) AS linhas, count(*) - count("first_name") AS nulos FROM public."employees"
```

| linhas   | nulos   |
|----------|---------|
| 9        | 0       |

## nulos_employees_title

```sql
SELECT count(*) AS linhas, count(*) - count("title") AS nulos FROM public."employees"
```

| linhas   | nulos   |
|----------|---------|
| 9        | 0       |

## nulos_employees_title_of_courtesy

```sql
SELECT count(*) AS linhas, count(*) - count("title_of_courtesy") AS nulos FROM public."employees"
```

| linhas   | nulos   |
|----------|---------|
| 9        | 0       |

## nulos_employees_birth_date

```sql
SELECT count(*) AS linhas, count(*) - count("birth_date") AS nulos FROM public."employees"
```

| linhas   | nulos   |
|----------|---------|
| 9        | 0       |

## nulos_employees_hire_date

```sql
SELECT count(*) AS linhas, count(*) - count("hire_date") AS nulos FROM public."employees"
```

| linhas   | nulos   |
|----------|---------|
| 9        | 0       |

## nulos_employees_address

```sql
SELECT count(*) AS linhas, count(*) - count("address") AS nulos FROM public."employees"
```

| linhas   | nulos   |
|----------|---------|
| 9        | 0       |

## nulos_employees_city

```sql
SELECT count(*) AS linhas, count(*) - count("city") AS nulos FROM public."employees"
```

| linhas   | nulos   |
|----------|---------|
| 9        | 0       |

## nulos_employees_region

```sql
SELECT count(*) AS linhas, count(*) - count("region") AS nulos FROM public."employees"
```

| linhas   | nulos   |
|----------|---------|
| 9        | 4       |

## nulos_employees_postal_code

```sql
SELECT count(*) AS linhas, count(*) - count("postal_code") AS nulos FROM public."employees"
```

| linhas   | nulos   |
|----------|---------|
| 9        | 0       |

## nulos_employees_country

```sql
SELECT count(*) AS linhas, count(*) - count("country") AS nulos FROM public."employees"
```

| linhas   | nulos   |
|----------|---------|
| 9        | 0       |

## nulos_employees_home_phone

```sql
SELECT count(*) AS linhas, count(*) - count("home_phone") AS nulos FROM public."employees"
```

| linhas   | nulos   |
|----------|---------|
| 9        | 0       |

## nulos_employees_extension

```sql
SELECT count(*) AS linhas, count(*) - count("extension") AS nulos FROM public."employees"
```

| linhas   | nulos   |
|----------|---------|
| 9        | 0       |

## nulos_employees_photo

```sql
SELECT count(*) AS linhas, count(*) - count("photo") AS nulos FROM public."employees"
```

| linhas   | nulos   |
|----------|---------|
| 9        | 0       |

## nulos_employees_notes

```sql
SELECT count(*) AS linhas, count(*) - count("notes") AS nulos FROM public."employees"
```

| linhas   | nulos   |
|----------|---------|
| 9        | 0       |

## nulos_employees_reports_to

```sql
SELECT count(*) AS linhas, count(*) - count("reports_to") AS nulos FROM public."employees"
```

| linhas   | nulos   |
|----------|---------|
| 9        | 1       |

## nulos_employees_photo_path

```sql
SELECT count(*) AS linhas, count(*) - count("photo_path") AS nulos FROM public."employees"
```

| linhas   | nulos   |
|----------|---------|
| 9        | 0       |

## contagem_order_details

```sql
SELECT count(*) AS linhas FROM public."order_details"
```

| linhas   |
|----------|
| 2155     |

## nulos_order_details_order_id

```sql
SELECT count(*) AS linhas, count(*) - count("order_id") AS nulos FROM public."order_details"
```

| linhas   | nulos   |
|----------|---------|
| 2155     | 0       |

## nulos_order_details_product_id

```sql
SELECT count(*) AS linhas, count(*) - count("product_id") AS nulos FROM public."order_details"
```

| linhas   | nulos   |
|----------|---------|
| 2155     | 0       |

## nulos_order_details_unit_price

```sql
SELECT count(*) AS linhas, count(*) - count("unit_price") AS nulos FROM public."order_details"
```

| linhas   | nulos   |
|----------|---------|
| 2155     | 0       |

## nulos_order_details_quantity

```sql
SELECT count(*) AS linhas, count(*) - count("quantity") AS nulos FROM public."order_details"
```

| linhas   | nulos   |
|----------|---------|
| 2155     | 0       |

## nulos_order_details_discount

```sql
SELECT count(*) AS linhas, count(*) - count("discount") AS nulos FROM public."order_details"
```

| linhas   | nulos   |
|----------|---------|
| 2155     | 0       |

## contagem_orders

```sql
SELECT count(*) AS linhas FROM public."orders"
```

| linhas   |
|----------|
| 830      |

## nulos_orders_order_id

```sql
SELECT count(*) AS linhas, count(*) - count("order_id") AS nulos FROM public."orders"
```

| linhas   | nulos   |
|----------|---------|
| 830      | 0       |

## nulos_orders_customer_id

```sql
SELECT count(*) AS linhas, count(*) - count("customer_id") AS nulos FROM public."orders"
```

| linhas   | nulos   |
|----------|---------|
| 830      | 0       |

## nulos_orders_employee_id

```sql
SELECT count(*) AS linhas, count(*) - count("employee_id") AS nulos FROM public."orders"
```

| linhas   | nulos   |
|----------|---------|
| 830      | 0       |

## nulos_orders_order_date

```sql
SELECT count(*) AS linhas, count(*) - count("order_date") AS nulos FROM public."orders"
```

| linhas   | nulos   |
|----------|---------|
| 830      | 0       |

## nulos_orders_required_date

```sql
SELECT count(*) AS linhas, count(*) - count("required_date") AS nulos FROM public."orders"
```

| linhas   | nulos   |
|----------|---------|
| 830      | 0       |

## nulos_orders_shipped_date

```sql
SELECT count(*) AS linhas, count(*) - count("shipped_date") AS nulos FROM public."orders"
```

| linhas   | nulos   |
|----------|---------|
| 830      | 21      |

## nulos_orders_ship_via

```sql
SELECT count(*) AS linhas, count(*) - count("ship_via") AS nulos FROM public."orders"
```

| linhas   | nulos   |
|----------|---------|
| 830      | 0       |

## nulos_orders_freight

```sql
SELECT count(*) AS linhas, count(*) - count("freight") AS nulos FROM public."orders"
```

| linhas   | nulos   |
|----------|---------|
| 830      | 0       |

## nulos_orders_ship_name

```sql
SELECT count(*) AS linhas, count(*) - count("ship_name") AS nulos FROM public."orders"
```

| linhas   | nulos   |
|----------|---------|
| 830      | 0       |

## nulos_orders_ship_address

```sql
SELECT count(*) AS linhas, count(*) - count("ship_address") AS nulos FROM public."orders"
```

| linhas   | nulos   |
|----------|---------|
| 830      | 0       |

## nulos_orders_ship_city

```sql
SELECT count(*) AS linhas, count(*) - count("ship_city") AS nulos FROM public."orders"
```

| linhas   | nulos   |
|----------|---------|
| 830      | 0       |

## nulos_orders_ship_region

```sql
SELECT count(*) AS linhas, count(*) - count("ship_region") AS nulos FROM public."orders"
```

| linhas   | nulos   |
|----------|---------|
| 830      | 507     |

## nulos_orders_ship_postal_code

```sql
SELECT count(*) AS linhas, count(*) - count("ship_postal_code") AS nulos FROM public."orders"
```

| linhas   | nulos   |
|----------|---------|
| 830      | 19      |

## nulos_orders_ship_country

```sql
SELECT count(*) AS linhas, count(*) - count("ship_country") AS nulos FROM public."orders"
```

| linhas   | nulos   |
|----------|---------|
| 830      | 0       |

## contagem_products

```sql
SELECT count(*) AS linhas FROM public."products"
```

| linhas   |
|----------|
| 77       |

## nulos_products_product_id

```sql
SELECT count(*) AS linhas, count(*) - count("product_id") AS nulos FROM public."products"
```

| linhas   | nulos   |
|----------|---------|
| 77       | 0       |

## nulos_products_product_name

```sql
SELECT count(*) AS linhas, count(*) - count("product_name") AS nulos FROM public."products"
```

| linhas   | nulos   |
|----------|---------|
| 77       | 0       |

## nulos_products_supplier_id

```sql
SELECT count(*) AS linhas, count(*) - count("supplier_id") AS nulos FROM public."products"
```

| linhas   | nulos   |
|----------|---------|
| 77       | 0       |

## nulos_products_category_id

```sql
SELECT count(*) AS linhas, count(*) - count("category_id") AS nulos FROM public."products"
```

| linhas   | nulos   |
|----------|---------|
| 77       | 0       |

## nulos_products_quantity_per_unit

```sql
SELECT count(*) AS linhas, count(*) - count("quantity_per_unit") AS nulos FROM public."products"
```

| linhas   | nulos   |
|----------|---------|
| 77       | 0       |

## nulos_products_unit_price

```sql
SELECT count(*) AS linhas, count(*) - count("unit_price") AS nulos FROM public."products"
```

| linhas   | nulos   |
|----------|---------|
| 77       | 0       |

## nulos_products_units_in_stock

```sql
SELECT count(*) AS linhas, count(*) - count("units_in_stock") AS nulos FROM public."products"
```

| linhas   | nulos   |
|----------|---------|
| 77       | 0       |

## nulos_products_units_on_order

```sql
SELECT count(*) AS linhas, count(*) - count("units_on_order") AS nulos FROM public."products"
```

| linhas   | nulos   |
|----------|---------|
| 77       | 0       |

## nulos_products_reorder_level

```sql
SELECT count(*) AS linhas, count(*) - count("reorder_level") AS nulos FROM public."products"
```

| linhas   | nulos   |
|----------|---------|
| 77       | 0       |

## nulos_products_discontinued

```sql
SELECT count(*) AS linhas, count(*) - count("discontinued") AS nulos FROM public."products"
```

| linhas   | nulos   |
|----------|---------|
| 77       | 0       |

## contagem_region

```sql
SELECT count(*) AS linhas FROM public."region"
```

| linhas   |
|----------|
| 4        |

## nulos_region_region_id

```sql
SELECT count(*) AS linhas, count(*) - count("region_id") AS nulos FROM public."region"
```

| linhas   | nulos   |
|----------|---------|
| 4        | 0       |

## nulos_region_region_description

```sql
SELECT count(*) AS linhas, count(*) - count("region_description") AS nulos FROM public."region"
```

| linhas   | nulos   |
|----------|---------|
| 4        | 0       |

## contagem_shippers

```sql
SELECT count(*) AS linhas FROM public."shippers"
```

| linhas   |
|----------|
| 6        |

## nulos_shippers_shipper_id

```sql
SELECT count(*) AS linhas, count(*) - count("shipper_id") AS nulos FROM public."shippers"
```

| linhas   | nulos   |
|----------|---------|
| 6        | 0       |

## nulos_shippers_company_name

```sql
SELECT count(*) AS linhas, count(*) - count("company_name") AS nulos FROM public."shippers"
```

| linhas   | nulos   |
|----------|---------|
| 6        | 0       |

## nulos_shippers_phone

```sql
SELECT count(*) AS linhas, count(*) - count("phone") AS nulos FROM public."shippers"
```

| linhas   | nulos   |
|----------|---------|
| 6        | 0       |

## contagem_suppliers

```sql
SELECT count(*) AS linhas FROM public."suppliers"
```

| linhas   |
|----------|
| 29       |

## nulos_suppliers_supplier_id

```sql
SELECT count(*) AS linhas, count(*) - count("supplier_id") AS nulos FROM public."suppliers"
```

| linhas   | nulos   |
|----------|---------|
| 29       | 0       |

## nulos_suppliers_company_name

```sql
SELECT count(*) AS linhas, count(*) - count("company_name") AS nulos FROM public."suppliers"
```

| linhas   | nulos   |
|----------|---------|
| 29       | 0       |

## nulos_suppliers_contact_name

```sql
SELECT count(*) AS linhas, count(*) - count("contact_name") AS nulos FROM public."suppliers"
```

| linhas   | nulos   |
|----------|---------|
| 29       | 0       |

## nulos_suppliers_contact_title

```sql
SELECT count(*) AS linhas, count(*) - count("contact_title") AS nulos FROM public."suppliers"
```

| linhas   | nulos   |
|----------|---------|
| 29       | 0       |

## nulos_suppliers_address

```sql
SELECT count(*) AS linhas, count(*) - count("address") AS nulos FROM public."suppliers"
```

| linhas   | nulos   |
|----------|---------|
| 29       | 0       |

## nulos_suppliers_city

```sql
SELECT count(*) AS linhas, count(*) - count("city") AS nulos FROM public."suppliers"
```

| linhas   | nulos   |
|----------|---------|
| 29       | 0       |

## nulos_suppliers_region

```sql
SELECT count(*) AS linhas, count(*) - count("region") AS nulos FROM public."suppliers"
```

| linhas   | nulos   |
|----------|---------|
| 29       | 20      |

## nulos_suppliers_postal_code

```sql
SELECT count(*) AS linhas, count(*) - count("postal_code") AS nulos FROM public."suppliers"
```

| linhas   | nulos   |
|----------|---------|
| 29       | 0       |

## nulos_suppliers_country

```sql
SELECT count(*) AS linhas, count(*) - count("country") AS nulos FROM public."suppliers"
```

| linhas   | nulos   |
|----------|---------|
| 29       | 0       |

## nulos_suppliers_phone

```sql
SELECT count(*) AS linhas, count(*) - count("phone") AS nulos FROM public."suppliers"
```

| linhas   | nulos   |
|----------|---------|
| 29       | 0       |

## nulos_suppliers_fax

```sql
SELECT count(*) AS linhas, count(*) - count("fax") AS nulos FROM public."suppliers"
```

| linhas   | nulos   |
|----------|---------|
| 29       | 16      |

## nulos_suppliers_homepage

```sql
SELECT count(*) AS linhas, count(*) - count("homepage") AS nulos FROM public."suppliers"
```

| linhas   | nulos   |
|----------|---------|
| 29       | 24      |

## contagem_territories

```sql
SELECT count(*) AS linhas FROM public."territories"
```

| linhas   |
|----------|
| 53       |

## nulos_territories_territory_id

```sql
SELECT count(*) AS linhas, count(*) - count("territory_id") AS nulos FROM public."territories"
```

| linhas   | nulos   |
|----------|---------|
| 53       | 0       |

## nulos_territories_territory_description

```sql
SELECT count(*) AS linhas, count(*) - count("territory_description") AS nulos FROM public."territories"
```

| linhas   | nulos   |
|----------|---------|
| 53       | 0       |

## nulos_territories_region_id

```sql
SELECT count(*) AS linhas, count(*) - count("region_id") AS nulos FROM public."territories"
```

| linhas   | nulos   |
|----------|---------|
| 53       | 0       |

## contagem_us_states

```sql
SELECT count(*) AS linhas FROM public."us_states"
```

| linhas   |
|----------|
| 51       |

## nulos_us_states_state_id

```sql
SELECT count(*) AS linhas, count(*) - count("state_id") AS nulos FROM public."us_states"
```

| linhas   | nulos   |
|----------|---------|
| 51       | 0       |

## nulos_us_states_state_name

```sql
SELECT count(*) AS linhas, count(*) - count("state_name") AS nulos FROM public."us_states"
```

| linhas   | nulos   |
|----------|---------|
| 51       | 0       |

## nulos_us_states_state_abbr

```sql
SELECT count(*) AS linhas, count(*) - count("state_abbr") AS nulos FROM public."us_states"
```

| linhas   | nulos   |
|----------|---------|
| 51       | 0       |

## nulos_us_states_state_region

```sql
SELECT count(*) AS linhas, count(*) - count("state_region") AS nulos FROM public."us_states"
```

| linhas   | nulos   |
|----------|---------|
| 51       | 0       |

## inventario

| Tabela                 | Linhas   | Colunas   |
|------------------------|----------|-----------|
| categories             | 8        | 4         |
| customer_customer_demo | 0        | 2         |
| customer_demographics  | 0        | 2         |
| customers              | 91       | 11        |
| employee_territories   | 49       | 2         |
| employees              | 9        | 18        |
| order_details          | 2155     | 5         |
| orders                 | 830      | 14        |
| products               | 77       | 10        |
| region                 | 4        | 2         |
| shippers               | 6        | 3         |
| suppliers              | 29       | 12        |
| territories            | 53       | 3         |
| us_states              | 51       | 4         |

## nulos

| Coluna                  | Nulos   | Total   | %     |
|-------------------------|---------|---------|-------|
| customers.region        | 60      | 91      | 65.93 |
| customers.postal_code   | 1       | 91      | 1.10  |
| customers.fax           | 22      | 91      | 24.18 |
| employees.region        | 4       | 9       | 44.44 |
| employees.reports_to    | 1       | 9       | 11.11 |
| orders.shipped_date     | 21      | 830     | 2.53  |
| orders.ship_region      | 507     | 830     | 61.08 |
| orders.ship_postal_code | 19      | 830     | 2.29  |
| suppliers.region        | 20      | 29      | 68.97 |
| suppliers.fax           | 16      | 29      | 55.17 |
| suppliers.homepage      | 24      | 29      | 82.76 |

## constraints

```sql
SELECT n.nspname AS schema, c.contype AS tipo, count(*) AS quantidade FROM pg_constraint c JOIN pg_namespace n ON n.oid=c.connamespace WHERE n.nspname IN ('public','nw') GROUP BY 1,2 ORDER BY 1,2
```

| schema   | tipo   | quantidade   |
|----------|--------|--------------|
| nw       | c      | 17           |
| nw       | f      | 11           |
| nw       | p      | 11           |
| nw       | u      | 4            |
| public   | f      | 13           |
| public   | p      | 14           |

## indices_views

```sql
SELECT 'índices nw' AS objeto, count(*) FROM pg_indexes WHERE schemaname='nw' UNION ALL SELECT 'views nw', count(*) FROM information_schema.views WHERE table_schema='nw'
```

| objeto     | count   |
|------------|---------|
| índices nw | 19      |
| views nw   | 4       |

## tipos

```sql
SELECT table_name, column_name, data_type, is_nullable FROM information_schema.columns WHERE table_schema='public' ORDER BY table_name,ordinal_position
```

| table_name             | column_name           | data_type         | is_nullable   |
|------------------------|-----------------------|-------------------|---------------|
| categories             | category_id           | smallint          | NO            |
| categories             | category_name         | character varying | NO            |
| categories             | description           | text              | YES           |
| categories             | picture               | bytea             | YES           |
| customer_customer_demo | customer_id           | character varying | NO            |
| customer_customer_demo | customer_type_id      | character varying | NO            |
| customer_demographics  | customer_type_id      | character varying | NO            |
| customer_demographics  | customer_desc         | text              | YES           |
| customers              | customer_id           | character varying | NO            |
| customers              | company_name          | character varying | NO            |
| customers              | contact_name          | character varying | YES           |
| customers              | contact_title         | character varying | YES           |
| customers              | address               | character varying | YES           |
| customers              | city                  | character varying | YES           |
| customers              | region                | character varying | YES           |
| customers              | postal_code           | character varying | YES           |
| customers              | country               | character varying | YES           |
| customers              | phone                 | character varying | YES           |
| customers              | fax                   | character varying | YES           |
| employee_territories   | employee_id           | smallint          | NO            |
| employee_territories   | territory_id          | character varying | NO            |
| employees              | employee_id           | smallint          | NO            |
| employees              | last_name             | character varying | NO            |
| employees              | first_name            | character varying | NO            |
| employees              | title                 | character varying | YES           |
| employees              | title_of_courtesy     | character varying | YES           |
| employees              | birth_date            | date              | YES           |
| employees              | hire_date             | date              | YES           |
| employees              | address               | character varying | YES           |
| employees              | city                  | character varying | YES           |
| employees              | region                | character varying | YES           |
| employees              | postal_code           | character varying | YES           |
| employees              | country               | character varying | YES           |
| employees              | home_phone            | character varying | YES           |
| employees              | extension             | character varying | YES           |
| employees              | photo                 | bytea             | YES           |
| employees              | notes                 | text              | YES           |
| employees              | reports_to            | smallint          | YES           |
| employees              | photo_path            | character varying | YES           |
| order_details          | order_id              | smallint          | NO            |
| order_details          | product_id            | smallint          | NO            |
| order_details          | unit_price            | real              | NO            |
| order_details          | quantity              | smallint          | NO            |
| order_details          | discount              | real              | NO            |
| orders                 | order_id              | smallint          | NO            |
| orders                 | customer_id           | character varying | YES           |
| orders                 | employee_id           | smallint          | YES           |
| orders                 | order_date            | date              | YES           |
| orders                 | required_date         | date              | YES           |
| orders                 | shipped_date          | date              | YES           |
| orders                 | ship_via              | smallint          | YES           |
| orders                 | freight               | real              | YES           |
| orders                 | ship_name             | character varying | YES           |
| orders                 | ship_address          | character varying | YES           |
| orders                 | ship_city             | character varying | YES           |
| orders                 | ship_region           | character varying | YES           |
| orders                 | ship_postal_code      | character varying | YES           |
| orders                 | ship_country          | character varying | YES           |
| products               | product_id            | smallint          | NO            |
| products               | product_name          | character varying | NO            |
| products               | supplier_id           | smallint          | YES           |
| products               | category_id           | smallint          | YES           |
| products               | quantity_per_unit     | character varying | YES           |
| products               | unit_price            | real              | YES           |
| products               | units_in_stock        | smallint          | YES           |
| products               | units_on_order        | smallint          | YES           |
| products               | reorder_level         | smallint          | YES           |
| products               | discontinued          | integer           | NO            |
| region                 | region_id             | smallint          | NO            |
| region                 | region_description    | character varying | NO            |
| shippers               | shipper_id            | smallint          | NO            |
| shippers               | company_name          | character varying | NO            |
| shippers               | phone                 | character varying | YES           |
| suppliers              | supplier_id           | smallint          | NO            |
| suppliers              | company_name          | character varying | NO            |
| suppliers              | contact_name          | character varying | YES           |
| suppliers              | contact_title         | character varying | YES           |
| suppliers              | address               | character varying | YES           |
| suppliers              | city                  | character varying | YES           |
| suppliers              | region                | character varying | YES           |
| suppliers              | postal_code           | character varying | YES           |
| suppliers              | country               | character varying | YES           |
| suppliers              | phone                 | character varying | YES           |
| suppliers              | fax                   | character varying | YES           |
| suppliers              | homepage              | text              | YES           |
| territories            | territory_id          | character varying | NO            |
| territories            | territory_description | character varying | NO            |
| territories            | region_id             | smallint          | NO            |
| us_states              | state_id              | smallint          | NO            |
| us_states              | state_name            | character varying | YES           |
| us_states              | state_abbr            | character varying | YES           |
| us_states              | state_region          | character varying | YES           |

## fk_fk_customer_customer_demo_customer_demographics

```sql
SELECT count(*) AS orfaos FROM public."customer_customer_demo" f WHERE f."customer_type_id" IS NOT NULL AND NOT EXISTS (SELECT 1 FROM public."customer_demographics" p WHERE p."customer_type_id" = f."customer_type_id")
```

| orfaos   |
|----------|
| 0        |

## fk_fk_customer_customer_demo_customers

```sql
SELECT count(*) AS orfaos FROM public."customer_customer_demo" f WHERE f."customer_id" IS NOT NULL AND NOT EXISTS (SELECT 1 FROM public."customers" p WHERE p."customer_id" = f."customer_id")
```

| orfaos   |
|----------|
| 0        |

## fk_fk_employee_territories_employees

```sql
SELECT count(*) AS orfaos FROM public."employee_territories" f WHERE f."employee_id" IS NOT NULL AND NOT EXISTS (SELECT 1 FROM public."employees" p WHERE p."employee_id" = f."employee_id")
```

| orfaos   |
|----------|
| 0        |

## fk_fk_employee_territories_territories

```sql
SELECT count(*) AS orfaos FROM public."employee_territories" f WHERE f."territory_id" IS NOT NULL AND NOT EXISTS (SELECT 1 FROM public."territories" p WHERE p."territory_id" = f."territory_id")
```

| orfaos   |
|----------|
| 0        |

## fk_fk_employees_employees

```sql
SELECT count(*) AS orfaos FROM public."employees" f WHERE f."reports_to" IS NOT NULL AND NOT EXISTS (SELECT 1 FROM public."employees" p WHERE p."employee_id" = f."reports_to")
```

| orfaos   |
|----------|
| 0        |

## fk_fk_order_details_orders

```sql
SELECT count(*) AS orfaos FROM public."order_details" f WHERE f."order_id" IS NOT NULL AND NOT EXISTS (SELECT 1 FROM public."orders" p WHERE p."order_id" = f."order_id")
```

| orfaos   |
|----------|
| 0        |

## fk_fk_order_details_products

```sql
SELECT count(*) AS orfaos FROM public."order_details" f WHERE f."product_id" IS NOT NULL AND NOT EXISTS (SELECT 1 FROM public."products" p WHERE p."product_id" = f."product_id")
```

| orfaos   |
|----------|
| 0        |

## fk_fk_orders_customers

```sql
SELECT count(*) AS orfaos FROM public."orders" f WHERE f."customer_id" IS NOT NULL AND NOT EXISTS (SELECT 1 FROM public."customers" p WHERE p."customer_id" = f."customer_id")
```

| orfaos   |
|----------|
| 0        |

## fk_fk_orders_employees

```sql
SELECT count(*) AS orfaos FROM public."orders" f WHERE f."employee_id" IS NOT NULL AND NOT EXISTS (SELECT 1 FROM public."employees" p WHERE p."employee_id" = f."employee_id")
```

| orfaos   |
|----------|
| 0        |

## fk_fk_orders_shippers

```sql
SELECT count(*) AS orfaos FROM public."orders" f WHERE f."ship_via" IS NOT NULL AND NOT EXISTS (SELECT 1 FROM public."shippers" p WHERE p."shipper_id" = f."ship_via")
```

| orfaos   |
|----------|
| 0        |

## fk_fk_products_categories

```sql
SELECT count(*) AS orfaos FROM public."products" f WHERE f."category_id" IS NOT NULL AND NOT EXISTS (SELECT 1 FROM public."categories" p WHERE p."category_id" = f."category_id")
```

| orfaos   |
|----------|
| 0        |

## fk_fk_products_suppliers

```sql
SELECT count(*) AS orfaos FROM public."products" f WHERE f."supplier_id" IS NOT NULL AND NOT EXISTS (SELECT 1 FROM public."suppliers" p WHERE p."supplier_id" = f."supplier_id")
```

| orfaos   |
|----------|
| 0        |

## fk_fk_territories_region

```sql
SELECT count(*) AS orfaos FROM public."territories" f WHERE f."region_id" IS NOT NULL AND NOT EXISTS (SELECT 1 FROM public."region" p WHERE p."region_id" = f."region_id")
```

| orfaos   |
|----------|
| 0        |

## pk_categories

```sql
SELECT count(*) AS grupos_duplicados FROM (SELECT "category_id" FROM public."categories" GROUP BY "category_id" HAVING count(*) > 1) d
```

| grupos_duplicados   |
|---------------------|
| 0                   |

## pk_customer_customer_demo

```sql
SELECT count(*) AS grupos_duplicados FROM (SELECT "customer_id","customer_type_id" FROM public."customer_customer_demo" GROUP BY "customer_id","customer_type_id" HAVING count(*) > 1) d
```

| grupos_duplicados   |
|---------------------|
| 0                   |

## pk_customer_demographics

```sql
SELECT count(*) AS grupos_duplicados FROM (SELECT "customer_type_id" FROM public."customer_demographics" GROUP BY "customer_type_id" HAVING count(*) > 1) d
```

| grupos_duplicados   |
|---------------------|
| 0                   |

## pk_customers

```sql
SELECT count(*) AS grupos_duplicados FROM (SELECT "customer_id" FROM public."customers" GROUP BY "customer_id" HAVING count(*) > 1) d
```

| grupos_duplicados   |
|---------------------|
| 0                   |

## pk_employees

```sql
SELECT count(*) AS grupos_duplicados FROM (SELECT "employee_id" FROM public."employees" GROUP BY "employee_id" HAVING count(*) > 1) d
```

| grupos_duplicados   |
|---------------------|
| 0                   |

## pk_employee_territories

```sql
SELECT count(*) AS grupos_duplicados FROM (SELECT "employee_id","territory_id" FROM public."employee_territories" GROUP BY "employee_id","territory_id" HAVING count(*) > 1) d
```

| grupos_duplicados   |
|---------------------|
| 0                   |

## pk_order_details

```sql
SELECT count(*) AS grupos_duplicados FROM (SELECT "order_id","product_id" FROM public."order_details" GROUP BY "order_id","product_id" HAVING count(*) > 1) d
```

| grupos_duplicados   |
|---------------------|
| 0                   |

## pk_orders

```sql
SELECT count(*) AS grupos_duplicados FROM (SELECT "order_id" FROM public."orders" GROUP BY "order_id" HAVING count(*) > 1) d
```

| grupos_duplicados   |
|---------------------|
| 0                   |

## pk_products

```sql
SELECT count(*) AS grupos_duplicados FROM (SELECT "product_id" FROM public."products" GROUP BY "product_id" HAVING count(*) > 1) d
```

| grupos_duplicados   |
|---------------------|
| 0                   |

## pk_region

```sql
SELECT count(*) AS grupos_duplicados FROM (SELECT "region_id" FROM public."region" GROUP BY "region_id" HAVING count(*) > 1) d
```

| grupos_duplicados   |
|---------------------|
| 0                   |

## pk_shippers

```sql
SELECT count(*) AS grupos_duplicados FROM (SELECT "shipper_id" FROM public."shippers" GROUP BY "shipper_id" HAVING count(*) > 1) d
```

| grupos_duplicados   |
|---------------------|
| 0                   |

## pk_suppliers

```sql
SELECT count(*) AS grupos_duplicados FROM (SELECT "supplier_id" FROM public."suppliers" GROUP BY "supplier_id" HAVING count(*) > 1) d
```

| grupos_duplicados   |
|---------------------|
| 0                   |

## pk_territories

```sql
SELECT count(*) AS grupos_duplicados FROM (SELECT "territory_id" FROM public."territories" GROUP BY "territory_id" HAVING count(*) > 1) d
```

| grupos_duplicados   |
|---------------------|
| 0                   |

## pk_us_states

```sql
SELECT count(*) AS grupos_duplicados FROM (SELECT "state_id" FROM public."us_states" GROUP BY "state_id" HAVING count(*) > 1) d
```

| grupos_duplicados   |
|---------------------|
| 0                   |

## migracao_regions

```sql
SELECT 'origem sem equivalente' AS sentido, count(*) AS diferencas FROM ((SELECT region_id, btrim(region_description)
FROM public.region) EXCEPT ALL (SELECT region_id, region_name FROM nw.regions)) x UNION ALL SELECT 'destino sem equivalente', count(*) FROM ((SELECT region_id, region_name FROM nw.regions) EXCEPT ALL (SELECT region_id, btrim(region_description)
FROM public.region)) y
```

| sentido                 | diferencas   |
|-------------------------|--------------|
| origem sem equivalente  | 0            |
| destino sem equivalente | 0            |

## migracao_territories

```sql
SELECT 'origem sem equivalente' AS sentido, count(*) AS diferencas FROM ((SELECT btrim(territory_id), btrim(territory_description), region_id
FROM public.territories) EXCEPT ALL (SELECT territory_id, territory_name, region_id FROM nw.territories)) x UNION ALL SELECT 'destino sem equivalente', count(*) FROM ((SELECT territory_id, territory_name, region_id FROM nw.territories) EXCEPT ALL (SELECT btrim(territory_id), btrim(territory_description), region_id
FROM public.territories)) y
```

| sentido                 | diferencas   |
|-------------------------|--------------|
| origem sem equivalente  | 0            |
| destino sem equivalente | 0            |

## migracao_categories

```sql
SELECT 'origem sem equivalente' AS sentido, count(*) AS diferencas FROM ((SELECT category_id, btrim(category_name), description
FROM public.categories) EXCEPT ALL (SELECT category_id, category_name, description FROM nw.categories)) x UNION ALL SELECT 'destino sem equivalente', count(*) FROM ((SELECT category_id, category_name, description FROM nw.categories) EXCEPT ALL (SELECT category_id, btrim(category_name), description
FROM public.categories)) y
```

| sentido                 | diferencas   |
|-------------------------|--------------|
| origem sem equivalente  | 0            |
| destino sem equivalente | 0            |

## migracao_suppliers

```sql
SELECT 'origem sem equivalente' AS sentido, count(*) AS diferencas FROM ((SELECT supplier_id, btrim(company_name), contact_name, contact_title,
       address, city, region, postal_code, country, phone, fax, homepage
FROM public.suppliers) EXCEPT ALL (SELECT supplier_id, company_name, contact_name, contact_title,
                       address, city, region, postal_code, country,
                       phone, fax, homepage FROM nw.suppliers)) x UNION ALL SELECT 'destino sem equivalente', count(*) FROM ((SELECT supplier_id, company_name, contact_name, contact_title,
                       address, city, region, postal_code, country,
                       phone, fax, homepage FROM nw.suppliers) EXCEPT ALL (SELECT supplier_id, btrim(company_name), contact_name, contact_title,
       address, city, region, postal_code, country, phone, fax, homepage
FROM public.suppliers)) y
```

| sentido                 | diferencas   |
|-------------------------|--------------|
| origem sem equivalente  | 0            |
| destino sem equivalente | 0            |

## migracao_shippers

```sql
SELECT 'origem sem equivalente' AS sentido, count(*) AS diferencas FROM ((SELECT shipper_id, btrim(company_name), phone
FROM public.shippers) EXCEPT ALL (SELECT shipper_id, company_name, phone FROM nw.shippers)) x UNION ALL SELECT 'destino sem equivalente', count(*) FROM ((SELECT shipper_id, company_name, phone FROM nw.shippers) EXCEPT ALL (SELECT shipper_id, btrim(company_name), phone
FROM public.shippers)) y
```

| sentido                 | diferencas   |
|-------------------------|--------------|
| origem sem equivalente  | 0            |
| destino sem equivalente | 0            |

## migracao_customers

```sql
SELECT 'origem sem equivalente' AS sentido, count(*) AS diferencas FROM ((SELECT btrim(customer_id), btrim(company_name), contact_name, contact_title,
       address, city, region, postal_code, country, phone, fax
FROM public.customers) EXCEPT ALL (SELECT customer_id, company_name, contact_name, contact_title,
                       address, city, region, postal_code, country, phone, fax FROM nw.customers)) x UNION ALL SELECT 'destino sem equivalente', count(*) FROM ((SELECT customer_id, company_name, contact_name, contact_title,
                       address, city, region, postal_code, country, phone, fax FROM nw.customers) EXCEPT ALL (SELECT btrim(customer_id), btrim(company_name), contact_name, contact_title,
       address, city, region, postal_code, country, phone, fax
FROM public.customers)) y
```

| sentido                 | diferencas   |
|-------------------------|--------------|
| origem sem equivalente  | 0            |
| destino sem equivalente | 0            |

## migracao_employees

```sql
SELECT 'origem sem equivalente' AS sentido, count(*) AS diferencas FROM ((SELECT employee_id, last_name, first_name, title,
       title_of_courtesy, birth_date, hire_date, address,
       city, region, postal_code, country, home_phone,
       extension, notes, reports_to
FROM public.employees) EXCEPT ALL (SELECT employee_id, last_name, first_name, title,
                       title_of_courtesy, birth_date, hire_date, address,
                       city, region, postal_code, country, home_phone,
                       extension, notes, reports_to FROM nw.employees)) x UNION ALL SELECT 'destino sem equivalente', count(*) FROM ((SELECT employee_id, last_name, first_name, title,
                       title_of_courtesy, birth_date, hire_date, address,
                       city, region, postal_code, country, home_phone,
                       extension, notes, reports_to FROM nw.employees) EXCEPT ALL (SELECT employee_id, last_name, first_name, title,
       title_of_courtesy, birth_date, hire_date, address,
       city, region, postal_code, country, home_phone,
       extension, notes, reports_to
FROM public.employees)) y
```

| sentido                 | diferencas   |
|-------------------------|--------------|
| origem sem equivalente  | 0            |
| destino sem equivalente | 0            |

## migracao_employee_territories

```sql
SELECT 'origem sem equivalente' AS sentido, count(*) AS diferencas FROM ((SELECT employee_id, btrim(territory_id)
FROM public.employee_territories) EXCEPT ALL (SELECT employee_id, territory_id FROM nw.employee_territories)) x UNION ALL SELECT 'destino sem equivalente', count(*) FROM ((SELECT employee_id, territory_id FROM nw.employee_territories) EXCEPT ALL (SELECT employee_id, btrim(territory_id)
FROM public.employee_territories)) y
```

| sentido                 | diferencas   |
|-------------------------|--------------|
| origem sem equivalente  | 0            |
| destino sem equivalente | 0            |

## migracao_products

```sql
SELECT 'origem sem equivalente' AS sentido, count(*) AS diferencas FROM ((SELECT product_id, btrim(product_name), supplier_id, category_id,
       quantity_per_unit,
       unit_price::numeric(10,2),
       units_in_stock, units_on_order, reorder_level,
       (discontinued = 1)
FROM public.products) EXCEPT ALL (SELECT product_id, product_name, supplier_id, category_id,
                      quantity_per_unit, unit_price, units_in_stock,
                      units_on_order, reorder_level, discontinued FROM nw.products)) x UNION ALL SELECT 'destino sem equivalente', count(*) FROM ((SELECT product_id, product_name, supplier_id, category_id,
                      quantity_per_unit, unit_price, units_in_stock,
                      units_on_order, reorder_level, discontinued FROM nw.products) EXCEPT ALL (SELECT product_id, btrim(product_name), supplier_id, category_id,
       quantity_per_unit,
       unit_price::numeric(10,2),
       units_in_stock, units_on_order, reorder_level,
       (discontinued = 1)
FROM public.products)) y
```

| sentido                 | diferencas   |
|-------------------------|--------------|
| origem sem equivalente  | 0            |
| destino sem equivalente | 0            |

## migracao_orders

```sql
SELECT 'origem sem equivalente' AS sentido, count(*) AS diferencas FROM ((SELECT order_id, btrim(customer_id), employee_id, ship_via,
       order_date, required_date, shipped_date,
       freight::numeric(10,2),
       ship_name, ship_address, ship_city, ship_region,
       ship_postal_code, ship_country
FROM public.orders) EXCEPT ALL (SELECT order_id, customer_id, employee_id, shipper_id,
                    order_date, required_date, shipped_date, freight,
                    ship_name, ship_address, ship_city, ship_region,
                    ship_postal_code, ship_country FROM nw.orders)) x UNION ALL SELECT 'destino sem equivalente', count(*) FROM ((SELECT order_id, customer_id, employee_id, shipper_id,
                    order_date, required_date, shipped_date, freight,
                    ship_name, ship_address, ship_city, ship_region,
                    ship_postal_code, ship_country FROM nw.orders) EXCEPT ALL (SELECT order_id, btrim(customer_id), employee_id, ship_via,
       order_date, required_date, shipped_date,
       freight::numeric(10,2),
       ship_name, ship_address, ship_city, ship_region,
       ship_postal_code, ship_country
FROM public.orders)) y
```

| sentido                 | diferencas   |
|-------------------------|--------------|
| origem sem equivalente  | 0            |
| destino sem equivalente | 0            |

## migracao_order_items

```sql
SELECT 'origem sem equivalente' AS sentido, count(*) AS diferencas FROM ((SELECT order_id, product_id,
       unit_price::numeric(10,2),
       quantity,
       discount::numeric(4,3)
FROM public.order_details) EXCEPT ALL (SELECT order_id, product_id, unit_price, quantity, discount FROM nw.order_items)) x UNION ALL SELECT 'destino sem equivalente', count(*) FROM ((SELECT order_id, product_id, unit_price, quantity, discount FROM nw.order_items) EXCEPT ALL (SELECT order_id, product_id,
       unit_price::numeric(10,2),
       quantity,
       discount::numeric(4,3)
FROM public.order_details)) y
```

| sentido                 | diferencas   |
|-------------------------|--------------|
| origem sem equivalente  | 0            |
| destino sem equivalente | 0            |

## historico_endereco

```sql
SELECT count(*) AS pedidos, count(*) FILTER (WHERE ROW(o.ship_name,o.ship_address,o.ship_city,o.ship_region,o.ship_postal_code,o.ship_country) IS NOT DISTINCT FROM ROW(c.company_name,c.address,c.city,c.region,c.postal_code,c.country)) AS seis_campos_iguais FROM public.orders o JOIN public.customers c USING(customer_id)
```

| pedidos   | seis_campos_iguais   |
|-----------|----------------------|
| 830       | 748                  |

## cobertura

```sql
SELECT 'clientes sem pedido' AS indicador, count(*) AS quantidade FROM public.customers c WHERE NOT EXISTS (SELECT 1 FROM public.orders o WHERE o.customer_id=c.customer_id) UNION ALL SELECT 'produtos sem item', count(*) FROM public.products p WHERE NOT EXISTS (SELECT 1 FROM public.order_details d WHERE d.product_id=p.product_id) UNION ALL SELECT 'transportadoras sem pedido', count(*) FROM public.shippers s WHERE NOT EXISTS (SELECT 1 FROM public.orders o WHERE o.ship_via=s.shipper_id) UNION ALL SELECT 'territórios sem funcionário', count(*) FROM public.territories t WHERE NOT EXISTS (SELECT 1 FROM public.employee_territories e WHERE e.territory_id=t.territory_id)
```

| indicador                   | quantidade   |
|-----------------------------|--------------|
| clientes sem pedido         | 2            |
| produtos sem item           | 0            |
| transportadoras sem pedido  | 3            |
| territórios sem funcionário | 4            |

## territorios

```sql
SELECT count(*) AS vinculos, count(DISTINCT employee_id) AS funcionarios, count(DISTINCT territory_id) AS territorios FROM public.employee_territories
```

| vinculos   | funcionarios   | territorios   |
|------------|----------------|---------------|
| 49         | 9              | 49            |

## itens_por_pedido

```sql
SELECT min(n) AS minimo, round(avg(n),2) AS media,max(n) AS maximo FROM (SELECT order_id,count(*) n FROM public.order_details GROUP BY order_id) t
```

| minimo   | media   | maximo   |
|----------|---------|----------|
| 1        | 2.60    | 25       |

## faixas

```sql
SELECT min(unit_price)::numeric AS menor_preco,max(unit_price)::numeric AS maior_preco,min(quantity) AS menor_quantidade,max(quantity) AS maior_quantidade,min(discount)::numeric AS menor_desconto,max(discount)::numeric AS maior_desconto FROM public.order_details
```

| menor_preco   | maior_preco   | menor_quantidade   | maior_quantidade   | menor_desconto   | maior_desconto   |
|---------------|---------------|--------------------|--------------------|------------------|------------------|
| 2             | 263.5         | 1                  | 130                | 0                | 0.25             |

## real_numeric

```sql
SELECT sum(unit_price*quantity*(1-discount)) AS ponto_flutuante,sum(unit_price::numeric*quantity*(1-discount::numeric)) AS decimal FROM public.order_details
```

| ponto_flutuante   | decimal      |
|-------------------|--------------|
| 1265793.038653364 | 1265793.0395 |

## valores_views

```sql
SELECT (SELECT sum(receita) FROM nw.vw_venda_item) AS soma_itens, (SELECT sum(valor_pedido) FROM nw.vw_pedido_resumo) AS soma_pedidos
```

| soma_itens   | soma_pedidos   |
|--------------|----------------|
| 1265793.29   | 1265793.29     |
