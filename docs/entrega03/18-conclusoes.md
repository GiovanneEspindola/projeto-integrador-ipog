# 18. Conclusões e reprodução

A Entrega 3 implementou 16 análises equivalentes, quatro views e três procedures, além de recursos documentais e MapReduce. A migração permaneceu consistente e todos os pares foram conferidos, incluindo valores, nulos, duplicidades e ordenação. A revisão padronizou o cálculo monetário sem arredondamento intermediário e distinguiu envio registrado de entrega efetiva.

## 18.1 Conclusões de negócio

Beverages concentra 21,16% do valor dos pedidos. Pela regra declarada, 34 dos 89 clientes com compras formam a classe A, que completa os primeiros 80% do valor. Cinco clientes não compram desde antes do corte de inatividade e dois nunca compraram; entre os inativos está MEREP, cliente da classe A, o caso que mais justifica uma ação de relacionamento. Esses resultados indicam onde investigar, sem provar o retorno financeiro de uma ação.

A análise de estoque identifica 18 produtos abaixo do ponto de reposição, dos quais dois não seriam cobertos pelas quantidades encomendadas. É necessário revisar a validade do cadastro e os produtos descontinuados antes de transformar o indicador em recomendação de compra.

Os intervalos por transportadora medem dias até o envio registrado e preservam as 21 ausências de data. Os pares de produtos mais frequentes têm suporte inferior a 1%; a base sustenta uma descrição das combinações, mas não uma conclusão causal sobre venda conjunta.

## 18.2 Conclusões técnicas

O PostgreSQL apresentou menor mediana nos 16 pares nesta execução local. A conclusão é restrita às consultas, aos índices e às condições medidas; em particular, o MongoDB não tinha índice em employee_id nem em shipper_id. O MongoDB reuniu itens e atributos de leitura no documento do pedido, mas as análises que partem de cadastros sem movimento ou percorrem a hierarquia ainda exigiram $lookup e $graphLookup. A escolha de tecnologia deve considerar integridade, manutenção e padrão de acesso, além do tempo.

Nos quatro estudos, as versões foram medidas de forma intercalada, e os efeitos da reescrita e do índice foram separados. As reduções observadas valem para esta execução e este volume; quando os intervalos Q1–Q3 se sobrepõem, a diferença foi tratada como inconclusiva. Escalabilidade e concorrência não foram medidas.

## 18.3 Reprodução local

O projeto usa Docker Compose com PostgreSQL e MongoDB e os drivers do ambiente Python. Após a carga e conferência das Entregas 1 e 2, executar, na raiz do projeto:

```bash
# Criar somente os objetos analíticos novos.
docker compose exec -T postgres psql -U pi -d northwind \
  -v ON_ERROR_STOP=1 -f /sql/entrega03/00_views.sql
docker compose exec -T postgres psql -U pi -d northwind \
  -v ON_ERROR_STOP=1 -f /sql/entrega03/10_procedures.sql
uv run python etl/validar_analytics.py
(cd etl && uv run python testar_analytics.py)
uv run python bench/entrega03.py
```

As demonstrações documentais podem ser executadas com mongosh nos arquivos mongo/entrega03/recursos_documentais.js e mapreduce.js. Os scripts P01–P16 podem ser executados individualmente por mongosh; os Q01–Q16 podem ser abertos no cliente SQL ou passados ao psql. O README contém os comandos de geração dos documentos e a sequência de reprodução.

A Entrega 4 consolidará as análises, a recomendação de uso de cada tecnologia e a apresentação final.
