"""Gera um guia pessoal HTML portátil, separado do relatório acadêmico."""
from pathlib import Path
import base64,html,json,re,unicodedata
import mistune
ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'docs/estudo';E=ROOT/'apresentacao/evidencias/entrega03'

def read(p):return json.loads((ROOT/p).read_text())
def main():
    text=(D/'guia-completo.md').read_text()
    lessons=read('docs/entrega04/interpretacoes.json')
    titles=read('docs/entrega04/catalogo.json')
    results=read('apresentacao/evidencias/entrega03/resultados.json')
    questions={
      1:('O que você precisaria acrescentar para transformar participação de vendas em margem?','Custos de aquisição e uma regra de apuração de margem. A base não contém esses dados; participação no valor não substitui lucratividade.'),
      2:('Um pedido de três itens vale 90 e outro de um item vale 10. Qual é o ticket?','O valor é 100 e existem dois pedidos: ticket 50. Dividir pelos quatro itens daria 25, que responde a outra pergunta.'),
      3:('Por que partir de products, e não só de order_items?','Porque o produto sem vendas não aparece em order_items. É necessário começar pelo universo de produtos e procurar a ausência de correspondência.'),
      4:('Qual informação falta para interpretar a diferença entre vendedores como produtividade?','Pelo menos exposição e contexto: carteira, território, período trabalhado e oportunidades. A soma registrada descreve resultados, não isola suas causas.'),
      5:('Estoque 4, encomendado 8 e ponto 10: o produto aparece? A cobertura é insuficiente?','Aparece, pois 4 < 10. Mas 4 + 8 = 12 cobre o ponto. A chegada é um dado cadastral, não garantia de prazo.'),
      6:('Compra em 06/11/1997 entra em mais de seis meses em 06/05/1998?','Não: está exatamente no corte. Uma compra em 05/11/1997 entra. Cliente sem compra é classificado separadamente.'),
      7:('Dois produtos empatados na quinta posição precisam ambos aparecer?','Na regra adotada, não. A consulta retorna até cinco e desempata pelo menor ID. Outra regra seria legítima, mas precisaria ser aplicada nos dois bancos e documentada.'),
      8:('Se o acumulado subiu, o valor mensal também subiu?','Não. Basta o mês ter valor positivo para o acumulado crescer, mesmo quando vende menos que o mês anterior.'),
      9:('Como interpretar variação de zero para 100?','A diferença absoluta é 100, mas a divisão por zero torna o percentual indefinido. O resultado percentual fica null.'),
      10:('Se o acumulado anterior é 79% e o cliente atual leva a 83%, qual classe recebe?','Classe A, porque o critério é o acumulado anterior. Ele completa o grupo que estava abaixo de 80%. Por isso o total da classe pode ultrapassar ligeiramente o limiar.'),
      11:('Um cliente com R=3 e M=1 é necessariamente ruim?','Não. Ele comprou recentemente, mas tem valor baixo segundo a faixa escolhida. Os componentes respondem a aspectos diferentes; os escores são didáticos.'),
      12:('Quantos pares um pedido com três produtos diferentes gera?','Três pares únicos: A–B, A–C e B–C. O produto não é pareado consigo e não repetimos B–A. A fórmula é n(n−1)/2.'),
      13:('Uma data de envio nula entra como zero na média?','Não. A média usa somente os envios registrados; as ausências aparecem na contagem sem_data. Transformar ausência em zero reduziria artificialmente a média.'),
      14:('Taxas de desconto de 10% e 20% têm sempre média ponderada 15%?','Só se as bases monetárias forem iguais. Um desconto de 10% sobre 100 e de 20% sobre 10 soma 12 sobre 110, aproximadamente 10,91%.'),
      15:('Por que a equipe do gestor máximo tem o total da empresa e isso não é duplicação dentro dela?','Cada funcionário integra essa equipe uma vez e cada pedido pertence a um funcionário. A duplicação surge ao somar linhas de equipes diferentes, porque essas equipes se sobrepõem.'),
      16:('Posso somar todas as 72 linhas para obter o total geral?','Não. Há linhas de total trimestral e linhas de categoria que detalham o mesmo valor. Some somente um nível por vez.')}
    # Onde a regra decisiva aparece em cada código: é isso que a banca pede para mostrar.
    onde={
      1:('`100*t.valor/nullif(sum(t.valor) OVER (),0)`: a janela vazia OVER () soma todas as categorias sem agrupar as linhas.','`$setWindowFields` com janela `["unbounded","unbounded"]` calcula o mesmo total em cada documento.'),
      2:('`vw_pedido_valor` já tem uma linha por pedido; `generate_series` cria os 23 meses e o LEFT JOIN mantém meses vazios.','`$map` soma os itens dentro do pedido; `$range` + `$dateAdd` montam o calendário e `$ifNull` põe zero no mês vazio.'),
      3:('`WHERE NOT EXISTS (...)`: o produto só aparece se não houver nenhum item dele na janela.','`$lookup` com `$limit: 1` e depois `$match: {vendas: {$size: 0}}`: array vazio significa nenhuma venda.'),
      4:('`FROM nw.employees e LEFT JOIN ...`: começar pelo cadastro preserva quem não vendeu.','A consulta começa na coleção employees; `$ifNull` transforma o array vazio do `$lookup` em zero pedidos.'),
      5:('`WHERE p.units_in_stock<p.reorder_level` compara duas colunas da mesma linha.','`$expr` é necessário para comparar dois campos do mesmo documento dentro de `$match`.'),
      6:('`ultima<DATE \'1997-11-06\'` usa “menor que”: quem comprou no dia do corte não entra.','`$lt: ISODate("1997-11-06...")` com a mesma regra; `{ultima: null}` pega quem nunca comprou.'),
      7:('`row_number() OVER (PARTITION BY category_id ORDER BY valor DESC, product_id)`.','`$setWindowFields` com `partitionBy`, `sortBy: {valor: -1, product_id: 1}` e `$sum: 1` acumulado.'),
      8:('`sum(valor) OVER (ORDER BY mes ROWS UNBOUNDED PRECEDING)`: da primeira linha até a atual.','`$setWindowFields` com `window: {documents: ["unbounded","current"]}`.'),
      9:('`lag(valor) OVER (ORDER BY mes)` e `nullif(anterior,0)` para não dividir por zero.','`$shift` com `by: -1` e `$cond` que devolve null quando o anterior é zero.'),
      10:('`acumulado-valor<total*0.80`: compara o acumulado ANTES do cliente com o limite.','`$subtract: ["$acumulado","$valor"]` dentro do `$switch`, com a mesma regra.'),
      11:('Os três `CASE` com faixas fixas; `frequencia=0` vem primeiro para dar zero a quem não comprou.','Três `$cond` aninhados com as mesmas faixas; `$dateDiff` calcula os dias.'),
      12:('`JOIN nw.order_items b ON b.order_id=a.order_id AND a.product_id<b.product_id`.','Dois `$unwind` da mesma lista de IDs e `$match` com `$lt`; o total de pedidos vem de outra faceta.'),
      13:('`count(o.shipped_date)` ignora nulos; `avg(o.shipped_date-o.order_date)` também.','`$dateDiff` devolve null quando falta a data e `$sum` ignora null; a média é soma ÷ com_envio.'),
      14:('`100*sum(desconto)/nullif(sum(bruto),0)`: razão de somas, não média de taxas.','`$divide` do desconto somado pelo bruto somado, depois do `$group`.'),
      15:('`WITH RECURSIVE equipe` desce pela hierarquia; `caminho` impede repetir alguém.','`$graphLookup` de `_id` para `reports_to`; `$setUnion` inclui o próprio gestor.'),
      16:('`GROUPING SETS ((ano,trimestre,category_id),(ano,trimestre))` gera os dois níveis de uma vez.','`$facet` com dois ramos (total e categoria) e `$concatArrays` para juntar.')}
    blocks=[]
    for n in range(1,17):
        k=str(n);m=lessons[k];d=results[k];q,a=questions[n]
        blocks.append(f'### {n:02}. {titles[k]}\n\n**Pergunta:** {m["pergunta"]}\n\n**Raciocínio:** {m["logica"]}\n\n**No PostgreSQL:** {m["sql"]}.\n\n**No MongoDB:** {m["mongo"]}.\n\n**Resultado que você pode explicar:** {m["leitura"]}\n\n**Armadilha:** {m["cuidado"]}\n\nForam conferidas {d["row_count"]} linhas equivalentes nesse par.\n')
        blocks.append(f'**Onde está a regra no SQL:** {onde[n][0]}\n\n**Onde está a regra no MongoDB:** {onde[n][1]}\n')
        blocks.append(f'<details class="exercise"><summary>Teste seu entendimento: {q}</summary>\n\n{a}\n\n</details>\n')
        for label,p in [('SQL',ROOT/f'sql/queries/Q{n:02}.sql'),('MongoDB',ROOT/f'mongo/pipelines/P{n:02}.js')]:
            blocks.append(f'<details class="source"><summary>Abrir código completo — {label} {n:02}</summary>\n\n<pre><code>{html.escape(p.read_text())}</code></pre>\n\n</details>\n')
    text=text.replace('<!-- lessons -->','\n'.join(blocks))
    perf=read('bench/results/entrega03/catalogo.json')
    table='| Par | PostgreSQL mediana (ms) | MongoDB mediana (ms) |\n|---|---|---|\n'
    for n in range(1,17):
        d=perf[str(n)];table+=f'| {n:02} | {d["postgres"]["mediana_ms"]:.3f} | {d["mongo"]["mediana_ms"]:.3f} |\n'
    image=lambda p,alt:'<figure><img src="data:image/png;base64,'+base64.b64encode((ROOT/p).read_bytes()).decode()+'" alt="'+html.escape(alt)+'"><figcaption>'+html.escape(alt)+'</figcaption></figure>'
    text=text.replace('<!-- measured-performance -->',table+'\n'+image('apresentacao/evidencias/entrega03/tempos.png','Medianas e dispersão da execução medida. Consulte Q1–Q3 no relatório para interpretar diferenças pequenas.'))
    text=text.replace('## 5. Modelo conceitual e modelo relacional',image('docs/diagramas/er-conceitual-relatorio.png','As 11 entidades do modelo conceitual. Amplie a imagem no navegador para acompanhar os relacionamentos.')+'\n\n## 5. Modelo conceitual e modelo relacional')
    renderer=mistune.create_markdown(escape=False,plugins=['table','url'])
    body=renderer(text)
    navigation=[]
    def heading(m):
        content=m.group(1);plain=re.sub('<[^>]+>','',content)
        slug=re.sub(r'[^a-z0-9]+','-',unicodedata.normalize('NFKD',plain).encode('ascii','ignore').decode().lower()).strip('-')
        navigation.append((slug,plain))
        return f'<h2 id="{slug}">{content}</h2>'
    body=re.sub(r'<h2>(.*?)</h2>',heading,body)
    nav=''.join(f'<a href="#{slug}">{html.escape(title)}</a>' for slug,title in navigation)
    page='''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Guia de estudo — Projeto Northwind</title><style>
:root{--ink:#233447;--blue:#205473;--muted:#576878;--line:#d7e1e8;--paper:#fff;--bg:#f3f6f8}
*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:30px}body{margin:0;background:var(--bg);color:var(--ink);font:17px/1.75 system-ui,-apple-system,Segoe UI,sans-serif}nav{position:fixed;inset:0 auto 0 0;width:285px;padding:25px 20px;overflow:auto;border-right:1px solid var(--line);background:#eaf0f4}nav strong{display:block;color:var(--blue);font-size:20px;margin-bottom:6px}nav p{font-size:13px;color:var(--muted);line-height:1.5}nav a{display:block;text-decoration:none;color:var(--ink);font-size:13px;line-height:1.45;padding:7px 8px;border-radius:5px}nav a:hover,nav a:focus{background:#d8e6ef}nav input{width:100%;padding:9px;border:1px solid #aabfcd;border-radius:5px;margin:10px 0}main{max-width:1120px;margin-left:285px;padding:45px 65px 90px;background:var(--paper);min-height:100vh}h1{font-size:38px;line-height:1.2;color:var(--blue);margin-top:15px}h2{font-size:27px;line-height:1.3;margin-top:65px;border-top:2px solid var(--line);padding-top:30px;color:var(--blue)}h3{font-size:22px;line-height:1.35;margin-top:32px}p{margin:15px 0}a{color:var(--blue)}table{width:100%;border-collapse:collapse;font-size:14px;line-height:1.5;margin:25px 0}th,td{padding:10px 12px;border:1px solid var(--line);vertical-align:top}th{background:#e7eff5;text-align:left}tr:nth-child(even){background:#f7fafc}blockquote{border-left:4px solid #4e8aa6;background:#f0f6fa;margin:22px 0;padding:5px 24px}code{font-family:Consolas,monospace;font-size:.88em}p code{background:#edf2f6;padding:2px 5px;border-radius:3px}pre{background:#f0f4f7;border:1px solid var(--line);border-radius:6px;padding:18px;overflow:auto;line-height:1.5;font-size:14px}details{border:1px solid #bfd1de;border-radius:7px;padding:12px 17px;margin:16px 0;background:#f6fafc}summary{cursor:pointer;font-weight:650;color:var(--blue)}details[open] summary{margin-bottom:15px}details.source{background:#fff}details.exercise{border-left:4px solid #3c8871}figure{margin:30px 0}figure img{max-width:100%;height:auto}figcaption{font-size:13px;color:var(--muted)}.toolbar{display:flex;flex-wrap:wrap;gap:12px;align-items:center;font-size:13px;color:var(--muted)}button{padding:9px 13px;background:var(--blue);color:white;border:0;border-radius:5px;cursor:pointer}.badge{font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:#31755f;font-weight:700}footer{border-top:1px solid var(--line);margin-top:40px;padding-top:20px;font-size:13px;color:var(--muted)}
@media(max-width:1000px){nav{position:relative;width:auto;max-height:300px;border-bottom:1px solid var(--line)}main{margin:0;padding:25px;max-width:100%;width:100%;overflow-wrap:anywhere}h1{font-size:30px}table{display:block;overflow:auto}}
@media print{nav,.toolbar{display:none}main{margin:0;padding:0;max-width:none}body{font:11pt/1.5 Georgia,serif;background:white}h1{font-size:24pt}h2{page-break-before:always;font-size:19pt}h3,summary{break-after:avoid}table{font-size:9pt}pre{white-space:pre-wrap;font-size:8pt}details.source:not([open]){display:none}figure img{max-height:20cm;object-fit:contain}a{color:inherit}button{display:none}}
</style><nav><strong>Northwind • guia pessoal</strong><p>Entregas 1 a 4<br>Um material para entender, praticar e apresentar.</p><input id="filter" aria-label="Filtrar tópicos do sumário" placeholder="Filtrar tópicos…">NAV</nav><main><div class="toolbar"><span class="badge">Estudo • atualização: 05/10/2026</span><button onclick="window.print()">Imprimir / salvar PDF</button></div>BODY<footer>Guia independente do DOCX acadêmico. Códigos e medições incorporados dos arquivos conferidos. Fonte editável em guia-completo.md.</footer></main><script>
document.querySelector('#filter').addEventListener('input',function(){const q=this.value.normalize('NFD').replace(/[\\u0300-\\u036f]/g,'').toLowerCase();document.querySelectorAll('nav a').forEach(a=>{const t=a.textContent.normalize('NFD').replace(/[\\u0300-\\u036f]/g,'').toLowerCase();a.hidden=!t.includes(q);});});
</script></html>'''.replace('NAV',nav).replace('BODY',body)
    (D/'guia-completo.html').write_text(page)
    print(D/'guia-completo.html')
if __name__=='__main__':main()
