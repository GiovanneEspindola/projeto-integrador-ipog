# 8. Transformação, carga e validação dos documentos

## 8.1 Do relacional ao documento

Os documentos foram montados no próprio PostgreSQL, com funções JSON, numa transação REPEATABLE READ para que todas as tabelas fossem lidas no mesmo instante. A operação central agrupa os itens de cada pedido num array.

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

Na transformação completa, cada pedido recebe também datas, frete, endereço e os dados de leitura do produto. Os territórios dos funcionários seguem a mesma lógica. Os valores decimais viajam em Extended JSON, como {"$numberDecimal": "14.00"}, e chegam ao MongoDB já como Decimal128.

## 8.2 Carga repetível

O mongosh grava os documentos com substituição por identificador:

```javascript
db.orders.replaceOne(
  { _id: documento._id },
  documento,
  { upsert: true }
);
```

Se o documento não existe, ele é inserido; se existe, é substituído por inteiro. Rodar a carga duas vezes não duplica nada:

| Execução | Inseridos | Modificados |
|---|---|---|
| Primeira carga | 1.107 | 0 |
| Repetição | 0 | 0 |

Se a origem perder um registro que ainda existe no MongoDB, a carga para antes de gravar, para revisão. O MongoDB roda em modo standalone, sem transação que envolva todas as coleções; se a carga for interrompida, a recuperação é repeti-la inteira e conferir de novo.

## 8.3 Validadores

Sem regras, o MongoDB aceitaria um preço em texto ou uma quantidade zero. As nove coleções receberam validadores JSON Schema, inclusive para objetos e arrays aninhados.

| Campo | Regra |
|---|---|
| Preços e frete | Decimal128, maior ou igual a zero |
| Quantidade | Inteiro, maior ou igual a um |
| Desconto | Decimal128, de zero a menos de um |
| Datas | BSON Date; data de envio admite null |
| Endereço de envio | Objeto obrigatório com os seis campos |
| Itens | Array de objetos com produto, preço, quantidade e desconto |

```javascript
discount: {
  bsonType: "decimal",
  minimum: Decimal128("0"),
  maximum: Decimal128("1"),
  exclusiveMaximum: true
}
```

Cinco alterações inválidas foram testadas numa base isolada: preço como texto, quantidade zero, desconto de 100%, data como texto e pedido sem endereço. **As cinco foram rejeitadas** (erro 121) e o documento original ficou intacto.

O validador confere a forma do documento, mas não sabe se o customer_id existe em customers. Essa checagem, que no PostgreSQL é feita pela chave estrangeira, foi feita por consulta depois da carga.
