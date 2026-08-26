#!/usr/bin/env python3
"""Perfilamento completo do Northwind carregado no schema `public`.

O que faz, em uma frase: mede a base original — tamanho, tipos, chaves, nulos,
cardinalidade e faixas de data — e grava tudo como evidência bruta.

Por que existe: nenhum número do relatório pode ser estimado. Todo dado que
aparece em `docs/01-analise-negocio.md` sai daqui, de uma consulta executada
contra o banco de verdade. Este arquivo é o que permite a qualquer pessoa
(inclusive a banca) reproduzir cada número do relatório.

Uso:
    uv run python etl/perfilamento.py

Gera os arquivos 01-perfil-*.txt em apresentacao/evidencias/.
"""

from __future__ import annotations

import os
import pathlib
import sys

import psycopg
from psycopg import sql
from tabulate import tabulate

DSN = os.environ.get("PG_DSN", "postgresql://pi:pi@localhost:5432/northwind")
EVID = pathlib.Path(__file__).resolve().parent.parent / "apresentacao" / "evidencias"


def escreve(nome: str, titulo: str, blocos: list[tuple[str, str]]) -> None:
    """Grava um arquivo de evidência: título, e para cada bloco o comando e a saída."""
    destino = EVID / nome
    with destino.open("w", encoding="utf-8") as f:
        f.write(f"# {titulo}\n")
        f.write(f"# Gerado por: uv run python etl/perfilamento.py\n")
        f.write(f"# Fonte: {DSN.replace(':pi@', ':***@')} · schema public\n\n")
        for comando, saida in blocos:
            f.write("-" * 78 + "\n")
            f.write(f"$ {comando}\n")
            f.write("-" * 78 + "\n")
            f.write(saida.rstrip() + "\n\n")
    print(f"  -> {destino.relative_to(pathlib.Path.cwd())}")


def tab(cur, query: str, params=None) -> str:
    cur.execute(query, params)
    cols = [d.name for d in cur.description]
    return tabulate(cur.fetchall(), headers=cols, tablefmt="github")


