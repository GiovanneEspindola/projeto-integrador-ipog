-- Execute com psql -X -qAt -v ON_ERROR_STOP=1; a saída é UM arquivo Extended JSON.
-- Só lê nw. As funções pg_temp existem apenas nesta conexão.
BEGIN ISOLATION LEVEL REPEATABLE READ;

-- JSON comum não distingue decimal, data e inteiro. Estes marcadores preservam
-- os tipos BSON quando o mongosh ler o arquivo com EJSON.parse.
CREATE FUNCTION pg_temp.tipar(linha jsonb) RETURNS jsonb LANGUAGE plpgsql AS $$
DECLARE k text; v jsonb; saida jsonb := '{}';
BEGIN
  FOR k, v IN SELECT * FROM jsonb_each(linha) LOOP
    IF v = 'null'::jsonb THEN NULL; -- mantém NULL, sem inventar preenchimento
    ELSIF k IN ('unit_price','discount','freight') THEN
      v := jsonb_build_object('$numberDecimal', v #>> '{}');
    ELSIF k IN ('order_date','required_date','shipped_date','birth_date','hire_date') THEN
      v := jsonb_build_object('$date', jsonb_build_object('$numberLong',
        (((v #>> '{}')::date - DATE '1970-01-01')::bigint * 86400000)::text));
    ELSIF jsonb_typeof(v) = 'number' THEN
      v := jsonb_build_object('$numberInt', v #>> '{}');
    END IF;
    saida := saida || jsonb_build_object(k,v);
  END LOOP;
  RETURN saida;
END $$;

CREATE FUNCTION pg_temp.endereco(linha jsonb) RETURNS jsonb LANGUAGE sql AS $$
 SELECT jsonb_build_object('street',linha->'address','city',linha->'city',
   'region',linha->'region','postal_code',linha->'postal_code','country',linha->'country')
$$;

WITH documentos AS (
 SELECT 'orders' AS colecao,
   (pg_temp.tipar(to_jsonb(o)) - ARRAY['order_id','ship_name','ship_address',
      'ship_city','ship_region','ship_postal_code','ship_country']) ||
   jsonb_build_object('_id',jsonb_build_object('$numberInt',o.order_id::text),
     'shipping',jsonb_build_object('name',o.ship_name,'street',o.ship_address,
       'city',o.ship_city,'region',o.ship_region,'postal_code',o.ship_postal_code,
       'country',o.ship_country),
     'items',COALESCE((SELECT jsonb_agg(
       (pg_temp.tipar(to_jsonb(i)) - ARRAY['order_id','product_id']) ||
       jsonb_build_object('product',jsonb_build_object(
         '_id',jsonb_build_object('$numberInt',p.product_id::text),
         'name',p.product_name,'category',jsonb_build_object(
           '_id',jsonb_build_object('$numberInt',c.category_id::text),
           'name',c.category_name))) ORDER BY i.product_id)
       FROM nw.order_items i JOIN nw.products p USING(product_id)
       JOIN nw.categories c USING(category_id) WHERE i.order_id=o.order_id),'[]'::jsonb)) AS documento
 FROM nw.orders o
 UNION ALL
 SELECT 'products', (pg_temp.tipar(to_jsonb(p)) - ARRAY['product_id','category_id','supplier_id']) ||
   jsonb_build_object('_id',jsonb_build_object('$numberInt',p.product_id::text),
     'category',jsonb_build_object('_id',jsonb_build_object('$numberInt',c.category_id::text),'name',c.category_name),
     'supplier',jsonb_build_object('_id',jsonb_build_object('$numberInt',s.supplier_id::text),'name',s.company_name))
 FROM nw.products p JOIN nw.categories c USING(category_id) JOIN nw.suppliers s USING(supplier_id)
 UNION ALL
 SELECT 'customers', (pg_temp.tipar(to_jsonb(c)) - ARRAY['customer_id','address','city','region','postal_code','country']) ||
   jsonb_build_object('_id',c.customer_id,'address',pg_temp.endereco(to_jsonb(c))) FROM nw.customers c
 UNION ALL
 SELECT 'suppliers', (pg_temp.tipar(to_jsonb(s)) - ARRAY['supplier_id','address','city','region','postal_code','country']) ||
   jsonb_build_object('_id',jsonb_build_object('$numberInt',s.supplier_id::text),'address',pg_temp.endereco(to_jsonb(s))) FROM nw.suppliers s
 UNION ALL
 SELECT 'employees', (pg_temp.tipar(to_jsonb(e)) - ARRAY['employee_id','address','city','region','postal_code','country']) ||
   jsonb_build_object('_id',jsonb_build_object('$numberInt',e.employee_id::text),'address',pg_temp.endereco(to_jsonb(e)),
     'territories',COALESCE((SELECT jsonb_agg(pg_temp.tipar(to_jsonb(t)) ORDER BY t.territory_id)
       FROM nw.employee_territories et JOIN nw.territories t USING(territory_id)
       WHERE et.employee_id=e.employee_id),'[]'::jsonb)) FROM nw.employees e
 UNION ALL
 SELECT 'categories',(pg_temp.tipar(to_jsonb(c))-'category_id') || jsonb_build_object('_id',jsonb_build_object('$numberInt',c.category_id::text)) FROM nw.categories c
 UNION ALL
 SELECT 'shippers',(pg_temp.tipar(to_jsonb(s))-'shipper_id') || jsonb_build_object('_id',jsonb_build_object('$numberInt',s.shipper_id::text)) FROM nw.shippers s
 UNION ALL
 SELECT 'territories',(pg_temp.tipar(to_jsonb(t))-'territory_id') || jsonb_build_object('_id',t.territory_id) FROM nw.territories t
 UNION ALL
 SELECT 'regions',(pg_temp.tipar(to_jsonb(r))-'region_id') || jsonb_build_object('_id',jsonb_build_object('$numberInt',r.region_id::text)) FROM nw.regions r
), colecoes AS (
 SELECT colecao,jsonb_agg(documento ORDER BY documento->'_id') AS dados FROM documentos GROUP BY colecao
)
SELECT jsonb_build_object('format','northwind-semana4-v1','collections',jsonb_object_agg(colecao,dados)) FROM colecoes;
COMMIT;
