# 5. Arquitetura híbrida

A exploração mostrou dois tipos de necessidade. Para registrar vendas, a base precisa de regras rígidas: preço não negativo, desconto abaixo de 100%, item ligado a um pedido existente. Para ler um pedido completo, o ideal é ter tudo num só lugar. O projeto testa as duas formas lado a lado, com um fluxo de mão única.

<!-- image:apresentacao/evidencias/entrega04/arquitetura.png -->

Figura 2 — Fluxo de dados do projeto.

O schema **public** guarda a base original sem alterações. O schema **nw** é o modelo relacional do projeto e funciona como fonte da verdade. A partir dele, uma extração em SQL gera os documentos, que o mongosh carrega no MongoDB. O MongoDB não recebe escritas diretas: é uma cópia orientada à leitura, reconstruída a partir do PostgreSQL quando necessário.

A mão única evita que o mesmo dado tenha dois donos. Se os dois bancos aceitassem alterações, seria preciso decidir qual vale em caso de conflito. A carga em lote, e não em tempo real, é suficiente porque nenhuma das perguntas do projeto depende de dados atualizados ao segundo.
