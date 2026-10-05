"""Benchmark aquecido: 5 aquecimentos, 20 amostras, resultados consumidos.

uv run python bench/entrega03.py
Não mede abertura de conexão nem impressão; EXPLAIN é coletado separadamente.
Os estudos usam cópias temporárias (sem índice extra, com índice por data e com índice
composto), removidas ao terminar; as versões de cada estudo são medidas intercaladas.
"""
from pathlib import Path
import sys, time, statistics, json, platform, os, uuid, subprocess
from copy import deepcopy
from datetime import datetime
from decimal import Decimal
from bson import json_util
from psycopg import sql
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'etl'))
from validar_analytics import connections, export_specs, sql_query, compare, save, OUT
DEST=ROOT/'bench/results/entrega03'
WARM=5; REPEATS=20

def timed(fn):
    t=time.perf_counter_ns(); rows=fn(); elapsed=(time.perf_counter_ns()-t)/1e6
    return elapsed,rows

def stats(values):
    q=statistics.quantiles(values,n=4,method='inclusive')
    return {'amostras_ms':values,'mediana_ms':statistics.median(values),
            'q1_ms':q[0],'q3_ms':q[2],'iqr_ms':q[2]-q[0],
            'min_ms':min(values),'max_ms':max(values)}

def measure(pg,db,query,spec,stem):
    runners={'postgres':lambda:pg.execute(query).fetchall(),
             'mongo':lambda:list(db[spec['collection']].aggregate(spec['pipeline']))}
    compare(runners['postgres'](),runners['mongo'](),stem)
    values={k:[] for k in runners}
    for i in range(WARM+REPEATS):
        order=['postgres','mongo'] if i%2==0 else ['mongo','postgres']
        for k in order:
            ms,_=timed(runners[k])
            if i>=WARM:values[k].append(ms)
    plan=pg.execute('EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) '+query).fetchone()
    save(DEST/(stem+'-postgres-plan.json'),plan)
    mp=db.command('explain',{'aggregate':spec['collection'],'pipeline':spec['pipeline'],'cursor':{}},verbosity='executionStats')
    (DEST/(stem+'-mongo-plan.ejson')).write_text(json_util.dumps(mp,indent=2))
    return {k:stats(v) for k,v in values.items()}

def measure_study(pg,runs,case):
    """Mede todas as versões de um estudo na mesma sequência de rodadas.

    Em cada rodada a ordem das versões é rotacionada e a ordem dos bancos alterna,
    para que uma deriva do ambiente não favoreça sistematicamente uma versão.
    """
    reference=None
    runners=[]
    for variant,q,spec,mdb in runs:
        rows=pg.execute(q).fetchall()
        if reference is None:reference=rows
        else:compare(reference,rows,case+' antes/depois')
        compare(rows,list(mdb[spec['collection']].aggregate(spec['pipeline'])),case+'-'+variant)
        runners.append((variant,{'postgres':(lambda q=q:pg.execute(q).fetchall()),
            'mongo':(lambda s=spec,d=mdb:list(d[s['collection']].aggregate(s['pipeline'])))}))
    values={v:{'postgres':[],'mongo':[]} for v,_ in runners}
    for i in range(WARM+REPEATS):
        k=i%len(runners);order=runners[k:]+runners[:k]
        banks=['postgres','mongo'] if i%2==0 else ['mongo','postgres']
        for variant,fns in order:
            for b in banks:
                ms,_=timed(fns[b])
                if i>=WARM:values[variant][b].append(ms)
    out={}
    for variant,q,spec,mdb in runs:
        stem=f'{case}-{variant}'
        save(DEST/(stem+'-postgres-plan.json'),pg.execute('EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) '+q).fetchone())
        mp=mdb.command('explain',{'aggregate':spec['collection'],'pipeline':spec['pipeline'],'cursor':{}},verbosity='executionStats')
        (DEST/(stem+'-mongo-plan.ejson')).write_text(json_util.dumps(mp,indent=2))
        out[variant]={b:stats(v) for b,v in values[variant].items()}
    return out

