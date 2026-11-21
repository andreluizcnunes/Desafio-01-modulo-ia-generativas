# Desenho do processo — Instrução de pedidos de diárias (SEMA-MT)

Etapa 1 do Desafio 01. Este documento foi escrito **antes de qualquer código**, como
pede a Aula 01 (Seção 9: as cinco perguntas antes da tecnologia). Os números de
custo aqui são **estimativas**; o `relatorio.md` os confronta com o que foi medido.

---

## 1. O processo como o servidor o executa hoje

1. Recebe o pedido protocolado (matrícula, nome, destino, datas, transporte, justificativa).
2. Confere se o pedido está completo (todas as datas, destino, justificativa) — art. 9º.
3. Consulta o **cadastro funcional** pela matrícula e confere se o nome bate; anota cargo,
   grupo da diária e unidade de lotação — art. 3º e art. 9º.
4. Conta a **antecedência** em dias corridos entre o protocolo e a partida; se for menor
   que 10 dias, verifica se a justificativa descreve urgência (§ 1º) e se há autorização
   **escrita** do Secretário Adjunto (§ 2º) — art. 5º.
5. Calcula a **quantidade** de diárias (uma por pernoite + meia no retorno; meia sem
   pernoite) e o **valor** pela tabela do Anexo I (grupo × destino) — art. 3º e 4º.
6. Consulta o **histórico de diárias**: soma as diárias do mês da partida e confere o
   limite de 10 por mês — art. 6º.
7. Confere as **prestações de contas** pendentes: vencida (mais de 5 dias úteis após o
   retorno) impede nova diária; no prazo não impede — art. 7º.
8. Consulta o **saldo da dotação** da unidade e compara com o valor — art. 8º.
9. Redige a instrução: recomendação (apto / não recomendado / diligência) e minuta do
   despacho; encaminha ao **ordenador de despesa**, que defere ou indefere — art. 10.
10. Se o pedido foi devolvido em diligência, ao receber a complementação, **reconstitui o
    caso desde o começo** e refaz as etapas 2 a 9.

## 2. O processo como o agente o executará

| # | Quem faz | O quê | Regra |
|---|---|---|---|
| 1 | Código | Recebe o pedido; o **filtro de dados pessoais** mascara CPF e conta bancária antes do modelo (Aula 06, 5.2) | LGPD art. 6º, III |
| 2 | Modelo → `consultar_servidor` | Cadastro pela matrícula; a ferramenta diz se o nome confere; não devolve CPF nem e-mail | art. 9º |
| 3 | Modelo → `calcular_diarias` | Quantidade, valor e antecedência **calculados no código** | art. 3º, 4º, 5º |
| 4 | Modelo → `consultar_historico_diarias` | Diárias do mês + pedidas vs. limite; prestações vencidas ou no prazo, **no código** | art. 6º, 7º |
| 5 | Modelo → `consultar_saldo_diarias` | Saldo da unidade vs. valor, **no código** | art. 8º |
| 6 | Modelo | Devolve o objeto `Instrucao` validado (Pydantic) com as seis verificações, recomendação e minuta | Aula 02, 5 |
| 7 | Código | **Barreira**: confere `status`, e que toda matrícula e data usadas constam do pedido ou da complementação, e que os números vieram das ferramentas (Aula 03, 7; Aula 04, 8; Aula 06, 5.3) | — |
| 7b | Código | **Textos factuais**: com a instrução liberada, monta os fundamentos, as pendências e a minuta com os dados das consultas válidas, cada um no seu papel (valor unitário, total, saldo, situação da prestação), no lugar dos textos do modelo; os alertas do modelo só passam se cada dado tiver fonte (Aula 04, 8; Aula 01, 8) | arts. 4º a 10 |
| 8 | Servidor | Confere no formulário, edita a minuta, registra o encaminhamento que decidiu (Aula 06, 6.2) | — |
| 9 | Ordenador | Defere ou indefere | art. 10 |

Na diligência, a complementação é enviada **na mesma sessão** (`session_id` = número do
pedido) e o agente recupera o caso pelo histórico (Aula 07, 2).

