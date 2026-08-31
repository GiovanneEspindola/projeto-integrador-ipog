-- =============================================================================
-- 10_ddl.sql — schema nw: o modelo relacional do projeto
-- =============================================================================
-- O schema public guarda o Northwind original, intocado, como fonte.
-- O schema nw é o modelo deste projeto: tipos corrigidos, regras de negócio
-- explícitas e cada objeto comentado.
--
-- Cada bloco abaixo responde a uma fraqueza medida e documentada em
-- docs/01-analise-negocio.md §4. As decisões estão justificadas em
-- docs/04-modelo-relacional.md.
--
-- Idempotente: recria o schema do zero a cada execução.
--   docker compose exec -T postgres psql -U pi -d northwind -f /sql/10_ddl.sql
-- =============================================================================

DROP SCHEMA IF EXISTS nw CASCADE;
CREATE SCHEMA nw;

SET search_path TO nw;

-- -----------------------------------------------------------------------------
-- REGIÃO e TERRITÓRIO — a malha comercial
-- -----------------------------------------------------------------------------

CREATE TABLE regions (
    region_id     integer      PRIMARY KEY,
    region_name   varchar(60)  NOT NULL,

    CONSTRAINT regions_name_unica    UNIQUE (region_name),
    CONSTRAINT regions_name_nao_vazio CHECK (btrim(region_name) <> '')
);

CREATE TABLE territories (
    territory_id    varchar(20) PRIMARY KEY,
    territory_name  varchar(60) NOT NULL,
    region_id       integer     NOT NULL,

    CONSTRAINT territories_region_fk FOREIGN KEY (region_id)
        REFERENCES regions (region_id) ON DELETE RESTRICT,
    CONSTRAINT territories_name_nao_vazio CHECK (btrim(territory_name) <> '')
);

-- -----------------------------------------------------------------------------
-- CATEGORIA, FORNECEDOR, TRANSPORTADORA — os cadastros de apoio
-- -----------------------------------------------------------------------------

CREATE TABLE categories (
    category_id   integer     PRIMARY KEY,
    category_name varchar(15) NOT NULL,
    description   text        NOT NULL,

    CONSTRAINT categories_name_unica UNIQUE (category_name)
);

CREATE TABLE suppliers (
    supplier_id   integer     PRIMARY KEY,
    company_name  varchar(40) NOT NULL,
    contact_name  varchar(30),
    contact_title varchar(30),
    address       varchar(60),
    city          varchar(15),
    region        varchar(15),
    postal_code   varchar(10),
    country       varchar(15),
    phone         varchar(24),
    fax           varchar(24),
    homepage      text,

    CONSTRAINT suppliers_name_nao_vazio CHECK (btrim(company_name) <> '')
);

CREATE TABLE shippers (
    shipper_id   integer     PRIMARY KEY,
    company_name varchar(40) NOT NULL,
    phone        varchar(24),

    CONSTRAINT shippers_name_unica UNIQUE (company_name)
);

-- -----------------------------------------------------------------------------
-- CLIENTE e FUNCIONÁRIO
-- -----------------------------------------------------------------------------

CREATE TABLE customers (
    customer_id   char(5)     PRIMARY KEY,
    company_name  varchar(40) NOT NULL,
    contact_name  varchar(30) NOT NULL,
    contact_title varchar(30),
    address       varchar(60),
    city          varchar(15),
    region        varchar(15),
    postal_code   varchar(10),
    country       varchar(15),
    phone         varchar(24),
    fax           varchar(24),

    CONSTRAINT customers_id_formato   CHECK (customer_id ~ '^[A-Z]{5}$'),
    CONSTRAINT customers_name_nao_vazio CHECK (btrim(company_name) <> '')
);

CREATE TABLE employees (
    employee_id integer     PRIMARY KEY,
    last_name   varchar(20) NOT NULL,
    first_name  varchar(10) NOT NULL,
    title       varchar(30) NOT NULL,
    birth_date  date        NOT NULL,
    hire_date   date        NOT NULL,
    address     varchar(60),
    city        varchar(15),
    region      varchar(15),
    postal_code varchar(10),
    country     varchar(15),
    home_phone  varchar(24),
    extension   varchar(4),
    notes       text,
    reports_to  integer,

    CONSTRAINT employees_chefe_fk FOREIGN KEY (reports_to)
        REFERENCES employees (employee_id) ON DELETE RESTRICT,
    CONSTRAINT employees_nao_chefia_a_si CHECK (reports_to <> employee_id),
    CONSTRAINT employees_admissao_apos_nascimento CHECK (hire_date > birth_date)
);

