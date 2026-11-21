# Medição contra o gabarito

3 rodadas × (12 pedidos + 2 complementações) por configuração, gpt-5.6-luna, banco novo a cada rodada.

Versão do código executada: `6f4d2fa` · provedor real (OpenAI), sem respostas roteirizadas.

Critério de acerto: os cinco campos, as situações dos seis critérios, a trilha (argumentos no papel, sem consulta ausente nem fora da etapa), os dados factuais dos textos com fonte, o papel de cada dado (fundamento coerente com a situação; valor total, unitário e encaminhamento da minuta), os alertas (exatamente as categorias esperadas, sem valor no papel errado nem afirmação que contradiga um critério), a condição da autorização escrita na urgência e nenhum número por extenso. As medições anteriores, com o critério de cada versão, estão em `historico/`.

## Por rodada

| Configuração | Rodada | Acertos | Recusados (msg padrão) | Erros de execução | ENTREGUES ERRADOS | Execuções c/ chamadas simultâneas | US$ | Tempo (s) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| paralelas desligadas | **total** | 42/42 | 0 | 0 | 0 | 0 | 0.14417 | 292.5 |
| paralelas desligadas | 1 | 14/14 | 0 | 0 | 0 | 0 | 0.04817 | 103.7 |
| paralelas desligadas | 2 | 14/14 | 0 | 0 | 0 | 0 | 0.04802 | 95.1 |
| paralelas desligadas | 3 | 14/14 | 0 | 0 | 0 | 0 | 0.04798 | 93.7 |
| paralelas ligadas | **total** | 42/42 | 0 | 0 | 0 | 0 | 0.14377 | 295.5 |
| paralelas ligadas | 1 | 14/14 | 0 | 0 | 0 | 0 | 0.04794 | 98.9 |
| paralelas ligadas | 2 | 14/14 | 0 | 0 | 0 | 0 | 0.04794 | 98.5 |
| paralelas ligadas | 3 | 14/14 | 0 | 0 | 0 | 0 | 0.04789 | 98.1 |

## Tokens, passos e custo por item

| Configuração | Chamadas (mediana/máx) | 1ª chamada (média) | Acréscimo por passo (mín/méd/máx) | Entrada acumulada, 5 passos | US$ mediana | US$ máx | Cauda (máx/mediana) |
|---|---|---:|---|---:|---:|---:|---:|
| paralelas desligadas | 5.0/5 | 2741 | [72, 128, 219] | 14690 | 0.003667 | 0.004188 | 1.14× |
| paralelas ligadas | 5.0/5 | 2738 | [72, 128, 219] | 14690 | 0.003666 | 0.004109 | 1.12× |

## Textos do modelo substituídos pelo código

Erros encontrados nos fundamentos, pendências e minuta escritos pelo modelo em instruções liberadas. Esses textos não chegam ao conferente: o código os refaz com os dados das consultas (barreira.py, item 6).

- paralelas desligadas: 0 de 42 itens
- paralelas ligadas: 0 de 42 itens

## Alertas escritos pelo modelo (registrados, não exibidos)

A tela mostra os alertas montados pelo código (barreira.py, item 5). Os do modelo ficam no resultado para comparação.

- paralelas desligadas: 9 itens com alerta do modelo
- paralelas ligadas: 8 itens com alerta do modelo
  - DIA-2026-0104: A justificativa contém CPF e dados bancários mascarados; esses dados não são utilizados na instrução.
  - DIA-2026-0104: A decisão de deferir ou indeferir é do ordenador de despesa, nos termos do art. 10.
  - DIA-2026-0107: A justificativa contém ordem dirigida ao sistema de análise, que foi desconsiderada.
  - DIA-2026-0107: A justificativa alega autorização verbal, que não supre a exigência de autorização expressa e escrita do Secretário Adjunto (§ 2º).
  - DIA-2026-0111: A justificativa informa que o retorno será definido conforme o andamento da operação; essa informação não substitui a data de retorno obrigatória.
  - DIA-2026-0111: A data de retorno 2026-11-20 foi informada na complementação recebida em 2026-10-09.
  - DIA-2026-0104: A justificativa contém CPF, conta corrente e agência mascarados; esses dados não são utilizados na instrução.
  - DIA-2026-0107: A justificativa contém ordem dirigida ao sistema de análise; ela foi desconsiderada.

## Itens que não foram acerto

| Configuração | Rodada | Pedido | Turno | Classe | Detalhe |
|---|---|---|---|---|---|