O modelo **não calcula nada**: antecedência, quantidade, valor, soma do mês, prazo da
prestação e comparação com o saldo saem prontos das ferramentas (Aula 06, 1: "falta de
habilidade para cálculos precisos"; Aula 03, problema da abertura).

O modelo também **não redige nenhum trecho factual que chegue ao conferente**. A
primeira barreira conferia se cada número citado existia nas fontes, e isso deixava
passar um valor certo no lugar errado: o valor unitário de R$ 280,00 apresentado como
total, ou uma prestação vencida descrita como "regularizada". Por isso, depois que as
situações, a recomendação, a quantidade, o valor e a exceção são conferidos, o código
monta os fundamentos (a frase da ferramenta que sustenta cada situação), as pendências
e a minuta com os dados das consultas. Do modelo, chegam à tela os campos estruturados
conferidos e os alertas, que só passam se cada dado tiver fonte, sem número por extenso
e sem afirmar que a autorização escrita é dispensável. A minuta continua editável pelo
servidor.

## 3. Quadro PEAS (Aula 01, Seção 1.1)

| Elemento | Agente de instrução de diárias |
|---|---|
| **Medida de desempenho** (Performance) | Por pedido e por complementação, comparado ao `gabarito.json`: (a) **recomendação** igual à do gabarito; (b) **quantidade** e **valor** iguais (nulos na diligência); (c) `exige_autorizacao_superior` igual; (d) **nenhuma instrução entregue ao conferente com dado que não veio do pedido nem das ferramentas** (barreira). Secundárias: tokens, tempo e custo por pedido. Instrução recusada pela barreira conta como "devolvida à análise manual", não como acerto. |
| **Ambiente** (Environment) | Pedidos protocolados e complementações; cadastro funcional (`servidores.csv`); histórico de diárias e prestações (`historico_diarias.csv`); tabela de valores e regras (`tabela_diarias.json`); saldo das unidades (`unidades.json`); a IN SEMA nº 07/2026 (`normas.md`); o servidor conferente e o ordenador. |
| **Atuadores** (Actuators) | Chamadas às quatro ferramentas de consulta; o objeto `Instrucao` (verificações, recomendação, pendências, alertas, minuta do despacho). O agente **não** defere, não indefere e não altera dado algum. |
| **Sensores** (Sensors) | Texto do pedido (já filtrado de CPF e conta), texto da complementação, resultados das ferramentas e o histórico da sessão do pedido. |

## 4. Número de passos e confiabilidade composta (Aula 01, Seção 6)

Cada **chamada ao modelo** é um passo. As quatro ferramentas formam uma **cadeia de
dependência**: o cálculo precisa do grupo (vem do cadastro), o histórico precisa da
quantidade (vem do cálculo) e o saldo precisa da unidade (cadastro) e do valor (cálculo).
Por isso as chamadas paralelas ficam **desligadas** (Aula 06, 4.3) e o caminho completo é:

| Passo | Chamada ao modelo |
|---|---|
| 1 | Lê o pedido e pede `consultar_servidor` |
| 2 | Recebe o cadastro e pede `calcular_diarias` |
| 3 | Recebe o cálculo e pede `consultar_historico_diarias` |
| 4 | Recebe o histórico e pede `consultar_saldo_diarias` |
| 5 | Recebe o saldo e devolve a `Instrucao` |

Pedido completo: **5 passos**. Diligência por dado ausente: 2 a 3 passos. Complementação:
mais 5 passos.

| Passos | 99% por passo | 95% por passo |
|---:|---:|---:|
| 1 | 99,0% | 95,0% |
| 3 | 97,0% | 85,7% |
| **5** | **95,1%** | **77,4%** |
| 10 (pedido + complementação) | 90,4% | 59,9% |

Leitura: a 95% por passo, cerca de **1 em cada 4 pedidos** completos teria algum passo
errado. Em 400 pedidos por mês, isso são cerca de 90 instruções com algum erro. A essa
taxa, a instrução **não pode** seguir sem barreira em código e conferência humana. A
cadeia mínima de 5 passos já é a mais curta possível com quatro consultas dependentes
("encurtar a cadeia é a intervenção mais eficaz", Aula 01, 6).

## 5. Custo por passos (Aula 01, Seção 6; Aula 06, Seção 4.2)

**Entrada da primeira chamada**, estimada por partes (≈ 4 caracteres por token):

| Parte | Tokens estimados |
|---|---:|
| Instrução de sistema (regras da IN, ordem das consultas, proibição de supor dados) | 750 |
| Esquemas das 4 ferramentas (nome, docstring, parâmetros) | 550 |
| Esquema da saída `Instrucao` (Pydantic → JSON Schema) | 500 |
| Pedido (dados + justificativa) | 200 |
| Acréscimos do framework | 60 |
| **Primeira chamada (E₁)** | **≈ 2.060** |

Cada passo seguinte reenvia tudo e **acrescenta** o pedido de ferramenta e o resultado,
estimado em 90 a 150 tokens (média 120), conforme a execução de referência do enunciado.

Entrada acumulada em *n* passos: `n·E₁ + 120·(1 + 2 + … + (n−1))`.

| Passos | Entrada do último passo | Entrada acumulada | Saída estimada | US$ (luna) |
|---:|---:|---:|---:|---:|
| 1 | 2.060 | 2.060 | 450 | 0,00095 |
| 3 | 2.300 | 6.540 | 530 | 0,00194 |
| **5** | **2.540** | **11.500** | **610** | **0,00303** |
| 10 | 3.140 | 26.000 | 810 | 0,00617 |

Preços do gpt-5.6-luna: US$ 0,20 por milhão de tokens de entrada e US$ 1,20 por milhão de
saída (Aula 01, 6; Aula 06, 4.2). A saída considera cerca de 40 tokens por pedido de
ferramenta e 450 na `Instrucao` final.

**Volume mensal adotado**: 400 pedidos por mês ("centenas de pedidos", enunciado), com
17% voltando em diligência (2 dos 12 pedidos do acervo), ou seja, cerca de 68
complementações.

| Item | Execuções/mês | US$ por execução | US$/mês |
|---|---:|---:|---:|
| Pedidos (5 passos) | 400 | 0,00303 | 1,21 |
| Complementações (5 passos + histórico ≈ +800 tokens por passo) | 68 | 0,00383 | 0,26 |
| **Total** | 468 | — | **≈ 1,47** |

O custo é baixo. O que pesa na decisão é a confiabilidade (Seção 4), não o custo. O
`tool_call_limit=8` (Figura 1 do enunciado) cobre os 4 passos com ferramenta e deixa
margem para uma repetição por erro de argumento. Ele também impede a cauda de custo da
Aula 03, 5.4.

## 6. Quadrante de autonomia (Aula 01, Seção 5)

| | Erro detectado logo | Erro detectado tarde |
|---|---|---|
| **Reversível** | Agente age dentro de limites | Agente age, com auditoria por amostra |
| **Irreversível** | Agente age mediante aprovação | **Agente apenas aconselha** ← *instrução de diárias* |

- **Detecção**: **tarde**. O erro (diária concedida a quem tem prestação vencida, urgência
  aceita sem autorização escrita) costuma aparecer meses depois, na auditoria (enunciado,
  "Problema").
- **Reversibilidade**: só em tese. A diária paga indevidamente "pode ser devolvida", mas
  isso exige processo de ressarcimento contra o servidor, depois que o dinheiro já foi
  gasto na viagem e a despesa já foi empenhada e paga. Na prática o efeito do erro está
  consumado quando ele é notado. Isso aproxima o processo do quadrante irreversível.
- **Norma**: o art. 10 reserva a decisão ao ordenador de despesa.

**Conclusão**: o processo fica no quadrante em que **o agente não age sozinho**. O agente
**prepara a instrução e a minuta, e a pessoa confere e assina** (Aula 01, 5: "ali o
agente prepare a minuta e a pessoa assine"). A conferência humana é uma etapa do fluxo
(Aula 05, 5) e tem lugar físico no formulário (Aula 06, 6.2), onde o servidor registra o
encaminhamento que decidiu ao lado do sugerido.

## 7. Informação que o agente não terá (Aula 01, Seção 9, quarta pergunta)

- **Autorização escrita do Secretário Adjunto** (art. 5º, § 2º): fica no processo físico
  ou eletrônico, não no acervo. Por isso o agente só **sinaliza** `exige_autorizacao_superior`;
  quem confere a autorização é o servidor.
- **Feriados**: o prazo de prestação de contas é contado em dias úteis sem feriados, e a
  ferramenta declara esse limite no próprio resultado (como o `calcular_prazo` da
  Aula 06, 3.2).
- **Legitimidade da urgência**: a justificativa é texto livre. O agente avalia se descreve
  situação do § 1º, mas essa é exatamente a decisão que cabe à pessoa.

## 8. Decisão sobre o pedido urgente (DIA-2026-0106)

O enunciado não fixa a recomendação esperada para o pedido urgente legítimo, só que ele
não pode ser tratado como o DIA-2026-0107. Pela norma, a urgência do § 1º **admite**
antecedência menor, e o § 2º a condiciona à autorização escrita, que será registrada no
processo. Adotamos então: antecedência **atende** pelo § 1º, recomendação
**`apto_para_autorizacao`** com **`exige_autorizacao_superior = true`**. O despacho fica
condicionado à juntada da autorização escrita, e é esse campo que avisa o conferente.
O DIA-2026-0107 alega só autorização **verbal** (que o § 2º diz não suprir), descreve
capacitação (não é urgência do § 1º) e traz ordem dirigida ao sistema. Fica com
**`nao_recomendado`** e alerta da ordem embutida.

**Quem decide que há urgência.** Uma marcação feita pelo modelo não basta para abrir a
exceção. A barreira (`barreira.py`) reconhece a urgência por código, pelas hipóteses
que o § 1º lista (incêndio, desastre ambiental, infração ambiental em curso,
determinação judicial), e só a aceita quando `calcular_diarias` devolveu antecedência
"NÃO ATENDE". Nessa situação, a instrução precisa vir como apto (se os demais critérios
atendem), com `exige_autorizacao_superior = true` e com a minuta condicionando a
autorização à autorização escrita do Secretário Adjunto. Em qualquer outro caso, a
exigência fica `false`. A leitura é conservadora: o § 1º usa "como", e uma emergência
fora da lista sai como "não recomendado" pela antecedência. Quem pode reconhecê-la é o
conferente, não o agente.
