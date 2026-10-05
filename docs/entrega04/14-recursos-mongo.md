# 14. Recursos próprios do MongoDB e MapReduce

Além dos 16 pipelines, três consultas mostram recursos que dependem da estrutura em documento.

**Condições no mesmo item ($elemMatch).** A pergunta é: quais pedidos têm um item do produto 11, com pelo menos 10 unidades e algum desconto? Com $elemMatch, as três condições precisam valer para o mesmo item do array. Escritas separadamente, cada condição pode ser atendida por um item diferente do mesmo pedido.

**Valor do pedido sem desmontá-lo ($map e $reduce).** O $reduce soma os itens dentro do documento e o $map extrai os nomes dos produtos, sem transformar o pedido em várias linhas.

**Várias respostas numa consulta ($facet).** Uma única consulta sobre os pedidos de 1997 devolve o volume, a situação da data de envio e a distribuição por quantidade de itens.

<!-- recursos -->

## 14.1 MapReduce

O MapReduce somou a quantidade vendida de cada produto. A função map emite o par (produto, quantidade) para cada item, e a função reduce soma as quantidades de cada produto. O resultado foi comparado automaticamente com um pipeline de $unwind e $group: **77 produtos, 51.317 unidades e todos os totais iguais**.

```javascript
map: function () {
  this.items.forEach(function (i) { emit(i.product._id, i.quantity); });
},
reduce: function (produto, quantidades) { return Array.sum(quantidades); }
```

O MapReduce está depreciado desde o MongoDB 5.0, e a documentação recomenda pipelines para novos desenvolvimentos [7]. Ele foi implementado porque a disciplina o pede, e a comparação mostra que o pipeline equivalente é mais curto e mais legível. A demonstração usa só quantidades inteiras, para não passar dinheiro por números de ponto flutuante do JavaScript.
