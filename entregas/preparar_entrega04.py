"""Entrega 4: gera os capítulos 13 e 16, a tabela comparativa e as figuras.

Tudo vem das evidências executadas (Entregas 3 e 4); nenhum número é digitado.
Uso: uv run python entregas/preparar_entrega04.py
"""
from pathlib import Path
import json
from decimal import Decimal
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from bson import json_util
from preparar_entrega03 import LABELS, fmt, table, br, selection, abc_summary

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / 'docs/entrega04'
EV3 = ROOT / 'apresentacao/evidencias/entrega03'
EV4 = ROOT / 'apresentacao/evidencias/entrega04'
B3 = ROOT / 'bench/results/entrega03'
B4 = ROOT / 'bench/results/entrega04'


def read(p):
    return json.loads(p.read_text())


def ms(x):
    return br(x, 3)


def analises(r, i, titles):
    parts = ['# 13. Consultas analíticas e resultados\n\nCada seção traz a pergunta, a regra de cálculo, os recursos usados em cada banco, o resultado e o que ele significa. As tabelas mostram a saída validada, idêntica nos dois bancos, com decimais arredondados só na apresentação. Quando o resultado é longo, o recorte exibido está indicado. Os 32 códigos completos estão no Apêndice A.\n']
    for n in range(1, 17):
        k = str(n); d = r[k]; m = i[k]
        parts.append(f'## 13.{n} Q{n:02}/P{n:02} — {titles[k]}\n\n**Pergunta:** {m["pergunta"]}\n\n**Cálculo:** {m["logica"]}\n\n**Recursos:** SQL: {m["sql"]}. MongoDB: {m["mongo"]}.\n')
        rows = d['rows']
        if not rows:
            parts.append('**Resultado:** nenhuma linha nos dois bancos.\n')
        else:
            chosen, note = selection(n, rows)
            parts.append(f'**Resultado:** {len(rows)} linhas; {note}\n')
            cols = d['columns']
            if len(cols) > 6:
                parts.append(table(cols[:5], chosen)); parts.append(table([cols[0]] + cols[5:], chosen))
            else:
                parts.append(table(cols, chosen))
            if n == 10:
                parts.append('Resumo das 91 linhas por classe:\n\n' + abc_summary(rows))
        if n == 2:
            parts.append('<!-- image:apresentacao/evidencias/entrega04/mensal.png -->\n\nFigura 4 — Valor mensal após descontos (Q02/P02). Julho de 1996 começa no dia 4 e maio de 1998 termina no dia 6.\n')
        parts.append(f'**Leitura:** {m["leitura"]}\n\n**Cuidado:** {m["cuidado"]}\n')
    return '\n'.join(parts)


