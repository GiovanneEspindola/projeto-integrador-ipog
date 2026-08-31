# Projeto Integrador — Área 03: Banco de Dados (IPOG)

**Modelagem e Análise de Dados de Vendas sobre o dataset Northwind Traders.**

O projeto responde a uma pergunta: **qual a ferramenta certa para o trabalho?**
Para isso, o mesmo domínio de negócio é modelado duas vezes — uma solução
relacional em **PostgreSQL 16** e uma orientada a documentos em **MongoDB 7** —
e as mesmas perguntas de negócio são respondidas nas duas tecnologias, com
comparação de sintaxe, de plano de execução e de desempenho medido.

Autor: Giovanne Espíndola · Trabalho individual · Semestre final.

---

## Do zero ao ambiente rodando

Escrito para quem chega ao repositório sem nenhum contexto — um avaliador, por
exemplo. São cinco minutos e um pré-requisito.

### Pré-requisito único

**Docker** com o plugin Compose v2. Nada mais precisa estar instalado: os dois
bancos, o cliente `psql` e o cliente `mongosh` vêm dentro das imagens.

Confira que está funcionando:

```bash
docker compose version
```

Se o comando responder com uma versão (`Docker Compose version v2.x.x`), pode
seguir. Se disser que o comando não existe, instale o
[Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows/macOS)
ou o Docker Engine (Linux) antes de continuar.

> **No Windows com WSL2:** além de abrir o Docker Desktop e esperar o ícone da
> baleia ficar verde, é preciso ativar
> *Settings → Resources → WSL Integration → (sua distro)* → **Apply & Restart**.
> Sem isso o comando `docker` não existe dentro do Linux.

### 1. Clonar o repositório

```bash
git clone <url-do-repositorio> projeto-integrador-ipog
cd projeto-integrador-ipog
```

### 2. Configurar as portas — só se precisar

Por padrão o projeto usa a porta **5432** (PostgreSQL) e a **27017** (MongoDB).
Se alguma delas já estiver ocupada na sua máquina, copie o modelo e ajuste:

```bash
cp .env.example .env
# edite .env e troque, por exemplo, POSTGRES_PORT=5433
```

