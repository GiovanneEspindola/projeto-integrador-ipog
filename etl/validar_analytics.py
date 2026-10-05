"""Executa os arquivos Q/PNN, confere equivalência e salva evidências.

Uso: .venv/bin/python etl/validar_analytics.py
PG_DSN e MONGO_URI permitem ajustar portas/credenciais locais.
"""
from pathlib import Path
from decimal import Decimal
from datetime import date, datetime, timezone
import hashlib
import json
import os
import subprocess
import sys

import psycopg
from psycopg.rows import dict_row
from pymongo import MongoClient
from bson import json_util, Decimal128

ROOT = Path(__file__).resolve().parents[1]
# EVIDENCIAS permite gravar uma reexecução em outra pasta sem sobrescrever a da Entrega 3.
OUT = ROOT / os.getenv('EVIDENCIAS', 'apresentacao/evidencias/entrega03')
RATIOS = {'participacao', 'ticket', 'percentual', 'suporte',
          'media_dias', 'percentual_desconto'}


def connections():
    pg = psycopg.connect(os.getenv('PG_DSN', 'postgresql://pi:pi@localhost:5432/northwind'),
                         row_factory=dict_row, autocommit=True)
    mg = MongoClient(os.getenv('MONGO_URI', 'mongodb://pi:pi@localhost:27017/?authSource=admin'),
                     serverSelectionTimeoutMS=5000)
    return pg, mg


def mongo_script(script):
    args = ['docker', 'compose', 'exec', '-T', 'mongo', 'mongosh',
            '-u', 'pi', '-p', 'pi', '--authenticationDatabase', 'admin', '--quiet']
    return subprocess.check_output(args + ['--eval', script + '; void 0;'], cwd=ROOT, text=True)


def export_specs():
    # Compila os scripts reais, não uma segunda implementação em Python.
    raw = mongo_script('var ANALYTICS_EXPORT=true; var specs={}; '
        'for(var n=1;n<=16;n++){load("/mongo/pipelines/P"+String(n).padStart(2,"0")+".js");'
        'specs[String(n)]=consulta;} print(EJSON.stringify(specs));')
    (OUT / 'pipelines.ejson').write_text(raw)
    return json_util.loads(raw)