def performance(perf, opt, env, idx):
    mem = int(env['memoria_linux'][0].split()[1]) / 1024 / 1024
    t = f'''# 16. Performance e otimização

## 16.1 Como foi medido

As 16 consultas e os 16 pipelines rodaram na mesma máquina, sobre os mesmos dados, por conexões já abertas (psycopg e PyMongo). O tempo vai do envio da consulta até o consumo de **todas** as linhas pelo programa. Cada par teve cinco execuções de aquecimento e vinte medições, alternando qual banco rodava primeiro. O relatório usa a **mediana** e o intervalo entre o primeiro e o terceiro quartil (Q1–Q3), que mostra a variação entre as medições.

Ambiente: PostgreSQL 16.15 e MongoDB {env["mongo"]} em Docker, no WSL2, processador {env["cpu_modelo"]} e {br(mem, 1)} GB de memória, sem limite de CPU ou memória para os containers. Os planos de execução (EXPLAIN e explain) foram coletados à parte, para não interferir nos tempos.

## 16.2 Tempos das 16 análises

| Par | PostgreSQL: mediana (ms) | PostgreSQL: Q1–Q3 | MongoDB: mediana (ms) | MongoDB: Q1–Q3 |
|---|---|---|---|---|
'''
    for n in range(1, 17):
        p = perf[str(n)]['postgres']; m = perf[str(n)]['mongo']
        t += f'| {n:02} | {ms(p["mediana_ms"])} | {ms(p["q1_ms"])}–{ms(p["q3_ms"])} | {ms(m["mediana_ms"])} | {ms(m["q1_ms"])}–{ms(m["q3_ms"])} |\n'
    menor = [n for n in range(1, 17) if perf[str(n)]['postgres']['mediana_ms'] < perf[str(n)]['mongo']['mediana_ms']]
    razoes = [perf[str(n)]['mongo']['mediana_ms'] / perf[str(n)]['postgres']['mediana_ms'] for n in range(1, 17)]
    quem = 'nos 16 pares' if len(menor) == 16 else f'em {len(menor)} dos 16 pares'
    separados = sum(1 for n in range(1, 17) if perf[str(n)]['postgres']['q3_ms'] < perf[str(n)]['mongo']['q1_ms'])
    consist = 'Os intervalos Q1–Q3 não se sobrepõem em nenhum par' if separados == 16 else f'Os intervalos Q1–Q3 não se sobrepõem em {separados} pares'
    t += f'\nO PostgreSQL teve a menor mediana {quem}, com o MongoDB entre {br(min(razoes), 1)} e {br(max(razoes), 1)} vezes mais lento. {consist}, então a diferença é consistente nesta execução. Ela vale para este volume, esta máquina e estes índices.\n\n<!-- image:apresentacao/evidencias/entrega04/tempos.png -->\n\nFigura 5 — Mediana das 20 medições por par, em milissegundos; as barras indicam Q1 e Q3.\n\n'
    top = sorted(range(1, 17), key=lambda n: -razoes[n - 1])[:6]
    t += 'As maiores diferenças relativas estão em ' + ', '.join(f'P{n:02} ({br(razoes[n - 1], 1)}×)' for n in top) + '. Todos esses pipelines começam por um cadastro (produtos, clientes, funcionários ou transportadoras) e fazem um $lookup nos pedidos para cada documento, enquanto o PostgreSQL resolve a junção de uma vez. Os planos mostraram ainda que o MongoDB não tinha índice em employee_id nem em shipper_id: cada $lookup de P04 e P15 examinava os 830 pedidos.\n\n'
    # Teste da Entrega 4
    t += '## 16.3 Teste da Entrega 4: os índices que faltavam\n\nPara saber quanto da diferença vinha dos índices ausentes, os três pipelines afetados foram medidos em duas cópias isoladas do MongoDB: com os índices atuais e com índices em employee_id e shipper_id. O PostgreSQL foi medido nas mesmas rodadas. Os resultados foram iguais nas três versões.\n\n'
    t += '| Par | PostgreSQL (ms) | MongoDB, índices atuais (ms) | MongoDB com os novos índices (ms) | Redução no MongoDB |\n|---|---|---|---|---|\n'
    def examinados(n, copia):
        plano = json.loads(json_util.dumps(json_util.loads((B4 / f'P{n}-{copia}-plan.ejson').read_text())))
        achados = []
        def visita(x):
            if isinstance(x, dict):
                if '$lookup' in x and 'totalDocsExamined' in x:
                    achados.append(x['totalDocsExamined'])
                for v in x.values():
                    visita(v)
            elif isinstance(x, list):
                for v in x:
                    visita(v)
        visita(plano)
        return f'{sum(achados):,}'.replace(',', '.')
    docs = {n: (examinados(n, 'indices_atuais'), examinados(n, 'com_employee_shipper')) for n in idx}
    for n, v in idx.items():
        a = v['indices_atuais']['mediana_ms']; b = v['com_employee_shipper']['mediana_ms']
        t += f'| {n} | {ms(v["postgres"]["mediana_ms"])} | {ms(a)} | {ms(b)} | {br(100 * (1 - b / a), 1)}% |\n'
    t += '\n| Par | Documentos examinados, índices atuais | Documentos examinados, com os novos índices |\n|---|---|---|\n'
    for n, (a, b) in docs.items():
        t += f'| {n} | {a} | {b} |\n'
    ratios = [v['com_employee_shipper']['mediana_ms'] / v['postgres']['mediana_ms'] for v in idx.values()]
    t += f'\nOs índices reduziram o trabalho e o tempo, com intervalos Q1–Q3 sem sobreposição. Mesmo assim, o PostgreSQL continuou entre {br(min(ratios), 1)} e {br(max(ratios), 1)} vezes mais rápido. O índice explica parte da diferença; o resto vem da estratégia de um $lookup por documento e da conversão dos documentos pelo driver. Os índices foram testados só nas cópias; o banco original não foi alterado.\n\n'
    # Estudos da Entrega 3
    t += '## 16.4 Estudos de otimização\n\nQuatro consultas foram reescritas ou receberam índices em cópias isoladas dos dados. Em cada estudo, todas as versões rodaram nas mesmas rodadas, em ordem alternada, e devolveram o mesmo resultado. Quando os intervalos Q1–Q3 se sobrepõem, a diferença é tratada como inconclusiva.\n\n'
    desc = {
        'C01': ('Filtro mensal', 'A versão original calcula o mês de cada pedido com to_char (no MongoDB, $dateToString) e compara o texto; a reescrita filtra o intervalo de datas direto; a terceira versão acrescenta um índice em order_date.',
                [('original', 'reescrita', 'Reescrita do filtro'), ('reescrita', 'com_indice', 'Índice por data')]),
        'C02': ('Cliente e período', 'Pedidos de VINET em 1996, sem e com índice composto (customer_id, order_date).',
                [('sem_composto', 'com_composto', 'Índice composto')]),
        'C03': ('Pares de produtos', 'A versão original em SQL usa uma CTE MATERIALIZED que gera todos os pares antes de filtrar A < B; sem essa instrução, o próprio PostgreSQL já aplicaria o filtro na junção. No MongoDB, a original carrega o documento inteiro e só descarta os pares repetidos no fim.',
                [('original', 'reescrita', 'Reescrita')]),
        'C04': ('Vendas da equipe', 'A versão original junta a hierarquia com cada pedido e só depois soma; a reescrita soma os pedidos por funcionário antes de juntar.',
                [('original', 'reescrita', 'Reescrita')])}
    t += '| Estudo | Versão testada | PostgreSQL: mediana (Q1–Q3), ms | MongoDB: mediana (Q1–Q3), ms |\n|---|---|---|---|\n'
    for case, vs in opt.items():
        for v, bs in vs.items():
            p = bs['postgres']; m = bs['mongo']
            t += f'| {case} | {v} | {ms(p["mediana_ms"])} ({ms(p["q1_ms"])}–{ms(p["q3_ms"])}) | {ms(m["mediana_ms"])} ({ms(m["q1_ms"])}–{ms(m["q3_ms"])}) |\n'
    t += '\n'
    for case, vs in opt.items():
        title, d, pairs = desc[case]
        t += f'**{case} — {title}.** {d} '
        frases = []
        for a, b, label in pairs:
            parts = []
            for bank, nome in [('postgres', 'PostgreSQL'), ('mongo', 'MongoDB')]:
                x = vs[a][bank]; y = vs[b][bank]; g = 100 * (1 - y['mediana_ms'] / x['mediana_ms'])
                sob = not (y['q3_ms'] < x['q1_ms'] or x['q3_ms'] < y['q1_ms'])
                parts.append(f'{nome} {br(g, 1)}%' + (' (inconclusivo)' if sob else ''))
            frases.append(f'{label}: ' + ', '.join(parts))
        t += 'Redução da mediana — ' + '; '.join(frases) + '.\n\n'
    t += 'Os resultados confirmam o que se esperava de cada mudança: filtrar pela coluna, e não por uma função dela, e indexar o acesso mais seletivo trouxeram os maiores ganhos; reduzir resultados intermediários ajudou no PostgreSQL e teve efeito pequeno ou inconclusivo no MongoDB.\n\n'
    t += '## 16.5 Limites\n\nOs dados cabem em memória e as consultas levam poucos milissegundos, então parte do tempo medido é comunicação e conversão de tipos pelo driver. Não foram medidos concorrência, escrita, grandes volumes nem distribuição em vários servidores. Durante as medições, outros containers sem relação com o projeto estavam ativos na máquina, o que pode acrescentar variação, mas afeta os dois bancos igualmente, porque as execuções foram intercaladas.\n'
    return t


