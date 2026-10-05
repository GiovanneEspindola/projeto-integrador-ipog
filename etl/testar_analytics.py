"""Casos de fronteira em cópias temporárias; os dados Northwind ficam intactos."""
from copy import deepcopy
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
import json
import uuid

from bson import Decimal128
from psycopg import sql
import psycopg

from validar_analytics import ROOT, OUT, connections, export_specs, compare, save, sql_query


def by(rows, key, value):
    return next(r for r in rows if str(r[key]) == str(value))


def _q02(a):
    assert len(a) == 23 and sum(r['pedidos'] for r in a) == 4
    nov, jan, feb, mar = (by(a, 'mes', m) for m in ['1997-11-01', '1998-01-01', '1998-02-01', '1998-03-01'])
    assert (nov['pedidos'], nov['valor'], nov['ticket']) == (2, 20, 10)
    assert (jan['pedidos'], jan['valor'], jan['ticket']) == (1, 20, 20)
    assert (feb['pedidos'], feb['valor'], feb['ticket']) == (0, 0, None)
    assert (mar['pedidos'], mar['valor'], mar['ticket']) == (1, Decimal('0.005'), Decimal('0.005'))


def _q06(a):
    ids = {r['customer_id']: r for r in a}
    assert 'ANATR' not in ids and 'ALFKI' not in ids
    assert ids['ANTON']['recencia'] == 182 and ids['ANTON']['situacao'] == 'inativo'
    assert len(a) == 89 and sum(r['situacao'] == 'sem compras' for r in a) == 88


def _q09(a):
    feb, mar = by(a, 'mes', '1998-02-01'), by(a, 'mes', '1998-03-01')
    assert (feb['anterior'], feb['variacao'], feb['percentual']) == (20, -20, -100)
    assert (mar['anterior'], mar['variacao'], mar['percentual']) == (0, Decimal('0.005'), None)


def _q10(a):
    assert [(r['customer_id'], r['classe']) for r in a[:3]] == [('ALFKI', 'A'), ('ANATR', 'A'), ('ANTON', 'A')]
    assert a[0]['valor'] == Decimal('20.005') and all(r['classe'] == 'sem compras' for r in a[3:])


def _q11(a):
    alfki, anatr, bergs = by(a, 'customer_id', 'ALFKI'), by(a, 'customer_id', 'ANATR'), by(a, 'customer_id', 'BERGS')
    assert (alfki['recencia'], alfki['frequencia'], alfki['r'], alfki['f'], alfki['m']) == (62, 2, 2, 1, 1)
    assert (anatr['recencia'], anatr['r']) == (181, 1)
    assert (bergs['recencia'], bergs['frequencia'], bergs['r'], bergs['f'], bergs['m']) == (None, 0, 0, 0, 0)


def _q13(a):
    s1 = by(a, 'shipper_id', 1)
    assert (s1['pedidos'], s1['com_envio'], s1['sem_data'], s1['soma_dias'], s1['media_dias'], s1['apos_requerida']) == (4, 3, 1, 30, 10, 3)
    assert all(r['pedidos'] == 0 and r['media_dias'] is None for r in a if r['shipper_id'] != 1)


def _q15(a):
    g1, g2, g5 = by(a, 'gestor_id', 1), by(a, 'gestor_id', 2), by(a, 'gestor_id', 5)
    assert (g1['membros'], g1['valor_proprio'], g1['pedidos_equipe']) == (1, Decimal('40.005'), 4)
    assert (g2['membros'], g2['valor_proprio'], g2['pedidos_equipe'], g2['valor_equipe']) == (9, 0, 4, Decimal('40.005'))
    assert g5['pedidos_equipe'] == 0


