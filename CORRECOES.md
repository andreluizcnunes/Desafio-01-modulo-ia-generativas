# Correções das revisões

Duas revisões apontaram falhas. A primeira, da versão `8b61395`, em quatro frentes; a
segunda, da versão `0f67cf5`, em cinco. Este arquivo registra cada critério de aceite,
onde está a evidência e o que ficou pendente. A segunda revisão vem primeiro.

# Segunda revisão (versão 0f67cf5)

Testes e medições executados em 21/11/2026.

## 1. Fundamentação das instruções

| Critério de aceite | Situação | Onde está a evidência |
|---|---|---|
| 0101 com campos estruturados corretos e minuta com total de R$ 280,00: a saída exibida tem o total de R$ 980,00 ou vai à análise manual; a versão incorreta nunca conta como acerto | executado | `teste_barreira.py`, caso "0101 com o valor unitário como total": a instrução entregue traz a minuta do código, com "Valor total: R$ 980,00"; parte 2b: a minuta do modelo, entregue sem a barreira, é `entregue_errado` ("valor total 280.0 ≠ 980.0"); `teste_app.py`, passo A1b, pela tela |
| 0108 com prestação vencida e fundamento "regularizada": a versão exibida reflete o histórico ou vai à análise manual | executado | caso "0108 com situação vencida e fundamento dizendo 'regularizada e aprovada'": o fundamento entregue é a frase do histórico ("VENCIDA em 2026-09-25"); parte 2b: a versão do modelo é `entregue_errado` |
| 0101 com valor por extenso na minuta: o trecho fica fora da instrução entregue e da contagem de acertos | executado | caso "0101 com valor por extenso na minuta"; nos alertas, que vão à tela como o modelo escreve, o valor por extenso é recusado (caso "0101 com alerta citando valor por extenso") |
| Controle positivo com fundamentos e minuta coerentes com as consultas | executado | os 12 pedidos e as 2 complementações com a instrução correta são liberados e contam como acerto (`teste_barreira.py`, partes 1, 2 e 2b) |

**O que mudou.** Liberada a instrução, `barreira.redigir` monta os fundamentos, as
pendências e a minuta com os dados das consultas válidas, cada um no seu papel, e
substitui os textos do modelo (`desenho.md`, Seção 2, passo 7b). Os alertas do modelo
continuam na tela e são conferidos. Os erros dos textos substituídos ficam registrados
(`Resultado.textos_substituidos`) e aparecem na medição.

## 2. Diligência sem análise de mérito

| Critério de aceite | Situação | Onde está a evidência |
|---|---|---|
| 0112 inicial com cálculo, histórico e saldo de 207481 após a divergência: recusado, fora da tela e do acerto | executado | caso "0112 diligência correta, mas com cálculo, histórico e saldo de 207481": recusado; parte 2b: `entregue_errado` ("consultas fora da etapa") |
| 0112 inicial regular: diligência com o motivo cadastral e sem consultas de mérito; após a complementação, mesma sessão e consultas da matrícula 207418 | executado | casos "0112 diligência correta" e "0112 complementação correta"; "0112 complementação com o histórico da matrícula digitada 207481": recusado; `teste_app.py` e medição com a sessão do pedido |
| 0111: falta de retorno gera diligência; a complementação na mesma sessão volta ao mérito | executado | casos "0111 diligência correta", "0111 … tentativa de cálculo sem retorno" (recusado) e "0111 complementação correta"; `teste_app.py`, passo A3 |
| A medição confere ferramentas extras e fora da etapa, além das ausentes | executado | `medir.conferir`: "consultas fora da etapa" |

## 3. Urgência com condição de autorização escrita

| Critério de aceite | Situação | Onde está a evidência |
|---|---|---|
| 0106 com minuta que dispensa a autorização escrita: recusar ou gerar a minuta com a condição | executado | caso "0106 urgente com minuta que dispensa a autorização escrita": a minuta entregue é a do código, com a condição; o alerta que afirma a dispensa é recusado |
| Variante do 0106 com capacitação programada, incêndio negado e autorização verbal: a menção a incêndio não produz aptidão | executado | casos "variante do 0106 …": urgência ambígua, recusada nas duas respostas do modelo (apto ou não recomendado) e encaminhada à análise manual; `teste_barreira.py`, parte 5 |
| 0106 original com a condição escrita explícita; 0107 não recomendado | executado | casos "0106 urgente correto" e "0107 correto"; medição: 0106 correto em 12 de 12 execuções e 0107 em 12 de 12 (`resultados/medicao.md`) |

