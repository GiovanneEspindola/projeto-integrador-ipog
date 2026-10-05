# 1. Introdução e objetivo

A Northwind Traders é uma distribuidora fictícia de alimentos, usada como base didática de vendas. Seus registros cobrem clientes, produtos, fornecedores, pedidos e a equipe comercial. Este projeto parte de uma pergunta simples: **qual é a ferramenta certa para cada trabalho com esses dados?** Para respondê-la, o mesmo conjunto foi implementado em um banco relacional (PostgreSQL) e em um banco orientado a documentos (MongoDB), e as mesmas 16 perguntas de negócio foram respondidas nos dois.

O objetivo de negócio é entender como o valor dos pedidos se distribui entre produtos, categorias, clientes, vendedores e meses, além de observar o estoque e os envios. O objetivo técnico é comparar os dois modelos em correção dos resultados, forma de escrever as consultas, desempenho e manutenção, e transformar essa comparação em critérios de escolha.

## 1.1 Método: CRISP-DM

O CRISP-DM organiza projetos de dados em seis fases [1]. Aqui ele foi adaptado a um projeto de banco de dados: a “modelagem” é das estruturas de armazenamento, não de modelos estatísticos.

| Fase | O que foi feito |
|---|---|
| Compreensão do negócio | Contexto da empresa, perguntas a responder e limites da base. |
| Compreensão dos dados | Inventário, nulos, chaves, faixas de valores e precisão decimal. |
| Preparação dos dados | Schema relacional próprio e transformação das tabelas em documentos. |
| Modelagem | Modelo relacional normalizado e modelo documental com itens incorporados. |
| Avaliação | Comparação dos resultados nos dois bancos e medição de desempenho. |
| Implantação | Guia de decisão, scripts reproduzíveis e documentação. |

As fases se retroalimentaram. A falta de custos na base, descoberta na exploração, fez com que as perguntas financeiras tratassem do valor dos pedidos, e não de lucro.

## 1.2 Organização deste relatório

O documento é cumulativo e segue a ordem das semanas do projeto [3].

| Entrega | Semanas | Capítulos |
|---|---|---|
| 1 | 02 — compreensão do negócio e dos dados | 1 a 4 |
| 2 | 03 e 04 — modelagem relacional e NoSQL | 5 a 10 |
| 3 | 05 e 06 — consultas, views, procedures, pipelines e performance | 11 a 16 |
| 4 | 07 — guia de decisão, escalabilidade, conclusões e reprodução | 17 a 20 |

Os códigos completos das 16 consultas SQL e dos 16 pipelines estão no Apêndice A. As views, as procedures, as demonstrações de recursos do MongoDB e o MapReduce estão no Apêndice B.

## 1.3 Base e ferramentas

A base é a adaptação do Northwind para PostgreSQL mantida no repositório **pthom/northwind_psql** [2]. Os dois bancos rodam em containers Docker: PostgreSQL 16 e MongoDB 7. A exploração usou SQL e um notebook Jupyter; a transformação para documentos foi feita em SQL e carregada com o mongosh; a validação e as medições usaram Python.