# Quatro pedidos sintéticos: 90001 ALFKI jan/98 (produtos 1 e 2, sem data de envio),
# 90002 ALFKI mar/98 (valor 0,005), 90003 ANATR no corte 06/11/97, 90004 ANTON um dia antes.
EXPECTED = {
    1: ('categoria 1: 5 unidades, valor 40,005, participação 100%', lambda a: [
        (r['category_id'], r['unidades'], r['valor'], r['participacao']) for r in a] == [(1, 5, Decimal('40.005'), 100)] or _fail()),
    2: ('23 meses; fev/98 vazio com ticket nulo; mar/98 com 0,005', _q02),
    3: ('75 produtos sem venda: todos menos 1 e 2', lambda a: [r['product_id'] for r in a] == list(range(3, 78)) or _fail()),
    4: ('funcionário 1 com 4 pedidos e 100%; demais com ticket nulo', lambda a: (
        by(a, 'employee_id', 1)['pedidos'] == 4 and by(a, 'employee_id', 1)['participacao'] == 100
        and all(r['ticket'] is None for r in a if r['employee_id'] != 1)) or _fail()),
    6: ('ANATR no corte fica fora; ANTON inativo com 182 dias; 88 sem compras', _q06),
    7: ('categoria 1: produto 1 (30,005) antes do 2 (10)', lambda a: [
        (r['product_id'], r['valor'], r['posicao']) for r in a] == [(1, Decimal('30.005'), 1), (2, 10, 2)] or _fail()),
    8: ('acumulado final 40,005', lambda a: a[-1]['acumulado'] == Decimal('40.005') or _fail()),
    9: ('fev/98 −100%; mar/98 com anterior zero e percentual nulo', _q09),
    10: ('três clientes A e 88 sem compras', _q10),
    11: ('ALFKI R=2 F=1 M=1; ANATR R=1; sem compras com escores zero', _q11),
    12: ('um par 1–2, denominador 4, suporte 25%', lambda a: [
        (r['produto_a'], r['produto_b'], r['pedidos'], r['denominador'], r['suporte']) for r in a] == [(1, 2, 1, 4, 25)] or _fail()),
    13: ('transportadora 1: 4 pedidos, 3 envios, 1 sem data, média 10 dias', _q13),
    14: ('categoria 1: bruto 40,05, desconto 0,045, valor 40,005', lambda a: [
        (r['bruto'], r['desconto'], r['valor']) for r in a] == [(Decimal('40.05'), Decimal('0.045'), Decimal('40.005'))] or _fail()),
    15: ('gestor 2 contém os 4 pedidos do funcionário 1; gestor 5 nenhum', _q15),
    16: ('4T/1997 = 20 e 1T/1998 = 20,005, sem trimestre parcial', lambda a: [
        (r['ano'], r['trimestre'], r['nivel'], r['valor'], r['parcial']) for r in a] == [
        (1997, 4, 'total', 20, False), (1997, 4, 'categoria', 20, False),
        (1998, 1, 'total', Decimal('20.005'), False), (1998, 1, 'categoria', Decimal('20.005'), False)] or _fail()),
}


def _fail():
    raise AssertionError('valor esperado não conferiu')


