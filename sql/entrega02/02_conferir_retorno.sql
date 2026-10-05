-- Rode após exportar o MongoDB e copiar retorno.json para /tmp/retorno.json
-- no container PostgreSQL. Somente tabelas temporárias são criadas.
\set ON_ERROR_STOP on
BEGIN ISOLATION LEVEL REPEATABLE READ;
CREATE TEMP TABLE retorno (dados jsonb);
\copy retorno FROM '/tmp/retorno.json' WITH (FORMAT csv, QUOTE E'\x01', DELIMITER E'\x02');
CREATE TEMP TABLE resultado (tabela text, origem bigint, destino bigint, divergencias bigint);
DO $$
DECLARE t text; n bigint;
BEGIN
 FOREACH t IN ARRAY ARRAY['regions','territories','categories','shippers','suppliers',
   'customers','employees','employee_territories','products','orders','order_items'] LOOP
   -- Converte somente o transporte decimal textual para numeric SEM escala fixa.
   -- Assim casas decimais extras não são arredondadas antes da comparação.
   -- EXCEPT ALL detecta registros faltantes, extras, alterados e duplicados.
   EXECUTE format($q$
     WITH atual AS (SELECT (SELECT jsonb_object_agg(k,
       CASE WHEN k IN ('unit_price','discount','freight') AND v <> 'null'::jsonb
         THEN to_jsonb((v #>> '{}')::numeric) ELSE v END)
       FROM jsonb_each(x) AS campos(k,v)) AS linha
       FROM retorno r, LATERAL jsonb_array_elements(r.dados->%L) x),
     original AS (SELECT to_jsonb(x) AS linha FROM nw.%I x),
     diferencas AS ((SELECT * FROM original EXCEPT ALL SELECT * FROM atual)
       UNION ALL (SELECT * FROM atual EXCEPT ALL SELECT * FROM original))
     INSERT INTO resultado SELECT %L,(SELECT count(*) FROM original),
       (SELECT count(*) FROM atual),(SELECT count(*) FROM diferencas)
   $q$,t,t,t);
 END LOOP;
 SELECT sum(divergencias) INTO n FROM resultado;
 IF n <> 0 THEN RAISE EXCEPTION 'Conferência falhou: % diferenças. Não usar a carga.',n; END IF;
END $$;
TABLE resultado;
SELECT sum(origem) AS linhas_origem,sum(destino) AS linhas_reconstruidas,
       sum(divergencias) AS divergencias FROM resultado;
SELECT sum(unit_price*quantity*(1-discount)) AS valor_exato,
 round(sum(unit_price*quantity*(1-discount)),2) AS arredondado_no_total FROM nw.order_items;
COMMIT;
