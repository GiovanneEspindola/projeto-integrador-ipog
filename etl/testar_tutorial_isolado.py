"""Testa o tutorial em PostgreSQL temporário, reconstruído do dump local.

Não se conecta aos containers do projeto. Requer binários PostgreSQL 16 locais
e psycopg. Remove o cluster temporário ao terminar; preserva as evidências.
Uso: .venv/bin/python etl/testar_tutorial_isolado.py
"""
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

import psycopg
from recalcular_csv_entrega01 import recalcular

ROOT = Path(__file__).resolve().parents[1]
BIN = Path(os.environ.get("PG_BIN", "/usr/lib/postgresql/16/bin"))
OUT = ROOT / "apresentacao/evidencias/tutorial-entrega01"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    csvdir = OUT / "csv-referencia"
    csvdir.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="pi-tutorial-pg-") as tmp:
        data = Path(tmp) / "data"
        running = False
        try:
            with (OUT / "reconstrucao.log").open("w") as log:
                def command(args):
                    subprocess.run(list(map(str, args)), check=True, stdout=log, stderr=subprocess.STDOUT)
                command([BIN / "initdb", "-D", data, "-U", "pi", "--auth-local=trust", "--auth-host=reject", "--no-locale", "-E", "UTF8"])
                command([BIN / "pg_ctl", "-D", data, "-l", Path(tmp)/"servidor.log", "-o", f"-k {tmp} -p 55439 -c listen_addresses=''", "-w", "start"])
                running = True
                base = [BIN / "psql", "-h", tmp, "-p", "55439", "-U", "pi", "-X", "-v", "ON_ERROR_STOP=1"]
                command(base + ["-d", "postgres", "-c", "CREATE DATABASE northwind"])
                source_files = ["00_northwind_original", "10_ddl", "20_load", "30_indexes", "40_views"]
                for name in source_files:
                    command(base + ["-d", "northwind", "-f", ROOT / f"sql/{name}.sql"])
            queries = (ROOT / "sql/estudo/entrega01-dbeaver.sql").read_text()
            results = {}
            with psycopg.connect(host=tmp, port=55439, user="pi", dbname="northwind") as cx:
                cx.execute("BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY")
                for match in re.finditer(r"^-- @(\d+) ([^\n]+)\n(.*?)(?=^-- @|\Z)", queries, re.M|re.S):
                    key, title, query = match.groups()
                    cur = cx.execute(query)
                    results[key] = {"titulo":title,"sql":query.strip(),"colunas":[c.name for c in cur.description],"linhas":cur.fetchall()}
                cx.rollback()
            assert len(results) == 31
            for key in ("12", "13", "14", "22"):
                assert all(row[1] == 0 for row in results[key]["linhas"]), key
            assert len(results["02"]["linhas"]) == 92
            assert len(results["09"]["linhas"]) == 11
            assert results["24"]["linhas"][0] == (830,2155,1,25,0)
            # Comparação da fonte reconstruída com os resultados do relatório
            # obtidos antes no banco dos containers, nas consultas equivalentes.
            previous = json.loads((ROOT / "apresentacao/evidencias/revisao-entrega01/resultados.json").read_text())
            mappings = {"05":"resumo","06":"valores","07":"anos","08":"categorias","10":"envio","17":"precos","18":"historico_endereco","19":"arredondamento"}
            differences = {}
            for key, oldkey in mappings.items():
                current = json.loads(json.dumps(results[key]["linhas"],default=str))
                if current != previous[oldkey]["rows"]:
                    differences[key] = {"atual":current,"anterior":previous[oldkey]["rows"]}
            for key, name in {"26":"itens","27":"pedidos","28":"produtos","29":"categorias","30":"clientes"}.items():
                with (csvdir / f"{name}.csv").open("w",encoding="utf-8",newline="") as stream:
                    writer=csv.writer(stream)
                    writer.writerow(results[key]["colunas"])
                    writer.writerows(results[key]["linhas"])
            python_results = recalcular(csvdir)
            (OUT / "recalculo-python.json").write_text(json.dumps(python_results,ensure_ascii=False,indent=2)+"\n")
            (OUT / "consultas-resultados.json").write_text(json.dumps(results,ensure_ascii=False,indent=2,default=str)+"\n")
            metadata = {
                "ambiente":"PostgreSQL temporário, apenas socket Unix; não conectado aos bancos do Docker",
                "binarios":str(BIN), "contexto":results["00"]["linhas"],
                "sha256_entradas":{f"sql/{name}.sql":hashlib.sha256((ROOT/f"sql/{name}.sql").read_bytes()).hexdigest() for name in source_files},
                "diferencas_resultados_anteriores":differences,
                "diferencas_python_relatorio":python_results["diferencas_relatorio"],
                "consultas_executadas":len(results),
                "limite":"Reconstrução da cópia local do dump; não certifica sua procedência externa nem compara toda a instância Docker indisponível.",
            }
            (OUT / "resumo.json").write_text(json.dumps(metadata,ensure_ascii=False,indent=2,default=str)+"\n")
            assert not differences, differences
            assert not python_results["diferencas_relatorio"],python_results["diferencas_relatorio"]
            print("31 consultas executadas na cópia reconstruída. Sem divergências nas comparações selecionadas ou no recálculo Python.")
            print(OUT)
        finally:
            if running:
                subprocess.run([str(BIN/"pg_ctl"),"-D",str(data),"-m","fast","-w","stop"],check=True,stdout=subprocess.DEVNULL)


if __name__ == "__main__":
    main()
