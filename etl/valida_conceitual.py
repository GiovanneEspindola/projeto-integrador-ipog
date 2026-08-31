"""Confere o ER conceitual contra o banco: entidades, atributos, identificadores,
cardinalidades e os números citados no diagrama e em docs/02-modelo-conceitual.md.

Sai com código 1 se qualquer verificação falhar, para poder rodar em automação.
"""
import builtins
import io, os, pathlib, sys
import psycopg

DSN = os.environ.get("PG_DSN", "postgresql://pi:pi@localhost:5432/northwind")
ROOT = pathlib.Path(__file__).resolve().parent.parent
EVID = ROOT / "apresentacao" / "evidencias" / "02-validacao-er-conceitual.txt"
BUF = io.StringIO()

def print(*a, **k):
    builtins.print(*a, **k)
    builtins.print(*a, **{**k, "file": BUF})

falhas = []
def ok(cond, msg):
    print(("  OK   " if cond else "  FALHA ") + msg)
    if not cond: falhas.append(msg)

ENT = {
 "FORNECEDOR": ("suppliers", ["supplier_id"], {
   "código do fornecedor":["supplier_id"], "razão social":["company_name"],
   "cidade / país":["city","country"]}),
 "CATEGORIA": ("categories", ["category_id"], {
   "código da categoria":["category_id"], "nome":["category_name"], "descrição":["description"]}),
 "PRODUTO": ("products", ["product_id"], {
   "código do produto":["product_id"], "nome":["product_name"],
   "preço de tabela":["unit_price"], "quantidade em estoque":["units_in_stock"],
   "ponto de reposição":["reorder_level"], "descontinuado":["discontinued"]}),
 "ITEM DO PEDIDO": ("order_details", ["order_id","product_id"], {
   "número do pedido":["order_id"], "código do produto":["product_id"],
   "quantidade":["quantity"], "preço unitário praticado":["unit_price"], "desconto":["discount"]}),
 "PEDIDO": ("orders", ["order_id"], {
   "número do pedido":["order_id"], "data do pedido":["order_date"],
   "data prometida":["required_date"], "data de envio":["shipped_date"],
   "valor do frete":["freight"], "endereço de entrega":["ship_address"]}),
 "CLIENTE": ("customers", ["customer_id"], {
   "código do cliente":["customer_id"], "empresa":["company_name"],
   "contato":["contact_name"], "cidade / país":["city","country"]}),
 "FUNCIONÁRIO": ("employees", ["employee_id"], {
   "matrícula":["employee_id"], "nome":["first_name","last_name"],
   "cargo":["title"], "data de admissão":["hire_date"]}),
 "TRANSPORTADORA": ("shippers", ["shipper_id"], {
   "código da transportadora":["shipper_id"], "nome":["company_name"], "telefone":["phone"]}),
 "TERRITÓRIO": ("territories", ["territory_id"], {
   "código do território":["territory_id"], "descrição":["territory_description"]}),
 "REGIÃO": ("region", ["region_id"], {
   "código da região":["region_id"], "nome":["region_description"]}),
 "ATUAÇÃO": ("employee_territories", ["employee_id","territory_id"], {
   "matrícula":["employee_id"], "código do território":["territory_id"]}),
}

# rel: (rótulo, tabela_filho, fk, tabela_pai, pk_pai, min_filho, max_pai_min)
REL = [
 ("fornece",       "products","supplier_id","suppliers","supplier_id","1,1","0,N"),
 ("classifica",    "products","category_id","categories","category_id","1,1","0,N"),
 ("é vendido em",  "order_details","product_id","products","product_id","1,1","0,N"),
 ("contém",        "order_details","order_id","orders","order_id","1,1","1,N"),
 ("faz",           "orders","customer_id","customers","customer_id","1,1","0,N"),
 ("registra",      "orders","employee_id","employees","employee_id","1,1","0,N"),
 ("entrega",       "orders","ship_via","shippers","shipper_id","1,1","0,N"),
 ("agrupa",        "territories","region_id","region","region_id","1,1","1,N"),
 ("é coberto por", "employee_territories","territory_id","territories","territory_id","1,1","0,N"),
 ("atua em",       "employee_territories","employee_id","employees","employee_id","1,1","0,N"),
 ("chefia",        "employees","reports_to","employees","employee_id","0,1","0,N"),
]

