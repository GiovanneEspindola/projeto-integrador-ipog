# 19. Conclusões

O projeto implementou a mesma base de vendas em PostgreSQL e MongoDB, provou que a migração preservou todos os dados e respondeu a 16 perguntas de negócio nos dois bancos, com resultados idênticos e conferidos por um terceiro cálculo.

## 19.1 O que os dados mostram

- **A receita registrada é concentrada.** Beverages responde por 21,16% do valor, e um único produto, o Côte de Blaye, por 11,17% de tudo o que foi vendido no período.
- **Poucos clientes sustentam a maior parte do valor.** 34 dos 89 clientes com compras formam a classe A da curva ABC, com 80% do valor.
- **Há um cliente importante parado.** A Mère Paillarde, da classe A, não compra desde 30/10/1997, mais de seis meses antes do fim da base. Cruzar a curva ABC com a análise de inatividade aponta onde agir primeiro.
- **O valor mensal cresceu ao longo de 1997 e no início de 1998**, com o pico em abril de 1998. A queda em maio de 1998 é efeito da base, que termina no dia 6, e não uma retração.
- **O estoque tem 18 produtos abaixo do ponto de reposição**, dois deles sem cobertura nem com o que já foi encomendado. Um dos 18 está descontinuado, o que mostra que o indicador precisa ser lido junto com o status do produto.

Todas essas conclusões tratam de valor registrado. Sem custos, a base não permite falar em lucro, e sem histórico longo, não permite afirmar sazonalidade.

## 19.2 O que a comparação mostra

- **Os dois modelos chegam às mesmas respostas**, desde que as regras de cálculo sejam fixadas antes, principalmente o arredondamento.
- **O documento simplifica o que gira em torno do pedido**; o relacional é mais direto quando a pergunta parte de um cadastro ou cruza entidades.
- **O PostgreSQL foi mais rápido nos 16 pares** neste volume e nesta máquina. Parte da diferença vinha de índices ausentes no MongoDB, mas, mesmo com eles, o PostgreSQL continuou de 1,9 a 4,3 vezes mais rápido nos pares testados.
- **A escolha depende do padrão de acesso.** Para a Northwind, o PostgreSQL atende sozinho; o MongoDB passa a compensar quando há muitas leituras de pedidos completos ou dados de formato variável.

## 19.3 Limites

O volume é pequeno, as medições foram feitas numa única máquina, sem concorrência nem teste de escala, e o MongoDB rodou em um único servidor. A base não tem custos, pagamentos nem datas de entrega. Esses limites não invalidam as conclusões, mas definem até onde elas valem.
