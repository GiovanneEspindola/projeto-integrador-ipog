"""Reexecuta evidências e audita os dados sem modificar os bancos.

Gera JSON para o Word e Markdown com consultas e saídas completas.
Uso: .venv/bin/python etl/revisar_entrega01.py
"""
import datetime as dt
import hashlib
import json
import os
import pathlib
import re
from decimal import Decimal

import psycopg
from psycopg import sql
from tabulate import tabulate
from pymongo import MongoClient

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "apresentacao/evidencias/revisao-entrega01"


def serial(value):
    if isinstance(value, (Decimal, dt.date, dt.datetime)):
        return str(value)
    raise TypeError(type(value).__name__)


def main():
    results = {}
    with psycopg.connect(os.environ.get(
        "PG_DSN", "postgresql://pi:pi@localhost:5432/northwind"
    )) as conn:
        conn.execute("BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY")

        def run(key, query, params=None):
            cur = conn.execute(query, params)
            result = {"sql": query.strip(),
                      "columns": [c.name for c in cur.description],
                      "rows": cur.fetchall()}
            results[key] = result
            return result["rows"]

        run("ambiente", "SELECT current_database() AS banco, version() AS versao, current_timestamp AS verificado_em")
        selected = (ROOT / "sql/02_evidencias_entrega01.sql").read_text()
        for match in re.finditer(r"^-- @(\w+) ([^\n]+)\n(.*?)(?=^-- @|\Z)", selected, re.M | re.S):
            key, title, query = match.groups()
            run(key, query)
            results[key]["title"] = title

        tables = conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE' ORDER BY table_name").fetchall()
        inventory = []
        for (table,) in tables:
            count = run("contagem_" + table, sql.SQL("SELECT count(*) AS linhas FROM public.{}").format(sql.Identifier(table)).as_string(conn))[0][0]
            cols = conn.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name=%s ORDER BY ordinal_position", (table,)).fetchall()
            inventory.append([table, count, len(cols)])
            for (col,) in cols:
                run("nulos_" + table + "_" + col, sql.SQL("SELECT count(*) AS linhas, count(*) - count({}) AS nulos FROM public.{}").format(sql.Identifier(col), sql.Identifier(table)).as_string(conn))
        results["inventario"] = {"columns": ["Tabela", "Linhas", "Colunas"], "rows": inventory}
        results["nulos"] = {"columns": ["Coluna", "Nulos", "Total", "%"], "rows": [
            [key[6:], r["rows"][0][1], r["rows"][0][0],
             round(Decimal(r["rows"][0][1]) * 100 / r["rows"][0][0], 2)]
            for key, r in results.items() if key.startswith("nulos_") and r["rows"][0][1]
        ]}
        # Reconstituir os nomes sem confundir '_' presente em tabelas e colunas.
        for row in results["nulos"]["rows"]:
            table = max((t[0] for t in tables if row[0].startswith(t[0] + "_")), key=len)
            row[0] = table + "." + row[0][len(table) + 1:]

        run("constraints", "SELECT n.nspname AS schema, c.contype AS tipo, count(*) AS quantidade FROM pg_constraint c JOIN pg_namespace n ON n.oid=c.connamespace WHERE n.nspname IN ('public','nw') GROUP BY 1,2 ORDER BY 1,2")
        run("indices_views", "SELECT 'índices nw' AS objeto, count(*) FROM pg_indexes WHERE schemaname='nw' UNION ALL SELECT 'views nw', count(*) FROM information_schema.views WHERE table_schema='nw'")
        run("tipos", "SELECT table_name, column_name, data_type, is_nullable FROM information_schema.columns WHERE table_schema='public' ORDER BY table_name,ordinal_position")

        fks = conn.execute("SELECT c.conname,c.conrelid::regclass::text,c.confrelid::regclass::text, ARRAY(SELECT a.attname FROM unnest(c.conkey) WITH ORDINALITY k(n,i) JOIN pg_attribute a ON a.attrelid=c.conrelid AND a.attnum=k.n ORDER BY k.i), ARRAY(SELECT a.attname FROM unnest(c.confkey) WITH ORDINALITY k(n,i) JOIN pg_attribute a ON a.attrelid=c.confrelid AND a.attnum=k.n ORDER BY k.i) FROM pg_constraint c JOIN pg_namespace ns ON ns.oid=c.connamespace WHERE ns.nspname='public' AND c.contype='f' ORDER BY c.conname").fetchall()
        for name, child, parent, ccols, pcols in fks:
            join = sql.SQL(' AND ').join(sql.SQL('p.{} = f.{}').format(sql.Identifier(p), sql.Identifier(c)) for c, p in zip(ccols, pcols))
            nonnull = sql.SQL(' AND ').join(sql.SQL('f.{} IS NOT NULL').format(sql.Identifier(c)) for c in ccols)
            query = sql.SQL('SELECT count(*) AS orfaos FROM public.{} f WHERE {} AND NOT EXISTS (SELECT 1 FROM public.{} p WHERE {})').format(sql.Identifier(child.split('.')[-1]), nonnull, sql.Identifier(parent.split('.')[-1]), join)
            assert run("fk_" + name, query.as_string(conn))[0][0] == 0, name

        pks = conn.execute("SELECT c.conrelid::regclass::text, ARRAY(SELECT a.attname FROM unnest(c.conkey) WITH ORDINALITY k(n,i) JOIN pg_attribute a ON a.attrelid=c.conrelid AND a.attnum=k.n ORDER BY k.i) FROM pg_constraint c JOIN pg_namespace ns ON ns.oid=c.connamespace WHERE ns.nspname='public' AND c.contype='p'").fetchall()
        for table, cols in pks:
            query = sql.SQL('SELECT count(*) AS grupos_duplicados FROM (SELECT {} FROM public.{} GROUP BY {} HAVING count(*) > 1) d').format(sql.SQL(',').join(map(sql.Identifier, cols)),sql.Identifier(table.split('.')[-1]),sql.SQL(',').join(map(sql.Identifier, cols)))
            assert run("pk_" + table, query.as_string(conn))[0][0] == 0, table

        # Comparar todas as colunas migradas nos dois sentidos, com as mesmas
        # conversões explícitas da carga. EXCEPT ALL também detecta multiplicidade.
        load = (ROOT / "sql/20_load.sql").read_text()
        migrations = re.findall(r"INSERT INTO (\w+)\s*\((.*?)\)\s*(SELECT.*?);", load, re.S)
        assert len(migrations) == 11
        for table, columns, origin in migrations:
            dest = "SELECT " + columns + " FROM nw." + table
            query = f"SELECT 'origem sem equivalente' AS sentido, count(*) AS diferencas FROM (({origin}) EXCEPT ALL ({dest})) x UNION ALL SELECT 'destino sem equivalente', count(*) FROM (({dest}) EXCEPT ALL ({origin})) y"
            rows = run("migracao_" + table, query)
            assert all(row[1] == 0 for row in rows), table
        run("historico_endereco", "SELECT count(*) AS pedidos, count(*) FILTER (WHERE ROW(o.ship_name,o.ship_address,o.ship_city,o.ship_region,o.ship_postal_code,o.ship_country) IS NOT DISTINCT FROM ROW(c.company_name,c.address,c.city,c.region,c.postal_code,c.country)) AS seis_campos_iguais FROM public.orders o JOIN public.customers c USING(customer_id)")
        run("cobertura", "SELECT 'clientes sem pedido' AS indicador, count(*) AS quantidade FROM public.customers c WHERE NOT EXISTS (SELECT 1 FROM public.orders o WHERE o.customer_id=c.customer_id) UNION ALL SELECT 'produtos sem item', count(*) FROM public.products p WHERE NOT EXISTS (SELECT 1 FROM public.order_details d WHERE d.product_id=p.product_id) UNION ALL SELECT 'transportadoras sem pedido', count(*) FROM public.shippers s WHERE NOT EXISTS (SELECT 1 FROM public.orders o WHERE o.ship_via=s.shipper_id) UNION ALL SELECT 'territórios sem funcionário', count(*) FROM public.territories t WHERE NOT EXISTS (SELECT 1 FROM public.employee_territories e WHERE e.territory_id=t.territory_id)")
        run("territorios", "SELECT count(*) AS vinculos, count(DISTINCT employee_id) AS funcionarios, count(DISTINCT territory_id) AS territorios FROM public.employee_territories")
        run("itens_por_pedido", "SELECT min(n) AS minimo, round(avg(n),2) AS media,max(n) AS maximo FROM (SELECT order_id,count(*) n FROM public.order_details GROUP BY order_id) t")
        run("faixas", "SELECT min(unit_price)::numeric AS menor_preco,max(unit_price)::numeric AS maior_preco,min(quantity) AS menor_quantidade,max(quantity) AS maior_quantidade,min(discount)::numeric AS menor_desconto,max(discount)::numeric AS maior_desconto FROM public.order_details")
        run("real_numeric", "SELECT sum(unit_price*quantity*(1-discount)) AS ponto_flutuante,sum(unit_price::numeric*quantity*(1-discount::numeric)) AS decimal FROM public.order_details")
        run("valores_views", "SELECT (SELECT sum(receita) FROM nw.vw_venda_item) AS soma_itens, (SELECT sum(valor_pedido) FROM nw.vw_pedido_resumo) AS soma_pedidos")
        assert sum(r[1] for r in inventory) == 3362
        assert sum(r[2] for r in inventory) == 92
        assert results["valores"]["rows"][0][0] == Decimal("1265793.04")
        conn.rollback()

    with MongoClient(os.environ.get("MONGO_URI", "mongodb://pi:pi@localhost:27017/?authSource=admin"), serverSelectionTimeoutMS=5000) as mongo:
        results["mongo"] = {
            "versao": mongo.server_info()["version"],
            "bancos": mongo.list_database_names(),
            "colecoes_northwind": mongo["northwind"].list_collection_names(),
        }

    results["proveniencia"] = {
        "dump": "sql/00_northwind_original.sql",
        "sha256": hashlib.sha256((ROOT / "sql/00_northwind_original.sql").read_bytes()).hexdigest(),
        "fonte": "https://github.com/pthom/northwind_psql",
        "modo": "REPEATABLE READ, READ ONLY",
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "resultados.json").write_text(json.dumps(results, ensure_ascii=False, indent=2, default=serial) + "\n")
    blocks = ["# Conferência da Entrega 1\n", "Consultas executadas em uma transação somente leitura.\n", "Dump SHA-256: `" + results["proveniencia"]["sha256"] + "`\n"]
    for key, result in results.items():
        if "rows" not in result:
            continue
        blocks += ["## " + key + "\n"]
        if "sql" in result:
            blocks += ["```sql\n" + result["sql"] + "\n```\n"]
        blocks += [tabulate(result["rows"], headers=result["columns"], tablefmt="github", disable_numparse=True) + "\n"]
    (OUT / "conferencia.md").write_text("\n".join(blocks))
    print(f"Conferência concluída: {len(fks)} FKs, {len(pks)} PKs, 11 tabelas migradas sem divergência em nenhuma coluna comparada.")
    print(OUT / "resultados.json")


if __name__ == "__main__":
    main()