CREATE TABLE employee_territories (
    employee_id  integer     NOT NULL,
    territory_id varchar(20) NOT NULL,

    CONSTRAINT employee_territories_pk PRIMARY KEY (employee_id, territory_id),
    CONSTRAINT employee_territories_employee_fk FOREIGN KEY (employee_id)
        REFERENCES employees (employee_id) ON DELETE CASCADE,
    CONSTRAINT employee_territories_territory_fk FOREIGN KEY (territory_id)
        REFERENCES territories (territory_id) ON DELETE CASCADE
);

-- -----------------------------------------------------------------------------
-- PRODUTO
-- -----------------------------------------------------------------------------

CREATE TABLE products (
    product_id        integer       PRIMARY KEY,
    product_name      varchar(40)   NOT NULL,
    supplier_id       integer       NOT NULL,
    category_id       integer       NOT NULL,
    quantity_per_unit varchar(20)   NOT NULL,
    unit_price        numeric(10,2) NOT NULL,
    units_in_stock    smallint      NOT NULL DEFAULT 0,
    units_on_order    smallint      NOT NULL DEFAULT 0,
    reorder_level     smallint      NOT NULL DEFAULT 0,
    discontinued      boolean       NOT NULL DEFAULT false,

    CONSTRAINT products_supplier_fk FOREIGN KEY (supplier_id)
        REFERENCES suppliers (supplier_id) ON DELETE RESTRICT,
    CONSTRAINT products_category_fk FOREIGN KEY (category_id)
        REFERENCES categories (category_id) ON DELETE RESTRICT,
    CONSTRAINT products_name_unica     UNIQUE (product_name),
    CONSTRAINT products_preco_positivo CHECK (unit_price > 0),
    CONSTRAINT products_estoque_nao_negativo   CHECK (units_in_stock >= 0),
    CONSTRAINT products_encomenda_nao_negativa CHECK (units_on_order >= 0),
    CONSTRAINT products_reposicao_nao_negativa CHECK (reorder_level  >= 0)
);

-- -----------------------------------------------------------------------------
-- PEDIDO e ITEM DO PEDIDO — o núcleo transacional
-- -----------------------------------------------------------------------------

CREATE TABLE orders (
    order_id         integer       PRIMARY KEY,
    customer_id      char(5)       NOT NULL,
    employee_id      integer       NOT NULL,
    shipper_id       integer       NOT NULL,
    order_date       date          NOT NULL,
    required_date    date          NOT NULL,
    shipped_date     date,
    freight          numeric(10,2) NOT NULL DEFAULT 0,
    ship_name        varchar(40)   NOT NULL,
    ship_address     varchar(60)   NOT NULL,
    ship_city        varchar(15)   NOT NULL,
    ship_region      varchar(15),
    ship_postal_code varchar(10),
    ship_country     varchar(15)   NOT NULL,

    CONSTRAINT orders_customer_fk FOREIGN KEY (customer_id)
        REFERENCES customers (customer_id) ON DELETE RESTRICT,
    CONSTRAINT orders_employee_fk FOREIGN KEY (employee_id)
        REFERENCES employees (employee_id) ON DELETE RESTRICT,
    CONSTRAINT orders_shipper_fk  FOREIGN KEY (shipper_id)
        REFERENCES shippers (shipper_id)   ON DELETE RESTRICT,
    CONSTRAINT orders_frete_nao_negativo CHECK (freight >= 0),
    CONSTRAINT orders_prazo_apos_pedido  CHECK (required_date >= order_date),
    CONSTRAINT orders_envio_apos_pedido  CHECK (shipped_date IS NULL
                                                OR shipped_date >= order_date)
);

