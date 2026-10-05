# 17. Guia de decisão: quando usar cada tecnologia

A comparação não aponta um vencedor geral. Ela mostra que cada modelo resolve melhor um tipo de problema. O quadro abaixo resume os critérios, sempre com a evidência que o projeto produziu.

| Critério | PostgreSQL | MongoDB | O que o projeto mostrou |
|---|---|---|---|
| Integridade entre entidades | Chaves estrangeiras, CHECK e UNIQUE garantidos pelo banco | Validador só confere o formato do documento | No MongoDB, referências foram conferidas por consulta depois da carga (cap. 8) |
| Ler um pedido completo | Junção entre orders e order_items | Um único documento | O pedido 10248 é 4 linhas em 2 tabelas ou 1 documento (cap. 7) |
| Perguntas que partem de cadastros | LEFT JOIN direto | $lookup por documento | P06, P10, P11 e P15 estão entre as maiores diferenças de tempo (cap. 16) |
| Relatórios que cruzam várias entidades | Natural, com junções e janelas | Possível, com pipelines mais longos | Os 16 pares foram equivalentes, mas os de calendário e cadastro ficaram mais longos no MongoDB (cap. 15) |
| Mudança em dados de cadastro | Um único lugar para alterar | Cópias nos documentos precisam ser atualizadas | Nome e categoria do produto estão copiados em cada item (cap. 7) |
| Estrutura variável entre registros | Exige colunas ou tabelas novas | Cada documento pode ter campos próprios | Não exercitado: a Northwind tem estrutura uniforme |
| Precisão de valores monetários | numeric | Decimal128 | Os dois deram o mesmo total exato; o risco está no arredondamento, não no banco (cap. 4) |
| Desempenho neste volume | Mediana menor nos 16 pares | 1,8 a 14,8 vezes mais lento | Diferença real, mas parte dela vinha de índices ausentes (cap. 16) |

## 17.1 Quando escolher cada um

**PostgreSQL** é a escolha para o **sistema de registro**: onde as vendas são gravadas e precisam respeitar regras, onde várias entidades se relacionam e onde surgem perguntas novas a cada dia. A Northwind é um caso típico: dados estruturados, relacionamentos fortes e relatórios que cruzam clientes, produtos, funcionários e datas.

**MongoDB** faz sentido quando o acesso principal é **ler ou gravar um agregado inteiro**, como um pedido com seus itens numa tela de “meus pedidos”, um catálogo cujos produtos têm atributos diferentes entre si ou um registro de eventos com formato variável. Nesses casos, um documento evita juntar peças a cada leitura.

**A arquitetura híbrida** se justifica quando os dois padrões convivem em volume: o relacional registra e garante as regras; o documental serve leituras específicas. O preço é manter a extração, as cópias e dois bancos em operação.

## 17.2 Recomendação para a Northwind

Para o volume e as perguntas deste projeto, **o PostgreSQL sozinho atende** com folga: respondeu às 16 perguntas mais rápido, garante a integridade sem código extra e não exige sincronização. A camada MongoDB passaria a valer o custo se a empresa criasse, por exemplo, um portal em que muitos clientes consultam o histórico completo de pedidos. Nesse caso, a arquitetura deste projeto, com o PostgreSQL como fonte e o MongoDB como cópia de leitura, já está pronta e validada.