def main() -> int:
    with psycopg.connect(DSN) as conn:
        cur = conn.cursor()

        # ------------------------------------------------------------------
        # 1. Inventário: tabelas, contagem EXATA de linhas e tamanho em disco
        # ------------------------------------------------------------------
        cur.execute("""
            SELECT c.relname
            FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public' AND c.relkind = 'r'
            ORDER BY 1
        """)
        tabelas = [r[0] for r in cur.fetchall()]

        linhas = []
        for t in tabelas:
            cur.execute(sql.SQL("SELECT count(*) FROM public.{}").format(sql.Identifier(t)))
            n = cur.fetchone()[0]
            cur.execute("""
                SELECT count(*) FROM information_schema.columns
                WHERE table_schema='public' AND table_name=%s
            """, (t,))
            ncol = cur.fetchone()[0]
            cur.execute("SELECT pg_size_pretty(pg_total_relation_size(%s))", (f"public.{t}",))
            tam = cur.fetchone()[0]
            linhas.append([t, n, ncol, tam])

        total = sum(r[1] for r in linhas)
        inventario = tabulate(
            linhas + [["**TOTAL**", total, "", ""]],
            headers=["tabela", "linhas", "colunas", "tamanho em disco"],
            tablefmt="github",
        )
        escreve(
            "01-perfil-01-inventario.txt",
            "Perfilamento 1/6 — Inventário de tabelas (contagem EXATA, sem estimativa)",
            [("SELECT count(*) FROM public.<cada tabela>;  -- 14 execuções", inventario)],
        )

        # ------------------------------------------------------------------
        # 2. Colunas e tipos
        # ------------------------------------------------------------------
        q_col = """
            SELECT table_name  AS tabela,
                   ordinal_position AS pos,
                   column_name AS coluna,
                   CASE
                     WHEN data_type IN ('character varying','character')
                       THEN data_type || '(' || coalesce(character_maximum_length::text,'') || ')'
                     WHEN data_type = 'numeric' AND numeric_precision IS NOT NULL
                       THEN 'numeric(' || numeric_precision || ',' || numeric_scale || ')'
                     ELSE data_type
                   END AS tipo,
                   is_nullable AS aceita_nulo,
                   coalesce(column_default,'') AS padrao
            FROM information_schema.columns
            WHERE table_schema = 'public'
            ORDER BY table_name, ordinal_position
        """
        escreve(
            "01-perfil-02-colunas-e-tipos.txt",
            "Perfilamento 2/6 — Colunas, tipos declarados e nulabilidade",
            [("SELECT ... FROM information_schema.columns WHERE table_schema='public'", tab(cur, q_col))],
        )

        # ------------------------------------------------------------------
        # 3. Chaves e constraints
        # ------------------------------------------------------------------
        q_con = """
            SELECT rel.relname AS tabela,
                   con.conname AS constraint,
                   CASE con.contype WHEN 'p' THEN 'PRIMARY KEY'
                                    WHEN 'f' THEN 'FOREIGN KEY'
                                    WHEN 'u' THEN 'UNIQUE'
                                    WHEN 'c' THEN 'CHECK'
                                    ELSE con.contype::text END AS tipo,
                   pg_get_constraintdef(con.oid) AS definicao
            FROM pg_constraint con
            JOIN pg_class rel ON rel.oid = con.conrelid
            JOIN pg_namespace n ON n.oid = rel.relnamespace
            WHERE n.nspname = 'public'
            ORDER BY rel.relname, con.contype DESC, con.conname
        """
        q_resumo_con = """
            SELECT CASE con.contype WHEN 'p' THEN 'PRIMARY KEY'
                                    WHEN 'f' THEN 'FOREIGN KEY'
                                    WHEN 'u' THEN 'UNIQUE'
                                    WHEN 'c' THEN 'CHECK'
                                    ELSE con.contype::text END AS tipo,
                   count(*) AS quantidade
            FROM pg_constraint con
            JOIN pg_class rel ON rel.oid = con.conrelid
            JOIN pg_namespace n ON n.oid = rel.relnamespace
            WHERE n.nspname = 'public'
            GROUP BY 1 ORDER BY 2 DESC
        """
        q_idx = """
            SELECT tablename AS tabela, indexname AS indice, indexdef AS definicao
            FROM pg_indexes WHERE schemaname='public' ORDER BY 1,2
        """
        q_sem_pk = """
            SELECT rel.relname AS tabela_sem_primary_key
            FROM pg_class rel JOIN pg_namespace n ON n.oid = rel.relnamespace
            WHERE n.nspname='public' AND rel.relkind='r'
              AND NOT EXISTS (SELECT 1 FROM pg_constraint c
                              WHERE c.conrelid=rel.oid AND c.contype='p')
            ORDER BY 1
        """
        escreve(
            "01-perfil-03-chaves-e-constraints.txt",
            "Perfilamento 3/6 — Chaves, constraints e índices existentes",
            [
                ("SELECT tipo, count(*) FROM pg_constraint ... GROUP BY tipo", tab(cur, q_resumo_con)),
                ("SELECT ... pg_get_constraintdef(con.oid) FROM pg_constraint ...", tab(cur, q_con)),
                ("SELECT ... FROM pg_indexes WHERE schemaname='public'", tab(cur, q_idx)),
                ("-- tabelas SEM PRIMARY KEY", tab(cur, q_sem_pk) or "(nenhuma)"),
            ],
        )

        # ------------------------------------------------------------------
        # 4. Nulos por coluna (contados de verdade, coluna a coluna)
        # ------------------------------------------------------------------
        cur.execute("""
            SELECT table_name, column_name
            FROM information_schema.columns
            WHERE table_schema='public'
            ORDER BY table_name, ordinal_position
        """)
        colunas = cur.fetchall()

        nulos = []
        for t, c in colunas:
            cur.execute(
                sql.SQL("SELECT count(*), count({col}) FROM public.{tab}").format(
                    col=sql.Identifier(c), tab=sql.Identifier(t)
                )
            )
            total_l, preenchidos = cur.fetchone()
            n_nulos = total_l - preenchidos
            pct = (n_nulos / total_l * 100) if total_l else 0.0
            nulos.append([t, c, total_l, n_nulos, f"{pct:.1f}%"])

        so_com_nulo = [r for r in nulos if r[3] > 0]
        escreve(
            "01-perfil-04-nulos-por-coluna.txt",
            "Perfilamento 4/6 — Nulos por coluna (count(*) - count(coluna), executado em todas as %d colunas)" % len(colunas),
            [
                (
                    "-- APENAS as colunas que têm pelo menos um nulo",
                    tabulate(so_com_nulo, headers=["tabela", "coluna", "linhas", "nulos", "% nulo"], tablefmt="github")
                    or "(nenhuma coluna com nulo)",
                ),
                (
                    "-- TODAS as %d colunas da base" % len(colunas),
                    tabulate(nulos, headers=["tabela", "coluna", "linhas", "nulos", "% nulo"], tablefmt="github"),
                ),
            ],
        )

        # ------------------------------------------------------------------
        # 5. Cardinalidade das colunas de junção (as que participam de FK)
        # ------------------------------------------------------------------
        cur.execute("""
            SELECT con.conname,
                   filho.relname   AS tabela_filho,
                   (SELECT string_agg(att.attname, ',' ORDER BY x.ord)
                      FROM unnest(con.conkey) WITH ORDINALITY AS x(attnum, ord)
                      JOIN pg_attribute att ON att.attrelid = con.conrelid AND att.attnum = x.attnum
                   ) AS colunas_filho,
                   pai.relname     AS tabela_pai,
                   (SELECT string_agg(att.attname, ',' ORDER BY x.ord)
                      FROM unnest(con.confkey) WITH ORDINALITY AS x(attnum, ord)
                      JOIN pg_attribute att ON att.attrelid = con.confrelid AND att.attnum = x.attnum
                   ) AS colunas_pai
            FROM pg_constraint con
            JOIN pg_class filho ON filho.oid = con.conrelid
            JOIN pg_class pai   ON pai.oid   = con.confrelid
            JOIN pg_namespace n ON n.oid = filho.relnamespace
            WHERE n.nspname='public' AND con.contype='f'
            ORDER BY filho.relname, con.conname
        """)
        fks = cur.fetchall()

        card, orfaos = [], []
        for conname, t_filho, c_filho, t_pai, c_pai in fks:
            cols_f = c_filho.split(",")
            cols_p = c_pai.split(",")
            expr_f = sql.SQL(", ").join(sql.Identifier(c) for c in cols_f)

            cur.execute(
                sql.SQL("SELECT count(*), count(DISTINCT ({f})) FROM public.{t}").format(
                    f=expr_f, t=sql.Identifier(t_filho)
                )
            )
            n_filho, d_filho = cur.fetchone()

            cur.execute(
                sql.SQL("SELECT count(*) FROM public.{t} WHERE {cond}").format(
                    t=sql.Identifier(t_filho),
                    cond=sql.SQL(" OR ").join(
                        sql.SQL("{} IS NULL").format(sql.Identifier(c)) for c in cols_f
                    ),
                )
            )
            n_nulo = cur.fetchone()[0]

            cur.execute(sql.SQL("SELECT count(*) FROM public.{t}").format(t=sql.Identifier(t_pai)))
            n_pai = cur.fetchone()[0]

            media = (n_filho - n_nulo) / d_filho if d_filho else 0
            cobertura = d_filho / n_pai * 100 if n_pai else 0
            card.append([
                f"{t_filho}.{c_filho}", f"-> {t_pai}.{c_pai}",
                n_filho, n_nulo, d_filho, n_pai,
                f"{media:.1f}", f"{cobertura:.0f}%",
            ])

            # órfãos: filho aponta para pai inexistente (não deveria haver, há FK)
            join_cond = sql.SQL(" AND ").join(
                sql.SQL("p.{} = f.{}").format(sql.Identifier(p), sql.Identifier(f))
                for p, f in zip(cols_p, cols_f)
            )
            null_cond = sql.SQL(" AND ").join(
                sql.SQL("f.{} IS NOT NULL").format(sql.Identifier(f)) for f in cols_f
            )
            cur.execute(
                sql.SQL("""SELECT count(*) FROM public.{tf} f
                           WHERE {nn} AND NOT EXISTS (
                             SELECT 1 FROM public.{tp} p WHERE {jc})""").format(
                    tf=sql.Identifier(t_filho), tp=sql.Identifier(t_pai),
                    nn=null_cond, jc=join_cond,
                )
            )
            orfaos.append([conname, f"{t_filho}.{c_filho} -> {t_pai}.{c_pai}", cur.fetchone()[0]])

        escreve(
            "01-perfil-05-cardinalidade-juncoes.txt",
            "Perfilamento 5/6 — Cardinalidade das colunas de junção e verificação de órfãos",
            [
                (
                    "-- para cada FK: linhas, nulos, valores distintos no filho, linhas no pai",
                    tabulate(
                        card,
                        headers=["coluna de junção", "aponta para", "linhas filho",
                                 "nulos", "distintos", "linhas pai",
                                 "média filhos/pai", "% do pai referenciado"],
                        tablefmt="github",
                    ),
                ),
                (
                    "-- anti-join: filhos apontando para pai inexistente (esperado: 0 em todas)",
                    tabulate(orfaos, headers=["constraint", "relação", "órfãos"], tablefmt="github"),
                ),
            ],
        )

        # ------------------------------------------------------------------
        # 6. Faixa de datas em toda coluna temporal
        # ------------------------------------------------------------------
        cur.execute("""
            SELECT table_name, column_name, data_type
            FROM information_schema.columns
            WHERE table_schema='public'
              AND data_type IN ('date','timestamp without time zone',
                                'timestamp with time zone','time without time zone')
            ORDER BY table_name, ordinal_position
        """)
        temporais = cur.fetchall()

        faixas = []
        for t, c, tipo in temporais:
            cur.execute(
                sql.SQL("""SELECT min({c}), max({c}), count({c}), count(*) - count({c}),
                                  count(DISTINCT {c})
                           FROM public.{t}""").format(c=sql.Identifier(c), t=sql.Identifier(t))
            )
            mn, mx, preenchidos, n_nulos, distintos = cur.fetchone()
            faixas.append([f"{t}.{c}", tipo, str(mn), str(mx), preenchidos, n_nulos, distintos])

        escreve(
            "01-perfil-06-faixas-de-data.txt",
            "Perfilamento 6/6 — Faixa de valores em toda coluna temporal",
            [(
                "SELECT min(col), max(col), count(col), nulos, count(DISTINCT col) -- por coluna temporal",
                tabulate(
                    faixas,
                    headers=["coluna", "tipo", "mínimo", "máximo", "preenchidos", "nulos", "distintos"],
                    tablefmt="github",
                ),
            )],
        )

    return 0


if __name__ == "__main__":
    print("Perfilando o schema public...")
    sys.exit(main())
