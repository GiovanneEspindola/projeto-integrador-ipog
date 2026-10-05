# Plano da Entrega 3 — consultas e análises em PostgreSQL e MongoDB

Planejamento elaborado em 22/09/2026, após revisão dos documentos entregues, dos scripts, do material da disciplina e dos bancos locais. O plano foi autorizado e implementado em 22/09/2026. O catálogo, os testes e as medições estão executados; os documentos finais e a revisão de paginação estão registrados nas evidências da etapa.

## 1. Resultado esperado e escopo

Produzir **um DOCX cumulativo**, reunindo o conteúdo revisado das Entregas 1 e 2 e as análises das semanas 5 e 6. O arquivo destinado à professora será `entregas/entrega-03/Projeto-Integrador-Banco-de-Dados-Entrega-03.docx`.

O Word deverá permitir avaliar o trabalho sem abrir o repositório: perguntas, definições, códigos, resultados executados, interpretação, comparação e evidências de performance estarão no próprio documento. Scripts e saídas completas permanecerão no projeto para reprodução.

O Livro Digital, páginas 5–6, confirma os requisitos informados pelo usuário. O resumo da aula registra 27/09/2026 como data da terceira entrega; essa é a referência do cronograma proposto abaixo. O formato DOCX cumulativo segue a orientação atual do usuário.

| Requisito | Implementação planejada | Evidência no Word |
|---|---|---|
| Pelo menos 15 consultas SQL simples e complexas | 16 consultas Q01–Q16, com progressão de complexidade | Catálogo, código completo, resultados e interpretação |
| Views para relatórios | 4 views analíticas com cálculos consistentes | Definições, finalidade e exemplos de uso |
| Stored procedures | 3 procedures PL/pgSQL, criadas com `CREATE PROCEDURE` e executadas com `CALL` | Código, parâmetros, chamadas e resultados |
| Relatório de performance | Medição das 16 análises e 4 estudos de otimização | Método, tempos, planos antes/depois e limites |
| 15+ aggregation pipelines complexos | 16 pipelines P01–P16, equivalentes às perguntas SQL | Código completo, explicação das etapas e saídas |
| Recursos próprios do MongoDB | 3 demonstrações adicionais sobre arrays/documentos, além dos recursos usados nos 16 pares | Código e interpretação das particularidades documentais |
| MapReduce | 1 análise de quantidade por produto, com pipeline equivalente | Código, execução, conferência e contexto de uso legado |
| Comparação de sintaxe e complexidade | Matriz dos 16 pares e discussão detalhada de 4 casos | Diferenças de estrutura, manutenção e execução |
| Pipelines otimizados e documentados | Versões de referência e revisadas dos estudos selecionados | Justificativa de cada alteração e efeito observado |

As consultas exploratórias das entregas anteriores permanecem no relatório, mas não serão usadas para completar artificialmente a contagem das 16 novas análises. MapReduce e demonstrações adicionais também não substituem os 16 pipelines.

## 2. O que foi revisado e confirmado

Foram examinados os dois DOCX por extração de seu conteúdo, os capítulos Markdown, o gerador Word, os scripts SQL/MongoDB, as evidências da Entrega 2, o plano anterior e os dois PDFs locais da disciplina. A revisão atual dos DOCX foi de conteúdo e estrutura, sem nova inspeção visual de todas as páginas.

Consultas de leitura executadas em 22/09/2026 confirmaram:

