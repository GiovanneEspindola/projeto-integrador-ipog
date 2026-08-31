-- =============================================================================
-- 30_indexes.sql — índices do schema nw
-- =============================================================================
-- Regra que este arquivo segue: NENHUM índice entra sem EXPLAIN provando que o
-- planejador o escolhe. Nove candidatos foram testados; quatro entraram.
-- Os cinco recusados estão no fim do arquivo, com o motivo medido — porque
-- saber quando NÃO criar índice vale tanto quanto saber criar.
--
-- O contexto que explica quase tudo: a base é minúscula. A maior tabela,
-- orders, ocupa 15 páginas de 8 kB. Varrer 15 páginas é barato, então o
-- planejador só troca a varredura por índice quando o filtro é bem seletivo.
--
-- Evidência: apresentacao/evidencias/04-indices-explain.txt
--   docker compose exec -T postgres psql -U pi -d northwind -f /sql/30_indexes.sql
-- =============================================================================

SET search_path TO nw;

-- 1. Pedidos de um cliente — perguntas 06, 10, 11 (inatividade, curva ABC, RFM)
-- 89 clientes distintos em 830 pedidos: ~9 linhas por cliente. Filtro seletivo.
-- EXPLAIN: Bitmap Index Scan.
CREATE INDEX IF NOT EXISTS orders_customer_idx ON orders (customer_id);

-- 2. Pedidos de um vendedor — perguntas 04 e 15 (faturamento por vendedor e por equipe)
-- Só 9 valores distintos, ~92 linhas cada: seletividade baixa, e mesmo assim o
-- planejador prefere o índice. Foi testado justamente por ser o caso duvidoso.
-- EXPLAIN: Bitmap Index Scan.
CREATE INDEX IF NOT EXISTS orders_employee_idx ON orders (employee_id);

-- 3. Pedidos por período — perguntas 02, 08, 09, 16 (mensal, acumulado, sazonalidade)
-- O melhor caso dos quatro: como a consulta só precisa da data, o PostgreSQL
-- responde sem tocar na tabela.
-- EXPLAIN: Index Only Scan.
CREATE INDEX IF NOT EXISTS orders_date_idx ON orders (order_date);

-- 4. Itens de um produto — perguntas 01, 07, 12 (faturamento por categoria, ranking, cesta)
-- A PK de order_items é (order_id, product_id). Índice composto só serve para
-- busca que começa pela primeira coluna, então a PK atende "itens do pedido X"
-- mas não atende "vendas do produto Y". Daí este índice existir e o de
-- order_id NÃO existir.
-- EXPLAIN: Bitmap Index Scan.
CREATE INDEX IF NOT EXISTS order_items_product_idx ON order_items (product_id);

ANALYZE;

COMMENT ON INDEX orders_customer_idx     IS 'Pedidos de um cliente. ~9 linhas por valor: seletivo.';
COMMENT ON INDEX orders_employee_idx     IS 'Pedidos de um vendedor. ~92 linhas por valor: pouco seletivo, mas o planejador usa.';
COMMENT ON INDEX orders_date_idx         IS 'Pedidos por período. Permite Index Only Scan em contagens por data.';
COMMENT ON INDEX order_items_product_idx IS 'Vendas de um produto. A PK composta não cobre esta busca, porque product_id não é a primeira coluna dela.';

-- =============================================================================
-- Os cinco candidatos recusados, e a medição que os recusou
-- =============================================================================
--
-- order_items (order_id)
--   Recusado por REDUNDÂNCIA. A PK (order_id, product_id) já começa por
--   order_id, então ela própria atende a busca.
--   EXPLAIN: "Index Scan using order_items_pk".
--
-- orders (customer_id, order_date)  -- índice composto
--   Recusado por INUTILIDADE MEDIDA. Foi criado para a consulta "últimos
--   pedidos do cliente X ordenados por data", que é o caso clássico dele.
--   O planejador ignorou e preferiu ler orders_date_idx de trás para frente.
--   O plano ficou idêntico com e sem ele.
--
-- products (category_id), territories (region_id),
-- employee_territories (territory_id)
--   Recusados por TAMANHO. Essas tabelas ocupam UMA página de 8 kB. Ler a
--   página inteira custa um acesso; ler o índice e depois buscar na tabela
--   custa dois. O planejador escolheu Seq Scan em todos os testes.
--   Criá-los seria custo de escrita e de espaço sem nenhum retorno.
--
-- products (supplier_id)
--   Recusado por DOIS motivos somados, e o primeiro é o interessante:
--   a constraint UNIQUE (supplier_id, product_name) de 10_ddl.sql JÁ CRIA um
--   índice, e supplier_id é a primeira coluna dele — criar outro seria
--   duplicata. Toda UNIQUE vem com índice embutido, e vale conferir o que já
--   se tem antes de criar mais um.
--   O segundo motivo é o de sempre: com a tabela em uma página, o planejador
--   nem esse índice de brinde usa. EXPLAIN devolve Seq Scan.
--
-- Um caso de fronteira, registrado para não parecer descuido:
--   employee_territories.territory_id tem ON DELETE CASCADE e NÃO tem índice.
--   Apagar um território faz varredura sequencial para achar os filhos a
--   cascatear. Em 49 linhas de uma página isso é irrelevante, e vale o mesmo
--   raciocínio de tamanho acima — mas em tabela grande um CASCADE sem índice
--   de apoio é problema clássico de desempenho.
--
-- Nota honesta para a defesa: em produção, com milhões de pedidos, três desses
-- cinco provavelmente passariam a valer a pena. A decisão aqui vale para ESTE
-- volume, e está registrada assim de propósito.