CREATE TABLE order_items (
    order_id   integer       NOT NULL,
    product_id integer       NOT NULL,
    unit_price numeric(10,2) NOT NULL,
    quantity   smallint      NOT NULL,
    discount   numeric(4,3)  NOT NULL DEFAULT 0,

    CONSTRAINT order_items_pk PRIMARY KEY (order_id, product_id),
    CONSTRAINT order_items_order_fk FOREIGN KEY (order_id)
        REFERENCES orders (order_id) ON DELETE CASCADE,
    CONSTRAINT order_items_product_fk FOREIGN KEY (product_id)
        REFERENCES products (product_id) ON DELETE RESTRICT,
    CONSTRAINT order_items_preco_positivo     CHECK (unit_price > 0),
    CONSTRAINT order_items_quantidade_positiva CHECK (quantity > 0),
    CONSTRAINT order_items_desconto_valido     CHECK (discount >= 0 AND discount < 1)
);

-- =============================================================================
-- Documentação no próprio banco
-- =============================================================================
-- COMMENT ON grava a explicação dentro do catálogo do PostgreSQL: aparece no
-- \d+ do psql, no pgAdmin e em qualquer ferramenta de engenharia reversa.
-- Comentário em arquivo se perde; comentário no catálogo viaja com o banco.
-- Estão comentadas as 11 tabelas e apenas as colunas cujo nome não se explica.

COMMENT ON SCHEMA nw IS
  'Modelo relacional do projeto. O schema public guarda o Northwind original como fonte imutável; aqui os tipos estão corrigidos e as regras de negócio são explícitas.';

COMMENT ON TABLE regions     IS 'Grandes áreas comerciais que agrupam territórios.';
COMMENT ON TABLE territories IS 'Praças de atuação comercial. Nome não é único: "New York" aparece em dois territórios distintos (10019 e 10038).';
COMMENT ON TABLE categories  IS 'Classificação do catálogo de produtos.';
COMMENT ON TABLE suppliers   IS 'Quem fornece os produtos revendidos.';
COMMENT ON TABLE shippers    IS 'Transportadoras que entregam os pedidos.';
COMMENT ON TABLE customers   IS 'Empresas compradoras. Identificadas por código natural de 5 letras herdado do sistema de origem.';
COMMENT ON TABLE employees   IS 'Equipe de vendas, com hierarquia por auto-relacionamento em reports_to.';
COMMENT ON TABLE employee_territories IS 'Entidade associativa: quais territórios cada funcionário atende.';
COMMENT ON TABLE products    IS 'Catálogo de produtos revendidos.';
COMMENT ON TABLE orders      IS 'Cabeçalho da venda: quem comprou, quem vendeu, quem entrega e para onde.';
COMMENT ON TABLE order_items IS 'Corpo da venda: uma linha por produto vendido. É onde está o dinheiro.';

COMMENT ON COLUMN customers.customer_id IS
  'Chave natural de 5 letras maiúsculas derivada do nome da empresa (ALFKI = Alfreds Futterkiste). Mantida por compatibilidade com a origem; o acoplamento entre identificador e nome está discutido em docs/04.';
COMMENT ON COLUMN employees.reports_to IS
  'Superior imediato. NULL identifica o topo da hierarquia, não ausência de dado.';
COMMENT ON COLUMN products.quantity_per_unit IS
  'Descrição livre da embalagem, ex.: "10 boxes x 20 bags". Texto não consultável: mantido como veio, sem tentar interpretar.';
COMMENT ON COLUMN products.reorder_level IS
  'Estoque mínimo antes de repor. Comparado com units_in_stock responde a pergunta de ruptura de estoque.';
COMMENT ON COLUMN products.discontinued IS
  'Produto fora de linha. Era integer 0/1 na origem; aqui é boolean, que é o que o dado sempre significou.';
COMMENT ON COLUMN orders.shipped_date IS
  'Data de envio. NULL significa pedido ainda não enviado — é informação de negócio, não falta de dado.';
COMMENT ON COLUMN orders.ship_name IS
  'Destinatário da entrega no momento da venda. Coincide com o nome do cliente em 96% dos pedidos, mas os 4% restantes justificam guardar separado.';
COMMENT ON COLUMN orders.freight IS
  'Valor do frete cobrado no pedido, em numeric. Na origem era real (ponto flutuante), impróprio para dinheiro.';
COMMENT ON COLUMN order_items.unit_price IS
  'Preço congelado no dia da venda. Difere do preço de catálogo atual em 31% dos itens: por isso é coluna própria e não uma consulta a products.';
COMMENT ON COLUMN order_items.discount IS
  'Desconto como fração do preço, de 0 a 1 (0.25 = 25%). Receita do item = unit_price * quantity * (1 - discount).';
