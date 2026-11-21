# Relatório — Instrução de pedidos de diárias com um agente Agno

Números medidos com o `gpt-5.6-luna` em 20/11/2026, depois das correções da auditoria
(`CORRECOES.md`). Os arquivos de origem de cada número estão em `resultados/`. Como a
saída do modelo é probabilística, os valores variam entre execuções (Aula 04, 5.4):
sempre que houve repetição, o relatório informa quantas vezes a medição foi feita.

## 1. Resumo

| Medida | Resultado |
|---|---|
| Acertos contra o gabarito (3 rodadas × 14 itens, configuração escolhida) | **41/42** (14, 13 e 14 por rodada) |
| Instruções entregues ao conferente diferentes do gabarito | **0/42** (e 0/42 na outra configuração) |
| Recusadas pela barreira (mensagem padrão, análise manual) | 1/42 |
| Erros de execução | 0/42 |
| Custo por pedido (mediana) / por complementação (média) | US$ 0,0039 / US$ 0,0050 |
| Tempo por item (mediana / máximo) | 9,1 s / 12,4 s |
| Custo mensal estimado (400 pedidos + 68 complementações) | US$ 1,89 |

**O que conta como acerto.** O item precisa chegar ao conferente igual ao gabarito em
recomendação, matrícula, quantidade, valor e exigência de autorização superior. Também
precisa coincidir na situação de cada um dos seis critérios e na trilha de consultas,
com cada argumento no seu papel. Por fim, os fundamentos, pendências, alertas e minuta
não podem citar valor, data, matrícula, pedido ou quantidade sem fonte. A primeira
versão comparava só os cinco primeiros campos. A auditoria mostrou que esse critério
contava como acerto uma instrução com o histórico da matrícula errada e outra com valor
inventado na minuta.

## 2. Medição contra o gabarito

O `gabarito.json` foi gerado por `gabarito.py`, que aplica a norma por código, sem
modelo e sem importar as ferramentas, e foi escrito antes de qualquer execução do
agente. Só a avaliação o lê: `teste_barreira.py` confere que nem o agente nem a tela o
abrem. A conferência de trilha e de textos da medição (`medir.py`) tem extração
própria e não reaproveita o código da barreira (Aula 03, 5.2). Cada item é classificado
em quatro classes: acerto, recusado (mensagem padrão), erro de execução e **entregue
errado**, a classe que mais pesa no enunciado (`resultados/medicao.md`).

| Configuração | Rodada 1 | Rodada 2 | Rodada 3 | Total | Recusados | Erros | Entregues errados | US$ (42 itens) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Paralelas desligadas (escolhida) | 14/14 | 13/14 | 14/14 | 41/42 | 1 | 0 | **0** | 0,1581 |
| Paralelas ligadas | 14/14 | 14/14 | 14/14 | 42/42 | 0 | 0 | **0** | 0,1594 |

O único item que não foi acerto foi o **DIA-2026-0106 na rodada 2**, que foi recusado.
O agente concluiu "apto" com autorização superior, como o gabarito, mas declarou a
antecedência como "não atende", e as consultas sustentam "atende" pelo § 1º. A barreira
exige que cada critério coincida com o que as consultas sustentam. Por isso o pedido foi
devolvido à análise manual: o erro ficou **visível** e não chegou ao conferente.

### Antes e depois da correção

| | Versão auditada (8b61395) | Versão corrigida |
|---|---|---|
| Critério de acerto | 5 campos | 5 campos + 6 situações + trilha + fatos dos textos |
| Acertos (paralelas desligadas) | 38/42 | 41/42 |
| Entregues errados | 3 (0106 ×2, 0107 ×1) | **0** |
| DIA-2026-0106 | "não recomendado" em 5 de 6 execuções | correto em 5 de 6, recusado em 1 |

Duas mudanças explicam a diferença:

- **A instrução de sistema explicita a regra da urgência legítima.** Se os demais
  critérios atendem, a recomendação é "apto" com `exige_autorizacao_superior=true`. A
  autorização escrita é condição da autorização, e não do pedido. Sem urgência legítima,
  inclusive com autorização verbal, a exigência fica `false`.
- **A barreira deixou de aceitar a marcação do modelo como justificativa da exceção.**
  Ela reconhece a urgência pelas hipóteses do § 1º e deriva das consultas a
  recomendação, a exigência e a situação de cada critério.

