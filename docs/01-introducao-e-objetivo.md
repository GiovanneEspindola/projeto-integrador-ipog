# 1. Introdução e objetivo

A Northwind Traders é uma empresa fictícia de distribuição de alimentos usada em uma base didática de vendas. Seus registros permitem estudar clientes, produtos, pedidos, fornecedores e a organização da equipe comercial. Este projeto utiliza essa base para desenvolver e comparar uma solução relacional em PostgreSQL e uma solução orientada a documentos em MongoDB.

O objetivo de negócio é identificar como o valor dos pedidos se distribui entre produtos, categorias, clientes e períodos, além de avaliar informações de estoque e de envio. O objetivo técnico é representar esse domínio nos dois bancos, executar consultas equivalentes e analisar os resultados, a organização dos dados e o desempenho observado.

**Esta primeira entrega apresenta a compreensão do negócio e dos dados, o diagrama conceitual, a análise exploratória e a avaliação da qualidade da base.** O plano híbrido indica como o trabalho continuará. A implementação documental e a comparação de desempenho serão desenvolvidas nas próximas entregas.

## 1.1 Orientação metodológica

O CRISP-DM organiza projetos de dados em seis fases relacionadas: compreensão do negócio, compreensão dos dados, preparação, modelagem, avaliação e implantação [1]. Nesta entrega, a orientação se concentra nas duas primeiras fases.

| Fase | Aplicação no projeto |
|---|---|
| Compreensão do negócio | Definir o contexto, as perguntas e os limites da análise. |
| Compreensão dos dados | Examinar tabelas, relacionamentos, valores, ausências e consistência. |
| Preparação dos dados | Ajustar tipos e regras e preparar a transformação para documentos. |
| Modelagem | Desenvolver os modelos relacional e documental. |
| Avaliação | Conferir a equivalência das consultas e medir o desempenho. |
| Implantação | Organizar scripts, relatório acumulativo e apresentação final. |

O uso é adaptado a um projeto de banco de dados: a modelagem será de estruturas de armazenamento, sem treinamento de modelos estatísticos. As fases podem ser retomadas. Por exemplo, a ausência de custos de aquisição levou a limitar as perguntas financeiras ao valor dos pedidos, sem calcular lucro.

## 1.2 Base e ferramentas

Foi utilizada a adaptação do Northwind para PostgreSQL mantida no repositório **pthom/northwind_psql** [2], cuja cópia SQL está preservada no projeto. A análise usa PostgreSQL 16, consultas SQL e um notebook Jupyter em Python. O PostgreSQL permite trabalhar com relacionamentos, restrições e valores decimais, além de inspecionar os planos das consultas.

O MongoDB 7 foi escolhido como o banco documental previsto no projeto da disciplina [3].