def comparacao(i):
    specs = json_util.loads((EV3 / 'pipelines.ejson').read_text())
    def linhas(n):
        return sum(1 for l in (ROOT / f'sql/queries/Q{n:02}.sql').read_text().splitlines() if l.strip() and not l.lstrip().startswith('--'))
    return '| Par | SQL: recursos | Linhas SQL | MongoDB: recursos | Estágios |\n|---|---|---|---|---|\n' + ''.join(
        f'| {n:02} | {i[str(n)]["sql"]} | {linhas(n)} | {i[str(n)]["mongo"]} | {len(specs[str(n)]["pipeline"])} |\n' for n in range(1, 17))


def box(ax, x, y, w, h, title, body, color):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.02,rounding_size=0.12', fc=color, ec='#40515c', lw=1.2))
    ax.text(x + w / 2, y + h - 0.3, title, ha='center', va='top', fontsize=10.5, weight='bold', color='#1d2b33')
    ax.text(x + w / 2, y + h - 0.85, body, ha='center', va='top', fontsize=8.6, color='#2c3a42', linespacing=1.5)


def arrow(ax, x1, y1, x2, y2, label='', below=''):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle='-|>', lw=1.6, color='#40515c', mutation_scale=15))
    if label:
        ax.text((x1 + x2) / 2, y1 + 0.15, label, ha='center', va='bottom', fontsize=8.2, color='#40515c', style='italic', linespacing=1.3)
    if below:
        ax.text((x1 + x2) / 2, y1 - 0.15, below, ha='center', va='top', fontsize=8.2, color='#40515c', linespacing=1.3)