| Verificação | Estado observado |
|---|---|
| Docker | PostgreSQL e MongoDB saudáveis |
| Versões em execução | PostgreSQL 16.15; MongoDB 7.0.40 |
| Estrutura relacional | 14 tabelas em `public`; 11 em `nw` |
| Estrutura documental | 9 coleções; 1.107 documentos |
| Pedidos e itens | 830 pedidos; 2.155 itens nos dois modelos |
| Cadastros principais | 91 clientes; 77 produtos |
| Período dos pedidos | 04/07/1996 a 06/05/1998 |
| Datas de envio ausentes | 21 pedidos |
| Clientes sem pedidos | 2 |
| Produtos nunca vendidos | 0 |
| Total decimal nos dois bancos | `1265793.03950` |
| Total arredondado ao final | `1265793.04` |
| Soma com arredondamento por item | `1265793.29` |
| Views existentes | 4 no schema `nw` |
| Funções/procedures em `nw` | Nenhuma |
| Índices analíticos existentes | 4 adicionais em PostgreSQL; 3 adicionais em MongoDB |
| Diretórios de novas análises | `sql/queries/`, `mongo/pipelines/` e `bench/results/` ainda sem implementação |

Também foi executado MapReduce com resultado em memória (`out: {inline: 1}`): a contagem retornou 830 pedidos distribuídos entre 89 clientes com compras. Isso confirma a disponibilidade do recurso nesta instalação; não é ainda a análise final proposta.

A equivalência completa de 3.311 linhas, campo a campo, está documentada nas evidências da Entrega 2. Nesta revisão foram reconferidos os volumes principais e o total decimal; a conferência completa deve ser repetida antes das novas análises.

## 3. Ajustes nas entregas anteriores

### Preservar o que já está adequado

Manter a compreensão do negócio, o diagrama conceitual, a exploração da fonte, a separação `public`/`nw`, o modelo de nove coleções, os itens incorporados, Decimal128, datas em UTC e a validação independente da migração. Não há evidência, nesta revisão, de necessidade de refazer a carga ou redesenhar o modelo documental.

Os dois DOCX já entregues serão preservados. As atualizações de texto entrarão na versão cumulativa da Entrega 3, com datas de conferência e distinção entre resultados históricos e novos.

### Corrigir antes das análises

| Achado | Ação planejada |
|---|---|
| `sql/40_views.sql` arredonda os valores por item, divergindo do critério do DOCX | Criar a camada de analytics com valores exatos e proibir o uso das views monetárias antigas nos novos pares. Documentar a diferença de 0,25. |
| A view antiga usa `entregue_com_atraso` e interpreta data nula como “nunca enviado” | Nas novas views e textos, usar “envio registrado após a data requerida” e “sem data de envio registrada”. A base não comprova entrega ao cliente. |
| Comentários antigos atribuem reais aos valores | Usar unidades monetárias da base, sem inventar moeda. |
| O capítulo relacional existe em `docs/06-modelo-relacional.md`, mas não integra os DOCX examinados | Incluir uma síntese revisada: `public` versus `nw`, ER lógico, tipos, chaves, restrições, normalização e índices. |
| O texto relacional declara violação de 1FN e depois afirma BCNF para todas as tabelas | Revisar a argumentação: atomicidade depende do domínio e do uso do atributo; retirar a afirmação irrestrita de BCNF sem demonstração consistente. |
| O plano antigo propõe margem, prazo de entrega, ABC por `NTILE` e funções como procedures | Usar valor após descontos, intervalo até envio, ABC por participação acumulada e procedures reais. |
| O plano antigo adia as medições para a Entrega 4 | Entregar performance e otimização já na Entrega 3, como exige a semana 5. A etapa seguinte consolida e aprofunda. |
| Introdução e conclusões ainda anunciam análises futuras | Atualizá-las após a execução, mantendo os limites da base e registrando o que foi efetivamente concluído. |
| O gerador aceita apenas as entregas 1 e 2 | Acrescentar `--entrega=3` e o comando `docx:entrega03`, preservando as saídas anteriores. |
| Não há sumário nos DOCX; `preencher_sumario.py` aponta para um nome antigo da Entrega 1 | Implementar sumário compatível com o novo documento e parametrizar a ferramenta, validando as páginas após renderização. |

