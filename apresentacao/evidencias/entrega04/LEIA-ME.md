# Evidências executadas — Entrega 4

Reexecução em 05/10/2026 sobre PostgreSQL 16.15 e MongoDB 7.0.40, gravada nesta pasta para não sobrescrever a Entrega 3.

| Arquivo | Conteúdo |
|---|---|
| migracao.json, retorno-migracao.json, estruturas-mongo.txt | Nova reconstrução das 3.311 linhas: zero divergências |
| resultados.json | Os 16 pares novamente equivalentes; idênticos aos da Entrega 3 |
| conferencia-python.json | Recálculo independente em Python: sem divergências |
| testes-fronteira.json, procedures.json | 38 verificações com dados sintéticos isolados: todas aprovadas |
| arquitetura.png, mensal.png, tempos.png | Figuras do relatório final |
| paginacao.json | Páginas e sumário do Word final |

O teste de índices da Entrega 4 está em `bench/results/entrega04/`: P04, P13 e P15 medidos em duas cópias isoladas do MongoDB (índices atuais e com employee_id/shipper_id), com o PostgreSQL nas mesmas rodadas. Cinco aquecimentos, vinte medições, ordem alternada. O banco original não foi alterado.