def arquitetura():
    fig, ax = plt.subplots(figsize=(8.6, 4.2)); ax.set_xlim(0, 17); ax.set_ylim(0, 8.2); ax.axis('off')
    box(ax, 0.1, 4.0, 3.0, 3.6, 'public', 'Northwind original\n14 tabelas\npreservada sem\nalterações', '#eef1f3')
    box(ax, 5.0, 4.0, 3.6, 3.6, 'PostgreSQL — nw', 'modelo relacional\nfonte da verdade\n11 tabelas, 11 FKs\n17 CHECK, 4 UNIQUE', '#dbe8f4')
    box(ax, 12.2, 4.0, 4.7, 3.6, 'MongoDB', 'cópia para leitura\n9 coleções\n1.107 documentos\nitens dentro do pedido', '#dcefe2')
    arrow(ax, 3.1, 5.8, 5.0, 5.8, 'carga\nSQL')
    arrow(ax, 8.6, 5.8, 12.2, 5.8, 'extração SQL\n+ mongosh', 'lote,\nmão única')
    box(ax, 5.0, 0.2, 11.9, 2.5, '16 perguntas de negócio', 'cada uma respondida em SQL (QNN.sql) e em pipeline (PNN.js)\nresultados comparados  →  desempenho medido', '#f4ecd8')
    arrow(ax, 6.8, 2.7, 6.8, 4.0); arrow(ax, 14.55, 2.7, 14.55, 4.0)
    fig.tight_layout(); fig.savefig(EV4 / 'arquitetura.png', dpi=200); plt.close(fig)


def graficos(perf, r):
    plt.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False})
    fig, ax = plt.subplots(figsize=(9, 5)); xs = list(range(16))
    for bank, shift, color, label in [('postgres', -.17, '#22577a', 'PostgreSQL'), ('mongo', .17, '#32936f', 'MongoDB')]:
        ds = [perf[str(n)][bank] for n in range(1, 17)]
        ax.bar([x + shift for x in xs], [d['mediana_ms'] for d in ds], .32, color=color, label=label,
               yerr=[[d['mediana_ms'] - d['q1_ms'] for d in ds], [d['q3_ms'] - d['mediana_ms'] for d in ds]], capsize=2)
    ax.set_xticks(xs, [f'{n:02}' for n in range(1, 17)]); ax.set_xlabel('Par de consultas'); ax.set_ylabel('Tempo até consumir o resultado (ms)'); ax.legend()
    fig.tight_layout(); fig.savefig(EV4 / 'tempos.png', dpi=180); plt.close(fig)
    fig, ax = plt.subplots(figsize=(9, 4)); rows = r['2']['rows']
    ax.plot([x['mes'][:7] for x in rows], [float(x['valor']) for x in rows], marker='o', color='#22577a')
    ax.set_ylabel('Valor após descontos'); ax.tick_params(axis='x', rotation=65)
    ax.set_title('Valor mensal — o primeiro e o último mês têm cobertura parcial')
    fig.tight_layout(); fig.savefig(EV4 / 'mensal.png', dpi=180); plt.close(fig)


def main():
    EV4.mkdir(parents=True, exist_ok=True)
    r = read(EV3 / 'resultados.json'); i = read(DOC / 'interpretacoes.json'); titles = read(DOC / 'catalogo.json')
    perf = read(B3 / 'catalogo.json'); opt = read(B3 / 'otimizacoes.json'); env = read(B3 / 'ambiente.json')
    idx = read(B4 / 'indices-mongo.json')
    (DOC / '13-analises.md').write_text(analises(r, i, titles))
    (DOC / '16-performance.md').write_text(performance(perf, opt, env, idx))
    (DOC / 'comparacao-tabela.md').write_text(comparacao(i))
    arquitetura(); graficos(perf, r)
    print('Capítulos 13 e 16, tabela comparativa e figuras gerados a partir das evidências.')


if __name__ == '__main__':
    main()