Não copiar integralmente o capítulo relacional antigo: ele contém trechos extensos, referências desatualizadas e conclusões que precisam ser ajustadas ao relatório atual. A síntese deve complementar a narrativa sem repetir toda a exploração.

## 4. Contrato comum das análises

Antes de escrever Q01/P01, registrar um contrato por pergunta: entrada, período, filtros, granularidade, colunas, tipos, tratamento de nulos, ordenação e regra de empate.

- **Valor:** preço praticado × quantidade × (1 − desconto), sem frete. Usar `numeric` e Decimal128; não converter dinheiro para ponto flutuante.
- **Arredondamento:** manter valores exatos nas somas e na validação. Formatar os resultados apresentados com uma regra única e explícita, por exemplo `Decimal` com `ROUND_HALF_UP`. `round(numeric)` e `$round` não têm a mesma regra em todos os empates.
- **Médias e proporções:** comparar também seus numeradores e denominadores. Para quocientes de expansão infinita, documentar a precisão/tolerância por coluna; não arredondar tudo para centavos antes de conferir.
- **Data de referência:** 06/05/1998, reproduzível e associada ao último pedido. Seis meses significa seis meses de calendário, com corte em 06/11/1997; “mais de seis meses” usa data estritamente anterior ao corte.
- **Períodos:** início inclusivo e fim exclusivo; datas MongoDB em UTC. Distinguir mês anterior do calendário de observação anterior; completar meses sem movimento quando necessário.
- **Granularidade:** calcular o valor do pedido antes do ticket médio. Não multiplicar pedidos, frete ou valor por causa de junções e expansão de arrays.
- **Identidade:** agrupar por identificador, usando nomes apenas como descrição. Fixar desempate por identificador onde a regra exigir ordem determinística.
- **Cadastros sem movimento:** preservar clientes, produtos e transportadoras quando a pergunta exigir. Separar cliente sem compras de cliente com compra antiga.
- **Limites:** não calcular margem, lucro ou recebimento; não inferir entrega efetiva; não tratar meses/trimestres parciais como períodos completos.

## 5. Catálogo das 16 análises equivalentes

Preservar a numeração do plano anterior quando possível, corrigindo as definições. Cada linha terá um arquivo QNN.sql e um PNN.js executável, com parâmetros e saída comparável.

| Par | Pergunta e resultado | SQL | Pipeline MongoDB |
|---|---|---|---|
| 01 | Valor por categoria, unidades e participação no total | Junções, agregação e percentual sobre total | `$unwind`, `$group`, cálculo do total e participação |
| 02 | Pedidos, valor e ticket médio por mês | Agregação por pedido e depois por mês | `$map`/`$reduce` dos itens, `$group` mensal e cálculo do ticket |
| 03 | Produtos sem venda no recorte, com categoria e fornecedor | `NOT EXISTS` e junções cadastrais | `$lookup` com filtro/limite de existência, anti-join e projeção cadastral |
| 04 | Valor, número de pedidos, ticket e participação por funcionário | Junções, agregação e classificação | `$lookup`, agregação dos pedidos e cálculo dos indicadores |
| 05 | Produtos abaixo do ponto de reposição, déficit e cobertura por categoria | Filtro entre colunas, `CASE` e agregação | `$expr`, `$set`, `$group` e detalhamento dos produtos |
| 06 | Clientes sem compra há mais de seis meses e clientes sem compras | `LEFT JOIN`, última compra e classificação | `$lookup`, última compra, cálculo de recência e classificação |
| 07 | Cinco produtos de maior valor por categoria | Agregação e `ROW_NUMBER` por categoria | `$unwind`, `$group`, `$setWindowFields` com `$documentNumber` |
| 08 | Evolução mensal e valor acumulado | Série mensal e `SUM OVER` | Agrupamento temporal, calendário e `$setWindowFields` |
| 09 | Variação do valor em relação ao mês anterior | `LAG`, diferença e percentual | Série mensal, `$shift` e expressões condicionais |
| 10 | Curva ABC de clientes por valor acumulado | Agregação, soma acumulada e `CASE` | `$lookup`, `$setWindowFields` e classificação |
| 11 | Perfil RFM: recência, frequência e valor por cliente | CTEs, última compra, contagem e faixas | `$lookup`, agregações, diferenças de datas e classificação |
| 12 | Pares de produtos comprados juntos e suporte por pedido | Autojunção dos itens e agregação | Expansão dos itens, formação de pares e `$group` |
| 13 | Intervalo entre pedido e envio por transportadora | Diferença de datas, contagens condicionais e média | `$lookup`, `$dateDiff`, `$group` e indicadores de ausência |
| 14 | Valor bruto, desconto e valor após descontos por categoria | Expressões decimais e agregação | `$unwind`, cálculos decimais, `$group` e proporções |
| 15 | Vendas próprias e da equipe de cada gestor | CTE recursiva e agregação | `$graphLookup`, `$lookup` e agregação da equipe |
| 16 | Distribuição trimestral por ano e categoria | Agregações e `GROUPING SETS` | `$facet` com visões trimestrais e por categoria |

