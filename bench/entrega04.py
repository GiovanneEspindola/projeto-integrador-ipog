"""Entrega 4: os índices que faltavam no MongoDB mudam a comparação?

Na Entrega 3, P04 e P15 (por funcionário) e P13 (por transportadora) percorriam
todos os pedidos em cada $lookup, porque o MongoDB não tinha índice em
employee_id nem em shipper_id. Este teste mede os três pipelines em duas cópias
isoladas do banco: com os índices atuais e com os dois índices acrescentados.
O PostgreSQL original é medido nas mesmas rodadas, como referência.

Uso: uv run python bench/entrega04.py
Mesma metodologia da Entrega 3: 5 aquecimentos, 20 medições, ordem alternada,
resultado consumido por inteiro. As cópias são removidas ao final.
"""
from pathlib import Path
import json, sys, uuid
from bson import json_util
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'etl'))
sys.path.insert(0, str(ROOT / 'bench'))
from validar_analytics import connections, export_specs, sql_query, compare, save
from entrega03 import timed, stats, WARM, REPEATS

DEST = ROOT / 'bench/results/entrega04'
PARES = [4, 13, 15]


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    pg, client = connections()
    specs = export_specs()
    tag = 'bench_e04_' + uuid.uuid4().hex[:8]
    copias = {'indices_atuais': client[tag + '_atual'], 'com_employee_shipper': client[tag + '_novo']}
    try:
        for db in copias.values():
            for col in client.northwind.list_collection_names():
                rows = list(client.northwind[col].find({}))
                if rows:
                    db[col].insert_many(rows)
            # Recria os índices do banco original em cada cópia.
            for col in client.northwind.list_collection_names():
                for ix in client.northwind[col].list_indexes():
                    if ix['name'] != '_id_':
                        db[col].create_index(list(ix['key'].items()), name=ix['name'])
        copias['com_employee_shipper'].orders.create_index('employee_id', name='pedido_funcionario')
        copias['com_employee_shipper'].orders.create_index('shipper_id', name='pedido_transportadora')

        resultado = {}
        for n in PARES:
            spec = specs[str(n)]
            query = sql_query(n)
            runners = {'postgres': lambda q=query: pg.execute(q).fetchall()}
            for nome, db in copias.items():
                runners[nome] = lambda s=spec, d=db: list(d[s['collection']].aggregate(s['pipeline']))
            referencia = runners['postgres']()
            for nome in copias:
                compare(referencia, runners[nome](), f'P{n:02} {nome}')
            nomes = list(runners)
            valores = {k: [] for k in nomes}
            for i in range(WARM + REPEATS):
                k = i % len(nomes)
                for nome in nomes[k:] + nomes[:k]:
                    ms, _ = timed(runners[nome])
                    if i >= WARM:
                        valores[nome].append(ms)
            resultado[f'{n:02}'] = {k: stats(v) for k, v in valores.items()}
            for nome, db in copias.items():
                plano = db.command('explain', {'aggregate': spec['collection'], 'pipeline': spec['pipeline'], 'cursor': {}},
                                   verbosity='executionStats')
                (DEST / f'P{n:02}-{nome}-plan.ejson').write_text(json_util.dumps(plano, indent=2))
            print(f'P{n:02}: ' + '; '.join(f'{k} {resultado[f"{n:02}"][k]["mediana_ms"]:.3f} ms' for k in nomes), flush=True)
        save(DEST / 'indices-mongo.json', resultado)
    finally:
        for db in copias.values():
            client.drop_database(db.name)
        pg.close()
        client.close()
    print('PASSOU: resultados iguais nas duas cópias; cópias removidas.')


if __name__ == '__main__':
    main()
