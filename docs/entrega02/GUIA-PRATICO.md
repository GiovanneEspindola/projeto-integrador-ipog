# Entrega 2: roteiro para executar, entender e demonstrar

Este guia trata somente da semana 4: transformar nw em documentos MongoDB, estudar o aninhamento e conferir os índices. Ele não exige Python, instalação de driver ou aplicação própria. Os arquivos `.js` são scripts do **mongosh**, o shell do MongoDB. Os comandos Bash abaixo apenas iniciam os clientes e transportam os arquivos entre eles.

## 1. O que já foi feito e o que você deve observar

O PostgreSQL e o MongoDB do projeto foram consultados com autenticação. Foram carregadas nove coleções na base `northwind`, preservando todos os campos das 11 tabelas de `nw`. O pedido 10248 contém os três itens e o endereço de envio. A carga foi repetida sem duplicações. A comparação de todos os registros retornou zero diferenças.

A conexão salva no Compass **ainda não foi verificada visualmente**. O computer use falhou antes de abrir a janela, com `sandboxCwd is not a local file URI` para o caminho WSL. Esse erro é do acesso à interface; não é uma mensagem de conexão recusada pelo MongoDB.

## 2. Conferir os bancos depois de reiniciar o computador

Abra um terminal **Ubuntu/WSL**, entre no projeto e execute:

```bash
cd /home/giovanne/projeto-integrador-ipog
docker compose up -d postgres mongo
docker compose ps
```

O comando `up -d` inicia os serviços mantendo os volumes existentes. Aguarde os dois ficarem `healthy`. Não use `down -v`, que apaga os volumes. Não execute novamente `10_ddl.sql` ou `20_load.sql` para estudar a Entrega 2: eles recriam/recarregam a origem e não são necessários agora.

Confira a origem com uma consulta de leitura:

```bash
docker compose exec -T postgres psql -X -U pi -d northwind \
  -c 'SELECT count(*) AS pedidos FROM nw.orders; SELECT count(*) AS itens FROM nw.order_items;'
```

Esperado nesta base: **830 pedidos e 2.155 itens**.

Após a reinicialização usada nesta sessão, o MongoDB ficou sem enxergar a pasta montada de scripts. Foi corrigido com `docker compose up -d --force-recreate mongo`, mantendo o volume de dados. Se um script existente der `ENOENT` para o caminho `/mongo/entrega02/`, confira `docker compose exec -T mongo ls /mongo/entrega02`; recrie somente o container dessa forma se a montagem estiver vazia.

## 3. Confirmar sua conexão no Compass

No Compass, conecte usando a conexão local:

```text
mongodb://pi:pi@127.0.0.1:27017/northwind?authSource=admin
```

`127.0.0.1:27017` é a porta publicada do container. O usuário e senha de estudo são `pi`/`pi`. `northwind` é a base do trabalho; `authSource=admin` indica onde o usuário foi criado. Não é necessário criar conta no Atlas para este banco local.

Depois de conectar, atualize a lista de bancos. Abra `northwind`. Você deve encontrar:

| Coleção | Documentos |
|---|---:|
| orders | 830 |
| products | 77 |
| customers | 91 |
| employees | 9 |
| categories | 8 |
| suppliers | 29 |
| shippers | 6 |
| territories | 53 |
| regions | 4 |

Se houver apenas `admin`, `config` e `local`, confirme que a lista foi atualizada e que a conexão usa a porta 27017. Se aparecer erro de autenticação, confira usuário, senha e `authSource`. Se aparecer conexão recusada, confira o Docker e `docker compose ps`.

## 4. Entender o pedido 10248 antes de executar a carga

No DBeaver, conectado ao PostgreSQL `northwind`, execute:

```sql
SELECT * FROM nw.orders WHERE order_id = 10248;
SELECT * FROM nw.order_items WHERE order_id = 10248 ORDER BY product_id;
```

A primeira consulta mostra o cabeçalho; a segunda mostra três linhas. No Compass, abra `northwind` → `orders` → **Documents**. No campo **Filter**, digite somente:

```javascript
{ _id: 10248 }
```

Clique em **Find**. Expanda `shipping`, depois `items`, o item de índice `0`, `product` e `category`. Os nomes e posições dos controles podem variar com a versão do Compass. Estas instruções de interface são um roteiro para você conferir; não há captura de tela validada nesta execução.

Observe:

- `_id` conserva o identificador do pedido.
- `shipping` é o endereço registrado no pedido, que pode diferir do cadastro do cliente.
- `items` é o array com três elementos. O índice `0` é a posição do primeiro item, não o código do produto.
- `items[0].product._id` é 11; seu nome é Queso Cabrales e sua categoria é Dairy Products.
- `items[0].unit_price` é o decimal 14,00; `quantity` é 12 e `discount` é 0.
- O total dos itens é `14 × 12 + 9,80 × 10 + 34,80 × 5 = 440,00`. O frete de 32,38 está separado.

A frase para explicar: **“O pedido e seus itens estavam em duas tabelas; eu agrupei os itens em um array dentro do pedido porque eles são consultados juntos.”**

O cliente não foi copiado inteiro: `customer_id` continua sendo uma referência. Para ver seu cadastro, abra `customers` e filtre `{ _id: "VINET" }`. Para estudar outro aninhamento, abra `employees`, filtre `{ _id: 1 }` e expanda `territories`.

## 5. Gerar os documentos com SQL

O arquivo `sql/entrega02/01_exportar_documentos.sql` é o script completo. Ele usa `jsonb_build_object` para montar objetos e `jsonb_agg` para agrupar itens. As funções temporárias marcam dinheiro, inteiros e datas como Extended JSON.

Execute no terminal WSL, **a partir da raiz do projeto**. O bloco usa `set -e`, para interromper se ocorrer um erro, e grava primeiro em arquivo temporário, preservando uma exportação anterior se a consulta falhar:

```bash
set -e
mkdir -p mongo/entrega02/dados
docker compose exec -T postgres psql -X -qAt -v ON_ERROR_STOP=1 \
  -U pi -d northwind -f /sql/entrega02/01_exportar_documentos.sql \
  > mongo/entrega02/dados/documentos.ejson.tmp
mv mongo/entrega02/dados/documentos.ejson.tmp mongo/entrega02/dados/documentos.ejson
```

O arquivo é uma fotografia das nove coleções. A transação REPEATABLE READ mantém a mesma visão de origem durante a extração. Evite editar `nw` entre a extração e a conferência, pois o objetivo é comparar a mesma versão dos dados. O script cria apenas funções temporárias no PostgreSQL; não altera as tabelas de `nw`.

Os parâmetros `-qAt` retiram cabeçalhos e mensagens de formatação do resultado; `ON_ERROR_STOP=1` faz o psql retornar erro se uma instrução falhar. `>` salva a saída em um arquivo. O `mv` publica o arquivo somente depois do sucesso.

## 6. Carregar e criar índices pelo mongosh

```bash
docker compose exec -T mongo mongosh -u pi -p pi \
  --authenticationDatabase admin --quiet \
  --file /mongo/entrega02/02_carregar.js

docker compose exec -T mongo mongosh -u pi -p pi \
  --authenticationDatabase admin --quiet \
  --file /mongo/entrega02/03_indices.js
```

O primeiro script carrega `01_modelo.js`, interpreta os tipos com `EJSON.parse` e grava com `replaceOne` e `upsert`. A identidade não muda: pedido 10248 continua sendo `_id: 10248`. Repetir o mesmo arquivo não cria um novo pedido.

O script mostra, por coleção, documentos existentes, inseridos e modificados. Como a carga já foi executada, é normal ver **zero inseridos e zero modificados**. Os índices também podem ser criados novamente com a mesma definição.

Uma origem com identificadores removidos ou uma coleção vazia é recusada antes da gravação para revisão. Esta entrega não implementa exclusão automática. Uma falha depois do início das escritas pode deixar carga parcial: corrija o erro, repita o **mesmo arquivo completo** e confira antes de usar os dados.

## 7. Conferir estrutura, totais e plano

```bash
docker compose exec -T mongo mongosh -u pi -p pi \
  --authenticationDatabase admin --quiet \
  --file /mongo/entrega02/05_verificar.js
```

Esperado: `PASSOU` para estruturas, referências e cópias; **2.155 itens**; soma decimal exata **1265793.03950**; consulta VINET/1996 com índice `cliente_data`, **3 documentos examinados e 3 retornados**. O script também mostra os índices e o pedido 10248.

No Compass, abra a aba **Indexes** de `orders`: confira `_id_`, `cliente_data` e `produto_no_pedido`. Em `products`, confira `_id_` e `categoria_produto`.

Para consultar pelo produto dentro do array, use em **Filter**:

```javascript
{ "items.product._id": 11 }
```