As análises simples em SQL devem continuar legíveis. Nos pipelines, a complexidade deve resultar das etapas necessárias à pergunta, como junções, manipulação de arrays, cálculos e agregações; não adicionar estágios sem finalidade apenas para aumentar o tamanho.

### Decisões específicas

- **Q03/P03:** o período completo retorna zero produtos nunca vendidos. Esse resultado é válido e deve aparecer no Word. Usar um período menor como exemplo adicional apenas se houver propósito explícito, sem alterar silenciosamente a pergunta.
- **Q07/P07:** retornar exatamente até cinco produtos por categoria, com valor decrescente e identificador crescente como desempate. Se for desejado preservar todos os empatados, mudar o contrato e as duas implementações conjuntamente.
- **Q10/P10:** ABC usa participação acumulada do valor, não quantidade de clientes em grupos iguais. Ordenar por valor e ID; classificar pelo acumulado anterior: A enquanto abaixo de 80%, B abaixo de 95%, C nos demais. Assim, o cliente que cruza o limite fica na classe que está sendo completada. Clientes sem compras ficam em grupo separado.
- **Q11/P11:** entregar R, F e M brutos e uma classificação com faixas explícitas iguais nos dois bancos. Preferir faixas determinísticas a duas implementações de quantis com empates tratados de forma diferente. Definir as faixas ao examinar a distribuição e registrá-las antes da validação final; não chamar a segmentação de modelo preditivo.
- **Q12/P12:** impor `produto_a < produto_b`, contar cada par uma vez por pedido e definir suporte como pedidos com o par / pedidos do recorte.
- **Q13/P13:** calcular a média somente onde há data de envio, exibindo também enviados registrados, ausências e total. Manter transportadoras sem pedidos quando o contrato incluir todo o cadastro.
- **Q15/P15:** incluir vendas próprias e descendentes uma única vez dentro da equipe. Totais de gestores podem se sobrepor; não somá-los como se fossem partes independentes do total geral. Verificar ausência de ciclos.
- **Q16/P16:** sinalizar períodos incompletos e usar “distribuição temporal”. O recorte curto não sustenta uma conclusão forte de sazonalidade recorrente.

## 6. Views e procedures

Criar o schema `nw_analytics`, lendo as tabelas de `nw`. Isso permite introduzir a regra decimal correta sem alterar silenciosamente as views usadas nas evidências antigas.

| View proposta | Finalidade |
|---|---|
| `vw_item_valor` | Uma linha por item, com valores bruto, desconto e líquido exatos |
| `vw_pedido_valor` | Uma linha por pedido, com contagens e valor, sem duplicação por item |
| `vw_vendas_mensais` | Pedidos, valor e ticket por mês |
| `vw_envio_transportadora` | Indicadores de envio registrado e de ausência de data |

