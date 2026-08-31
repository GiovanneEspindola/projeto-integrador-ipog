"""Confere o ER lógico contra o banco: o DBML de docs/diagramas/nw-schema.dbml
descreve exatamente as tabelas, colunas, tipos e chaves estrangeiras do schema nw?

O DBML é gerado por db2dbml e é a fonte do PNG exportado do dbdiagram.io. Se ele
divergir do banco, o diagrama entregue está mentindo — e é isso que este script
impede.

Sai com código 1 se qualquer verificação falhar, para poder rodar em automação.
"""
import builtins
import io, os, pathlib, re, sys
import psycopg

DSN = os.environ.get("PG_DSN", "postgresql://pi:pi@localhost:5432/northwind")
ROOT = pathlib.Path(__file__).resolve().parent.parent
DBML = ROOT / "docs" / "diagramas" / "nw-schema.dbml"
EVID = ROOT / "apresentacao" / "evidencias" / "05-validacao-er-logico.txt"
BUF = io.StringIO()

def print(*a, **k):
    builtins.print(*a, **k)
    builtins.print(*a, **{**k, "file": BUF})

falhas = []
def ok(cond, msg):
    print(("  OK   " if cond else "  FALHA ") + msg)
    if not cond: falhas.append(msg)

# --- lado do diagrama: o que o DBML declara ---------------------------------
texto = DBML.read_text(encoding="utf-8")
dbml = {}
for nome, corpo in re.findall(r'Table "nw"\."(\w+)" \{(.*?)\n\}', texto, re.S):
    cols = []
    for linha in corpo.splitlines():
        if linha.strip().startswith(("Note:", "Indexes", "(", "}")):
            continue
        m = re.match(r'\s*"(\w+)" ([\w()\[\], ]+?)(?: \[|$)', linha)
        if m:
            cols.append((m.group(1), m.group(2).strip()))
    dbml[nome] = cols
# Comparar so o NOME da FK deixaria passar um Ref com o nome certo apontando
# para a coluna errada. Por isso extrai-se tambem origem e destino.
refs_dbml = {
    m[0]: (m[1], m[2], m[3], m[4])
    for m in re.findall(
        r'Ref "(\w+)":"nw"\."(\w+)"\."(\w+)" \S+ "nw"\."(\w+)"\."(\w+)"', texto)
}

# --- lado do banco ----------------------------------------------------------
# os nomes de tipo do DBML sao os apelidos internos do PostgreSQL (int4, int2,
# bool), nao os nomes do padrao SQL que o information_schema devolve
APELIDO = {"integer": "int4", "smallint": "int2", "boolean": "bool"}

with psycopg.connect(DSN) as cx, cx.cursor() as cur:
    cur.execute("""
        SELECT c.table_name, c.column_name, c.data_type,
               c.character_maximum_length, c.numeric_precision, c.numeric_scale
          FROM information_schema.columns c
          JOIN information_schema.tables t
            ON t.table_schema = c.table_schema AND t.table_name = c.table_name
         WHERE c.table_schema = 'nw' AND t.table_type = 'BASE TABLE'
         ORDER BY c.table_name, c.ordinal_position""")
    banco = {}
    for tab, col, tipo, tam, prec, esc in cur.fetchall():
        if tipo == "character varying": t = f"varchar({tam})"
        elif tipo == "numeric":         t = f"numeric({prec},{esc})"
        else:                           t = APELIDO.get(tipo, tipo)
        banco.setdefault(tab, []).append((col, t))

    # o DBML escreve o Ref no sentido pai -> filho, entao a tupla e
    # (tabela_pai, coluna_pai, tabela_filho, coluna_filho)
    cur.execute("""
        SELECT c.conname, pai.relname, ap.attname, filho.relname, af.attname
          FROM pg_constraint c
          JOIN pg_class     filho ON filho.oid = c.conrelid
          JOIN pg_class     pai   ON pai.oid   = c.confrelid
          JOIN pg_namespace n     ON n.oid     = filho.relnamespace
          JOIN unnest(c.conkey)  WITH ORDINALITY AS k(att, ord) ON true
          JOIN unnest(c.confkey) WITH ORDINALITY AS fk(att, ord) ON fk.ord = k.ord
          JOIN pg_attribute af ON af.attrelid = filho.oid AND af.attnum = k.att
          JOIN pg_attribute ap ON ap.attrelid = pai.oid   AND ap.attnum = fk.att
         WHERE n.nspname = 'nw' AND c.contype = 'f'
         ORDER BY 1""")
    refs_banco = {r[0]: (r[1], r[2], r[3], r[4]) for r in cur.fetchall()}

print("== 1. Conjunto de tabelas ==")
ok(set(dbml) == set(banco),
   f"DBML tem {len(dbml)} tabelas, banco tem {len(banco)}"
   + (f"  DIFERENCA: {sorted(set(dbml) ^ set(banco))}" if set(dbml) != set(banco) else ""))

print("\n== 2. Colunas e tipos, tabela a tabela ==")
total = 0
for tab in sorted(banco):
    igual = dbml.get(tab) == banco[tab]
    ok(igual, f"{tab}: {len(banco[tab])} colunas"
       + ("" if igual else f"\n         DBML : {dbml.get(tab)}\n         banco: {banco[tab]}"))
    if igual: total += len(banco[tab])
print(f"  -> {total} colunas com nome, ordem e tipo idênticos")

print("\n== 3. Chaves estrangeiras ==")
ok(set(refs_dbml) == set(refs_banco),
   f"DBML declara {len(refs_dbml)} FKs, banco tem {len(refs_banco)}"
   + ("" if set(refs_dbml) == set(refs_banco) else
      f"\n         só no DBML : {sorted(set(refs_dbml) - set(refs_banco))}"
      f"\n         só no banco: {sorted(set(refs_banco) - set(refs_dbml))}"))

for nome in sorted(set(refs_dbml) & set(refs_banco)):
    d, b = refs_dbml[nome], refs_banco[nome]
    ok(d == b, f"{nome}: {b[0]}.{b[1]} <- {b[2]}.{b[3]}"
       + ("" if d == b else f"   DBML aponta para {d[0]}.{d[1]} <- {d[2]}.{d[3]}"))

print("\n" + "=" * 60)
print(f"RESULTADO: {len(falhas)} falha(s)" if falhas else "RESULTADO: o ER lógico corresponde ao schema nw")
for f in falhas:
    print("  -", f)

EVID.parent.mkdir(parents=True, exist_ok=True)
EVID.write_text(
    "# Validação do ER lógico contra o banco\n"
    "# Gerado por: uv run python etl/valida_dbml.py\n"
    "# Fonte: docs/diagramas/nw-schema.dbml  vs  postgresql://pi:***@localhost:5432/northwind (schema nw)\n\n"
    + BUF.getvalue(), encoding="utf-8")
sys.exit(1 if falhas else 0)
