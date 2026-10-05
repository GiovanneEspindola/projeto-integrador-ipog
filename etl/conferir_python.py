"""Terceiro caminho de cálculo: Python puro sobre as linhas de nw, sem SQL analítico.

SQL e MongoDB podem concordar entre si e ainda assim errar a mesma regra. Este
script recalcula os 16 resultados com laços e dicionários, a partir das linhas
brutas de nw, e compara com resultados.json (tolerância 1e-12 só em quocientes).

Uso: uv run python etl/conferir_python.py
"""
import os
import json, psycopg, itertools
from psycopg.rows import dict_row
from decimal import Decimal as D
from datetime import date
from collections import defaultdict
pg=psycopg.connect(os.getenv('PG_DSN','postgresql://pi:pi@localhost:5432/northwind'),row_factory=dict_row)
q=lambda s:pg.execute(s).fetchall()
O={o['order_id']:o for o in q('select * from nw.orders')}
I=q('select * from nw.order_items')
P={p['product_id']:p for p in q('select * from nw.products')}
C={c['customer_id']:c for c in q('select * from nw.customers')}
E={e['employee_id']:e for e in q('select * from nw.employees')}
S={s['shipper_id']:s for s in q('select * from nw.shippers')}
CAT={c['category_id']:c for c in q('select * from nw.categories')}
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];EV=ROOT/'apresentacao/evidencias/entrega03'
R=json.load(open(EV/'resultados.json'))
A,B=date(1996,7,1),date(1998,6,1); REF=date(1998,5,6); CUT=date(1997,11,6)
inp=lambda d:A<=d<B
val=lambda i:i['unit_price']*i['quantity']*(1-i['discount'])
ov=defaultdict(D); 
for i in I: ov[i['order_id']]+=val(i)
bad=[]
def chk(n,exp):
    got=R[str(n)]['rows']
    def eq(a,b):
        if a is None or b is None: return a is None and b is None
        if isinstance(a,(D,int,float)) and not isinstance(a,bool): return abs(D(str(a))-D(str(b)))<=D('1e-12')
        return str(a)==str(b)
    ok=len(got)==len(exp) and all(set(g)==set(e) and all(eq(e[k],g[k]) for k in e) for g,e in zip(got,exp))
    if not ok:
        bad.append(n)
        for g,e in zip(got,exp):
            if not(set(g)==set(e) and all(eq(e[k],g[k]) for k in e)): print('DIF',n,g,e);break
        if len(got)!=len(exp): print('LEN',n,len(got),len(exp))
# 1
t=defaultdict(lambda:[0,D(0)])
for i in I:
    if inp(O[i['order_id']]['order_date']):
        c=P[i['product_id']]['category_id'];t[c][0]+=i['quantity'];t[c][1]+=val(i)