with psycopg.connect(DSN) as cx, cx.cursor() as cur:
    cur.execute("select table_name, column_name from information_schema.columns where table_schema='public'")
    cols = {}
    for t,c in cur.fetchall(): cols.setdefault(t,set()).add(c)

    cur.execute("""select cl.relname, a.attname from pg_constraint k
      join pg_class cl on cl.oid=k.conrelid join pg_namespace n on n.oid=cl.relnamespace
      join unnest(k.conkey) ck(n) on true
      join pg_attribute a on a.attrelid=cl.oid and a.attnum=ck.n
      where k.contype='p' and n.nspname='public'""")
    pks = {}
    for t,c in cur.fetchall(): pks.setdefault(t,set()).add(c)

    print("== 1. Entidades, atributos e identificadores ==")
    for ent,(tab,pk,attrs) in ENT.items():
        ok(tab in cols, f"{ent} -> tabela public.{tab} existe")
        for rot, reais in attrs.items():
            falt = [c for c in reais if c not in cols.get(tab,())]
            ok(not falt, f"{ent}.'{rot}' -> {'+'.join(reais)}" + (f"  AUSENTE: {falt}" if falt else ""))
        ok(pks.get(tab)==set(pk), f"{ent}: PK do diagrama {pk} == PK real {sorted(pks.get(tab,[]))}")

    print("\n== 2. Cardinalidades ==")
    for rot,ct,fk,pt,pk,cmin,pmin in REL:
        cur.execute(f"select count(*), count(*) filter (where {fk} is null) from public.{ct}")
        tot, nulos = cur.fetchone()
        cur.execute(f"""select count(*) from public.{pt} p
                        where not exists (select 1 from public.{ct} c where c.{fk}=p.{pk})""")
        sem_filho, = cur.fetchone()
        cur.execute(f"select count(*) from public.{pt}")
        npai, = cur.fetchone()
        cur.execute(f"""select count(*) from public.{ct} c
                        where c.{fk} is not null
                          and not exists (select 1 from public.{pt} p where p.{pk}=c.{fk})""")
        orfaos, = cur.fetchone()

        obrig = (nulos == 0)
        ok(obrig if cmin=="1,1" else True,
           f"{rot}: lado filho {cmin} -> {nulos} nulos em {ct}.{fk} (de {tot})")
        ok(orfaos==0, f"{rot}: 0 órfãos ({orfaos})")
        if pmin=="1,N":
            ok(sem_filho==0, f"{rot}: lado pai (1,N) -> {sem_filho} de {npai} {pt} sem filho (tem de ser 0)")
        else:
            print(f"  INFO  {rot}: lado pai (0,N) -> {sem_filho} de {npai} {pt} sem filho"
                  + ("   [dados dizem 1..N; (0,N) é escolha de modelo]" if sem_filho==0 else ""))

    print("\n== 3. Números citados nas notas e em docs/02 ==")
    cur.execute("select count(*) from public.customer_demographics"); a,=cur.fetchone()
    cur.execute("select count(*) from public.customer_customer_demo"); b,=cur.fetchone()
    ok(a==0 and b==0, f"tabelas de segmentação vazias: {a} e {b} linhas")
    cur.execute("select count(*) from public.us_states"); us,=cur.fetchone()
    ok(us==51, f"us_states tem 51 linhas: {us}")
    cur.execute("""select count(*) from pg_constraint k join pg_class c on c.oid=k.confrelid
                   where k.contype='f' and c.relname='us_states'""")
    refs,=cur.fetchone()
    ok(refs==0, f"nenhuma FK aponta para us_states: {refs}")
    cur.execute("select count(*), count(distinct territory_id) from public.employee_territories")
    v,d=cur.fetchone(); ok(v==49 and d==49, f"49 vínculos para 49 territórios distintos: {v} / {d}")
    cur.execute("""select count(*) from public.territories t where not exists
                   (select 1 from public.employee_territories e where e.territory_id=t.territory_id)""")
    st,=cur.fetchone()
    cur.execute("select count(*) from public.territories"); nt,=cur.fetchone()
    ok(st==4 and nt==53, f"4 dos 53 territórios sem funcionário: {st} de {nt}")
    cur.execute("select round(count(*)::numeric/count(distinct order_id),1) from public.order_details")
    m,=cur.fetchone(); ok(float(m)==2.6, f"média 2,6 itens por pedido: {m}")
    cur.execute("select round(count(*)::numeric/count(distinct employee_id),1) from public.orders")
    m2,=cur.fetchone(); ok(float(m2)==92.2, f"média 92,2 pedidos por funcionário: {m2}")
    cur.execute("select count(distinct customer_id) from public.orders"); cc,=cur.fetchone()
    cur.execute("select count(*) from public.customers"); tc,=cur.fetchone()
    ok(cc==89 and tc==91, f"89 dos 91 clientes com pedido: {cc} de {tc}")
    cur.execute("select count(distinct ship_via) from public.orders"); sv,=cur.fetchone()
    cur.execute("select count(*) from public.shippers"); ts,=cur.fetchone()
    ok(sv==3 and ts==6, f"3 das 6 transportadoras usadas: {sv} de {ts}")
    cur.execute("select count(*) filter (where reports_to is null), count(distinct reports_to) from public.employees")
    sc,cd=cur.fetchone(); ok(sc==1 and cd==2, f"1 sem chefe e 2 chefes distintos: {sc} / {cd}")

    print("\n== 4. Cobertura: toda tabela da base está classificada ==")
    cur.execute("select table_name from information_schema.tables where table_schema='public' and table_type='BASE TABLE'")
    todas = {r[0] for r in cur.fetchall()}
    modeladas = {t for t,_,_ in ENT.values()}
    declaradas = {"customer_demographics","customer_customer_demo","us_states"}
    ok(todas == modeladas | declaradas,
       f"{len(todas)} tabelas = {len(modeladas)} modeladas + {len(declaradas)} declaradas fora"
       f"  | não classificadas: {sorted(todas - modeladas - declaradas)}")

print("\n" + ("=" * 60))
print(f"RESULTADO: {len(falhas)} falha(s)" if falhas else "RESULTADO: todas as verificações passaram")
for f in falhas:
    print("  -", f)

EVID.parent.mkdir(parents=True, exist_ok=True)
EVID.write_text(
    "# Validação do ER conceitual contra o banco\n"
    "# Gerado por: uv run python etl/valida_conceitual.py\n"
    "# Fonte: postgresql://pi:***@localhost:5432/northwind · schema public\n\n"
    + BUF.getvalue(), encoding="utf-8")
sys.exit(1 if falhas else 0)