def save_variant(case,variant,query,spec):
    sd=ROOT/'sql/entrega03/otimizacao';md=ROOT/'mongo/entrega03/otimizacao'
    sd.mkdir(exist_ok=True);md.mkdir(exist_ok=True)
    (sd/f'{case}-{variant}.sql').write_text(query+'\n')
    ejson=json_util.dumps(spec,ensure_ascii=False)
    (md/f'{case}-{variant}.js').write_text(
        '// Executar somente na cópia isolada definida pelo benchmark.\n'
        'var consulta = EJSON.parse('+json.dumps(ejson,ensure_ascii=False)+');\n'
        'print(EJSON.stringify(db.getCollection(consulta.collection)\n'
        '  .aggregate(consulta.pipeline).toArray(), null, 2));\n')

def main():
    DEST.mkdir(parents=True,exist_ok=True)
    pg,client=connections(); db=client.northwind
    specs=export_specs(); results={}
    env={'executado_em':datetime.now().isoformat(),'aquecimentos':WARM,'repeticoes':REPEATS,
         'cenario':'cache aquecido, execução e consumo integral no driver',
         'sistema':platform.platform(),'cpu':platform.processor(),'cpus_logicas':os.cpu_count(),
         'memoria_linux':Path('/proc/meminfo').read_text().splitlines()[:3],
         'postgres':pg.execute('select version() versao').fetchone(),
         'mongo':client.server_info()['version'],
         'config_pg':pg.execute("SELECT name,setting,unit FROM pg_settings WHERE name IN ('shared_buffers','work_mem','effective_cache_size','jit','max_parallel_workers_per_gather') ORDER BY name").fetchall(),
         'indices_pg':pg.execute("SELECT tablename,indexname,indexdef FROM pg_indexes WHERE schemaname='nw' ORDER BY tablename,indexname").fetchall(),
         'indices_mongo':{n:list(db[n].list_indexes()) for n in db.list_collection_names()}}
    env['docker']=json.loads(subprocess.check_output(['docker','inspect','pi-postgres','pi-mongo','--format','{{json .HostConfig}}'],text=True).splitlines()[0]) if False else subprocess.check_output(['docker','inspect','pi-postgres','pi-mongo','--format','{{.Name}} Memory={{.HostConfig.Memory}} NanoCpus={{.HostConfig.NanoCpus}}'],text=True).strip()
    env['cpu_modelo']=next((s.split(':',1)[1].strip() for s in Path('/proc/cpuinfo').read_text().splitlines() if s.startswith('model name')),'indisponível')
    save(DEST/'ambiente.json',env)
    for n in range(1,17):
        results[str(n)]=measure(pg,db,sql_query(n),specs[str(n)],f'Q{n:02}')
        print(f'Q{n:02}: PG {results[str(n)]["postgres"]["mediana_ms"]:.3f} ms; Mongo {results[str(n)]["mongo"]["mediana_ms"]:.3f} ms',flush=True)
    save(DEST/'catalogo.json',results)
    # Três cópias isoladas: sem índices extras, com índice por data e com índice composto.
    # Assim as versões de um estudo podem ser intercaladas em cada rodada, sem criar ou
    # remover índices entre medições.
    tag='bench_e03_'+uuid.uuid4().hex[:8]
    copies={k:{'schema':f'{tag}_{k}','views':f'{tag}_{k}_a','mongo':client[f'{tag}_{k}']} for k in ['base','data','cliente']}
    studies={}
    try:
        tables=['regions','territories','categories','shippers','suppliers','customers','employees','employee_territories','products','orders','order_items']
        vs=(ROOT/'sql/entrega03/00_views.sql').read_text().replace('CREATE SCHEMA IF NOT EXISTS nw_analytics;','')
        for key,c in copies.items():
            name=c['schema']
            pg.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(name)))
            pg.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(c['views'])))
            for t in tables:
                pg.execute(f'CREATE TABLE {name}.{t} (LIKE nw.{t} INCLUDING ALL)')
                pg.execute(f'INSERT INTO {name}.{t} SELECT * FROM nw.{t}')
            # Mantém índices PK/UNIQUE; remove apenas índices não únicos da cópia.
            indices=pg.execute("SELECT ci.relname nome FROM pg_index ix JOIN pg_class ci ON ci.oid=ix.indexrelid JOIN pg_namespace ns ON ns.oid=ci.relnamespace WHERE ns.nspname=%s AND NOT ix.indisunique",(name,)).fetchall()
            for ix in indices:pg.execute(sql.SQL('DROP INDEX {}.{}').format(sql.Identifier(name),sql.Identifier(ix['nome'])))
            if key=='data':pg.execute(f'CREATE INDEX orders_data ON {name}.orders(order_date)')
            if key=='cliente':pg.execute(f'CREATE INDEX orders_cliente_data ON {name}.orders(customer_id,order_date)')
            for t in tables:pg.execute(f'ANALYZE {name}.{t}')
            pg.execute(vs.replace('nw_analytics.',c['views']+'.').replace('nw.',name+'.'))
            for col in db.list_collection_names():
                rows=list(db[col].find({}))
                if rows:c['mongo'][col].insert_many(rows)
            if key=='data':c['mongo'].orders.create_index('order_date',name='orders_data')
            if key=='cliente':c['mongo'].orders.create_index([('customer_id',1),('order_date',1)],name='orders_cliente_data')
        # C01: filtro calculado versus intervalo; depois índice por data.
        base="""SELECT date_trunc('month',order_date)::date mes,count(*) pedidos,sum(valor) valor
FROM nw_analytics.vw_pedido_valor
WHERE to_char(order_date,'YYYY-MM')='1997-01' GROUP BY 1 ORDER BY 1;"""
        optimized=base.replace("to_char(order_date,'YYYY-MM')='1997-01'","order_date>=DATE '1997-01-01' AND order_date<DATE '1997-02-01'")
        item_value={'$sum':{'$map':{'input':'$items','as':'i','in':{'$multiply':['$$i.unit_price','$$i.quantity',{'$subtract':[{'$toDecimal':1},'$$i.discount']}]}}}}
        tail=[{'$group':{'_id':None,'pedidos':{'$sum':1},'valor':{'$sum':item_value}}},
              {'$project':{'_id':0,'mes':{'$literal':'1997-01-01'},'pedidos':1,'valor':1}}]
        mb={'collection':'orders','pipeline':[{'$set':{'mes':{'$dateToString':{'date':'$order_date','format':'%Y-%m'}}}},{'$match':{'mes':'1997-01'}}]+tail}
        mo={'collection':'orders','pipeline':[{'$match':{'order_date':{'$gte':datetime(1997,1,1),'$lt':datetime(1997,2,1)}}}]+tail}
        cases={'C01': [('original',base,mb,'base'),('reescrita',optimized,mo,'base'),('com_indice',optimized,mo,'data')]}
        # C02: mesma consulta antes/depois do índice composto.
        q="SELECT order_id,order_date FROM nw.orders WHERE customer_id='VINET' AND order_date>=DATE '1996-01-01' AND order_date<DATE '1997-01-01' ORDER BY order_date,order_id;"
        m={'collection':'orders','pipeline':[{'$match':{'customer_id':'VINET','order_date':{'$gte':datetime(1996,1,1),'$lt':datetime(1997,1,1)}}},{'$sort':{'order_date':1,'_id':1}},{'$project':{'_id':0,'order_id':'$_id','order_date':{'$dateToString':{'date':'$order_date','format':'%Y-%m-%d'}}}}]}
        cases['C02']=[('sem_composto',q,m,'base'),('com_composto',q,m,'cliente')]
        # C03: reduzir pares intermediários e largura do documento.
        q3="""WITH todos AS MATERIALIZED (
 SELECT a.order_id,a.product_id produto_a,b.product_id produto_b
 FROM nw.order_items a JOIN nw.order_items b USING(order_id)
), pares AS (
 SELECT produto_a,produto_b,count(*) pedidos FROM todos JOIN nw.orders USING(order_id)
 WHERE produto_a<produto_b AND order_date>=DATE '1996-07-01' AND order_date<DATE '1998-06-01'
 GROUP BY produto_a,produto_b
), total AS (SELECT count(*) denominador FROM nw.orders WHERE order_date>=DATE '1996-07-01' AND order_date<DATE '1998-06-01')
SELECT pares.*,denominador,100.0*pedidos/nullif(denominador,0) suporte
FROM pares CROSS JOIN total ORDER BY pedidos DESC,produto_a,produto_b;"""
        m3=deepcopy(specs['12']);st=m3['pipeline'][1]['$facet']['pares']
        st[0]={'$set':{'ids':'$items.product._id'}}
        early=st.pop(4)
        st.append({'$match':{'$expr':{'$lt':['$_id.a','$_id.b']}}})
        cases['C03']=[('original',q3,m3,'base'),('reescrita',sql_query(12),specs['12'],'base')]
        # C04: agrupar vendas antes da expansão por equipe.
        q4="""WITH RECURSIVE equipe AS (
 SELECT employee_id gestor_id,employee_id membro_id,ARRAY[employee_id] caminho FROM nw.employees
 UNION ALL SELECT q.gestor_id,e.employee_id,q.caminho||e.employee_id
 FROM equipe q JOIN nw.employees e ON e.reports_to=q.membro_id
 WHERE NOT e.employee_id=ANY(q.caminho)
)
SELECT q.gestor_id,count(DISTINCT q.membro_id) membros,
 coalesce(sum(v.valor) FILTER (WHERE q.membro_id=q.gestor_id),0) valor_proprio,
 count(v.order_id)::numeric pedidos_equipe,coalesce(sum(v.valor),0) valor_equipe
FROM equipe q LEFT JOIN nw_analytics.vw_pedido_valor v ON v.employee_id=q.membro_id
 AND v.order_date>=DATE '1996-07-01' AND v.order_date<DATE '1998-06-01'
GROUP BY q.gestor_id ORDER BY q.gestor_id;"""
        m4=deepcopy(specs['15']);m4['pipeline'][2]['$lookup']['pipeline']=m4['pipeline'][2]['$lookup']['pipeline'][:1]
        vo=deepcopy(item_value);vo['$sum']['$map']['input']='$$o.items'
        m4['pipeline'].insert(3,{'$set':{'vendas':{'$map':{'input':'$vendas','as':'o','in':{'_id':'$$o.employee_id','pedidos':1,'valor':vo}}}}})
        cases['C04']=[('original',q4,m4,'base'),('reescrita',sql_query(15),specs['15'],'base')]
        for case,variants in cases.items():
            runs=[]
            for variant,q,m,key in variants:
                save_variant(case,variant,q,m)
                c=copies[key]
                runs.append((variant,q.replace('nw_analytics.',c['views']+'.').replace('nw.',c['schema']+'.'),m,c['mongo']))
            studies[case]=measure_study(pg,runs,case)
            print(case,'versões conferidas e medidas de forma intercalada',flush=True)
        save(DEST/'otimizacoes.json',studies)
    finally:
        for c in copies.values():
            pg.execute(sql.SQL('DROP SCHEMA IF EXISTS {} CASCADE').format(sql.Identifier(c['views'])))
            pg.execute(sql.SQL('DROP SCHEMA IF EXISTS {} CASCADE').format(sql.Identifier(c['schema'])))
            client.drop_database(c['mongo'].name)
        pg.close();client.close()
    print('PASSOU: catálogo e quatro estudos; cópias removidas.')

if __name__=='__main__':main()
