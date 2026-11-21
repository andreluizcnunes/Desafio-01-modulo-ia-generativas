# Relatório — Instrução de pedidos de diárias com um agente Agno

Números medidos com o `gpt-5.6-luna` em 21/11/2026, depois das correções da terceira
revisão (`CORRECOES.md`). Os arquivos de origem de cada número estão em `resultados/`.
Como a saída do modelo é probabilística, os valores variam entre execuções (Aula 04,
5.4): sempre que houve repetição, o relatório informa quantas vezes a medição foi feita.

## Atualização da quarta revisão

Os números do provedor abaixo são da revisão `067e97b`. A nova revisão foi exercitada
com Agno real, ferramentas reais e respostas HTTP roteirizadas. As três rodadas por
configuração cobriram os 12 pedidos e as duas complementações, com 42/42 em cada.
As quatro falhas do exercício foram reproduzidas com HTTP local. Os casos adicionais
confirmaram que datas negadas ficam pendentes, argumentos indevidos são barrados
antes de executar e referências descritivas a sistemas não geram ordens falsas.
Os resultados locais estão em `resultados/teste_bloqueio.txt` e a trilha de regressão
está em `CORRECOES.md`.

A instrução de controle com o `gpt-5.6-luna` retornou erro de conexão neste ambiente.
As rodadas reais e as demais verificações que dependem do provedor seguem pendentes
para a quarta revisão. O teste com respostas roteirizadas não produz novas medidas
de acurácia do modelo, tokens, latência do provedor ou custo.

## 1. Resumo

| Medida | Resultado |
|---|---|
| Acertos contra o gabarito (3 rodadas × 14 itens, configuração escolhida) | **42/42** (14, 14 e 14 por rodada) |
| Instruções entregues ao conferente diferentes do gabarito | **0/42** (e 0/42 na outra configuração) |
| Recusadas pela barreira (mensagem padrão, análise manual) | 0/42 |
| Erros de execução | 0/42 |
| Custo por pedido (mediana) / por complementação (média) | US$ 0,0036 / US$ 0,0040 |
| Tempo por item (mediana / máximo) | 7,9 s / 9,0 s |
| Custo mensal estimado (400 pedidos + 68 complementações) | US$ 1,71 |

**O que conta como acerto.** O item precisa chegar ao conferente igual ao gabarito em
recomendação, matrícula, quantidade, valor e exigência de autorização superior, e na
situação de cada um dos seis critérios. A trilha de consultas precisa ter cada
argumento no seu papel, sem consulta ausente e sem consulta fora da etapa (na
diligência, só o cadastro). Nos textos que o conferente lê, cada dado precisa ter
fonte e estar no seu papel: o fundamento de cada critério diz o que a situação diz
(prestação "não atende" fala em vencida), a minuta traz o valor total, o unitário e o
encaminhamento esperados, a minuta urgente traz a condição da autorização escrita, e
nenhum número aparece por extenso. Os alertas precisam ser exatamente os das
categorias esperadas para o pedido (dados pessoais no 0104, ordem ao sistema e
autorização verbal no 0107, autorização escrita no 0106), sem alerta fora delas, sem
valor rotulado no papel errado e sem afirmação que contradiga um critério.

Esse critério é o quarto. O da primeira versão comparava só cinco campos. O da
versão `0f67cf5` (`resultados/historico/medicao_0f67cf5.md`, 41/42) acrescentou
situações, trilha e fatos dos textos, mas conferia só se cada número existia nas
fontes. O da versão `fb61dd9` (`resultados/historico/medicao_fb61dd9.md`, 42/42)
acrescentou o papel de cada dado nos fundamentos e na minuta, mas não nos alertas: a
terceira revisão mostrou que um alerta com o valor unitário como total, ou com a
prestação "regularizada", contava como acerto.

## 2. Medição contra o gabarito

