# Evidências executadas — Entrega 3

Execução inicial em 22/09/2026 e revisão completa em 24/09/2026, sobre PostgreSQL 16.15 e MongoDB 7.0.40. Os registros Northwind e os documentos Word anteriores foram preservados.

| Arquivo | Conteúdo |
|---|---|
| manifesto.json | Ambiente, regra decimal e hashes do código analítico conferido |
| migracao.json | Reconstrução das 11 tabelas: 3.311 linhas, zero divergências |
| retorno-migracao.json | Retorno independente lido do MongoDB |
| estruturas-mongo.txt | Tipos, referências, cópias e coerência temporal |
| pipelines.ejson | Definições compiladas dos 16 arquivos PNN.js |
| resultados.json | Saídas SQL e MongoDB completas, ordenadas e equivalentes |
| conferencia-python.json | Terceiro cálculo, em Python puro sobre as linhas de nw: 16 pares sem divergência |
| testes-fronteira.json | 38 verificações: pares com casos sintéticos (15 com valores esperados calculados à mão), pares vazios, empate, arredondamento e procedures |
| procedures.json / procedures.txt | Resultados reais das três procedures |
| recursos-documentais.json | Saídas das três demonstrações de recursos documentais, com o contraste $elemMatch (11) × condições independentes (16) |
| mapreduce.json | Quantidades por produto: MapReduce igual ao pipeline, 77 produtos e 51.317 unidades |
| anteriores.sha256.json | Hashes dos DOCX das Entregas 1 e 2 antes do trabalho |
| paginacao.json | Páginas reais, sumário estável e PDF de revisão |
| tempos.png / mensal.png | Gráficos derivados de medições/resultados |

As somas monetárias são comparadas exatamente. Quocientes permitem diferença absoluta até 1e-12, sem arredondamento prévio para centavos. A sequência dos resultados também é conferida, e a comparação rejeita ponto flutuante, lógicos trocados por números e datas fora da meia-noite UTC. Os dados de teste são isolados e não participam dos indicadores de negócio.

As amostras individuais e os planos de execução estão em `bench/results/entrega03/`. São cinco aquecimentos e vinte medições por banco/consulta. `catalogo.json` cobre os 16 pares; `otimizacoes.json` cobre quatro estudos; as versões de cada estudo são medidas de forma intercalada, e reescrita e índice ficam em cópias separadas. As cópias de teste preservam PK/UNIQUE no PostgreSQL e _id no MongoDB e são removidas ao final.

O DOCX contém códigos completos, resultados selecionados com indicação do recorte, método, tempos, dispersão e resumos dos planos. Não é necessário enviar estes arquivos para permitir a leitura acadêmica. O guia pessoal HTML é separado do documento da professora.
