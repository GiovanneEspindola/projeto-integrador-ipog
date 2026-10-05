# 7. Modelagem documental

## 7.1 Organização das coleções

A modelagem documental foi desenvolvida a partir das 11 tabelas do schema **nw**, preservando seus atributos, identificadores e relacionamentos. Os dados foram reorganizados em nove coleções no MongoDB. O principal agrupamento ocorreu entre pedidos e itens: o cabeçalho e os produtos vendidos passaram a compor um único documento por pedido.

| Coleção | Documentos | Organização dos dados |
|---|---|---|
| orders | 830 | Pedido com datas, frete, referências a cliente, funcionário e transportadora, endereço shipping e array items. |
| products | 77 | Produto com preço de catálogo, estoque, categoria e fornecedor identificados e nomeados. |
| customers | 91 | Cadastro do cliente com informações de contato e endereço agrupado em objeto. |
| employees | 9 | Cadastro do funcionário, endereço, referência ao superior e array de territórios. |
| categories | 8 | Identificador, nome e descrição da categoria. |
| suppliers | 29 | Cadastro do fornecedor com contato e endereço agrupado em objeto. |
| shippers | 6 | Identificador, nome e telefone da transportadora. |
| territories | 53 | Identificador e nome do território, com referência à região. |
| regions | 4 | Identificador e nome da região comercial. |

Foram obtidos **1.107 documentos**. A diferença em relação às 3.311 linhas relacionais decorre da incorporação dos 2.155 itens nos pedidos e dos 49 vínculos de território nos funcionários. Os cadastros sem movimento foram mantidos, incluindo clientes sem compra e transportadoras sem pedido associado.

## 7.2 Incorporação e referências

Os itens foram incorporados porque pertencem a um pedido e são consultados junto com ele. O endereço de envio também foi agrupado no pedido, preservando a informação registrada na venda. Essa decisão considera as diferenças de endereço identificadas na análise exploratória e evita substituí-lo pelo cadastro atual do cliente.

Produtos, clientes, funcionários e transportadoras permaneceram em coleções próprias, pois participam de vários pedidos e possuem atributos independentes de uma venda. Seus identificadores estabelecem as referências entre documentos. A organização combina incorporação e referências conforme as formas de acesso aos dados [5].

Nos funcionários, o array territories reúne os territórios de atuação, enquanto reports_to conserva a referência ao superior. As coleções territories e regions preservam a malha comercial completa, incluindo territórios sem funcionário vinculado. Os pedidos foram mantidos em coleção própria, evitando um array crescente de compras no cadastro de cada cliente.

<!-- page -->

# 7. Modelagem documental — estrutura do pedido

## 7.3 Representação do pedido 10248

O pedido 10248 pertence ao cliente VINET e contém três produtos. No modelo relacional, seus dados estão distribuídos entre orders e order_items. No MongoDB, o endereço de envio e os itens estão incorporados ao documento do pedido. O trecho abaixo apresenta os campos principais e o primeiro item; os demais itens foram omitidos somente desta representação.

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

Os três produtos são 11, 42 e 72, com quantidades 12, 10 e 5 e preços praticados de 14,00, 9,80 e 34,80. O valor dos itens é **440,00**, sem incluir o frete de 32,38. Os preços foram obtidos dos itens da venda, preservando a diferença em relação ao preço de catálogo.

O nome do produto e sua categoria foram copiados para os itens a partir dos cadastros disponíveis na extração. Essas informações facilitam a leitura do pedido, mas não constituem histórico do catálogo na data da venda. Uma atualização cadastral exige nova carga para atualizar as cópias.

## 7.4 Tipos e valores ausentes

Os identificadores numéricos e as quantidades foram armazenados como **Int32**. Os códigos de clientes e territórios permaneceram como **strings**, preservando possíveis zeros à esquerda. Preços, descontos e frete foram armazenados como **Decimal128**, e valores SQL NULL foram mantidos como **null**.

As datas foram convertidas para **BSON Date à meia-noite UTC**, conservando o dia registrado na origem. Esse horário é uma convenção de representação, pois o tipo date do PostgreSQL não registra a hora do evento. Campos opcionais, como região, CEP e data de envio, permaneceram presentes nos documentos, admitindo null conforme a origem.
