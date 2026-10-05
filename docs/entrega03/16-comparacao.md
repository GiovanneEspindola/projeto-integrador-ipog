# 16. Comparação de sintaxe e complexidade

SQL descreve o resultado desejado a partir de relações entre tabelas. Um pipeline descreve uma sequência de transformações aplicadas aos documentos. Nos dois casos há otimizador, e a ordem escrita não determina todos os detalhes da execução. A equivalência depende das regras de negócio e da granularidade, não apenas dos operadores. A tabela a seguir resume os recursos de cada par; o número de linhas de SQL (sem comentários) e de estágios do pipeline (no nível principal, sem contar os estágios internos de $lookup e $facet) é apenas um indicador auxiliar de tamanho, não de dificuldade.

<!-- comparacao -->

## 16.1 Ranking, ABC e RFM

No ranking, SQL agrega por produto e usa ROW_NUMBER particionado por categoria. MongoDB agrega os itens e usa uma janela com soma cumulativa de 1. Essa escolha preserva a ordenação por valor e ID: no MongoDB 7, $documentNumber exige sortBy com um único campo [17]. O resultado final mantém as mesmas 40 linhas nos dois bancos.

Na curva ABC, a etapa decisiva é acumular o **valor** em ordem decrescente. Dividir clientes em grupos de tamanho igual não responderia à mesma pergunta. A classificação usa o acumulado anterior ao cliente para definir a classe; os dois clientes sem compras ficam identificados separadamente. Em RFM, os dois códigos usam as mesmas faixas fixas e preservam os valores brutos para permitir interpretação além dos escores.

## 16.2 Produtos comprados juntos

SQL relaciona order_items consigo mesma pela chave do pedido e impõe produto_a < produto_b. MongoDB projeta os IDs dos itens, expande as duas listas e aplica a mesma condição. Ela elimina o produto pareado consigo próprio e as duplicações A–B/B–A. A quantidade de pares intermediários cresce com o tamanho do pedido, tornando a análise sensível à expansão dos arrays.

O denominador do suporte é a quantidade de pedidos do período, inclusive pedidos que não geram pares. O par mais frequente aparece em apenas oito de 830 pedidos. Frequência conjunta não comprova efeito causal nem eficácia de uma promoção.

## 16.3 Hierarquia e equipe

A CTE recursiva de PostgreSQL percorre funcionários subordinados. O $graphLookup faz o percurso equivalente pelos documentos de employees. Agregar os pedidos por funcionário antes de combinar com a equipe reduz a quantidade de registros intermediários. A cópia SQL impede repetição no caminho; a hierarquia original foi conferida sem ciclos.

Cada equipe inclui seu responsável. Equipes de gestores diferentes podem se sobrepor: o total do gestor máximo contém as vendas de subordinados que também aparecem em outras linhas. Somar a coluna de todas as equipes contaria vendas mais de uma vez.

## 16.4 Efeito da modelagem

O documento de pedido já reúne itens, nomes de produtos e categorias; isso simplifica algumas leituras. A cópia dos nomes exige manutenção quando o cadastro muda. Consultas iniciadas por customers para incluir clientes sem pedidos usam $lookup; consultas de hierarquia usam relações entre documentos. A incorporação não elimina toda necessidade de junção.

No SQL, as chaves e restrições explicitam a integridade entre tabelas. MongoDB usa validadores para a estrutura de cada documento e verificações separadas para referências e cópias. Legibilidade, consistência e manutenção devem ser avaliadas junto com o tempo observado, sem assumir um vencedor por paradigma.