O `gabarito.json` foi gerado por `gabarito.py`, que aplica a norma por código, sem
modelo e sem importar as ferramentas, e foi escrito antes de qualquer execução do
agente. Só a avaliação o lê: `teste_barreira.py` confere que nem o agente nem a tela o
abrem. A conferência da medição (`medir.py`) tem extração própria e não reaproveita o
código da barreira (Aula 03, 5.2). Cada item é classificado em quatro classes: acerto,
recusado (mensagem padrão), erro de execução e **entregue errado**, a classe que mais
pesa no enunciado (`resultados/medicao.md`).

| Configuração | Rodada 1 | Rodada 2 | Rodada 3 | Total | Recusados | Erros | Entregues errados | US$ (42 itens) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Paralelas desligadas (escolhida) | 14/14 | 14/14 | 14/14 | 42/42 | 0 | 0 | **0** | 0,1414 |
| Paralelas ligadas | 14/14 | 14/14 | 14/14 | 42/42 | 0 | 0 | **0** | 0,1441 |

**A medição consegue falhar?** Uma medição que dá 84/84 só vale se for capaz de acusar
o erro. A parte 2b de `teste_barreira.py` entrega à medição, sem passar pela barreira,
as 29 instruções erradas dos testes controlados. Todas são classificadas como
"entregue errado", cada uma pelo motivo certo: "valor total 280.0 ≠ 980.0", "fundamento
de prestacao_contas: falta 'vencida'", "consultas fora da etapa", "texto com número por
extenso", "alerta fora das categorias esperadas". Os dois alertas da terceira revisão
são apontados também pelo papel do dado: "alerta: valor total 280.0 ≠ 980.0" e "alerta
sobre prestacao_contas contradiz a situação com 'regularizada'". As 20 instruções
corretas são classificadas como acerto.

**Os textos medidos são os que o conferente lê.** Os fundamentos, as pendências, os
alertas e a minuta são montados pelo código com os dados das consultas (Seção 7 e
`desenho.md`, Seção 2), e é isso que a medição confere. Os textos que o modelo
escreveu são guardados à parte: a conferência de fontes da barreira não achou dado sem
fonte em nenhum dos 84 itens. Essa conferência não verifica o papel do dado, e por isso
o número não diz que os textos do modelo estavam certos, só que não citavam dado
inexistente. O modelo escreveu alertas em 16 dos 84 itens (0104, 0107 e 0111), todos
nas categorias esperadas ou no motivo da diligência; ficaram registrados em
`resultados/medicao.md`, fora da tela.

### Antes e depois das revisões

| | Versão 8b61395 | Versão 0f67cf5 | Versão fb61dd9 | Versão atual |
|---|---|---|---|---|
| Critério de acerto | 5 campos | + 6 situações, trilha, fatos dos textos | + papel de cada dado, consultas fora da etapa, número por extenso | + alertas por categoria e pelo papel do dado |
| Acertos (paralelas desligadas) | 38/42 | 41/42 | 42/42 | 42/42 |
| Entregues errados | 3 (0106 ×2, 0107 ×1) | 0 | 0 | **0** |
| Quem redige os textos | modelo | modelo | código, menos os alertas | código, inclusive os alertas |
| Consulta de mérito na diligência | executa | executa | executa, e a barreira recusa | barrada antes de executar |
| DIA-2026-0106 | "não recomendado" em 5 de 6 | correto em 5 de 6, recusado em 1 | correto em 6 de 6 | correto em 6 de 6 |

Com 6 execuções por configuração, uma recusa a mais ou a menos não é evidência
(Aula 04, 5.4).

**0106 e 0107.** O enunciado diz que "um agente que trata o 0106 e o 0107 da mesma forma
está errado". A diferença é garantida por código, além de ser pedida no prompt:

- **0107:** marcado apto, ou com a exceção, a barreira recusa. Sem hipótese do § 1º na
  justificativa, a antecedência só pode ser "não atende".
- **0106:** a urgência só é reconhecida porque a justificativa descreve o combate a
  um incêndio em curso, com focos ativos, sem sinal contrário. A condição da autorização expressa e escrita do Secretário
  Adjunto entra na minuta por regra do código.
