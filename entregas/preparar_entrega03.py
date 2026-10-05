"""Gera capítulos/tabelas/gráficos a partir de evidências executadas."""
from pathlib import Path
import json
from decimal import Decimal,ROUND_HALF_UP
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/'docs/entrega03';EV=ROOT/'apresentacao/evidencias/entrega03';B=ROOT/'bench/results/entrega03'

# Cabeçalhos legíveis para as colunas retornadas pelas consultas (alias SQL = campo MongoDB).
LABELS={'category_id':'categoria (ID)','categoria':'categoria','unidades':'unidades','valor':'valor',
 'participacao':'participação (%)','mes':'mês','pedidos':'pedidos','ticket':'ticket',
 'employee_id':'funcionário (ID)','funcionario':'funcionário','produtos':'produtos','deficit':'déficit',
 'reposicao_insuficiente':'cobertura insuficiente','produtos_ids':'produtos (IDs)',
 'customer_id':'cliente (código)','cliente':'cliente','ultima':'última compra','recencia':'recência (dias)',
 'situacao':'situação','product_id':'produto (ID)','posicao':'posição','acumulado':'acumulado',
 'anterior':'mês anterior','variacao':'variação','percentual':'variação (%)','classe':'classe',
 'frequencia':'frequência','r':'R','f':'F','m':'M','produto_a':'produto A','produto_b':'produto B',
 'denominador':'pedidos no período','suporte':'suporte (%)','shipper_id':'transportadora (ID)',
 'transportadora':'transportadora','com_envio':'com data de envio','sem_data':'sem data de envio',
 'soma_dias':'soma de dias','media_dias':'média (dias)','apos_requerida':'após data requerida',
 'bruto':'valor bruto','desconto':'desconto','percentual_desconto':'desconto (%)','gestor_id':'gestor (ID)',
 'membros':'membros','valor_proprio':'valor próprio','pedidos_equipe':'pedidos da equipe',
 'valor_equipe':'valor da equipe','ano':'ano','trimestre':'trimestre','nivel':'nível','parcial':'parcial'}

def read(p):return json.loads(p.read_text())
def br(x,casas=2):
 return f'{Decimal(str(x)).quantize(Decimal(1).scaleb(-casas),rounding=ROUND_HALF_UP):,.{casas}f}'.replace(',','@').replace('.',',').replace('@','.')
def fmt(x):
 if x is None:return '—'
 if isinstance(x,bool):return 'sim' if x else 'não'
 if isinstance(x,list):return ', '.join(map(str,x))
 if isinstance(x,int):return str(x)
 try:
  d=Decimal(x)
  if d==d.to_integral_value() and not '.' in str(x):return str(x)
  return br(d)
 except (ValueError,TypeError,ArithmeticError):return str(x)
def table(cols,rows):
 return '| '+' | '.join(LABELS.get(c,c) for c in cols)+' |\n| '+' | '.join('---' for _ in cols)+' |\n'+''.join('| '+' | '.join(fmt(row.get(c)) for c in cols)+' |\n' for row in rows)
def ms(x):return br(x,3)

def selection(n,rows):
 """Linhas exibidas no corpo do relatório e a frase que descreve o recorte."""
 if n in (2,8,9):return rows,'todas exibidas.'
 if n==7:return [x for x in rows if x['posicao']==1],'exibido o primeiro colocado de cada categoria.'
 if n==16:return [x for x in rows if x['nivel']=='total'],'exibidos os oito totais trimestrais.'
 if len(rows)<=9:return rows,'todas exibidas.'
 return rows[:5],'exibidas as cinco primeiras na ordenação definida.'

def abc_summary(rows):
 total=sum(Decimal(x['valor']) for x in rows);out=[]
 for c in ['A','B','C','sem compras']:
  g=[x for x in rows if x['classe']==c];v=sum((Decimal(x['valor']) for x in g),Decimal(0))
  out.append({'classe':c,'clientes':len(g),'valor':str(v),'participacao':str(100*v/total)})
 return '| classe | clientes | valor | participação (%) |\n|---|---|---|---|\n'+''.join(
  f'| {x["classe"]} | {x["clientes"]} | {br(x["valor"])} | {br(x["participacao"])} |\n' for x in out)