tot=sum(v[1] for v in t.values())
chk(1,[dict(category_id=c,categoria=CAT[c]['category_name'],unidades=u,valor=v,participacao=100*v/tot) for c,(u,v) in sorted(t.items())])
# 2,8,9
meses=[date(1996+(6+k)//12,(6+k)%12+1,1) for k in range(23)]
mp=defaultdict(lambda:[0,D(0)])
for o in O.values():
    if inp(o['order_date']): m=o['order_date'].replace(day=1);mp[m][0]+=1;mp[m][1]+=ov[o['order_id']]
chk(2,[dict(mes=m.isoformat(),pedidos=mp[m][0],valor=mp[m][1],ticket=(mp[m][1]/mp[m][0] if mp[m][0] else None)) for m in meses])
acc=D(0);rows=[]
for m in meses: acc+=mp[m][1];rows.append(dict(mes=m.isoformat(),valor=mp[m][1],acumulado=acc))
chk(8,rows)
rows=[];prev=None
for m in meses:
    v=mp[m][1];rows.append(dict(mes=m.isoformat(),valor=v,anterior=prev,variacao=None if prev is None else v-prev,percentual=None if not prev else 100*(v-prev)/prev));prev=v
chk(9,rows)
# 3
sold={i['product_id'] for i in I if inp(O[i['order_id']]['order_date'])}
chk(3,[dict(product_id=p,produto=P[p]['product_name'],categoria=CAT[P[p]['category_id']]['category_name'],fornecedor=None) for p in sorted(set(P)-sold)])
# 4
e4={e:[0,D(0)] for e in E}
for o in O.values():
    if inp(o['order_date']): e4[o['employee_id']][0]+=1;e4[o['employee_id']][1]+=ov[o['order_id']]
tot=sum(v[1] for v in e4.values())
chk(4,[dict(employee_id=e,funcionario=E[e]['first_name']+' '+E[e]['last_name'],pedidos=n,valor=v,ticket=v/n if n else None,participacao=100*v/tot) for e,(n,v) in sorted(e4.items())])
# 5
g=defaultdict(list)
for p in sorted(P.values(),key=lambda p:p['product_id']):
    if p['units_in_stock']<p['reorder_level']: g[p['category_id']].append(p)
chk(5,[dict(category_id=c,categoria=CAT[c]['category_name'],produtos=len(ps),deficit=sum(p['reorder_level']-p['units_in_stock'] for p in ps),reposicao_insuficiente=sum(p['units_in_stock']+p['units_on_order']<p['reorder_level'] for p in ps),produtos_ids=[p['product_id'] for p in ps]) for c,ps in sorted(g.items())])

# 6 / 11
last=defaultdict(lambda:None);freq=defaultdict(int);vv=defaultdict(D)
for o in O.values():
    if o['order_date']<=REF:
        c=o['customer_id'];last[c]=max(filter(None,[last[c],o['order_date']]));freq[c]+=1;vv[c]+=ov[o['order_id']]
chk(6,[dict(customer_id=c,cliente=C[c]['company_name'],ultima=last[c].isoformat() if last[c] else None,recencia=(REF-last[c]).days if last[c] else None,situacao='sem compras' if not last[c] else 'inativo') for c in sorted(C) if last[c] is None or last[c]<CUT])
def band(x,a,b): return 3 if x>=a else 2 if x>=b else 1
rows=[]
for c in sorted(C):
    f=freq[c];r=(REF-last[c]).days if last[c] else None
    rows.append(dict(customer_id=c,recencia=r,frequencia=f,valor=vv[c],r=0 if f==0 else 3 if r<=30 else 2 if r<=90 else 1,f=0 if f==0 else band(f,10,5),m=0 if f==0 else band(vv[c],10000,5000)))
chk(11,rows)
# 7
pv=defaultdict(D)
for i in I:
    if inp(O[i['order_id']]['order_date']): pv[(P[i['product_id']]['category_id'],i['product_id'])]+=val(i)
rows=[]
for c in sorted(CAT):
    items=sorted([(p,v) for (cc,p),v in pv.items() if cc==c],key=lambda x:(-x[1],x[0]))[:5]
    rows+= [dict(category_id=c,product_id=p,valor=v,posicao=k+1) for k,(p,v) in enumerate(items)]
chk(7,rows)
# 10
cv={c:[0,D(0)] for c in C}
for o in O.values():
    if inp(o['order_date']): cv[o['customer_id']][0]+=1;cv[o['customer_id']][1]+=ov[o['order_id']]
tot=sum(v[1] for v in cv.values());acc=D(0);rows=[]
for c,(n,v) in sorted(cv.items(),key=lambda x:(-x[1][1],x[0])):
    prev=acc;acc+=v
    rows.append(dict(customer_id=c,cliente=C[c]['company_name'],pedidos=n,valor=v,acumulado=acc,classe='sem compras' if n==0 else 'A' if prev<tot*D('0.80') else 'B' if prev<tot*D('0.95') else 'C'))
chk(10,rows)
from collections import Counter

# 12
items_by=defaultdict(set)
for i in I:
    if inp(O[i['order_id']]['order_date']): items_by[i['order_id']].add(i['product_id'])
den=sum(1 for o in O.values() if inp(o['order_date']))
pc=Counter()
for ps in items_by.values():
    for a,b in itertools.combinations(sorted(ps),2): pc[(a,b)]+=1
chk(12,[dict(produto_a=a,produto_b=b,pedidos=n,denominador=den,suporte=D(100)*n/den) for (a,b),n in sorted(pc.items(),key=lambda x:(-x[1],x[0]))])
# 13
rows=[]
for s in sorted(S):
    os_=[o for o in O.values() if o['shipper_id']==s and inp(o['order_date'])]
    sh=[o for o in os_ if o['shipped_date']]
    sd=sum((o['shipped_date']-o['order_date']).days for o in sh)
    rows.append(dict(shipper_id=s,transportadora=S[s]['company_name'],pedidos=len(os_),com_envio=len(sh),sem_data=len(os_)-len(sh),soma_dias=sd,media_dias=D(sd)/len(sh) if sh else None,apos_requerida=sum(o['shipped_date']>o['required_date'] for o in sh)))
chk(13,rows)
# 14
t=defaultdict(lambda:[D(0)]*3)
for i in I:
    if inp(O[i['order_id']]['order_date']):
        c=P[i['product_id']]['category_id'];b=i['unit_price']*i['quantity'];d=b*i['discount']
        t[c]=[t[c][0]+b,t[c][1]+d,t[c][2]+val(i)]
chk(14,[dict(category_id=c,bruto=b,desconto=d,valor=v,percentual_desconto=100*d/b) for c,(b,d,v) in sorted(t.items())])
# 15
def desc(e):
    out={e};fr=[e]
    while fr:
        x=fr.pop();ch=[k for k,v in E.items() if v['reports_to']==x and k not in out];out|=set(ch);fr+=ch
    return out
ev={e:[0,D(0)] for e in E}
for o in O.values():
    if inp(o['order_date']): ev[o['employee_id']][0]+=1;ev[o['employee_id']][1]+=ov[o['order_id']]
chk(15,[dict(gestor_id=e,membros=len(desc(e)),valor_proprio=ev[e][1],pedidos_equipe=sum(ev[m][0] for m in desc(e)),valor_equipe=sum(ev[m][1] for m in desc(e))) for e in sorted(E)])
# 16
tq=defaultdict(D);cq=defaultdict(D)
for i in I:
    d=O[i['order_id']]['order_date']
    if inp(d):
        k=(d.year,(d.month-1)//3+1);tq[k]+=val(i);cq[k+(P[i['product_id']]['category_id'],)]+=val(i)
mn=min(o['order_date'] for o in O.values());mx=max(o['order_date'] for o in O.values())
def parcial(y,t):
    s=date(y,(t-1)*3+1,1);e=date(y+(t*3)//12,(t*3)%12+1,1)
    return s<mn or e>date(mx.year,mx.month,mx.day+1)
rows=[]
for k in sorted(tq):
    rows.append(dict(ano=k[0],trimestre=k[1],category_id=None,valor=tq[k],nivel='total',parcial=parcial(*k)))
    for kk in sorted(x for x in cq if x[:2]==k): rows.append(dict(ano=k[0],trimestre=k[1],category_id=kk[2],valor=cq[kk],nivel='categoria',parcial=parcial(*k)))
chk(16,rows)
report={'metodo':'Python puro sobre as linhas de nw','pares':16,'divergentes':bad,
 'linhas':{str(n):len(R[str(n)]['rows']) for n in range(1,17)}}
(EV/'conferencia-python.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
assert not bad,bad
print('PASSOU: 16 pares recalculados em Python sem divergência.')
