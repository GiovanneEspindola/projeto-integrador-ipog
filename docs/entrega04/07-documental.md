# 7. Modelo documental

No MongoDB, a pergunta central de modelagem é o que deve ficar junto. A regra adotada foi: **incorporar o que pertence ao pedido e é lido com ele; referenciar o que existe por conta própria** [5].

| Coleção | Documentos | Conteúdo |
|---|---|---|
| orders | 830 | Pedido com datas, frete, endereço de envio (objeto shipping) e array items com os itens |
| products | 77 | Produto com estoque, categoria e fornecedor (id e nome) |
| customers | 91 | Cliente com endereço agrupado em objeto |
| employees | 9 | Funcionário, referência ao superior e array de territórios |
| categories, suppliers, shippers | 8, 29, 6 | Cadastros completos, inclusive sem movimento |
| territories, regions | 53, 4 | Malha comercial completa |

As 3.311 linhas viraram **1.107 documentos** porque duas tabelas deixaram de existir como coleção: os 2.155 itens foram para dentro dos pedidos e os 49 vínculos de território, para dentro dos funcionários (3.311 − 2.155 − 49 = 1.107).

## 7.1 O que foi incorporado e o que foi referenciado

**Itens dentro do pedido.** Um item não existe sem o pedido e quase sempre é lido com ele. Incorporar elimina a junção mais frequente das análises.

**Clientes, produtos e funcionários em coleções próprias.** Eles existem independentemente de uma venda e aparecem em muitos pedidos. Os pedidos guardam apenas o identificador, como customer_id e employee_id. Colocar os pedidos dentro do cliente criaria um array que cresce sem limite.

**Cópias de leitura.** Cada item guarda o id, o nome e a categoria do produto. Isso deixa o pedido legível sem consultar products, ao custo de atualizar as cópias quando o cadastro mudar. Essas cópias refletem o cadastro no momento da carga; o preço e o endereço, ao contrário, vêm da própria venda.

## 7.2 O pedido 10248 nos dois modelos

No PostgreSQL, o pedido 10248 ocupa uma linha em orders e três em order_items. No MongoDB, é um único documento (abaixo, com o primeiro dos três itens):

```javascript
{
  _id: 10248,
  customer_id: "VINET",
  order_date: ISODate("1996-07-04T00:00:00Z"),
  freight: Decimal128("32.38"),
  shipping: {
    name: "Vins et alcools Chevalier",
    street: "59 rue de l'Abbaye",
    city: "Reims", region: null,
    postal_code: "51100", country: "France"
  },
  items: [{
    product: {
      _id: 11, name: "Queso Cabrales",
      category: { _id: 4, name: "Dairy Products" }
    },
    unit_price: Decimal128("14.00"),
    quantity: 12, discount: Decimal128("0.000")
  }]
}
```

Os três itens valem 168,00 + 98,00 + 174,00 = **440,00**, sem o frete de 32,38.

## 7.3 Tipos

Identificadores e quantidades são inteiros; códigos de cliente e território continuam texto. Preços, descontos e frete usam **Decimal128**, o tipo decimal exato do MongoDB [6], para que nenhum valor passe por ponto flutuante. As datas viraram BSON Date à meia-noite UTC, já que o PostgreSQL guarda só o dia. Campos sem valor ficaram como null, e não ausentes, para que as consultas tratem os dois bancos da mesma forma.