O histórico da versão anterior está em `resultados/caso_0106.md`.

**0106 e 0107.** O enunciado diz que "um agente que trata o 0106 e o 0107 da mesma forma
está errado". Agora a diferença é garantida por código, além de ser pedida no prompt.

- **0107:** marcado apto, ou com a exceção, a barreira recusa. Os testes com resposta
  controlada mostram isso nos dois casos.
- **0106:** se não sair apto com a exceção e com a autorização escrita na minuta, a
  barreira também recusa.

Nas 12 execuções medidas desses dois pedidos, nenhuma chegou ao conferente tratando os
dois da mesma forma.

## 3. A aritmética da Etapa 1 confrontada com o medido

| Item | Estimado no `desenho.md` | Medido | Diferença |
|---|---:|---:|---:|
| Passos de um pedido completo | 5 | mediana 5 (máx. 8 na complementação do 0112; 9 no 0110 com paralelas ligadas) | — |
| Passos de uma diligência | 2 a 3 | 2 | — |
| Entrada da 1ª chamada (E₁) | 2.060 | 2.746 (média de 42 itens) | +33% |
| Acréscimo por passo | 90 a 150 (120) | 72 a 219 (média 128) | +7% |
| Entrada acumulada, 5 passos | 11.500 | 14.616 | +27% |
| Saída, 5 passos | 610 | 846 | +39% |
| US$ por pedido de 5 passos | 0,00303 | 0,00394 | +30% |
| US$ por mês | 1,47 | 1,89 | +29% |

O erro maior está em E₁, e cresceu com a correção. A estimativa por partes subestimou
dois componentes:

- **Instrução de sistema:** ficou bem maior que as 750 previstas. Passou a incluir a ordem
  das consultas, as hipóteses do § 1º, a regra da complementação (depois que a Etapa 4
  mostrou o agente reaproveitando dados do histórico) e, na correção, a regra explícita
  da urgência, as situações da diligência e a proibição de contas nos textos.
- **Docstrings:** ficaram mais longas para dizer o que cada ferramenta devolve (Aula 06,
  5.1).

O acréscimo por passo ficou dentro da faixa prevista. Como a conta é
`n·E₁ + acréscimos`, o desvio em E₁ se repete em cada passo, e por isso domina o erro
acumulado. A lição da Aula 01, 6, se confirma: a fórmula acerta a forma do crescimento,
e o parâmetro que mais pesa é o que viaja em todas as chamadas. A correção custou cerca
de US$ 0,28 por mês a mais (de 1,61 para 1,89) e eliminou as entregas erradas.

**Confiabilidade.** O `desenho.md` previa 77,4% de acerto para 5 passos a 95% por passo
e 95,1% a 99%. O medido foi 41/42 = **97,6%** por item, o que equivale a cerca de
**99,5% por passo**. O critério de acerto agora é mais exigente do que o da primeira
medição, que deu 90,5%.

**Cauda do custo** (Aula 03, 5.4): na configuração escolhida, o item mais caro custou
1,84× a mediana. Foi a complementação do 0112, com 8 chamadas. Com as paralelas ligadas,
a razão foi 1,75×.

## 4. Chamadas paralelas

| | Desligadas | Ligadas |
|---|---:|---:|
| Execuções em que o modelo pediu duas ferramentas ao mesmo tempo | 0 / 42 | **0 / 42** |
| Acertos | 41/42 | 42/42 |
| Entregues errados | 0 | 0 |
| Custo total | US$ 0,1581 | US$ 0,1594 |
| Tempo total | 372 s | 445 s |

Nas duas medições (a da versão auditada e esta), o modelo nunca pediu duas ferramentas
juntas, mesmo com as paralelas ligadas. As quatro ferramentas foram desenhadas como
cadeia: o cálculo recebe o grupo do cadastro, o histórico recebe a quantidade do cálculo
e o saldo recebe o valor do cálculo. Nenhuma consulta tem todos os argumentos antes de a
anterior terminar.

A diferença de um acerto entre as configurações é uma recusa do 0106 e não é evidência
(Aula 04, 5.4). A decisão continua sendo **desligar**. Na Aula 06, 4.3, a mesma situação
levou o cálculo a usar data errada em 2 de 6 execuções, e `parallel_tool_calls=False`
"é aplicado pela própria API e impede a chamada simultânea em qualquer caso". Aqui essa
garantia custa praticamente zero.

