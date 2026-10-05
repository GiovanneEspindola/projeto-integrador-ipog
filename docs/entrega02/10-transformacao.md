# 8. Transformação e carga dos dados

## 8.1 Agrupamento dos registros relacionais

A extração foi realizada no PostgreSQL em uma transação **REPEATABLE READ**, mantendo a mesma visão da origem durante a leitura das coleções. Os documentos foram construídos com funções JSON, sem alterações nos registros de nw. A operação central consistiu em agrupar as linhas de order_items pelo identificador do pedido.

**Consulta 9 — Agrupamento dos itens do pedido 10248.**

```sql
SELECT o.order_id,
       jsonb_agg(jsonb_build_object(
         'product_id', i.product_id,
         'unit_price', i.unit_price,
         'quantity', i.quantity,
         'discount', i.discount
       ) ORDER BY i.product_id) AS items
FROM nw.orders o
JOIN nw.order_items i USING (order_id)
WHERE o.order_id = 10248
GROUP BY o.order_id;
```

A consulta retorna uma linha para o pedido, com seus três itens no array items. O conteúdo obtido é apresentado abaixo, com quebras de linha para facilitar a leitura.

```json
{
  "order_id": 10248,
  "items": [
    {"product_id": 11, "unit_price": 14.00,
     "quantity": 12, "discount": 0.000},
    {"product_id": 42, "unit_price": 9.80,
     "quantity": 10, "discount": 0.000},
    {"product_id": 72, "unit_price": 34.80,
     "quantity": 5, "discount": 0.000}
  ]
}
```

A função **jsonb_build_object** formou os campos de cada item, e **jsonb_agg** reuniu os registros em um array ordenado por produto [12]. Na transformação completa, cada pedido recebeu também suas datas, frete, referências e endereço de envio. Os itens receberam o identificador e o nome do produto, além da categoria aninhada.

O mesmo princípio foi aplicado aos vínculos de território: os registros da relação entre funcionário e território foram agrupados por employee_id e incorporados ao funcionário. Os demais cadastros deram origem a documentos individuais em suas respectivas coleções.

<!-- page -->

# 8. Transformação — tipos e gravação

## 8.2 Preservação dos tipos BSON

O transporte utilizou **Extended JSON**, que permite representar tipos BSON não diferenciados pelo JSON comum [9]. Os valores monetários foram convertidos de numeric para uma representação decimal textual e interpretados como Decimal128 no MongoDB, sem passagem por ponto flutuante.

O preço 14,00 foi representado da seguinte forma:

```json
{"$numberDecimal": "14.00"}
```

A leitura com **EJSON.parse**, configurada com relaxed: false, converteu os marcadores de decimais, inteiros e datas nos respectivos tipos BSON. As funções JSON do PostgreSQL preservaram os caracteres de nomes e endereços, incluindo apóstrofos, e mantiveram os valores nulos.

## 8.3 Gravação por identificador

A carga foi executada pelo mongosh, utilizando operações de substituição agrupadas em bulkWrite. Cada documento conservou o identificador da origem no campo _id. O comando abaixo apresenta a operação aplicada aos pedidos, em que documento representa o registro completo produzido na transformação.

```javascript
db.orders.replaceOne(
  { _id: documento._id },
  documento,
  { upsert: true }
);
```

A opção **upsert** insere o documento quando o identificador ainda não existe. Quando existe, **replaceOne** substitui seu conteúdo, incluindo os objetos e arrays aninhados. Essa estratégia permite repetir a carga sem criar novos identificadores para os mesmos registros.

| Execução | Documentos inseridos | Documentos modificados |
|---|---|---|
| Primeira carga | 1.107 | 0 |
| Repetição da mesma carga | 0 | 0 |

O resultado da segunda execução confirmou a estabilidade da carga para o mesmo conjunto de dados. Alterações na origem exigem nova extração. A atualização é feita em lote, e identificadores existentes no destino que não aparecem na extração provocam interrupção antes das escritas, para revisão. Não foi adotada propagação automática de exclusões.

## 8.4 Limites da carga

O MongoDB foi utilizado em modo **standalone**, com atomicidade por documento, mas sem transação única envolvendo todas as coleções [8]. Uma interrupção durante a gravação pode deixar o lote incompleto. A recuperação adotada consiste na repetição integral da carga após corrigir a causa, seguida de nova conferência de integridade.

A rotina foi desenvolvida para o conjunto pequeno e estático do Northwind. Os documentos são lidos em memória, e coleções vazias são recusadas para revisão. A implementação não foi avaliada como mecanismo de sincronização contínua ou de migração de grandes volumes.

<!-- page -->

# 8. Validação da estrutura documental

## 8.5 Regras implementadas

As nove coleções receberam validadores de estrutura, aplicados também aos objetos e arrays aninhados. Foram definidos os campos obrigatórios, os tipos BSON e as faixas de valores. A validação foi configurada para rejeitar inserções e alterações incompatíveis com as regras [7].

| Campo ou grupo | Regra adotada |
|---|---|
| Preços e frete | Decimal128, com valor maior ou igual a zero. |
| Quantidade do item | Inteiro, com valor maior ou igual a um. |
| Desconto do item | Decimal128, maior ou igual a zero e menor que um. |
| Datas | BSON Date; data de envio admite null. |
| Endereço de envio | Objeto obrigatório, com destinatário, logradouro, cidade, região, CEP e país; região e CEP admitem null. |
| Itens do pedido | Array de objetos com produto, categoria, preço praticado, quantidade e desconto. |

O trecho a seguir apresenta a regra aplicada ao desconto dos itens, incluindo tipo, limites e exclusão do limite superior.

```javascript
discount: {
  bsonType: "decimal",
  minimum: Decimal128("0"),
  maximum: Decimal128("1"),
  exclusiveMaximum: true
}
```

## 8.6 Testes de rejeição

Foram realizadas cinco tentativas de substituição de um pedido válido em uma base temporária isolada. Cada tentativa alterou apenas o aspecto indicado na tabela.

| Alteração testada | Resultado |
|---|---|
| Preço armazenado como texto | Rejeitada: código 121. |
| Quantidade igual a zero | Rejeitada: código 121. |
| Desconto igual a 100% | Rejeitada: código 121. |
| Data do pedido armazenada como texto | Rejeitada: código 121. |
| Ausência do objeto de endereço de envio | Rejeitada: código 121. |

Todas as alterações foram rejeitadas, e o documento válido permaneceu inalterado. O resultado demonstra a atuação dos validadores diante das inconsistências testadas, além da constatação de que os documentos carregados atendiam às regras.

Os validadores não substituem as chaves estrangeiras nem reproduzem todas as restrições do modelo relacional. A existência dos cadastros referenciados, a coerência temporal e a ausência de produtos repetidos dentro de um pedido foram verificadas separadamente, após a carga.
