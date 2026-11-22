# Desafio 01 — Instrução de Pedidos de Diárias

Solução do Desafio 01 do módulo de IA generativa: um agente **Agno** que instrui
pedidos de diárias da SEMA-MT (Coordenadoria de Diárias e Passagens) segundo a
IN SEMA nº 07/2026, e um formulário **Streamlit** em que o servidor confere a
instrução antes do encaminhamento.

> Todos os dados do acervo (`dados/`) são hipotéticos. A instrução é uma sugestão
> para conferência: a decisão continua com o ordenador de despesa (art. 10).

## Sumário

- [Objetivo](#objetivo)
- [Tecnologias](#tecnologias)
- [Arquitetura](#arquitetura)
- [Estrutura de diretórios](#estrutura-de-diretórios)
- [Pré-requisitos](#pré-requisitos)
- [Instalação](#instalação)
- [Configuração do `.env`](#configuração-do-env)
- [Execução do formulário](#execução-do-formulário)
- [Testes](#testes)
- [Funcionalidades](#funcionalidades)
- [Limitações e conferência humana](#limitações-e-conferência-humana)
- [Documentação](#documentação)

## Objetivo

Hoje, o servidor instrui cada pedido de diárias à mão: confere o cadastro, os dados do
pedido, a antecedência, a prestação de contas, o limite mensal e o saldo, e redige a
minuta. O sistema faz essa instrução de ponta a ponta:

1. consulta os dados do órgão por quatro ferramentas;
2. devolve a instrução como um objeto validado (situação de cada critério,
   recomendação, quantidade e valor das diárias, pendências, alertas e minuta);
3. entrega a instrução ao servidor no formulário de conferência, onde ele edita a
   minuta e registra a sua decisão.

Quando falta dado ou o cadastro diverge, o pedido segue em **diligência**, e a
complementação do solicitante é aplicada na mesma sessão. Qualquer falha devolve o
pedido à **análise manual**.

## Tecnologias

| Tecnologia | Uso no projeto |
|---|---|
| Python | Linguagem da aplicação, das ferramentas e dos testes |
| [Agno](https://github.com/agno-agi/agno) 3.0.9 | Agente, ferramentas, `output_schema`, gancho de ferramentas (`tool_hooks`) e histórico da sessão |
| OpenAI (`gpt-5.6-luna`) | Modelo do agente, acessado pela biblioteca `openai` |
| Pydantic | Contrato `Instrucao` da saída do agente |
| Streamlit | Formulário de conferência e aba de eliminação de dados |
| SQLite (via SQLAlchemy) | Histórico das sessões do agente (`agente.db`, fora do controle de versão) |
| python-dotenv | Leitura da chave da API a partir do `.env` |

As versões exatas estão em [`requirements.txt`](requirements.txt).

## Arquitetura

```text
           ┌────────────────────┐
 Servidor ─▶  app.py (Streamlit) │◀── decisão registrada em resultados/conferencias.jsonl
           └─────────┬──────────┘
                     │ instruir(pedido, complementação)
           ┌─────────▼──────────┐   filtro de dados pessoais, histórico da sessão (SQLite)
           │ instrutor.py       │
           │ agente Agno        │── gancho guarda_de_merito: autoriza cada consulta antes de executar
           └─────────┬──────────┘
                     │ chamadas de ferramenta
           ┌─────────▼──────────┐
           │ ferramentas.py     │── lê dados/ (cadastro, tabela, histórico, saldo); as contas ficam no código
           └─────────┬──────────┘
                     │ objeto Instrucao
           ┌─────────▼──────────┐
           │ barreira.py        │── confere a instrução contra as consultas; redige fundamentos,
           └─────────┬──────────┘   pendências, alertas e minuta; recusa ⇒ mensagem padrão
                     ▼
              formulário de conferência
```

- **Um agente, quatro ferramentas.** As contas (antecedência, quantidade, valor, soma do
  mês, prazo da prestação e saldo) são feitas em Python, não pelo modelo.
- **Guarda antes da execução.** As consultas de cálculo, histórico e saldo só executam
  com o pedido vigente completo e o cadastro conferido nessa execução.
- **Barreira em código.** A instrução só chega ao conferente se coincidir com o que as
  consultas sustentam. Os textos exibidos são montados pelo código.

O desenho completo do processo, o quadro PEAS e as estimativas de custo estão em
[`desenho.md`](desenho.md).

## Estrutura de diretórios

```text
.
├── app.py                   # Formulário Streamlit (Etapa 5)
├── instrutor.py             # Agente: contrato Instrucao, instrução de sistema, filtro, memória, instruir()
├── ferramentas.py           # As quatro ferramentas
├── barreira.py              # Verificação em código e redação dos textos da instrução
├── eliminacao.py            # Rotina de eliminação dos dados do titular (LGPD)
├── memoria.py               # Custo da memória por turno (Etapa 4)
├── gabarito.py              # Gera o gabarito.json de avaliação, aplicando a norma por código
├── gabarito.json            # Gabarito de avaliação (lido só pela medição, nunca pelo agente)
├── medir.py                 # Medição contra o gabarito com o modelo real
├── falhas.py                # Falhas provocadas
├── simulacao.py             # Respostas controladas do agente, usadas pelos testes
├── verificar_etapa3.py      # Filtro de dados pessoais e varredura do banco (Etapa 3)
├── teste_*.py               # Testes (ver a seção Testes)
├── dados/                   # Acervo de entrada do desafio (hipotético, sem alteração)
├── resultados/              # Evidências: saídas dos testes, medições e histórico de medições
├── desenho.md               # Etapa 1: desenho do processo
├── relatorio.md             # Números medidos, falhas e decisão sobre a conferência humana
├── LEIA-ME.md               # Entregável: execução, decisões técnicas e respostas do enunciado
├── requirements.txt         # Dependências fixadas
└── .env.example             # Modelo do arquivo de configuração
```

## Pré-requisitos

- **Python 3.11 ou superior.** O `streamlit==1.67.0` fixado no `requirements.txt` exige
  Python 3.11 ou superior. O projeto foi executado com Python 3.12.3.
- **Git**, para clonar o repositório.
- **Chave da API da OpenAI**, para executar o formulário e as medições com o modelo
  real. Os testes marcados como "sem chave" dispensam a chave.

## Instalação

### 1. Clonar o repositório

```bash
git clone https://github.com/andreluizcnunes/Desafio-01-modulo-ia-generativas.git
cd Desafio-01-modulo-ia-generativas
```

### 2. Criar e ativar o ambiente virtual

**Linux / macOS**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell)**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**Windows (Prompt de Comando)**

```bat
python -m venv .venv
.venv\Scripts\activate.bat
```

### 3. Instalar as dependências

Com o ambiente virtual ativo:

```bash
pip install -r requirements.txt
```

## Configuração do `.env`

A aplicação lê a chave do arquivo `.env` na raiz do projeto. Esse arquivo está no
`.gitignore` e **nunca deve ser versionado**. Crie-o a partir do modelo:

```bash
# Linux / macOS
cp .env.example .env
```

```powershell
# Windows (PowerShell)
Copy-Item .env.example .env
```

```bat
:: Windows (Prompt de Comando)
copy .env.example .env
```

Depois, abra o `.env` em um editor e preencha a variável:

```dotenv
OPENAI_API_KEY=<sua-chave>
```

> Não publique a chave em commits, issues, capturas de tela ou registros de execução.
> Apenas o `.env.example`, sem valor, faz parte do repositório.

## Execução do formulário

Com o ambiente virtual ativo e o `.env` configurado:

```bash
streamlit run app.py
```

Abra no navegador o endereço indicado no terminal, por padrão
**<http://localhost:8501>**. O formulário tem duas abas:

- **Instrução e conferência:** escolha um pedido protocolado, clique em **Instruir**,
  acompanhe as consultas, confira a instrução, edite a minuta e registre a decisão.
  Quando o pedido está em diligência, envie a complementação pelo próprio formulário.
- **Eliminação de dados (LGPD):** informe matrícula e nome do titular para eliminar
  os seus dados do banco do agente.

Para encerrar, pressione `Ctrl+C` no terminal.

## Testes

Os comandos abaixo rodam a partir da raiz do projeto, com o ambiente virtual ativo.
As saídas são gravadas em `resultados/`, e os bancos SQLite temporários são apagados
ao final de cada script.

### Sem chave da API

| Comando | O que verifica |
|---|---|
| `python teste_ferramentas.py` | As quatro ferramentas com casos dos pedidos |
| `python teste_barreira.py` | Barreira e medição com respostas controladas: 50 casos, falhas do fluxo e leitura da urgência |
| `python teste_complementacao.py` | Contrato de confirmação dos campos da complementação e guarda do cálculo |
| `python teste_bloqueio.py` | Guarda das consultas de mérito com o Agno real e o modelo interceptado localmente |
| `python teste_eliminacao.py` | Rotina de eliminação em SQLite temporário |
| `python teste_app.py` | Formulário sem navegador (a parte A dispensa a chave; a parte B usa o modelo real) |

### Com chave da API (modelo real, gera custo)

| Comando | O que faz |
|---|---|
| `python medir.py` | Três rodadas contra o gabarito, com chamadas paralelas desligadas e ligadas |
| `python memoria.py` | Custo da memória por turno nas complementações |
| `python eliminacao.py` | Eliminação com as duas servidoras em diligência |
| `python falhas.py` | Quatro falhas provocadas |
| `python verificar_etapa3.py` | Filtro de dados pessoais e varredura do banco (a parte 3 usa a chave) |

A descrição completa de cada script está no [`LEIA-ME.md`](LEIA-ME.md#como-executar).

## Funcionalidades

- **Instrução completa do pedido:** os seis critérios (cadastro, dados completos,
  antecedência, prestação de contas, limite mensal e saldo orçamentário), com a
  recomendação, a quantidade e o valor das diárias calculados pelas ferramentas.
- **Diligência e complementação:** pedido incompleto ou com cadastro divergente não
  recebe consulta de mérito. A complementação é aplicada na mesma sessão, e só um
  campo confirmado sem ambiguidade alimenta o cálculo.
- **Barreira de verificação:** instrução incoerente com as consultas, resposta sem
  identificador da execução atual ou erro da API resultam em mensagem padrão e
  devolução à análise manual.
- **Textos redigidos pelo código:** fundamentos, pendências, alertas (dados pessoais,
  ordem dirigida ao sistema, autorização verbal, autorização escrita na urgência) e
  minuta usam os dados das consultas.
- **Exceção de urgência (art. 5º):** reconhecida pelo código. Menção isolada ou
  ambígua vai à análise manual.
- **Proteção de dados pessoais:** CPF e conta bancária digitados são mascarados antes do
  modelo e do banco. As ferramentas não devolvem CPF nem e-mail.
- **Conferência humana registrada:** minuta editável e decisão do servidor ao lado da
  sugestão do agente, com motivo obrigatório quando diverge.
- **Eliminação a pedido do titular:** a identidade é validada antes; a rotina apaga as
  sessões e as memórias e confere o banco tabela por tabela.

As decisões técnicas e as justificativas estão no [`LEIA-ME.md`](LEIA-ME.md).

## Limitações e conferência humana

O sistema **aconselha; não decide**. Toda instrução passa pelo servidor antes do
encaminhamento ao ordenador de despesa. As principais limitações conhecidas:

- **Amostra pequena:** 0 instruções erradas entregues em 84 execuções medidas não
  exclui erros em pedidos reais. O gabarito cobre 12 pedidos de um acervo hipotético.
- **Leitura de texto por regras:** a urgência e a complementação são lidas por padrões
  de texto. A leitura é conservadora: o que não é reconhecido vai à diligência ou à
  análise manual. Ainda assim, um texto que use as palavras esperadas sem corresponder
  aos fatos pode passar.
- **O que o código não verifica:** a existência da autorização escrita do § 2º no
  processo e a legitimidade de uma emergência fora da lista do § 1º.
- **Alertas só das categorias verificadas:** um alerta útil fora dessas categorias não
  chega à tela.
- **Filtro de dados pessoais por expressões regulares:** não reconhece CPF sem
  pontuação nem dado pessoal escrito por extenso.
- **Prazo da prestação de contas** contado sem feriados.
- **Expurgo automático por prazo** não implementado; a eliminação é acionada no
  formulário.

A lista completa está em [`relatorio.md`, Seção 10](relatorio.md#10-limitações), e a
decisão sobre o ponto de conferência humana, na
[Seção 8](relatorio.md#8-decisão-sobre-o-ponto-de-conferência-humana).

## Documentação

| Documento | Conteúdo |
|---|---|
| [`LEIA-ME.md`](LEIA-ME.md) | Entregável do desafio: execução, estrutura, decisões técnicas e respostas às perguntas do enunciado |
| [`desenho.md`](desenho.md) | Etapa 1: processo atual e com o agente, quadro PEAS, confiabilidade composta, custo por passos, quadrante de autonomia e decisão sobre o pedido urgente |
| [`relatorio.md`](relatorio.md) | Medição contra o gabarito, chamadas paralelas, memória, eliminação, falhas provocadas, conferência humana e limitações |
| [`resultados/`](resultados/) | Evidências geradas pelos testes e pelas medições |