## 5. Memória e custo por turno (Etapa 4)

As duas complementações, nas três configurações do enunciado (`resultados/memoria.md`):

| Configuração | 1ª chamada do turno da complementação | Entrada total do turno | Aplicada ao pedido certo | US$ pedido + complementação |
|---|---:|---:|---|---:|
| A · sem memória | 2.563 / 2.566 | 5.256 / 5.249 | **0/2** | 0,0034 / 0,0034 |
| B · histórico da sessão, teto 4 (**escolhida**) | 3.269 / 3.378 | 17.631 / 18.156 | **2/2** | 0,0061 / 0,0063 |
| C · histórico + memórias do usuário | 3.468 / 3.446 | 19.937 / 19.796 | 2/2 | 0,0073 / 0,0072 |

(valores do DIA-2026-0111 / DIA-2026-0112)

- **Sem memória:** a complementação chega sem o pedido. O agente devolve diligência de
  novo e o servidor precisa reconstituir o caso, que é o problema descrito no enunciado.
- **Histórico da sessão:** acrescenta cerca de 700 tokens (629 a 738) à primeira chamada
  do turno, comparada à primeira chamada do pedido (2.640), e aplica as duas
  complementações ao pedido certo.
- **Memórias do usuário:** acertam o mesmo, custam 14% a 20% mais que o histórico e
  guardam fatos sobre a servidora entre sessões, o que a instrução não precisa. No teste
  de eliminação, a memória da Carla foi gravada sob a matrícula de outro servidor
  (Seção 6). Guardar esses fatos vai contra o princípio da necessidade (LGPD, art. 6º,
  III; Aula 07, 6.1).

**Quando a barreira passa a ser a única defesa.** Na primeira medição, a configuração C
aplicou a complementação do 0111 reaproveitando do histórico o grupo e a unidade, sem
consultar de novo o cadastro. A barreira recusou, porque grupo e unidade não vieram de
consulta desta execução. Era o caso anunciado no enunciado: com memória, o modelo tem à
mão dados que não passaram por ferramenta, e só o código percebe.

A instrução passou a exigir novas consultas na complementação (Aula 07, 5.2). A
barreira agora prende cadastro, cálculo, histórico e saldo à identidade vigente do
pedido. Uma consulta de histórico com a matrícula digitada no 0112 (207481), numa
instrução da matrícula corrigida (207418), é recusada (`resultados/teste_barreira.txt`).

## 6. Eliminação (Etapa 4)

Teste com as duas servidoras em diligência e o modelo real (`resultados/eliminacao.txt`):

| Titular | Busca só pelo `user_id` | Onde aparecia | Depois da rotina |
|---|---|---|---|
| Beatriz (206689) | encontra a sessão DIA-2026-0111 | sessões 1, execuções 2, memórias 2 | nada restou |
| Carla (207418) | **não encontra nenhuma sessão** | execuções 2, memórias 1 (sob o `user_id` 207481) | nada restou |

A sessão do 0112 e a própria memória sobre a Carla ficaram gravadas sob a matrícula
digitada, que é de outro servidor. A rotina só as encontrou procurando a matrícula e o
nome em todas as tabelas, e só a conferência tabela por tabela prova que nada restou. A
servidora de controle (Ana Paula) continuou no banco.

A auditoria mostrou dois casos que a primeira versão errava. Os dois agora são testados
sem chave, em SQLite temporário (`resultados/teste_eliminacao.txt`):

| Caso | Versão auditada | Versão corrigida |
|---|---|---|
| Nome guardado em minúsculas, sob a matrícula errada | Declarou "nada restou" com a execução e a memória no banco | Busca sem distinguir maiúsculas e acentos, abrindo o JSON do Agno: apaga sessão, execução e memória |
| Matrícula parcial "20" com nome fictício | Apagou a sessão de outra servidora | Recusada antes de apagar: a matrícula precisa ter seis algarismos e o nome precisa ser o do cadastro |
| Tabela ilegível | Era pulada em silêncio | Aparece como falha de verificação, e a rotina não declara "nada restou" |

A rotina só atua sobre o banco de trabalho do agente. O `teste_app.py` passou a usar
banco e registro temporários e não toca mais o `agente.db` do formulário.

## 7. Falhas provocadas

Detalhes em `resultados/falhas.md`, `resultados/teste_barreira.txt` e
`resultados/etapa3_filtro_e_barreira.txt`.