def main():
 r=read(EV/'resultados.json');i=read(DOC/'interpretacoes.json'); titles=read(DOC/'catalogo.json')
 parts=['# 14. Consultas analíticas e resultados\n\nCada seção apresenta a pergunta, a regra de cálculo, os recursos usados em cada banco, o resultado executado e sua interpretação. As tabelas reproduzem a saída validada, idêntica nos dois bancos; os cabeçalhos traduzem os nomes das colunas e os decimais são arredondados para duas casas somente na apresentação. Quando o resultado é extenso, o recorte exibido está indicado; a validação considerou todas as linhas. Os 32 códigos completos estão no Apêndice A.\n']
 for n in range(1,17):
  k=str(n);d=r[k];m=i[k]
  parts.append(f'## 14.{n} Q{n:02}/P{n:02} — {titles[k]}\n\n**Pergunta:** {m["pergunta"]}\n\n**Cálculo:** {m["logica"]}\n\n**Implementação:** SQL: {m["sql"]}. MongoDB: {m["mongo"]}.\n')
  rows=d['rows'];count=len(rows)
  if not rows:parts.append('**Resultado:** zero linhas nos dois bancos.\n')
  else:
   chosen,note=selection(n,rows)
   parts.append(f'**Resultado:** {count} linhas conferidas; {note}\n')
   cols=d['columns']
   if len(cols)>6:
    # Repete a chave ao dividir a largura, preservando todos os indicadores.
    parts.append(table(cols[:5],chosen));parts.append(table([cols[0]]+cols[5:],chosen))
   else:parts.append(table(cols,chosen))
   if n==10:parts.append('Resumo das 91 linhas por classe, calculado a partir da mesma saída validada:\n\n'+abc_summary(rows))
  if n==2:parts.append('<!-- image:apresentacao/evidencias/entrega03/mensal.png -->\n\nFigura 3 — Valor mensal após descontos (Q02/P02). Julho de 1996 começa no dia 4 e maio de 1998 termina no dia 6.\n')
  parts.append(f'**Interpretação:** {m["leitura"]}\n\n**Limite de leitura:** {m["cuidado"]}\n')
 (DOC/'14-analises.md').write_text('\n'.join(parts))

 perf=read(B/'catalogo.json');opt=read(B/'otimizacoes.json');env=read(B/'ambiente.json')
 mem=int(env['memoria_linux'][0].split()[1])/1024/1024
 text='''# 17. Análise de performance e otimização

## 17.1 Método e ambiente

Os 16 pares foram medidos na mesma máquina, sobre os dados validados, com conexões persistentes dos drivers psycopg (PostgreSQL) e PyMongo (MongoDB). Cada medição inclui o envio da consulta, a execução, a transferência e o consumo de **todas** as linhas ou documentos pelo cliente. Abertura de conexão, inicialização de processos, impressão e gravação de arquivos ficaram fora do trecho cronometrado.

O cenário é de **cache aquecido**: cinco execuções de aquecimento e vinte medições por banco e consulta. A ordem entre PostgreSQL e MongoDB alterna a cada rodada. A mediana resume o valor central, e o intervalo entre o primeiro e o terceiro quartil (Q1–Q3) indica a dispersão. Não foram feitos teste de significância estatística nem teste de carga concorrente.

'''
 text+=f'O ambiente executou PostgreSQL 16.15 e MongoDB {env["mongo"]} em containers Docker, no WSL2, com processador {env["cpu_modelo"]} ({env["cpus_logicas"]} processadores lógicos visíveis) e {br(mem,1)} GB de memória visível no Linux. Os containers não tinham limite de CPU ou memória e compartilharam os recursos da máquina. '
 def setting(x):
  # Converte páginas de 8 kB e kB para uma unidade legível.
  if x['unit'] in ('8kB','kB'):
   kb=int(x['setting'])*(8 if x['unit']=='8kB' else 1)
   return f'{kb//1024//1024} GB' if kb>=1024*1024 else f'{kb//1024} MB'
  return x['setting']
 text+='Configuração relevante do PostgreSQL: '+', '.join(f"{x['name']} = {setting(x)}" for x in env['config_pg'])+'.\n\n'
 text+='Os planos de execução foram coletados à parte, com EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) e explain("executionStats") [15, 16], para não interferir nos tempos. Custos estimados e tempos internos de um servidor não são comparáveis diretamente com os do outro; a comparação de tempo usa apenas o cronômetro externo comum.\n\n## 17.2 Tempos do catálogo\n\n'
 text+='| Par | PostgreSQL: mediana (ms) | PostgreSQL: Q1–Q3 (ms) | MongoDB: mediana (ms) | MongoDB: Q1–Q3 (ms) |\n|---|---|---|---|---|\n'
 for n in range(1,17):
  p=perf[str(n)]['postgres'];m=perf[str(n)]['mongo']
  text+=f'| {n:02} | {ms(p["mediana_ms"])} | {ms(p["q1_ms"])}–{ms(p["q3_ms"])} | {ms(m["mediana_ms"])} | {ms(m["q1_ms"])}–{ms(m["q3_ms"])} |\n'
 pg_menor=[n for n in range(1,17) if perf[str(n)]['postgres']['mediana_ms']<perf[str(n)]['mongo']['mediana_ms']]
 sep=[n for n in pg_menor if perf[str(n)]['postgres']['q3_ms']<perf[str(n)]['mongo']['q1_ms']]
 quem=('O PostgreSQL apresentou menor mediana nos 16 pares' if len(pg_menor)==16 else f'O PostgreSQL apresentou menor mediana em {len(pg_menor)} dos 16 pares')
 sobre=('em todos eles' if len(sep)==len(pg_menor) else f'em {len(sep)} deles')
 text+=f'\n{quem} nesta execução; {sobre}, os intervalos Q1–Q3 dos dois bancos não se sobrepõem. O resultado vale para estes códigos, drivers, volume, ambiente e índices. Não demonstra superioridade geral nem indica o comportamento com milhões de pedidos.\n\n'
 text+='Dois fatores de configuração ajudam a interpretar a diferença. Primeiro, os índices não são simétricos: o PostgreSQL tem índices em orders(customer_id), orders(employee_id), orders(order_date) e order_items(product_id), enquanto o MongoDB tem cliente_data, produto_no_pedido e categoria_produto. Sem índice em employee_id e shipper_id, cada $lookup de P04 e P15 examinou os 830 pedidos para cada um dos 9 funcionários (7.470 documentos), e P13 examinou 4.980 documentos para as 6 transportadoras. Segundo, nos pares que partem de cadastros (clientes, funcionários, transportadoras), o pipeline executa uma subconsulta por documento, enquanto o PostgreSQL resolve a junção de uma só vez. Criar índices equivalentes no MongoDB é um teste pendente, não um resultado deste relatório.\n\n<!-- image:apresentacao/evidencias/entrega03/tempos.png -->\n\nFigura 4 — Medianas das 20 medições por par, em milissegundos; as barras de erro indicam Q1 e Q3.\n'
 text+='''
## 17.3 Estudos controlados

Os quatro estudos usam cópias isoladas dos dados. Nas cópias PostgreSQL, foram mantidos apenas os índices de PK e UNIQUE; nas cópias MongoDB, apenas o índice de _id. Para separar o efeito de um índice sem criá-lo ou removê-lo durante as medições, foram mantidas três cópias: sem índices adicionais, com índice em order_date e com índice composto (customer_id, order_date). Os bancos originais não receberam esses índices, e as estatísticas das cópias PostgreSQL foram atualizadas antes das medições.

Em cada estudo, todas as versões foram executadas na mesma sequência de rodadas. A ordem das versões muda a cada rodada, e a ordem dos bancos alterna. Assim, uma variação do ambiente ao longo do tempo não favorece sistematicamente a versão medida primeiro ou por último. Antes das medições, os resultados de todas as versões foram comparados e eram idênticos.

A diferença entre duas versões é considerada consistente nesta execução quando os intervalos Q1–Q3 não se sobrepõem. Isso é uma regra descritiva: não substitui repetição independente nem teste estatístico.

'''
 descriptions={
 'C01':('Filtro mensal','A versão original obtém o mês com to_char em cada pedido e compara o texto; no MongoDB, cria o campo com $dateToString antes do $match. A reescrita filtra o intervalo de datas diretamente. A terceira versão repete a reescrita na cópia com índice em order_date. As três devolvem o mesmo resultado para janeiro de 1997.',
   [('original','reescrita','efeito da reescrita do filtro'),('reescrita','com_indice','efeito do índice por data')]),
 'C02':('Cliente e período','A mesma consulta — pedidos de VINET em 1996, ordenados por data e ID — foi executada na cópia sem índices adicionais e na cópia com índice composto (customer_id, order_date). O índice já existente no MongoDB original não foi usado como prova: o efeito foi medido nas cópias.',
   [('sem_composto','com_composto','efeito do índice composto')]),
 'C03':('Pares de produtos','A versão original em SQL foi escrita com uma CTE MATERIALIZED que gera todos os pares de itens de cada pedido antes de aplicar A < B. Sem essa instrução, o PostgreSQL 16 incorporaria a CTE e aplicaria a condição durante a junção, como faz a reescrita (Q12). O estudo mede, portanto, o custo de materializar os pares intermediários, não uma limitação do otimizador. No MongoDB, a versão original mantém todos os campos do pedido e só descarta os pares A ≥ B depois do $group; a reescrita (P12) projeta somente os IDs e filtra antes de agrupar. Nenhum índice mudou.',
   [('original','reescrita','efeito da reescrita')]),
 'C04':('Vendas da equipe','A versão original combina a hierarquia com cada pedido e só depois agrega; a reescrita (Q15) agrega os pedidos por funcionário antes da combinação. No MongoDB, a versão original traz os pedidos completos no $lookup e calcula depois; a reescrita (P15) agrupa dentro do $lookup. Nenhum índice mudou.',
   [('original','reescrita','efeito da reescrita')])}
 for case,vs in opt.items():
  title,desc,pairs=descriptions[case];text+=f'### {case} — {title}\n\n{desc}\n\n| Versão | PostgreSQL: mediana (Q1–Q3), ms | MongoDB: mediana (Q1–Q3), ms |\n|---|---|---|\n'
  for v,bs in vs.items():
   p=bs['postgres'];m=bs['mongo'];text+=f'| {v} | {ms(p["mediana_ms"])} ({ms(p["q1_ms"])}–{ms(p["q3_ms"])}) | {ms(m["mediana_ms"])} ({ms(m["q1_ms"])}–{ms(m["q3_ms"])}) |\n'
  text+='\n'
  for a,b,label in pairs:
   frases=[]
   for bank,nome in [('postgres','PostgreSQL'),('mongo','MongoDB')]:
    before=vs[a][bank];after=vs[b][bank];gain=100*(1-after['mediana_ms']/before['mediana_ms'])
    overlap=not(after['q3_ms']<before['q1_ms'] or before['q3_ms']<after['q1_ms'])
    sentido='redução' if gain>=0 else 'aumento'
    frases.append(f'no {nome}, {sentido} de {br(abs(gain),1)}% na mediana, '+('com sobreposição dos intervalos Q1–Q3, portanto inconclusiva' if overlap else 'sem sobreposição dos intervalos Q1–Q3'))
   text+=f'**{label[0].upper()+label[1:]} ({a} → {b}):** '+'; '.join(frases)+'.\n\n'
  text+='<!-- plano:'+case+' -->\n\n'
 text+='''## 17.4 Leitura dos planos e limitações

Seq Scan (PostgreSQL) e COLLSCAN (MongoDB) indicam leitura de todas as linhas ou documentos; Index Scan e IXSCAN indicam acesso por índice. No MongoDB, FETCH indica a busca do documento depois da leitura do índice. Em C01, a versão original e a reescrita do PostgreSQL fazem a mesma varredura sequencial, que descarta 797 dos 830 pedidos. A diferença está no custo de converter e formatar a data com to_char em cada linha e na estimativa do otimizador: com to_char ele previu 4 pedidos (foram 33) e escolheu uma agregação com ordenação adicional; com o intervalo, previu 32 e usou agregação por hash. O índice só passa a ser usado na terceira versão. Em C02, o índice composto reduz a leitura a três pedidos nos dois bancos. Em C03 e C04, o objetivo é diminuir os resultados intermediários, não passar a usar índice.

Nos quadros, as linhas examinadas do PostgreSQL somam as linhas descartadas por filtros em todos os nós do plano. No MongoDB, as métricas do cursor inicial e as de cada $lookup são registradas separadamente. Buffers compartilhados indicam acessos a páginas em memória, não necessariamente leituras de disco.

Não foram forçados índices com hint nem desligadas as varreduras sequenciais. Os dados cabem em memória, as consultas são curtas e o tempo medido inclui a comunicação local e a conversão de tipos pelos drivers. O consumo completo pesa mais em Q12/P12, que retorna 1.535 linhas. O estudo não mede concorrência, custo de escrita, sincronização entre os bancos nem escalabilidade.
'''
 (DOC/'17-performance.md').write_text(text)
 # Tamanho como indicador auxiliar: linhas SQL sem comentários e estágios de primeiro nível.
 from bson import json_util
 specs=json_util.loads((EV/'pipelines.ejson').read_text())
 def sql_lines(n):
  return sum(1 for l in (ROOT/f'sql/queries/Q{n:02}.sql').read_text().splitlines() if l.strip() and not l.lstrip().startswith('--'))
 comparison='| Par | SQL: recursos | Linhas SQL | MongoDB: recursos | Estágios |\n|---|---|---|---|---|\n'+''.join(
  f'| {n:02} | {i[str(n)]["sql"]} | {sql_lines(n)} | {i[str(n)]["mongo"]} | {len(specs[str(n)]["pipeline"])} |\n' for n in range(1,17))
 (DOC/'comparacao-tabela.md').write_text(comparison)
 # Gráficos derivados dos resultados medidos.
 plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
 fig,ax=plt.subplots(figsize=(9,5));xs=list(range(16))
 for bank,shift,color,label in [('postgres',-.17,'#22577a','PostgreSQL'),('mongo',.17,'#32936f','MongoDB')]:
  ds=[perf[str(n)][bank] for n in range(1,17)]
  med=[d['mediana_ms'] for d in ds]
  ax.bar([x+shift for x in xs],med,.32,color=color,label=label,
         yerr=[[d['mediana_ms']-d['q1_ms'] for d in ds],[d['q3_ms']-d['mediana_ms'] for d in ds]],capsize=2)
 ax.set_xticks(xs,[f'{n:02}' for n in range(1,17)]);ax.set_xlabel('Par de consultas');ax.set_ylabel('Tempo até consumir o resultado (ms)');ax.legend();fig.tight_layout();fig.savefig(EV/'tempos.png',dpi=180);plt.close(fig)
 fig,ax=plt.subplots(figsize=(9,4));rows=r['2']['rows'];ax.plot([x['mes'][:7] for x in rows],[float(x['valor']) for x in rows],marker='o',color='#22577a');ax.set_ylabel('Valor após descontos');ax.tick_params(axis='x',rotation=65);ax.set_title('Valor mensal — o primeiro e o último mês têm cobertura parcial');fig.tight_layout();fig.savefig(EV/'mensal.png',dpi=180);plt.close(fig)
 print('Capítulos e gráficos gerados a partir das evidências.')
if __name__=='__main__':main()
