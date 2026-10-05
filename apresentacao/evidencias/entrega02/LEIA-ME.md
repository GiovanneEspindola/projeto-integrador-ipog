# Evidências da semana 4

Executadas em 10/09/2026 sobre o schema `nw` e a base MongoDB `northwind` do projeto local. A fonte foi preservada. Os bancos usam volumes Docker existentes; não houve reconstrução do schema relacional.

| Arquivo | O que demonstra |
|---|---|
| carga-01.txt | Primeira carga: 1.107 documentos inseridos nas nove coleções. |
| carga-02.txt | Repetição do mesmo arquivo: zero inserções e modificações. |
| conferencia-01.txt | Conferência inicial: 3.311 linhas reconstruídas, zero diferenças. |
| conferencia-02.txt | Conferência após repetição, já com comparação decimal sem escala fixa. |
| conferencia-final.txt | Conferência final após reinicialização: zero diferenças com a versão final dos scripts. |
| mongo-verificacao.txt | Tipos, referências, cópias, total exato, plano cliente_data e pedido 10248. |
| teste-validadores.txt | Cinco dados inválidos rejeitados em base temporária; documento válido preservado. |
| teste-conferencia-negativa.txt | Um retorno adulterado com preço 14.004 foi rejeitado. O erro registrado é o resultado esperado deste teste. |
| retorno.json | Linhas reconstruídas a partir do MongoDB efetivamente gravado. |
| ambiente.txt | Versões consultadas e momento da conferência final. |
| entrega01-preservada.sha256 | Hash do Word anterior; conferido novamente após a criação da Entrega 2. |
| scripts.sha256 | Hashes da versão final dos scripts e do arquivo de carga. |

O teste negativo alterou somente uma cópia do arquivo de retorno; não alterou nenhum registro de PostgreSQL ou MongoDB. O arquivo válido foi recolocado no container e a comparação final passou.

Na revisão independente foi identificado que converter o retorno usando o tipo de linha de `nw` arredondaria preços antes de compará-los. A versão final compara JSON campo a campo e converte os valores monetários para numeric sem escala fixa. O retorno também rejeita datas com horário diferente de meia-noite UTC. As evidências inicial e final são distinguidas na tabela acima para conservar o histórico de verificação.

Limites: a equivalência corresponde a esta fotografia de `nw`. Os validadores não implementam FKs nem todas as constraints SQL; as referências e cópias são conferidas separadamente. Somente o índice cliente_data teve plano observado nesta etapa. Não houve benchmark comparativo, sincronização contínua ou teste de escala.

Depois de reiniciar o computador, o bind mount de `/mongo` ficou vazio. O container MongoDB foi recriado com o mesmo volume `pi-bd_mongodata`; a contagem e a comparação final confirmaram a persistência dos dados.

O computer use falhou com `sandboxCwd is not a local file URI` antes de inspecionar qualquer janela. A falha persistiu após reiniciar o conector e após reiniciar o computador. Logo, estas evidências confirmam a conexão por mongosh e os dados; não confirmam a conexão salva nem a navegação do Compass.