Para cliente e período:

```javascript
{
  customer_id: "VINET",
  order_date: {
    $gte: ISODate("1996-01-01T00:00:00Z"),
    $lt: ISODate("1997-01-01T00:00:00Z")
  }
}
```

Abra as opções da consulta e use **Sort** `{ order_date: 1 }`. A opção **Explain Plan**, quando disponível, mostra o plano de execução. O caminho alternativo, confirmado por execução, é o script mongosh acima. `IXSCAN` significa leitura de índice; `FETCH`, busca dos documentos encontrados. Essa evidência vale para esta consulta e não é um comparativo de velocidade entre bancos.

## 8. Comparar todos os campos com o PostgreSQL

Não basta contar pedidos: uma carga poderia manter 830 documentos e alterar um preço. O roteiro abaixo exporta os documentos realmente gravados, reconstrói as 11 tabelas e compara linhas e campos nos dois sentidos.

```bash
set -e
mkdir -p apresentacao/evidencias/entrega02
docker compose exec -T mongo mongosh -u pi -p pi \
  --authenticationDatabase admin --quiet \
  --file /mongo/entrega02/04_exportar_conferencia.js \
  > apresentacao/evidencias/entrega02/retorno.json.tmp
mv apresentacao/evidencias/entrega02/retorno.json.tmp apresentacao/evidencias/entrega02/retorno.json

docker cp apresentacao/evidencias/entrega02/retorno.json pi-postgres:/tmp/retorno.json

docker compose exec -T postgres psql -X -v ON_ERROR_STOP=1 \
  -U pi -d northwind -f /sql/entrega02/02_conferir_retorno.sql
```

Esperado: **3.311 linhas na origem, 3.311 linhas reconstruídas e zero divergências**. `EXCEPT ALL` encontra diferenças entre os conjuntos, incluindo repetições. O script não arredonda preços e descontos antes de comparar. Também não preenche nulos com valores inventados.

Esse caminho é independente do SQL que montou os documentos, mas usa o mesmo contrato de campos; é uma conferência de integridade da migração, não uma prova de todas as regras futuras de negócio.

Para comprovar repetição, execute novamente o passo 6 (carga) e depois os passos 7–8. Esperado: nenhum documento novo ou modificado, e zero divergências.

## 9. Testar a proteção contra dados inválidos

Este teste é opcional para a demonstração, mas já foi executado como evidência:

```bash
docker compose exec -T mongo mongosh -u pi -p pi \
  --authenticationDatabase admin --quiet \
  --file /mongo/entrega02/06_testar_validadores.js
```

O script usa exclusivamente a base temporária `northwind_entrega02_teste_validadores`, recusa reutilizá-la se ela já contiver coleções e remove a base que criou ao terminar. Não altera `northwind`.

Ele tenta preço como string, quantidade zero, desconto de 100%, data como string e ausência de shipping. Esperado: **cinco rejeições com código 121** e preservação do documento válido. Isso mostra a diferença entre ter dados atualmente corretos e ter uma regra que rejeita certas alterações inválidas. Referências entre coleções continuam dependendo da conferência; os validadores não são FKs.

## 10. O que entregar e como estudar

O documento cumulativo está em `entregas/entrega-02/Projeto-Integrador-Banco-de-Dados-Entrega-02.docx`. O Word anterior continua em `entregas/entrega-01/`.

Os scripts completos estão em `sql/entrega02/` e `mongo/entrega02/`; as evidências, em `apresentacao/evidencias/entrega02/`. O arquivo `documentos.ejson` é dado gerado, não código de transformação. O pacote da Entrega 2 reúne Word, guia, scripts e evidências, mantendo esses caminhos.

Estude nesta ordem: pedido 10248 → `jsonb_build_object` e `jsonb_agg` → tipos BSON → `replaceOne`/`upsert` → índices → conferência. Você deve conseguir explicar o motivo de cada agrupamento e demonstrar um pedido. As análises extensas das semanas 5–7 ficam para depois.

Fontes técnicas: [Extended JSON](https://www.mongodb.com/docs/manual/reference/mongodb-extended-json/), [validação de schema](https://www.mongodb.com/docs/manual/core/schema-validation/), [índices multikey](https://www.mongodb.com/docs/manual/core/indexes/index-types/index-multikey/), [filtros no Compass](https://www.mongodb.com/docs/compass/query/filter/), [funções JSON do PostgreSQL](https://www.postgresql.org/docs/16/functions-json.html).
