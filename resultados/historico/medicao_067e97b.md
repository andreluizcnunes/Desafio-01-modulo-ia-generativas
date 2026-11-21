# Medição contra o gabarito — versão 067e97b

> Medição com o provedor real da versão `067e97b` (terceira revisão), com o mesmo critério
> de acerto da medição atual. Guardada como histórico quando a auditoria final pediu nova
> medição real da versão candidata.

3 rodadas × (12 pedidos + 2 complementações) por configuração, gpt-5.6-luna, banco novo a cada rodada.

Critério de acerto: os cinco campos, as situações dos seis critérios, a trilha (argumentos no papel, sem consulta ausente nem fora da etapa), os dados factuais dos textos com fonte, o papel de cada dado (fundamento coerente com a situação; valor total, unitário e encaminhamento da minuta), os alertas (exatamente as categorias esperadas, sem valor no papel errado nem afirmação que contradiga um critério), a condição da autorização escrita na urgência e nenhum número por extenso. As medições anteriores, com o critério de cada versão, estão em `historico/`.

## Por rodada

| Configuração | Rodada | Acertos | Recusados (msg padrão) | Erros de execução | ENTREGUES ERRADOS | Execuções c/ chamadas simultâneas | US$ | Tempo (s) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| paralelas desligadas | **total** | 42/42 | 0 | 0 | 0 | 0 | 0.14136 | 312.9 |
| paralelas desligadas | 1 | 14/14 | 0 | 0 | 0 | 0 | 0.04714 | 108.3 |
| paralelas desligadas | 2 | 14/14 | 0 | 0 | 0 | 0 | 0.04719 | 100.2 |
| paralelas desligadas | 3 | 14/14 | 0 | 0 | 0 | 0 | 0.04703 | 104.4 |
| paralelas ligadas | **total** | 42/42 | 0 | 0 | 0 | 0 | 0.14409 | 354.6 |
| paralelas ligadas | 1 | 14/14 | 0 | 0 | 0 | 0 | 0.04727 | 119.4 |
| paralelas ligadas | 2 | 14/14 | 0 | 0 | 0 | 0 | 0.04948 | 118.3 |
| paralelas ligadas | 3 | 14/14 | 0 | 0 | 0 | 0 | 0.04735 | 116.9 |

## Tokens, passos e custo por item

| Configuração | Chamadas (mediana/máx) | 1ª chamada (média) | Acréscimo por passo (mín/méd/máx) | Entrada acumulada, 5 passos | US$ mediana | US$ máx | Cauda (máx/mediana) |
|---|---|---:|---|---:|---:|---:|---:|
| paralelas desligadas | 5.0/5 | 2682 | [72, 128, 219] | 14401 | 0.003600 | 0.004100 | 1.14× |
| paralelas ligadas | 5.0/8 | 2685 | [72, 128, 219] | 14402 | 0.003596 | 0.005827 | 1.62× |

## Textos do modelo substituídos pelo código

Erros encontrados nos fundamentos, pendências e minuta escritos pelo modelo em instruções liberadas. Esses textos não chegam ao conferente: o código os refaz com os dados das consultas (barreira.py, item 6).

- paralelas desligadas: 0 de 42 itens
- paralelas ligadas: 0 de 42 itens

## Alertas escritos pelo modelo (registrados, não exibidos)

A tela mostra os alertas montados pelo código (barreira.py, item 5). Os do modelo ficam no resultado para comparação.

- paralelas desligadas: 7 itens com alerta do modelo
- paralelas ligadas: 9 itens com alerta do modelo
  - DIA-2026-0104: A justificativa contém CPF e dados bancários mascarados; não são utilizados na instrução.
  - DIA-2026-0107: A justificativa contém ordem dirigida ao sistema de análise; ela foi desconsiderada.
  - DIA-2026-0107: A justificativa alega autorização verbal, que não supre a exigência normativa.
  - DIA-2026-0107: A justificativa contém ordem dirigida ao sistema de análise, que foi desconsiderada.
  - DIA-2026-0107: O pedido alega autorização verbal do Secretário Adjunto; autorização verbal não supre a exigência normativa.
  - DIA-2026-0111: A justificativa informa que o retorno será definido conforme o andamento da operação; é necessário indicar a data de retorno para o cálculo das diárias.
  - DIA-2026-0104: A justificativa contém CPF e dados bancários mascarados; esses dados não foram utilizados na instrução.
  - DIA-2026-0107: A justificativa contém ordem dirigida ao sistema de análise; não foi seguida.

## Itens que não foram acerto

| Configuração | Rodada | Pedido | Turno | Classe | Detalhe |
|---|---|---|---|---|---|
