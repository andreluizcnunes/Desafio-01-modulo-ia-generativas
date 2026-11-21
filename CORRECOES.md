# Correções da auditoria

A auditoria da versão `8b61395` apontou falhas em quatro frentes. Este arquivo registra
cada critério de aceite, onde está a evidência e o que ficou pendente. Todos os testes e
medições abaixo foram executados em 20/11/2026.

## 1. Barreira de validação em código

| Critério de aceite | Situação | Onde está a evidência |
|---|---|---|
| 0112 após a complementação: recusar o histórico de 207481 para a instrução de 207418, liberar com as consultas corretas | executado | `teste_barreira.py`, casos "0112 complementação…" → `resultados/teste_barreira.txt` |
| 0101 com protocolo e partida trocados (35,5 diárias, R$ 9.940,00): validar cada data pelo seu papel, inclusive a partida usada no histórico; aplicar só correções do próprio pedido | executado | casos "0101 com protocolo e partida trocados", "…só no histórico" e "complementação do 0111 aplicada ao 0112" |
| 0108 sem a consulta de histórico: exigir evidência para cada verificação de mérito; preservar a diligência (sem mérito, quantidade e valor nulos) | executado | casos "0108 sem a consulta de histórico", "0111 diligência…", "0112 diligência…" |
| 0107 marcado apto com `exige_autorizacao_superior=true`: a marcação do modelo não justifica a exceção; o 0107 fica não recomendado; o 0106 trata a urgência de forma consistente e explicita a condição da autorização escrita | executado | casos "0107…" e "0106…"; medição: 0107 correto 6/6, 0106 correto 5/6 e recusado 1/6 (`resultados/medicao.md`) |
| 0101 com saldo inventado no fundamento e valor inventado na minuta: dados factuais dos textos com fonte no pedido ou nas ferramentas | executado | casos "0101 com saldo inventado…" e "…valor inventado na minuta" |

**O que mudou.** `barreira.py` foi reescrita. O agente (`instrutor.py`) teve a instrução
de sistema ajustada na regra da urgência, nas situações da diligência e na proibição de
contas nos textos. A urgência do § 1º passou a ser reconhecida por código (`desenho.md`,
Seção 8).

## 2. Medição e evidências

| Critério de aceite | Situação | Onde está a evidência |
|---|---|---|
| Acerto confere situações dos seis critérios, fundamentos, fatos da minuta e trilha de consultas; mantidas as quatro classes | executado | `medir.py` (`conferir`, `classificar`); `gabarito.json` com `situacoes`, `trilha` e `fatos` |
| Gabarito independente da implementação e lido só pela avaliação | executado | `gabarito.py` não importa as ferramentas; `teste_barreira.py`, parte 4, confere que agente e tela não o leem |
| Casos da seção 1 nos testes locais com respostas controladas, com controle positivo, diligência e as duas complementações; fundamentação inválida fora da tela e da contagem de acertos | executado | `simulacao.py`, `teste_barreira.py` (22 casos, partes 1 e 2); `teste_app.py`, passo A4 |
| Três rodadas com 12 pedidos e 2 complementações por configuração de paralelas; acertos, recusas, erros, tokens, tempo, custo | executado | `resultados/medicao.json` e `resultados/medicao.md`: 41/42 (desligadas) e 42/42 (ligadas), 0 entregues errados |
| Evidências das quatro falhas provocadas e justificativa do ponto de conferência humana | executado | `resultados/falhas.md`; `relatorio.md`, Seções 7 e 8 |
| Declarar a cobertura medida e o que depende de acesso ao modelo | executado | `relatorio.md`, Seção 9 |

## 3. Eliminação e conferência no SQLite

| Critério de aceite | Situação | Onde está a evidência |
|---|---|---|
| Titular sob a matrícula errada do 0112, com o nome em minúsculas: encontrar e comprovar a remoção de sessão, execução e memória, tabela por tabela | executado | `teste_eliminacao.py`, caso 1 → `resultados/teste_eliminacao.txt` |
| Tabela que não pôde ser conferida aparece como falha de verificação | executado | `teste_eliminacao.py`, caso 5 |
| Matrícula parcial "20" com nome fictício: validar identidade e formato antes de excluir; preservar os controles com dados inválidos e ao excluir titular válida | executado | `teste_eliminacao.py`, casos 1 a 3; `teste_app.py`, passo A5 |
| Exclusão restrita ao banco de trabalho do agente; `teste_app.py` isolado em banco temporário | executado | `eliminacao._banco_do_agente` (`teste_eliminacao.py`, caso 4); `teste_app.py` usa pasta temporária para banco e registro |

## 4. Mensagem padrão em falhas de execução

| Critério de aceite | Situação | Onde está a evidência |
|---|---|---|
| Retorno ausente ou execução não concluída é falha antes de ler o conteúdo; a resposta precisa pertencer à execução atual | executado | `instrutor.instruir`; `teste_barreira.py`, parte 3 (status ERROR, sem `RunOutput`, outra execução, exceção; com e sem progresso) |
| Na tela: mensagem padrão; sem instrução, minuta, argumentos ou detalhes técnicos da execução recusada | executado | `app.py` (`executar` limpa o progresso; medidas só para instrução entregue); `teste_app.py`, passo A4 |
| Teste pelo formulário: falha do fluxo simulado, status ERROR, recusa da barreira e processamento normal; divergência humana e complementação na mesma sessão | executado | `teste_app.py`, passos A1 a A4, e parte B com o modelo real → `resultados/etapa5_formulario.txt` |

## Pendências e limites

- **Leitura da urgência:** o código reconhece só as hipóteses listadas no § 1º e por
  palavras da justificativa. É uma leitura conservadora, e a decisão sobre emergência
  fora da lista fica com o conferente (`relatorio.md`, Seção 10).
- **Fatos dos textos:** números por extenso, ou sem "R$", centavos ou unidade, não são
  conferidos.
- **Gabarito reconstruído:** o `gabarito.json` e o `gerar_dados.py` originais do enunciado
  não estavam no material entregue. A medição usa o gabarito reconstruído por
  `gabarito.py`.
- **Expurgo automático por prazo:** continua não implementado (opcional da Aula 07).

O acervo do desafio (`dados/`) não foi alterado. A chave fica só no `.env` local; o
repositório guarda apenas o `.env.example`.
