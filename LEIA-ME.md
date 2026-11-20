# Desafio 01 — Instrução de Pedidos de Diárias (SEMA-MT)

Um único agente **Agno** instrui pedidos de diárias de ponta a ponta: consulta os dados
do órgão por quatro ferramentas, devolve a instrução em objeto validado e a entrega ao
servidor em um formulário de conferência. A decisão continua com o ordenador de
despesa (IN SEMA nº 07/2026, art. 10). Todos os dados são hipotéticos.

## Como executar

Requisitos: Python 3.10 ou superior. Chave da OpenAI em `.env`, que nunca é versionado.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env          # e preencha OPENAI_API_KEY
```

| Comando | O que faz | Precisa de chave? |
|---|---|---|
| `python teste_ferramentas.py` | Testa as quatro ferramentas com casos dos pedidos (Etapa 2) | Não |
| `python gabarito.py` | Gera o `gabarito.json` aplicando a norma por código | Não |
| `python verificar_etapa3.py` | Filtro de dados pessoais e barreira; instrui o 0104 e varre o banco (Etapa 3) | Sim |
| `python memoria.py` | Custo da memória por turno nas duas complementações (Etapa 4) | Sim |
| `python eliminacao.py` | Rotina de eliminação testada com as duas servidoras em diligência (Etapa 4) | Sim |
| `streamlit run app.py` | Formulário de conferência (Etapa 5) | Sim |
| `python teste_app.py` | Teste do formulário de ponta a ponta, sem navegador (Etapa 5) | Sim |
| `python medir.py` | Três rodadas contra o gabarito, paralelas desligadas e ligadas | Sim |
| `python falhas.py` | Quatro falhas provocadas | Sim |

As saídas ficam em `resultados/`. Os bancos SQLite dos testes são apagados ao final de
cada script, junto com os arquivos `-wal` e `-shm`.

## Estrutura

| Arquivo | Papel |
|---|---|
| `desenho.md` | Etapa 1: processo, PEAS, confiabilidade composta, custo por passos, quadrante |
| `ferramentas.py` | As quatro ferramentas, funções Python comuns com as contas no código |
| `instrutor.py` | O agente: contrato `Instrucao`, instrução de sistema, filtro, limites, memória, `instruir()` |
| `barreira.py` | A verificação em código entre o agente e o conferente |
| `memoria.py`, `eliminacao.py` | Etapa 4: custo da memória e rotina de eliminação |
| `app.py` | Etapa 5: formulário Streamlit |
| `gabarito.py`, `medir.py`, `falhas.py` | Medição contra o gabarito e falhas provocadas |
| `relatorio.md` | Números medidos, falhas e decisão sobre o ponto de conferência humana |
| `dados/` | O acervo de entrada do desafio, copiado sem alteração |

## Decisões técnicas e justificativas

| Decisão | Justificativa | Origem |
|---|---|---|
| Um agente, quatro ferramentas, modelo `gpt-5.6-luna` | Modelo de referência do curso; a tarefa é escolher entre quatro ferramentas bem descritas, o que o nível de menor custo resolve | Aula 03, 5.3; Aula 06, 4.1 |
| Contas no código (antecedência, quantidade, valor, soma do mês, prazo da prestação, saldo) | "A aritmética é onde o modelo erra com segurança": na falha 4, o modelo calculou 3,0 diárias em vez de 3,5 | Aula 06, 1; `resultados/falhas.md` |
| Ferramentas não devolvem CPF nem e-mail | Minimização (LGPD, art. 6º, III) | Aula 06, 5.2 |
| `output_schema=Instrucao`, sem campos além do contrato | A tela e a medição leem campos, não texto | Aula 02, 5; Aula 06, 6.1 |
| `reasoning_effort="none"` | Exigido pela família GPT-5.6 com ferramentas; sem ele a API devolve erro (falha 2) | Aula 03, 3.2; Aula 06, 5.3 |
| `telemetry=False`, `debug_mode` desligado | O registro de depuração leva o pedido inteiro | Aula 06, 5.2 e 5.4 |
| `PIIDetectionGuardrail` com SSN, cartão e telefone desligados; CPF por máscara; conta/agência | Os padrões de fábrica não mascaram o CPF brasileiro (falha 3) | Aula 06, 5.2 |
| `resposta.status` conferido antes do conteúdo | O Agno devolve o erro da API como conteúdo | Aula 06, 5.3 |
| Barreira em `barreira.py` | "A barreira pertence ao código, e não ao prompt" | Aula 01, 8; Aula 03, 7; Aula 04, 8 |
| `session_id` = número do pedido; `user_id` = matrícula do pedido; informados em cada `run` | Um agente em cache sem misturar pedidos; o `user_id` individualiza a pessoa | Aula 07, 2 e 5.1 |
| Formulário com `st.form`, `st.status`, minuta editável e registro da decisão | A conferência humana precisa de lugar físico na aplicação | Aula 06, 6.2 e 6.3 |
| Pedido urgente (0106): apto com `exige_autorizacao_superior=true` | O enunciado não fixa; ver `desenho.md`, Seção 8 | art. 5º, §§ 1º e 2º |

## As perguntas do enunciado

O enunciado anuncia "quatro perguntas", mas lista três. Respondo às três listadas.

### 1. Que configuração de chamadas paralelas, teto de chamadas e memória você escolheu, e com base em que número?

- **Chamadas paralelas: desligadas** (`request_params={"parallel_tool_calls": False}`).
  - As quatro ferramentas formam uma cadeia (grupo → cálculo → histórico e saldo), o caso
    em que a Aula 06, 4.3, mediu o cálculo feito com data errada em 2 de 6 execuções.
  - Na nossa medição, com as paralelas **ligadas**, o modelo pediu duas ferramentas ao
    mesmo tempo em **0 de 42** execuções, com os mesmos **38/42** acertos e custo
    praticamente igual (US$ 0,1430 contra 0,1442).
  - Desligar custa zero e passa a garantia do comportamento do modelo para a API.
- **Teto: `tool_call_limit=8`.**
  - O pedido completo usa 4 ferramentas em **5 chamadas** ao modelo (mediana medida, igual
    ao previsto no `desenho.md`).
  - O máximo observado foi 7 ferramentas em 8 chamadas, na complementação do 0112. O teto
    acomoda esse caso e corta a cauda: a razão entre o item mais caro e a mediana foi 1,9×
    (Aula 03, 5.4).
- **Memória: histórico da sessão com teto de 4 execuções**, sem memórias do usuário.
  - Sem memória, as complementações foram aplicadas ao pedido certo em **0/2**. Com o
    histórico, em **2/2**, acrescentando cerca de 700 tokens à primeira chamada do turno.
  - As memórias do usuário também acertaram 2/2, mas custaram 6% a 20% mais e guardaram
    fatos da servidora entre sessões, inclusive sob a matrícula de outro servidor no caso
    0112.
  - É a mesma conclusão da Aula 07, 3.3 e 7: histórico completo com teto para conversas
    curtas. Pedido mais complementação são 2 execuções, e o teto de 4 deixa folga para
    uma segunda complementação.

### 2. Como o sistema impede que uma instrução fundamentada em dado inventado chegue ao conferente?

Por cinco camadas, todas em código:

1. **As contas não ficam com o modelo.** Quantidade, valor, antecedência, soma do mês,
   prazo da prestação e comparação com o saldo saem prontos das ferramentas. Na falha 4b,
   o modelo que calculou de cabeça errou o art. 4º (3,0 diárias em vez de 3,5).
2. **`resposta.status` é conferido antes do conteúdo.** O erro da API chega como texto e
   com status `ERROR` (falha 2), e vai para a mensagem padrão.
3. **O contrato Pydantic.** Saída fora do esquema `Instrucao` não é aceita.
4. **A barreira (`barreira.py`)** confere o que o agente fez contra o que a aplicação tem
   em mãos:
   - toda matrícula consultada e toda data usada constam do pedido ou da complementação;
   - grupo e unidade vieram do cadastro dessa matrícula;
   - quantidade e valor da instrução são exatamente os que `calcular_diarias` devolveu,
     para o grupo do servidor cuja matrícula está na instrução, e o nome desse servidor
     confere com o pedido. Isso barra o "calculado para o servidor errado" do 0112;
   - "apto" não pode contrariar impedimento devolvido pela ferramenta (prestação
     vencida, limite excedido, saldo insuficiente, cadastro divergente);
   - os seis critérios estão presentes.
5. **Mensagem padrão.** Qualquer falha devolve o pedido à análise manual, e nada do
   conteúdo recusado aparece na tela (`teste_app.py`, passo 4).

Resultado medido: **0 instruções** entregues com dado fora do pedido ou das ferramentas,
em 84 execuções. Todas as instruções adulteradas de propósito foram recusadas: valor
plantado, matrícula fora do pedido, retorno inventado, servidor errado e aptidão com
prestação vencida. As 6 instruções calculadas sem ferramenta também foram recusadas
(`resultados/etapa3_filtro_e_barreira.txt`, `resultados/falhas.md`).

### 3. Que dados do servidor o agente guarda, por quanto tempo, e como o titular os elimina?

**O que guarda.** Só o banco do agente (`agente.db`, SQLite, fora do controle de
versão), em duas tabelas:

| Tabela | Conteúdo |
|---|---|
| `agno_sessions` | Uma por pedido: `session_id` = número do pedido, `user_id` = matrícula como protocolada |
| `agno_runs` | O texto do pedido: nome, matrícula, destino, datas, justificativa |
| `agno_runs` | As consultas: nome do cadastro, cargo, grupo, unidade, sede, diárias do mês e situação das prestações de contas |
| `agno_runs` | A instrução devolvida |

- **CPF e e-mail não são guardados.** As ferramentas não os devolvem, e o CPF e a conta
  bancária digitados na justificativa são mascarados pelo filtro antes do modelo e do
  banco. Isso foi verificado tabela por tabela no `verificar_etapa3.py`.
- **Memórias do usuário não são extraídas** (`update_memory_on_run` desligado).
- **Fora do agente:** o registro da conferência (`resultados/conferencias.jsonl`) é parte
  do processo de diárias, não do agente.

**Por quanto tempo.** O banco é cópia de trabalho. A retenção declarada é: enquanto o
pedido está em instrução e até **30 dias após a decisão do ordenador**, prazo para uma
eventual nova complementação. Depois disso, a eliminação é acionada pela rotina abaixo.
O expurgo automático por prazo não foi implementado (ver `relatorio.md`, Limitações).

**Como o titular elimina.** Na aba "Eliminação de dados (LGPD)" do formulário, ou por
`eliminacao.eliminar_titular(banco, matricula, nome)`. A rotina segue três etapas:

1. Apaga as sessões do titular, que levam junto as execuções. Considera as sessões sob o
   `user_id` dele **e** as que mencionam a matrícula ou o nome sob outro identificador.
2. Lista e apaga as memórias com `delete_user_memories`.
3. Confere o banco tabela por tabela, procurando a matrícula e o nome.

No teste com as duas servidoras em diligência, a Carla (207418) **não tinha nenhuma
sessão** sob o próprio `user_id`, porque a do 0112 foi gravada sob a matrícula digitada,
207481. Só a busca pela matrícula e pelo nome a alcançou. Depois da rotina, nada restou
das duas, e a servidora de controle continuou no banco (`resultados/eliminacao.txt`).

A rotina alcança somente o banco do agente. O processo de diárias é registro de despesa
pública, sujeito à transparência e à guarda das normas de prestação de contas, e não é
apagado por pedido do titular.