def norm(v):
    if isinstance(v, Decimal128):
        return v.to_decimal()
    if isinstance(v, datetime):
        # Só a convenção de meia-noite UTC equivale a um date; outro horário fica visível.
        return v.date().isoformat() if v.time() == datetime.min.time() else v.isoformat()
    if isinstance(v, date):
        return v.isoformat()
    if isinstance(v, dict):
        return {k: norm(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [norm(x) for x in v]
    return v


def compare(a, b, path='', column=''):
    a, b = norm(a), norm(b)
    if isinstance(a, dict) and isinstance(b, dict):
        assert a.keys() == b.keys(), (path, a.keys(), b.keys())
        for k in a:
            compare(a[k], b[k], path + '.' + k, k)
    elif isinstance(a, list) and isinstance(b, list):
        assert len(a) == len(b), (path, len(a), len(b))
        for i, (x, y) in enumerate(zip(a, b)):
            compare(x, y, f'{path}[{i}]', column)
    elif a is None or b is None:
        assert a is b, (path, a, b)
    elif isinstance(a, (Decimal, int, float)) and not isinstance(a, bool):
        assert isinstance(b, (Decimal, int, float)) and not isinstance(b, bool), (path, type(b))
        # Ponto flutuante indicaria cálculo aproximado; o contrato usa inteiros e decimais.
        assert not isinstance(a, float) and not isinstance(b, float), (path, 'float', a, b)
        delta = abs(Decimal(str(a)) - Decimal(str(b)))
        tolerance = Decimal('1e-12') if column in RATIOS else Decimal(0)
        assert delta <= tolerance, (path, a, b, delta)
    else:
        # Em Python, True == 1; o tipo lógico precisa coincidir nos dois bancos.
        assert isinstance(a, bool) == isinstance(b, bool), (path, 'bool', a, b)
        assert a == b, (path, a, b)


def save(path, data):
    path.write_text(json.dumps(norm(data), ensure_ascii=False, indent=2,
                              default=lambda x: str(x) if isinstance(x, Decimal) else str(x)))


def sql_query(n):
    return (ROOT / f'sql/queries/Q{n:02}.sql').read_text()


def migration(pg):
    raw = mongo_script("load('/mongo/entrega02/04_exportar_conferencia.js');")
    (OUT / 'retorno-migracao.json').write_text(raw)
    reconstructed = json.loads(raw)
    report = []
    for table, rows in reconstructed.items():
        actual = pg.execute('SELECT * FROM nw.' + table).fetchall()
        # Conversões por tipo da coluna, sem reduzir a escala decimal.
        types = {k: type(v) for row in actual for k, v in row.items() if v is not None}
        converted = [{k: Decimal(v) if types.get(k) is Decimal and v is not None else v
                      for k, v in row.items()} for row in rows]
        key = lambda row: json.dumps(norm(row), sort_keys=True, default=str)
        compare(sorted(actual, key=key), sorted(converted, key=key), table)
        report.append({'tabela': table, 'linhas': len(actual), 'divergencias': 0})
    assert sum(x['linhas'] for x in report) == 3311
    save(OUT / 'migracao.json', report)
    checks = mongo_script("load('/mongo/entrega02/05_verificar.js');")
    (OUT / 'estruturas-mongo.txt').write_text(checks)
    return report


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    pg, client = connections()
    db = client.northwind
    migration(pg)
    specs = export_specs()
    results = {}
    for n in range(1, 17):
        query = sql_query(n)
        sql_rows = pg.execute(query).fetchall()
        spec = specs[str(n)]
        mongo_rows = list(db[spec['collection']].aggregate(spec['pipeline']))
        compare(sql_rows, mongo_rows, f'Q{n:02}/P{n:02}')
        results[str(n)] = {'sql': query, 'columns': list(sql_rows[0]) if sql_rows else [],
                           'rows': norm(sql_rows), 'mongo_rows': norm(mongo_rows),
                           'row_count': len(sql_rows), 'equivalent': True}
        print(f'Q{n:02}/P{n:02}: {len(sql_rows)} linhas equivalentes', flush=True)
    total = pg.execute('SELECT sum(unit_price*quantity*(1-discount)) total FROM nw.order_items').fetchone()['total']
    assert total == Decimal('1265793.03950')
    for n in [1, 2, 4, 10, 11, 14]:
        assert sum(r['valor'] for r in results[str(n)]['rows']) == total, n
    assert results['8']['rows'][-1]['acumulado'] == total
    assert sum(r['pedidos'] for r in results['2']['rows']) == 830
    assert sum(r['sem_data'] for r in results['13']['rows']) == 21
    for r in results['14']['rows']:
        assert r['bruto'] - r['desconto'] == r['valor']
    hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
              for pattern in ['sql/queries/Q*.sql', 'mongo/pipelines/P*.js', 'sql/entrega03/*.sql']
              for p in ROOT.glob(pattern)}
    save(OUT / 'resultados.json', results)
    save(OUT / 'manifesto.json', {'executado_em': datetime.now(timezone.utc).isoformat(),
         'postgres': pg.execute('select version() v').fetchone()['v'],
         'mongo': client.server_info()['version'], 'total_exato': total,
         'regras': {'quocientes_tolerancia_absoluta': '1e-12', 'demais_numeros': 'exatos',
                    'ordenacao': 'comparação sequencial, sem reordenar os resultados'},
         'sha256': hashes})
    pg.close()
    client.close()
    print('PASSOU: migração, 16 pares, ordenação e controles analíticos.')


if __name__ == '__main__':
    main()