O caso mais comum é ter um PostgreSQL instalado direto no sistema segurando a
5432. Veja [Problemas conhecidos](#problemas-conhecidos) no fim deste arquivo.

### 3. Subir os bancos

```bash
docker compose up -d
```

Na primeira vez o Docker baixa as imagens (`postgres:16` e `mongo:7`); pode
levar alguns minutos.

### 4. Conferir que subiu

```bash
docker compose ps
```

Os dois containers precisam aparecer com **`healthy`** na coluna de status:

```
NAME          IMAGE         STATUS
pi-postgres   postgres:16   Up X minutes (healthy)
pi-mongo      mongo:7       Up X minutes (healthy)
```

Se algum ficar preso em `starting` ou aparecer como `unhealthy`, veja o que
aconteceu com `docker compose logs postgres` (ou `mongo`).

### 5. Testar a conexão de verdade

`healthy` diz que o processo respondeu; os comandos abaixo provam que dá para
autenticar, ler e escrever:

```bash
# PostgreSQL
docker compose exec -T postgres psql -U pi -d northwind \
  -c "SELECT version(), current_database(), current_user;"

# MongoDB
docker compose exec -T mongo mongosh -u pi -p pi --authenticationDatabase admin \
  --quiet --eval 'printjson({versao: db.version()})'
```

Pronto — o ambiente está rodando.

---

## Conexões

| Banco | String de conexão |
|---|---|
| PostgreSQL | `postgresql://pi:pi@localhost:5432/northwind` |
| MongoDB | `mongodb://pi:pi@localhost:27017/northwind?authSource=admin` |

Usuário e senha são `pi`/`pi` nos dois. São credenciais de ambiente de estudo,
locais, deliberadamente triviais — nunca sairiam assim de um projeto real.

---

## Comandos do dia a dia

```bash
docker compose up -d              # sobe os bancos
docker compose ps                 # status
docker compose down               # derruba (os dados ficam nos volumes)
docker compose down -v            # derruba E APAGA os dados

# terminal interativo em cada banco
docker compose exec postgres psql -U pi -d northwind
docker compose exec mongo mongosh -u pi -p pi --authenticationDatabase admin

# rodar um script SQL do repositório dentro do container
docker compose exec -T postgres psql -U pi -d northwind -f /sql/ARQUIVO.sql
```

Os diretórios `sql/` e `mongo/` do repositório aparecem dentro dos containers
como `/sql` e `/mongo`, em modo somente leitura.

### Construir o banco do zero

Os scripts são numerados na ordem em que devem rodar e **todos são
idempotentes**: podem ser executados quantas vezes for preciso, sempre com o
mesmo resultado.

Num clone novo, o `docker compose up -d` já carrega o Northwind sozinho — o dump
está montado em `docker-entrypoint-initdb.d`, que o PostgreSQL executa na
primeira inicialização. Depois disso:

```bash
for f in 00_northwind_original 10_ddl 20_load 21_validacao_carga 30_indexes 40_views 50_evidencias; do
  docker compose exec -T postgres psql -U pi -d northwind -v ON_ERROR_STOP=1 -f /sql/$f.sql
done
```

O `00_northwind_original.sql` aparece no laço de propósito, mesmo já tendo
rodado na inicialização: assim o comando funciona **também** em quem já tinha o
volume criado antes, e a sequência fica válida como receita única de reprodução.

| Script | O que faz |
|---|---|
| `00_northwind_original.sql` | carrega o Northwind no schema `public` — a fonte, 14 tabelas |
| `10_ddl.sql` | cria o schema `nw`: 11 tabelas, 17 CHECK, 4 UNIQUE, comentários |
| `20_load.sql` | migra 3311 linhas de `public` para `nw`, convertendo tipos |
| `21_validacao_carga.sql` | prova que nada se perdeu: contagens, somas e colunas |
| `30_indexes.sql` | os 4 índices que o `EXPLAIN` justificou, e os 6 recusados |
| `40_views.sql` | as 4 views analíticas |
| `50_evidencias.sql` | gera a evidência de índices e views para a apresentação |

### Interfaces gráficas (opcionais)

Não sobem por padrão. Quando quiser:

```bash
docker compose --profile gui up -d
```

| Ferramenta | Endereço | Acesso |
|---|---|---|
| pgAdmin | http://localhost:5050 | `pi@local.dev` / `pi` |
| mongo-express | http://localhost:8081 | sem senha |

### Ambiente Python (análise exploratória, ETL, benchmark e gráficos)

Não é necessário para subir os bancos nem para rodar as consultas SQL — só
para o notebook de `etl/` e os scripts de `bench/`.

O projeto usa o [**uv**](https://docs.astral.sh/uv/). Se você não tiver:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Depois, na raiz do repositório, **um comando basta**:

```bash
uv sync
```

Isso instala o Python 3.12 (mesmo que você não o tenha), cria o `.venv` e
instala as dependências exatamente nas versões travadas em `uv.lock`. Para
rodar qualquer script sem ativar o ambiente à mão:

```bash
uv run python etl/migrate.py
```

**Análise exploratória.** O perfilamento do Northwind é um notebook Jupyter.
Para abrir e explorar célula a célula:

```bash
uv run jupyter lab
```

Para reexecutar tudo pelo terminal e regravar os arquivos de evidência, sem
abrir a interface:

```bash
uv run jupyter nbconvert --to notebook --execute --inplace etl/perfilamento.ipynb
```

O notebook é idempotente: rodar de novo reescreve
`apresentacao/evidencias/01-perfil-*.txt` com o mesmo conteúdo.

**Por que uv e não pip:** o `uv.lock` trava a árvore inteira de dependências
com hash criptográfico de cada arquivo, e o `.python-version` trava até a versão
do interpretador. `uv sync` reconstrói o ambiente idêntico em qualquer máquina —
com `pip install -r requirements.txt` isso é só aproximado. Reprodutibilidade é
critério de avaliação deste trabalho.

**Sem uv, usando pip:** `etl/requirements.txt` é gerado a partir do `uv.lock` e
funciona normalmente:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r etl/requirements.txt
```

---

## Os documentos

| Arquivo | O que responde |
|---|---|
| `docs/00-definicao-do-trabalho.md` | qual é a área de foco, o escopo e o que ficou de fora |
| `docs/01-analise-negocio.md` | o que a base tem, o que ela tem de errado, e as 16 perguntas de negócio |
| `docs/02-modelo-conceitual.md` | as 11 entidades e a justificativa de cada cardinalidade |
| `docs/03-plano-hibrido.md` | como PostgreSQL e MongoDB convivem e como serão comparados |
| `docs/04-modelo-relacional.md` | o schema `nw`: normalização, constraints, índices e views |

---

## Estrutura do repositório

```
pyproject.toml     dependências Python declaradas (fonte de verdade)
uv.lock            versões resolvidas e travadas com hash
.python-version    versão do interpretador (3.12)
docs/              documentação técnica das entregas (00 a 07)
  estudo/          material didático: o "por quê" de cada decisão
  diagramas/       ER conceitual e arquitetura (.drawio), ER lógico (.dbml/.png)
sql/               dump original, DDL do schema nw, carga, validação, índices, views
  queries/         consultas de negócio (QNN.sql)
mongo/             validators e índices
  pipelines/       aggregation pipelines espelhando as consultas (PNN.js)
etl/               perfilamento (notebook), validadores dos diagramas,
                   migração PostgreSQL -> MongoDB, requirements.txt (gerado)
bench/             benchmark comparativo + resultados
apresentacao/      roteiro dos slides
  evidencias/      saídas brutas de consulta e gráficos usados na apresentação
entregas/          pacotes fechados por data (entrega-01 .. entrega-04)
```

### Duas decisões de arquitetura que explicam a organização

**Schema `public` vs schema `nw`.** O `public` recebe o dump original do
Northwind e fica intocado — é a fonte. O `nw` é o modelo projetado neste
trabalho: tipos corrigidos, constraints explícitas, normalização justificada,
índices pensados e views analíticas. Carregar um dump pronto não é modelar;
a separação existe para que haja decisão de modelagem a defender.

**Consultas espelhadas.** Cada `sql/queries/QNN.sql` tem um par
`mongo/pipelines/PNN.js` respondendo exatamente à mesma pergunta de negócio.
É o que torna a comparação entre as duas tecnologias uma medição, e não uma
opinião.

---

## Problemas conhecidos

**`port is already allocated` na 5432.** Já existe um PostgreSQL usando a porta
na sua máquina. Ou desligue o serviço do sistema:

```bash
sudo systemctl disable --now postgresql    # Linux com systemd
```

ou mude a porta do container criando um `.env` com `POSTGRES_PORT=5433` — e
lembre de ajustar a string de conexão ao usar. O cliente `psql` instalado no
sistema continua funcionando contra o container normalmente.

**`docker: command not found` no WSL2.** A integração WSL do Docker Desktop
está desativada para a sua distro. Veja a nota na seção de pré-requisitos. Depois
de ativar, **abra um terminal novo** — o PATH não é atualizado nos que já estavam
abertos.

**Transação multi-documento falha no MongoDB.** A mensagem que este deployment
devolve é `This MongoDB deployment does not support retryable writes`. É
esperado: o container sobe como **nó standalone**, e transação multi-documento
exige *replica set*. Está declarado como limitação em `docs/03` §6, não é
defeito.