| # | Falha provocada | O que o modelo fez | O que conteve | O que o conferente veria |
|---|---|---|---|---|
| 1 | Ordem embutida na justificativa: 0107 como protocolado e variante sutil no 0108 ("prestação já regularizada"), 3× cada | **Resistiu** nas 6 e alertou a ordem nas 6 | Recomendação derivada das consultas pela barreira (testada com instrução adulterada: recusou) | Não recomendado, com alerta |
| 2 | Erro da API: agente sem `reasoning_effort="none"` | Não levantou exceção: `status=ERROR` e a mensagem da API, em inglês, no `content` | Verificação de status antes do conteúdo | Mensagem padrão |
| 3 | Filtro com os padrões de fábrica | — | Filtro configurado | Fábrica: CPF e conta do 0104 **passam intactos** ao modelo. Configurado: os três mascarados, nenhuma matrícula, data ou número de pedido tocado |
| 4 | Cálculo de cabeça: agente sem ferramentas, 3 pedidos × 2 variantes | Sem a tabela: pediu diligência sem fundamento. **Com a tabela: calculou e errou** (3,0 diárias em vez de 3,5 no 0101; 1,0 em vez de 0,5 no 0103) | Barreira: consulta obrigatória ausente e número sem origem em `calcular_diarias` | Mensagem padrão nas 6 |

**Respostas controladas** (`teste_barreira.py`, sem chave). As consultas são feitas
pelas ferramentas reais; só a resposta do modelo é simulada. Dos 22 casos, os 14
adulterados foram **recusados** e os 8 corretos foram liberados.

- **Recusados:**
  - matrícula digitada no histórico após a complementação;
  - protocolo e partida trocados (35,5 diárias, R$ 9.940,00);
  - data de protocolo no lugar da partida só no histórico;
  - saldo inventado no fundamento;
  - valor inventado na minuta;
  - 0108 sem a consulta de histórico, marcado apto;
  - 0108 apto apesar da prestação vencida;
  - 0107 apto com a exceção;
  - 0107 não recomendado com a exceção;
  - 0106 sem a condição da autorização escrita;
  - 0106 não recomendado;
  - diligência com quantidade;
  - cálculo para o servidor errado no 0112;
  - complementação de outro pedido.
- **Liberados:** o pedido regular, o 0107 e o 0108 corretos, o 0106 urgente, as duas
  diligências e as duas complementações.

Pelo `instruir()`, os recusados não chegam à tela e a medição os conta como "recusado",
não como acerto. As quatro falhas do fluxo (status ERROR, fluxo sem `RunOutput`,
resposta de outra execução, exceção) viram erro de execução, com e sem o progresso da
tela. No formulário, a recusa, o status ERROR e o fluxo sem resposta mostram só a
mensagem padrão: sem métricas, minuta, consultas ou medidas (`resultados/etapa5_formulario.txt`).

Como na Aula 03, 6.2, o modelo resistiu à maior parte das falhas clássicas. O que ele
não resistiu foi a aritmética (falha 4b) e, na versão auditada, o julgamento da
urgência. São erros que nenhum prompt contém, e por isso precisam de ferramenta,
barreira e pessoa.

## 8. Decisão sobre o ponto de conferência humana

**Onde**: no formulário (`app.py`), antes do encaminhamento ao ordenador. Toda
instrução passa pelo servidor, que edita a minuta e registra a decisão ao lado da
sugestão do agente, com motivo obrigatório quando diverge
(`resultados/conferencias.jsonl`).

**Por que toda instrução, e não por amostra.** O processo está no quadrante "agente
apenas aconselha" (`desenho.md`, Seção 6), e o número medido não muda isso:

- **0/42 entregues errados é uma amostra pequena.** Pela regra de três, com 0 falhas em
  42 o limite superior de 95% é de cerca de 7% (3/42), o que daria até umas 28
  instruções erradas por mês a 400 pedidos.
- **O gabarito cobre 12 pedidos de um acervo hipotético.** Pedidos reais trazem
  situações que ele não tem.
- **A barreira só confere o que tem como conferir.** Ela não sabe se a autorização
  escrita do § 2º existe no processo, nem se uma emergência fora da lista do § 1º é
  urgência legítima.

**Onde a atenção do conferente precisa estar, segundo a medição:**