**O que mudou.** `barreira.ler_urgencia` só reconhece a hipótese do § 1º afirmada e sem
sinal contrário (menção negada, atividade programada, autorização verbal, ordem ao
sistema). Com antecedência insuficiente e urgência ambígua, a barreira recusa e o
conferente decide. A condição da autorização escrita entra na minuta por regra do
código (`desenho.md`, Seção 8).

## 4. Resultado pertencente à execução atual

| Critério de aceite | Situação | Onde está a evidência |
|---|---|---|
| Fluxo sem evento inicial e sem resposta final, com execução anterior válida da mesma sessão no banco: mensagem padrão, sem reutilizar a anterior | executado | `teste_barreira.py`, parte 3 ("sem evento inicial nem resposta; anterior válida no banco"), que falha na versão 0f67cf5; `teste_app.py`, passo A4 |
| Resposta ausente, status de erro, execução diferente e fluxo normal pelo formulário; complementação e registro da decisão preservados | executado | `teste_app.py`, passos A1 a A5 e parte B (`resultados/etapa5_formulario.txt`) |

**O que mudou.** Em `instrutor.instruir`, o banco só é consultado quando o
identificador da execução atual é conhecido, e a resposta recuperada precisa ter o
mesmo identificador e a mesma sessão e status concluído.

## 5. Medição e evidências

| Critério de aceite | Situação | Onde está a evidência |
|---|---|---|
| Medição confere cada situação e seu fundamento, o papel dos dados exibidos e a presença, identidade e pertinência das consultas; gabarito independente | executado | `medir.conferir` (fundamento coerente com a situação, total e unitário da minuta, encaminhamento, consultas fora da etapa, número por extenso, condição da autorização escrita); `gabarito.json` com `papeis`; parte 2b de `teste_barreira.py` |
| Testes locais de barreira, ferramentas, eliminação e formulário, com bancos temporários e controles positivos e negativos | executado | `teste_barreira.py` (44 casos, 12 falhas do fluxo), `teste_ferramentas.py`, `teste_eliminacao.py`, `teste_app.py` parte A |
| Três rodadas de 12 pedidos e 2 complementações em cada configuração; quatro falhas provocadas; acertos, recusas, erros, entregas divergentes, tokens, tempo e custo | executado | 84/84 acertos (42/42 com paralelas desligadas e 42/42 ligadas), 0 recusados, 0 erros, 0 entregues errados, US$ 0,1476 e 0,1458, 353 s e 336 s (`resultados/medicao.md`); `resultados/falhas.md` |
| Resultados anteriores identificados pelo critério que mediram | executado | `resultados/historico/medicao_0f67cf5.md`, com o critério daquela versão no cabeçalho |
| `resultados/`, `relatorio.md`, `LEIA-ME.md` e `CORRECOES.md` atualizados; acervo intacto; chave fora do Git | executado | `dados/` sem alteração (`git log -- dados`); só `.env.example` versionado |

## Pendências e limites da segunda revisão

- **Alertas do modelo:** são o único texto do modelo que vai à tela. A barreira confere
  as fontes dos dados citados, números por extenso e a afirmação de dispensa da
  autorização escrita; um alerta errado que não cite dado algum não é detectado.
- **Leitura da urgência:** continua por palavras da justificativa. Uma hipótese do § 1º
  afirmada sem sinal contrário e sem emergência real ainda abre a exceção; a autorização
  escrita e a leitura da justificativa ficam com o conferente (`relatorio.md`, Seção 10).
- **Diagnóstico dos textos substituídos:** os textos do modelo que o código refaz são
  conferidos só pelas fontes. Em 84 itens, nenhum citou dado sem fonte; esse número não
  mede o papel dos dados nos textos do modelo.
- **Falha 4:** nesta execução, o modelo sem ferramentas pediu diligência nas 6 em vez de
  calcular; o erro de cálculo citado (3,0 diárias em vez de 3,5) é da execução de
  20/11. Nas duas, a barreira recusou as 6.
- **Gabarito reconstruído e expurgo automático:** como na primeira revisão.

# Primeira revisão (versão 8b61395)

Testes e medições executados em 20/11/2026.

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

## Pendências e limites da primeira revisão

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