- **Variante do 0106** (mesmas datas, capacitação programada, "não há incêndio em
  curso", autorização verbal): a menção a incêndio não abre a exceção. A urgência é
  ambígua, a barreira recusa qualquer resposta do modelo e o pedido vai à análise
  manual (`resultados/teste_barreira.txt`, partes 1 e 5). O mesmo vale para «Incêndio.»
  (menção isolada) e para «O incêndio foi extinto. A viagem é para vistoria de rotina.»
  (ocorrência encerrada e rotina).

Nas 12 execuções medidas desses dois pedidos (6 de cada: 3 rodadas × 2 configurações), todas foram acerto.

## 3. A aritmética da Etapa 1 confrontada com o medido

| Item | Estimado no `desenho.md` | Medido | Diferença |
|---|---:|---:|---:|
| Passos de um pedido completo | 5 | mediana 5 (máx. 5 com paralelas desligadas; 8 no 0110 de uma rodada com paralelas ligadas) | — |
| Passos de uma diligência | 2 a 3 | 2 | — |
| Passos de uma complementação | 5 | 5 nas 12 | — |
| Entrada da 1ª chamada (E₁) | 2.060 | 2.682 (média de 42 itens) | +30% |
| Acréscimo por passo | 90 a 150 (120) | 72 a 219 (média 128) | +7% |
| Entrada acumulada, 5 passos | 11.500 | 14.401 | +25% |
| Saída, 5 passos | 610 | 601 | −1% |
| US$ por pedido de 5 passos | 0,00303 | 0,00360 | +19% |
| US$ por mês | 1,47 | 1,71 | +16% |

O erro maior continua em E₁. A estimativa por partes subestimou dois componentes:

- **Instrução de sistema:** ficou bem maior que as 750 previstas. Passou a incluir a ordem
  das consultas, as hipóteses do § 1º, a regra da complementação (depois que a Etapa 4
  mostrou o agente reaproveitando dados do histórico), a regra explícita da urgência e
  as situações da diligência.
- **Docstrings:** ficaram mais longas para dizer o que cada ferramenta devolve (Aula 06,
  5.1).

O acréscimo por passo ficou dentro da faixa prevista. Como a conta é
`n·E₁ + acréscimos`, o desvio em E₁ se repete em cada passo e domina o erro acumulado.
A lição da Aula 01, 6, se confirma: a fórmula acerta a forma do crescimento, e o
parâmetro que mais pesa é o que viaja em todas as chamadas.

A saída caiu de 846 tokens por pedido (versão `0f67cf5`) para 645 (versão `fb61dd9`) e
601 agora. Como o código redige fundamentos, pendências, alertas e minuta, a instrução
de sistema pede ao modelo só uma frase curta nesses campos. O custo mensal estimado foi
de US$ 1,89 para 1,74 e agora 1,71.

**Confiabilidade.** O `desenho.md` previa 77,4% de acerto para 5 passos a 95% por passo
e 95,1% a 99%. O medido foi 42/42 por item na configuração escolhida e 84/84 nas duas.
Isso não prova 100%: com 0 erros em 84, o limite superior de 95% pela regra de três é
de cerca de 3,6% de itens errados (Seção 8).

**Cauda do custo** (Aula 03, 5.4): na configuração escolhida, o item mais caro custou
1,14× a mediana, e nenhum item passou de 5 chamadas ao modelo. Com as paralelas
ligadas, a razão foi 1,62×: o 0110 de uma rodada usou 8 chamadas e saiu correto. Na
medição anterior, foi o inverso (9 chamadas com as paralelas desligadas); a cauda varia
entre execuções e não distingue as configurações.

## 4. Chamadas paralelas

| | Desligadas | Ligadas |
|---|---:|---:|
| Execuções em que o modelo pediu duas ferramentas ao mesmo tempo | 0 / 42 | **0 / 42** |
| Acertos | 42/42 | 42/42 |
| Entregues errados | 0 | 0 |
| Custo total | US$ 0,1414 | US$ 0,1441 |
| Tempo total | 313 s | 355 s |

Nas quatro medições feitas no projeto, o modelo nunca pediu duas ferramentas juntas,
mesmo com as paralelas ligadas. As quatro ferramentas foram desenhadas como cadeia: o
cálculo recebe o grupo do cadastro, o histórico recebe a quantidade do cálculo e o
saldo recebe o valor do cálculo. Nenhuma consulta tem todos os argumentos antes de a
anterior terminar.

As diferenças de custo e de tempo entre as configurações são pequenas e não são
evidência (Aula 04, 5.4). A decisão continua sendo **desligar**. Na Aula 06, 4.3, a
mesma situação levou o cálculo a usar data errada em 2 de 6 execuções, e
`parallel_tool_calls=False` "é aplicado pela própria API e impede a chamada simultânea
em qualquer caso". Aqui essa garantia custa praticamente zero.

## 5. Memória e custo por turno (Etapa 4)

As duas complementações, nas três configurações do enunciado (`resultados/memoria.md`):

| Configuração | 1ª chamada do turno da complementação | Entrada total do turno | Aplicada ao pedido certo | US$ pedido + complementação |
|---|---:|---:|---|---:|
| A · sem memória | 2.520 / 2.523 | 5.166 / 5.169 | **0/2** | 0,0030 / 0,0030 |
| B · histórico da sessão, teto 4 (**escolhida**) | 3.139 / 3.132 | 16.981 / 16.926 | **2/2** | 0,0056 / 0,0056 |
| C · histórico + memórias do usuário | 3.105 / 3.182 | 17.846 / 18.212 | 2/2 | 0,0061 / 0,0062 |

(valores do DIA-2026-0111 / DIA-2026-0112)

- **Sem memória:** a complementação chega sem o pedido. O agente devolve diligência de
  novo e o servidor precisa reconstituir o caso, que é o problema descrito no enunciado.
- **Histórico da sessão:** acrescenta cerca de 540 tokens (535 e 542) à primeira chamada
  do turno, comparada à primeira chamada do pedido (2.597), e aplica as duas
  complementações ao pedido certo.
- **Memórias do usuário:** acertam o mesmo, custam 8% a 11% mais que o histórico (16% a
  18% na medição anterior) e
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
instrução da matrícula corrigida (207418), é recusada. Antes da complementação, no
pedido em diligência, qualquer consulta de mérito é recusada, inclusive o cálculo, o
histórico e o saldo do servidor da matrícula digitada (`resultados/teste_barreira.txt`).

## 6. Eliminação (Etapa 4)

Teste com as duas servidoras em diligência e o modelo real (`resultados/eliminacao.txt`):

| Titular | Busca só pelo `user_id` | Onde aparecia | Depois da rotina |
|---|---|---|---|
| Beatriz (206689) | encontra a sessão DIA-2026-0111 | sessões 1, execuções 2, memórias 1 | nada restou |
| Carla (207418) | **não encontra nenhuma sessão** | execuções 2, memórias 1 (sob o `user_id` 207481) | nada restou |

A sessão do 0112 e a própria memória sobre a Carla ficaram gravadas sob a matrícula
digitada, que é de outro servidor. A rotina só as encontrou procurando a matrícula e o
nome em todas as tabelas, e só a conferência tabela por tabela prova que nada restou. A
servidora de controle (Ana Paula) continuou no banco.

A primeira revisão mostrou três casos que a versão 8b61395 errava. Os três agora são testados
sem chave, em SQLite temporário (`resultados/teste_eliminacao.txt`):

| Caso | Versão 8b61395 | Versão corrigida |
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
| 1 | Ordem embutida na justificativa: 0107 como protocolado e variante sutil no 0108 ("prestação já regularizada"), 3× cada | **Resistiu** nas 6 e alertou nas 6 (alertas registrados, fora da tela) | Recomendação derivada das consultas pela barreira (testada com instrução adulterada: recusou); fundamento da prestação redigido pelo código com a frase do histórico ("VENCIDA") | Não recomendado. No 0107, com o alerta do código sobre a ordem ao sistema; no 0108 sutil, sem alerta (o texto não se dirige ao sistema), com a prestação VENCIDA no fundamento |
| 2 | Erro da API: agente sem `reasoning_effort="none"` | Não levantou exceção: `status=ERROR` e a mensagem da API, em inglês, no `content` | Verificação de status antes do conteúdo | Mensagem padrão |
| 3 | Filtro com os padrões de fábrica | — | Filtro configurado | Fábrica: CPF e conta do 0104 **passam intactos** ao modelo. Configurado: os três mascarados, nenhuma matrícula, data ou número de pedido tocado |
| 4 | Cálculo de cabeça: agente sem ferramentas, 3 pedidos × 2 variantes | Nesta execução, sem a tabela, devolveu diligência nas 3; **com a tabela, calculou e errou nas 3** (3,0 diárias em vez de 3,5 no 0101; 1,0 em vez de 0,5 no 0103; 4,0 em vez de 4,5 no 0110). Na execução anterior de 21/11, pediu diligência nas 6 | Barreira: consulta obrigatória ausente e número sem origem em `calcular_diarias` | Mensagem padrão nas 6, em todas as execuções |

A falha 4 mostra a variação entre execuções da Aula 04, 5.4: o mesmo teste levou o
modelo a errar a conta numa execução e a se recusar a fazê-la em outra. Em todas, o que
o conferente viu foi a mensagem padrão, porque a barreira não depende do que o modelo
decide fazer.

**Respostas controladas** (`teste_barreira.py`, sem chave). As consultas são feitas
pelas ferramentas reais; só a resposta do modelo é simulada. São 50 casos:

- **18 recusados** (mensagem padrão): matrícula digitada no histórico após a
  complementação; protocolo e partida trocados; data de protocolo no lugar da partida
  só no histórico; 0108 apto sem a consulta de histórico, apto só com o histórico
  barrado pela guarda e apto apesar da prestação vencida; 0107 apto com a exceção e
  não recomendado com a exceção; 0106 não recomendado; quatro variantes do 0106 sem
  urgência legítima (a da capacitação, nas duas respostas, «Incêndio.» e «O incêndio
  foi extinto…»); diligência com quantidade; tentativa de cálculo no 0111 sem retorno;
  cálculo, histórico e saldo de 207481 no 0112 em diligência; cálculo para o servidor
  errado no 0112; complementação de outro pedido.
- **12 liberados com os textos do código**, em que o modelo acertou os campos e errou o
  texto: saldo inventado no fundamento; valor inventado na minuta; valor unitário como
  total na minuta (R$ 280,00); valor por extenso na minuta; prestação vencida descrita
  como "regularizada e aprovada"; minuta do 0106 que dispensa a autorização escrita; e
  seis alertas do modelo (saldo inventado, valor por extenso, «O valor total correto é
  R$ 280,00», «A prestação de contas foi regularizada», autorização escrita
  "dispensável" e um alerta fora das categorias do enunciado). Em todos, o trecho
  errado não aparece na instrução entregue.
- **20 liberados como vieram:** a instrução correta dos 12 pedidos e das 2
  complementações, os casos-controle do 0107, do 0108 e do 0106, as duas diligências
  e o 0101 com uma consulta de histórico barrada antes do cadastro e refeita depois.

Pelo `instruir()`, os recusados não chegam à tela e a medição os conta como "recusado".
As sete falhas do fluxo (status ERROR, fluxo sem `RunOutput`, resposta de outra
execução, exceção, fluxo sem evento inicial com uma execução anterior válida no banco,
banco que devolve a execução anterior e resposta concluída sem identificador) viram
erro de execução, com e sem o progresso da tela, e a instrução anterior não é
reaproveitada; a resposta desta execução, no pedido e na complementação, é entregue
(controles da parte 3b). No formulário, a recusa, o status ERROR, os três fluxos sem
resposta, a resposta sem identificador e a tentativa de mérito no 0112 em diligência
mostram só a mensagem padrão: sem métricas, minuta, consultas ou medidas
(`resultados/etapa5_formulario.txt`).

**Guarda das consultas de mérito** (`teste_bloqueio.py`, sem chave). Com o Agno real e
as requisições ao modelo interceptadas localmente, o modelo roteirizado tenta cálculo,
histórico e saldo no 0112 depois do DIVERGE, e o cálculo no 0111 sem retorno. Nenhuma
dessas funções executa: o gancho de ferramenta as barra antes, e o modelo recebe só o
motivo. As mensagens interceptadas e o banco temporário não têm dado de mérito, e a
instrução é recusada. As diligências legítimas, as complementações na mesma sessão
(0112 com a matrícula 207418, 0111 com o retorno) e o pedido regular seguem com as
quatro ferramentas (`resultados/teste_bloqueio.txt`). Sem o gancho, o teste falha.

Como na Aula 03, 6.2, o modelo resistiu à maior parte das falhas clássicas. O que ele
não resistiu foi a aritmética (falha 4, em 20/11) e, na versão `8b61395`, o julgamento
da urgência. São erros que nenhum prompt contém, e por isso precisam de ferramenta,
barreira e pessoa.

## 8. Decisão sobre o ponto de conferência humana

**Onde**: no formulário (`app.py`), antes do encaminhamento ao ordenador. Toda
instrução passa pelo servidor, que edita a minuta e registra a decisão ao lado da
sugestão do agente, com motivo obrigatório quando diverge
(`resultados/conferencias.jsonl`).

**Por que toda instrução, e não por amostra.** O processo está no quadrante "agente
apenas aconselha" (`desenho.md`, Seção 6), e o número medido não muda isso:

- **0/84 entregues errados é uma amostra pequena.** Pela regra de três, com 0 falhas em
  84 o limite superior de 95% é de cerca de 3,6% (3/84), o que daria até umas 14
  instruções erradas por mês a 400 pedidos.
- **O gabarito cobre 12 pedidos de um acervo hipotético.** Pedidos reais trazem
  situações que ele não tem.
- **A barreira só confere o que tem como conferir.** Ela não sabe se a autorização
  escrita do § 2º existe no processo, nem se uma emergência fora da lista do § 1º é
  urgência legítima. Nenhum texto do modelo vai à tela: fundamentos, pendências,
  alertas e minuta são do código, que só sabe dar os alertas das categorias que
  verifica.

**Onde a atenção do conferente precisa estar, segundo a medição:**

1. **Pedidos com antecedência abaixo de 10 dias ou com `exige_autorizacao_superior`.**
   Na versão `8b61395`, foram 100% dos erros entregues (3/3). Agora a exceção é derivada
   por código, por uma leitura conservadora do § 1º: só a hipótese listada, com
   situação emergencial em curso descrita na justificativa e sem sinal contrário. Uma emergência fora da lista sai como "não recomendado" pela
   antecedência, e uma justificativa ambígua vai à análise manual. A autorização
   escrita está no processo, não no acervo do agente: o conferente decide se há
   urgência e confere a autorização.
2. **Pedidos devolvidos à análise manual.** Foram 0/84 nesta medição e na da versão
   `fb61dd9`, e 1/42 na da versão `0f67cf5`. É o custo da barreira conservadora (Aula 03, 7), e o conferente instrui
   esses pedidos como faz hoje.

**Onde a conferência pode ser mais rápida.** Nos critérios calculados pelas
ferramentas (quantidade, valor, limite mensal, prestação de contas, saldo), houve 0
erros em 84 execuções. Cada situação precisa coincidir com a consulta, e o fundamento
mostrado ao lado de cada verificação é a frase da própria ferramenta, copiada pelo
código. Ali o conferente lê o fundamento, sem refazer a conta.

O registro das conferências permite medir, com o uso real, com que frequência o servidor
discorda do agente e em quais critérios. Esse é o número que deve orientar qualquer
mudança futura no ponto de conferência, não a medição de 42 itens deste relatório.

## 9. Cobertura efetivamente medida

| O quê | Como | Com modelo real? |
|---|---|---|
| 12 pedidos + 2 complementações, 3 rodadas × 2 configurações | `medir.py` | sim (84 execuções) |
| Barreira com 50 respostas controladas, 14 falhas do fluxo, 4 controles do vínculo com a execução, a medição sem a barreira (parte 2b) e a leitura da urgência | `teste_barreira.py` | não |
| Guarda das consultas de mérito, com o Agno real e o modelo interceptado: mensagens, banco e funções executadas | `teste_bloqueio.py` | não |
| Formulário: normal, minuta e alertas errados do modelo fora da tela, alertas exigidos, divergência, diligência e complementação, recusa, status ERROR, três fluxos sem resposta, resposta sem identificador, tentativa de mérito barrada, eliminação | `teste_app.py`, parte A | não |
| Formulário: 0101 e 0111 com complementação | `teste_app.py`, parte B | sim |
| Eliminação: casos da auditoria | `teste_eliminacao.py` | não |
| Eliminação: as duas servidoras em diligência | `eliminacao.py` | sim |
| Filtro de dados pessoais e varredura do banco | `verificar_etapa3.py` | parte 3 |
| Memória A/B/C | `memoria.py` | sim |
| Quatro falhas provocadas | `falhas.py` | sim |

Na terceira revisão (`067e97b`), as etapas que dependem do modelo foram a medição, a parte B do formulário, o teste de
eliminação com as servidoras reais, a memória, as falhas provocadas e a parte 3 da
Etapa 3. Todas foram executadas em 21/11/2026, depois das correções da terceira
revisão. As demais rodam sem chave. Para a quarta revisão, veja a atualização acima.

## 10. Limitações

- **Tamanho da amostra:** a medição tem 3 rodadas por configuração. Uma diferença de
  um acerto entre configurações ou entre medições não é evidência (Aula 04, 5.4).
- **Gabarito do 0106:** a recomendação esperada para o pedido urgente é uma decisão
  deste trabalho (`desenho.md`, Seção 8), porque o enunciado não a fixa. A instrução de
  sistema e a barreira seguem a mesma leitura. Com a leitura oposta (não recomendado até
  a juntada da autorização escrita), o 0106 passaria a ser recusado pela barreira, e não
  entregue errado.
- **Urgência por palavras:** o código reconhece só as hipóteses que o § 1º lista, com
  contexto afirmativo de emergência em curso na mesma frase, e recusa a exceção diante
  de menção isolada, negada, ocorrência encerrada, contexto passado, rotina, atividade
  programada, autorização verbal ou ordem ao sistema. Continua sendo leitura de
  palavras: uma justificativa que descreva, com essas palavras, uma emergência que não
  existe ainda passa com a exceção. Por isso a autorização escrita e a leitura da
  justificativa continuam com o conferente.
- **Alertas só do código:** o conferente vê os alertas que o código sabe dar (dados
  pessoais, ordem ao sistema, autorização verbal, autorização escrita na urgência). Um
  alerta útil que o modelo perceba fora dessas categorias não chega à tela; fica
  registrado no resultado (`alertas_do_modelo`) e na medição.
- **Guarda por estado da execução:** a guarda das consultas de mérito confia no
  resultado do cadastro desta execução e no pedido vigente que a aplicação calcula. Uma
  complementação que o código não consegue atribuir a um papel bloqueia o mérito e leva
  à análise manual.
- **Diagnóstico dos textos do modelo:** os textos que o código substitui são conferidos
  só pelas fontes, não pelo papel do dado. O "0 de 84" da Seção 2 não mede o quanto o
  modelo acertaria sem a redação por código.
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