Consultas reutilizarão essas views onde fizer sentido. As versões independentes usadas para conferir os totais devem calcular diretamente sobre as tabelas.

Implementar três procedures de leitura em PL/pgSQL:

1. `sp_resumo_vendas_periodo(inicio, fim, cursor)`: valor, pedidos, ticket e categorias no intervalo.
2. `sp_clientes_inativos(data_referencia, meses, cursor)`: clientes inativos e sem histórico.
3. `sp_desempenho_equipe(gestor_id, inicio, fim, cursor)`: vendas próprias e dos subordinados.

Usar `INOUT refcursor` para os resultados tabulares, com exemplos completos de `BEGIN`, `CALL`, `FETCH ALL` e `COMMIT`. Validar período invertido, número de meses inválido e gestor inexistente. As chamadas devem ser conferidas contra os pares analíticos correspondentes. Funções auxiliares são permitidas, mas não contam como procedures.

A documentação oficial distingue explicitamente `CREATE PROCEDURE`/`CALL` de funções: [PostgreSQL 16 — User-Defined Procedures](https://www.postgresql.org/docs/16/xproc.html).

## 7. Recursos documentais e MapReduce

Acrescentar três demonstrações curtas, separadas do catálogo mínimo:

1. **Condições no mesmo item:** `$elemMatch` para localizar pedidos com um item que satisfaça simultaneamente produto/quantidade/desconto, seguido de `$filter` para apresentar os itens correspondentes. Explicar por que condições independentes sobre o array podem combinar itens diferentes.
2. **Resumo do pedido sem expandir itens:** `$map`, `$filter` e `$reduce` para obter subtotal e subconjunto de itens dentro de cada documento; comparar o formato obtido com a expansão por `$unwind`.
3. **Relatório com múltiplas saídas:** `$facet` para devolver indicadores e distribuições no mesmo documento. Distinguir conveniência do formato de uma afirmação de maior velocidade.

Tratar esses casos como recursos característicos da abordagem documental, sem afirmar que não existem soluções equivalentes em SQL.

Para MapReduce, somar **quantidades inteiras vendidas por produto**, usando os itens incorporados. Entregar funções map/reduce, resultado real e pipeline equivalente, com comparação exata dos totais. Não usar valores monetários em JavaScript nessa demonstração.

Executar com saída em memória, suficiente para os 77 produtos. Registrar a versão testada e explicar que o requisito é atendido para fins didáticos: MapReduce está depreciado desde MongoDB 5.0, e a documentação recomenda pipelines para novos desenvolvimentos. Não omitir o requisito por estar depreciado. Fonte: [MongoDB 7.0 — Map-Reduce](https://www.mongodb.com/docs/v7.0/core/map-reduce/).

## 8. Validação e evidências

Implementar um executor que leia os mesmos arquivos usados nas execuções demonstradas, evitando versões copiadas da lógica. Cada par deverá produzir saídas estruturadas com os parâmetros utilizados.

Ordem da validação:

1. Repetir a conferência da migração, incluindo conteúdo e tipos, sobre a fotografia atual dos dois bancos.
2. Comparar colunas, chaves, quantidade de linhas e valores de cada par, incluindo duplicidades. Uma igualdade do total geral não basta.
3. Normalizar representação de datas, Decimal128, `numeric` e IDs sem descartar precisão. Comparar valores monetários exatos antes da formatação.
4. Conferir a ordenação contratada separadamente da comparação dos registros; não esconder erro de ranking reordenando tudo depois.
5. Executar casos de fronteira relevantes: intervalo vazio, cliente sem compra, data nula, empate no ranking, divisor zero e arredondamento em meio centavo.
6. Verificar identidades de controle: soma por categoria e por mês igual ao total geral; bruto − desconto = líquido; contagens de pedidos sem duplicação.

Casos artificiais necessários aos testes devem ser pequenos, identificados como testes e executados em estruturas isoladas; não serão acrescentados à base real para produzir resultados mais interessantes.

Salvar código/versão, parâmetros, ambiente, saídas SQL/MongoDB, conferência e planos em `apresentacao/evidencias/entrega03/`. Registrar hashes para vincular o código executado ao código inserido no Word. No documento, resultados extensos podem ser resumidos com a quantidade total de linhas e identificação clara do recorte exibido.

## 9. Relatório de performance e otimização

Entregar uma avaliação delimitada, já nesta etapa, sem prometer testar escalabilidade com 830 pedidos.

### Medição das 16 análises

- Executar sobre a mesma fotografia de dados e registrar CPU, memória disponível/limites, sistema, versões, configuração relevante e índices.
- Usar conexões persistentes pelos drivers existentes. Cronometrar a execução até consumir todo o resultado, excluindo abertura do processo, conexão, impressão, geração de arquivos e formatação.
- Fazer 5 aquecimentos e 20 execuções medidas por análise/banco; alternar a ordem dos bancos para reduzir viés temporal. Registrar cada amostra, mediana e intervalo interquartil.
- Chamar o cenário de cache aquecido. Reiniciar um container ou descartar a primeira execução não demonstra cache frio.
- Obter planos separadamente: `EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)` e `explain("executionStats")`. Apresentar custo estimado, tempo observado, linhas/documentos/chaves examinados e buffers como medidas distintas.
- Não equiparar diretamente milissegundos internos de `explain` de um banco aos do outro; usar a medição externa comum para a comparação de tempo e planos para explicar o trabalho realizado.
- Valores de tempo arredondados para zero no MongoDB não significam execução instantânea. Ganhos menores que a dispersão serão tratados como inconclusivos.

### Quatro estudos antes/depois

| Caso | Hipótese de otimização a testar |
|---|---|
| Valor mensal com filtro de período | Intervalo direto sobre a data, aplicação antecipada do filtro e avaliação de índice por data |
| Histórico/inatividade de clientes | Índice composto quando útil; uso e limites do `cliente_data` existente |
| Produtos comprados juntos | Reduzir expansão intermediária, eliminar pares simétricos e filtrar o período antes da combinação |
| Vendas da equipe | Agregar pedidos por funcionário antes de combinar com a hierarquia, evitando multiplicação do trabalho |

Cada estudo deve comprovar igualdade de resultados, explicar a hipótese, guardar planos e comparar execuções repetidas. Se o otimizador já produzir o mesmo plano ou a mudança não melhorar a medição, registrar esse resultado. O sucesso do trabalho não depende de obter ganho em todos os casos.

Mudanças e remoções de índices para comparação devem ocorrer em cópias isoladas. Preservar PKs, índices de unicidade e os objetos históricos; distinguir efeito da reescrita do efeito do índice. Não usar `enable_seqscan=off` ou `hint` como prova de escolha natural do otimizador.

No MongoDB, verificar as otimizações que o próprio servidor já faz. Uma projeção antecipada, por exemplo, não deve ser anunciada como ganho sem medição. Referências: [PostgreSQL 16 — EXPLAIN](https://www.postgresql.org/docs/16/sql-explain.html) e [MongoDB 7.0 — Pipeline Optimization](https://www.mongodb.com/docs/v7.0/core/aggregation-pipeline-optimization/).

Não é necessário gerar milhões de pedidos artificiais, configurar sharding ou replica set para satisfazer esta entrega. Esses cenários mudariam o escopo e não resolveriam a análise do conjunto fornecido.

## 10. Composição do DOCX cumulativo

Ordem proposta para a versão final:

1. Capa da Entrega 3 e sumário preenchido.
2. Introdução, objetivo e orientação CRISP-DM atualizados.
3. Compreensão do negócio e definições dos indicadores.
4. Modelo conceitual e análise exploratória preservados, com contexto das conferências históricas.
5. Abordagem híbrida e síntese revisada do modelo relacional, incluindo o ER lógico.
6. Modelo documental, transformação, índices e validação da Entrega 2.
7. Contrato analítico, views e catálogo das 16 perguntas.
8. Resultados e interpretação das 16 análises equivalentes.
9. Procedures, recursos documentais adicionais e MapReduce.
10. Comparação de sintaxe/complexidade e relatório de performance.
11. Conclusões de negócio, conclusões técnicas e limitações.
12. Referências e apêndices de código/evidências.

No corpo, cada análise terá pergunta, regra de cálculo, resultado real e interpretação. Discutir quatro pares em maior profundidade: ranking, ABC/RFM, cesta de produtos e hierarquia. A matriz comparativa dos 16 pares deve considerar junções, arrays, janelas, recursão, legibilidade e dependência da modelagem; quantidade de linhas de código será apenas um indicador auxiliar.

Inserir **os 16 SQL e os 16 pipelines completos no próprio Word**, além das definições das views, procedures, exemplos de chamada e MapReduce. Os apêndices permitem manter a leitura principal fluida. Helpers usados pelos scripts também precisam estar definidos, para não deixar código incompleto no documento.

Extrair código diretamente dos arquivos executados e resultados das evidências validadas. Evitar redigitar saídas. Usar tabelas editáveis e até quatro gráficos úteis, por exemplo evolução mensal, concentração por categoria, ABC e tempos com dispersão.

Revisar o gerador para blocos longos de código: o `keepNext` aplicado a todas as linhas pode causar paginação ruim. Ajustar larguras das tabelas, quebras, referências, legendas e orientação das páginas quando necessário. Não fixar uma meta de páginas antes de testar a legibilidade.

Renderizar uma cópia em PDF para revisão visual. O LibreOffice do Windows existe no ambiente; o fluxo deve ser testado cedo. O PDF é instrumento de revisão, enquanto o entregável continua sendo o DOCX.

## 11. Organização dos arquivos a implementar

```text
docs/entrega03/
  PLANO-ENTREGA-03.md          este planejamento
  contrato-analitico.md       definições comuns e por consulta
  *.md                       capítulos novos e revisados
sql/queries/Q01.sql ... Q16.sql
sql/entrega03/
  00_views.sql
  10_procedures.sql
  11_exemplos_procedures.sql
  otimizacao/                versões e índices dos estudos controlados
mongo/pipelines/P01.js ... P16.js
mongo/entrega03/
  recursos_documentais.js
  mapreduce.js
  otimizacao/
etl/validar_analytics.py
bench/entrega03.py
bench/results/entrega03/
apresentacao/evidencias/entrega03/
entregas/gerar_docx.js        suporte explícito a --entrega=3
entregas/entrega-03/
  Projeto-Integrador-Banco-de-Dados-Entrega-03.docx
```

Atualizar o README com comandos de reprodução após a implementação. Há alterações locais preexistentes da Entrega 2; preservá-las e distinguir os arquivos novos da Entrega 3.

## 12. Sequência de execução e critérios de conclusão

| Etapa | Trabalho | Critério para avançar |
|---|---|---|
| 1 — Revisão e contrato | Revalidar carga, revisar texto relacional, fixar métricas e preparar estrutura do Word | Dados equivalentes e definições explícitas |
| 2 — Base SQL | Criar views, Q01–Q16 e as três procedures | Execução real e controles internos aprovados |
| 3 — MongoDB | Criar P01–P16, recursos adicionais e MapReduce | 16 pares equivalentes e demonstrações executadas |
| 4 — Performance | Medir catálogo e os quatro estudos de otimização | Amostras e planos salvos, sem diferenças de resultado |
| 5 — Redação | Interpretar saídas e consolidar o DOCX | Todos os requisitos rastreáveis no documento |
| 6 — Revisão final | Conferir conteúdo, referências, reprodução e paginação | DOCX autossuficiente, legível e consistente |

Planejamento indicativo até a data registrada no material: 22/09 para revisão/contrato e base SQL; 23/09 para concluir SQL/procedures e iniciar pares; 24/09 para concluir MongoDB e equivalência; 25/09 para performance; 26/09 para consolidar e revisar o Word; 27/09 como margem final. Validar cada par durante sua implementação, sem acumular divergências para o último dia. Escrever as interpretações conforme os resultados forem confirmados.

### Checklist de aceite

- [x] DOCX cumulativo com o conteúdo das duas etapas anteriores e a nova etapa.
- [x] Síntese relacional revisada, coerente com o banco e o restante do relatório.
- [x] 16 consultas SQL identificadas e executadas.
- [x] 16 pipelines identificados, documentados e executados.
- [x] 16 pares conferidos, com precisão, nulos, ordenação e filtros consistentes.
- [x] Quatro views com regra monetária explícita e sem arredondamento intermediário.
- [x] Três procedures reais, com chamadas reproduzíveis e resultados.
- [x] Recursos documentais adicionais e MapReduce com saída conferida.
- [x] Relatório de performance com amostras, planos, quatro estudos e limitações.
- [x] Código completo e resultados suficientes dentro do Word, sem exigir acesso ao projeto.
- [x] Discussão de negócio apoiada nos resultados, sem conclusões financeiras ou logísticas que a base não sustenta.
- [x] Capa, sumário, tabelas, diagramas, código e referências conferidos após renderização.
- [x] Arquivos das Entregas 1 e 2 preservados.

O planejamento está concluído quando este escopo estiver definido; a Entrega 3 somente estará concluída após execução, conferência e revisão do novo DOCX.

## 13. Complemento solicitado: guia pessoal cumulativo

Foi acrescentado um documento de estudo separado do DOCX acadêmico, com fonte em `docs/estudo/guia-completo.md` e versão portátil em `docs/estudo/guia-completo.html`. Cobre as Entregas 1 a 3 e deve ser atualizado no mesmo arquivo durante a Entrega 4.

O guia acompanha o pedido 10248 nos dois modelos, explica negócio, qualidade, normalização, incorporação, migração, decimais, consultas, procedures, MapReduce e performance. Inclui os 16 estudos com códigos completos, exercícios com respostas, glossário, 22 perguntas de banca e roteiro de apresentação de 20 minutos. O gerador incorpora as evidências reais e dispensa internet para leitura.

Ajuste de implementação: P07 usa soma cumulativa de 1 na janela, porque `$documentNumber` no MongoDB 7 exige um único campo de ordenação; a soma mantém o desempate por valor e ID. As três procedures usam cursor e os testes comprovaram suas saídas e entradas inválidas. Foram concluídas 38 verificações adicionais em estruturas isoladas.

## 14. Revisão independente de 24/09/2026

A revisão reexecutou os 16 pares e recalculou os resultados por um terceiro caminho, em Python puro, sem divergências. As mudanças decorrentes foram:

- **Validação:** a comparação passou a rejeitar ponto flutuante, lógicos trocados por números e datas fora da meia-noite UTC; P16 passou a devolver o trimestre como inteiro. Os testes sintéticos ganharam valores esperados calculados à mão em 15 pares, e o recálculo em Python ficou em `etl/conferir_python.py`.
- **Performance:** as versões de cada estudo passaram a ser medidas de forma intercalada, em cópias separadas para cada configuração de índice. O efeito da reescrita e o do índice são relatados separadamente em C01. O relatório declara a assimetria de índices entre os bancos e que a versão original de C03 usa MATERIALIZED de propósito.
- **Relatório:** cabeçalhos de pergunta e resultado em todos os Q/P; séries mensais completas; resumo ABC por classe; contraste $elemMatch × condições independentes; capítulos herdados com tempo verbal atualizado; limites de leitura reescritos como frases declarativas.