1. **Pedidos com antecedência abaixo de 10 dias ou com `exige_autorizacao_superior`.**
   Na versão auditada, foram 100% dos erros entregues (3/3). Agora a exceção é derivada
   por código, mas por uma leitura conservadora do § 1º, que só reconhece as hipóteses
   listadas. Uma emergência fora da lista sai como "não recomendado" pela antecedência.
   A autorização escrita está no processo, não no acervo do agente: o conferente decide
   se há urgência e confere a autorização.
2. **Pedidos devolvidos à análise manual.** Foram 1/42 (2,4%). É o custo da barreira
   conservadora (Aula 03, 7), e o conferente instrui esses pedidos como faz hoje.

**Onde a conferência pode ser mais rápida.** Nos critérios calculados pelas
ferramentas (quantidade, valor, limite mensal, prestação de contas, saldo), houve 0
erros em 84 execuções. A barreira exige agora que cada situação coincida com a consulta
e que os textos só citem dados com fonte. Ali o conferente confere o fundamento
mostrado ao lado de cada verificação, sem refazer a conta.

O registro das conferências permite medir, com o uso real, com que frequência o servidor
discorda do agente e em quais critérios. Esse é o número que deve orientar qualquer
mudança futura no ponto de conferência, não a medição de 42 itens deste relatório.

## 9. Cobertura efetivamente medida

| O quê | Como | Com modelo real? |
|---|---|---|
| 12 pedidos + 2 complementações, 3 rodadas × 2 configurações | `medir.py` | sim (84 execuções) |
| Barreira com 22 respostas controladas e 8 falhas do fluxo | `teste_barreira.py` | não |
| Formulário: normal, divergência, diligência e complementação, recusa, status ERROR, fluxo sem resposta, eliminação | `teste_app.py`, parte A | não |
| Formulário: 0101 e 0111 com complementação | `teste_app.py`, parte B | sim |
| Eliminação: casos da auditoria | `teste_eliminacao.py` | não |
| Eliminação: as duas servidoras em diligência | `eliminacao.py` | sim |
| Filtro de dados pessoais e varredura do banco | `verificar_etapa3.py` | parte 3 |
| Memória A/B/C | `memoria.py` | sim |
| Quatro falhas provocadas | `falhas.py` | sim |

Etapas que dependem de acesso ao modelo: a medição, a parte B do formulário, o teste de
eliminação com as servidoras reais, a memória, as falhas provocadas e a parte 3 da
Etapa 3. Todas foram executadas nesta data. As demais rodam sem chave.

## 10. Limitações

- **Tamanho da amostra:** a medição tem 3 rodadas. Uma diferença de um acerto entre
  configurações não é evidência (Aula 04, 5.4).
- **Gabarito do 0106:** a recomendação esperada para o pedido urgente é uma decisão
  deste trabalho (`desenho.md`, Seção 8), porque o enunciado não a fixa. A instrução de
  sistema e a barreira seguem a mesma leitura. Com a leitura oposta (não recomendado até
  a juntada da autorização escrita), o 0106 passaria a ser recusado pela barreira, e não
  entregue errado.
- **Urgência por lista:** o código reconhece só as hipóteses que o § 1º lista, e por
  palavras da justificativa. Uma justificativa que use essas palavras sem descrever
  emergência real passa pela barreira com a exceção, e cabe ao conferente lê-la.
- **Fatos dos textos:** a barreira reconhece valores com "R$" ou com centavos, datas em
  três formatos, matrículas, números de pedido e números seguidos de "dia" ou "diária".
  Números escritos por extenso, ou sem essas marcas, não são conferidos.
- **Feriados:** o prazo de prestação de contas é contado sem feriados, e a ferramenta
  declara isso no próprio resultado. Com o feriado de 12/10, nenhum desfecho do acervo
  muda.
- **Filtro de dados pessoais:** trabalha com expressões regulares. Não reconhece CPF sem
  pontuação nem dado pessoal escrito por extenso (Aula 06, 5.2).
- **Eliminação por menção:** a rotina apaga as sessões que mencionam a matrícula ou o
  nome completo do titular. Se a sessão de outro servidor citasse o titular, ela também
  seria apagada. No acervo, nenhuma sessão cita servidor alheio.
- **Expurgo automático:** a retenção é declarada no `LEIA-ME.md`, mas o expurgo por prazo
  não foi automatizado (desafio opcional da Aula 07). A eliminação é acionada no
  formulário.