def main():
    pg, client = connections()
    specs = export_specs()
    test_name = 'teste_e03_' + uuid.uuid4().hex[:10]
    testdb = client[test_name]
    checks = []
    pg.execute('BEGIN')
    try:
        pg.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(test_name)))
        for table in ['regions','territories','categories','shippers','suppliers','customers',
                      'employees','employee_territories','products','orders','order_items']:
            pg.execute(sql.SQL('CREATE TABLE {}.{} AS SELECT * FROM nw.{}').format(
                sql.Identifier(test_name),sql.Identifier(table),sql.Identifier(table)))
        for table, keys in {'regions':'region_id','territories':'territory_id',
            'categories':'category_id','shippers':'shipper_id','suppliers':'supplier_id',
            'customers':'customer_id','employees':'employee_id','products':'product_id',
            'orders':'order_id','order_items':'order_id,product_id',
            'employee_territories':'employee_id,territory_id'}.items():
            pg.execute(f'ALTER TABLE {test_name}.{table} ADD PRIMARY KEY ({keys})')
        pg.execute(f'TRUNCATE {test_name}.orders, {test_name}.order_items')
        for name in client.northwind.list_collection_names():
            if name != 'orders':
                rows = list(client.northwind[name].find({}))
                if rows:
                    testdb[name].insert_many(rows)
        base = client.northwind.orders.find_one({'_id':10248})
        cases = [(90001,'ALFKI','1998-01-05',[(1,'10','0'),(2,'10','0')]),
                 (90002,'ALFKI','1998-03-05',[(1,'0.05','0.9')]),
                 (90003,'ANATR','1997-11-06',[(1,'10','0')]),
                 (90004,'ANTON','1997-11-05',[(1,'10','0')])]
        for oid, cid, day, items in cases:
            order = deepcopy(base)
            d = datetime.fromisoformat(day)
            order.update(_id=oid,customer_id=cid,employee_id=1,shipper_id=1,
                         order_date=d,required_date=d+timedelta(days=5),
                         shipped_date=None if oid==90001 else d+timedelta(days=10))
            order['items'] = []
            for pid, price, discount in items:
                product = testdb.products.find_one({'_id':pid})
                order['items'].append({'product':{'_id':pid,'name':product['product_name'],
                    'category':product['category']},'unit_price':Decimal128(price),
                    'quantity':1,'discount':Decimal128(discount)})
                pg.execute(f'INSERT INTO {test_name}.order_items '
                    '(order_id,product_id,unit_price,quantity,discount) VALUES (%s,%s,%s,1,%s)',
                    (oid,pid,Decimal(price),Decimal(discount)))
            testdb.orders.insert_one(order)
            pg.execute(f'INSERT INTO {test_name}.orders '
                '(order_id,customer_id,employee_id,shipper_id,order_date,required_date,shipped_date) '
                'VALUES (%s,%s,1,1,%s,%s,%s)',
                (oid,cid,d.date(),order['required_date'].date(),
                 order['shipped_date'].date() if order['shipped_date'] else None))
        view_sql = (ROOT/'sql/entrega03/00_views.sql').read_text()
        pg.execute(view_sql.replace('nw_analytics.',test_name+'.')
            .replace('nw.',test_name+'.').replace('CREATE SCHEMA IF NOT EXISTS nw_analytics;', ''))
        for n in range(1,17):
            query = sql_query(n).replace('nw_analytics.',test_name+'.').replace('nw.',test_name+'.')
            a=pg.execute(query).fetchall()
            spec=specs[str(n)]
            b=list(testdb[spec['collection']].aggregate(spec['pipeline']))
            compare(a,b,f'fixture Q{n:02}')
            # Além de SQL = MongoDB, valores calculados à mão para os quatro pedidos acima.
            esperado=EXPECTED.get(n)
            if esperado:
                esperado[1](a)
            checks.append({'teste':f'Q{n:02} dados de fronteira','resultado':'PASSOU','linhas':len(a),
                           **({'esperado':esperado[0]} if esperado else {})})
        # Empate real entre produtos 1 e 2 no mesmo período/categoria.
        pg.execute(f'UPDATE {test_name}.order_items SET unit_price=10,discount=0 WHERE product_id=2')
        tie_sql=sql_query(7).replace('nw_analytics.',test_name+'.').replace('nw.',test_name+'.')
        tie_sql=tie_sql.replace("DATE '1996-07-01'","DATE '1998-01-01'").replace("DATE '1998-06-01'","DATE '1998-02-01'")
        ties=pg.execute(tie_sql).fetchall()
        pipe=deepcopy(specs['7']['pipeline'])
        pipe[0]['$match']['order_date']={'$gte':datetime(1998,1,1),'$lt':datetime(1998,2,1)}
        compare(ties,list(testdb.orders.aggregate(pipe)),'empate')
        assert [r['product_id'] for r in ties]==[1,2]
        assert [r['posicao'] for r in ties]==[1,2]
        checks.append({'teste':'empate com desempate por ID','resultado':'PASSOU'})
        # Nenhum pedido: calendários permanecem completos; divisões viram null.
        pg.execute(f'TRUNCATE {test_name}.orders, {test_name}.order_items')
        testdb.orders.delete_many({})
        for n in range(1,17):
            query=sql_query(n).replace('nw_analytics.',test_name+'.').replace('nw.',test_name+'.')
            a=pg.execute(query).fetchall()
            spec=specs[str(n)]
            b=list(testdb[spec['collection']].aggregate(spec['pipeline']))
            compare(a,b,f'vazio Q{n:02}')
            checks.append({'teste':f'Q{n:02} sem pedidos','resultado':'PASSOU'})
        assert Decimal('0.005').quantize(Decimal('.01'),rounding=ROUND_HALF_UP)==Decimal('.01')
        pg_half=pg.execute('SELECT round(0.005::numeric,2) v').fetchone()['v']
        mongo_half=list(client.northwind.orders.aggregate([{'$limit':1},{'$project':{'_id':0,'v':{'$round':[Decimal128('0.005'),2]}}}]))[0]['v'].to_decimal()
        assert pg_half==Decimal('.01') and mongo_half==Decimal('0.00')
        checks.append({'teste':'empate de meio centavo demonstra regras diferentes',
                       'postgres':pg_half,'mongo':mongo_half,'resultado':'PASSOU'})
    finally:
        pg.execute('ROLLBACK')
        client.drop_database(test_name)
    # Procedures reais, com FETCH na mesma transação e comparação independente.
    with pg.transaction():
        pg.execute("CALL nw_analytics.sp_clientes_inativos('1998-05-06',6,'ci')")
        compare(pg.execute('FETCH ALL FROM ci').fetchall(),pg.execute(sql_query(6)).fetchall(),'procedure clientes')
        pg.execute("CALL nw_analytics.sp_desempenho_equipe(2,'1996-07-01','1998-06-01','ce')")
        compare(pg.execute('FETCH ALL FROM ce').fetchall(),
                [r for r in pg.execute(sql_query(15)).fetchall() if r['gestor_id']==2],'procedure equipe')
        pg.execute("CALL nw_analytics.sp_resumo_vendas_periodo('1996-07-01','1998-06-01','cv')")
        rows=pg.execute('FETCH ALL FROM cv').fetchall()
        direct=pg.execute("SELECT p.category_id,c.category_name categoria,count(DISTINCT o.order_id) pedidos,"
            "sum(i.unit_price*i.quantity*(1-i.discount)) valor,"
            "sum(i.unit_price*i.quantity*(1-i.discount))/count(DISTINCT o.order_id) ticket_categoria "
            "FROM nw.orders o JOIN nw.order_items i USING(order_id) JOIN nw.products p USING(product_id) "
            "JOIN nw.categories c USING(category_id) WHERE o.order_date>='1996-07-01' AND o.order_date<'1998-06-01' "
            "GROUP BY p.category_id,c.category_name ORDER BY p.category_id").fetchall()
        compare(rows,direct,'procedure vendas')
        save(OUT/'procedures.json',{'vendas_por_categoria':rows,
             'inativos':pg.execute(sql_query(6)).fetchall(),
             'equipe':[r for r in pg.execute(sql_query(15)).fetchall() if r['gestor_id']==2]})
    for statement in [
        "CALL nw_analytics.sp_resumo_vendas_periodo('1998-01-02','1998-01-01','x')",
        "CALL nw_analytics.sp_clientes_inativos('1998-05-06',0,'x')",
        "CALL nw_analytics.sp_desempenho_equipe(9999,'1997-01-01','1998-01-01','x')"]:
        try:
            with pg.transaction(): pg.execute(statement)
        except psycopg.errors.RaiseException:
            checks.append({'teste':statement,'resultado':'rejeitado corretamente'})
        else: raise AssertionError('Parâmetro inválido aceito')
    checks.append({'teste':'três procedures versus consultas independentes','resultado':'PASSOU'})
    save(OUT/'testes-fronteira.json',checks)
    print(f'PASSOU: {len(checks)} verificações; estruturas temporárias removidas.')
    pg.close();client.close()


if __name__=='__main__': main()
