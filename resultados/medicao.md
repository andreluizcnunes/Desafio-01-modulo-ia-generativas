# Medição contra o gabarito

3 rodadas × (12 pedidos + 2 complementações) por configuração, gpt-5.6-luna, banco novo a cada rodada.

Critério de acerto: os cinco campos, as situações dos seis critérios, a trilha (argumentos no papel, sem consulta ausente nem fora da etapa), os dados factuais dos textos com fonte, o papel de cada dado (fundamento coerente com a situação; valor total, unitário e encaminhamento da minuta), a condição da autorização escrita na urgência e nenhum número por extenso. A medição anterior, com o critério da versão 0f67cf5, está em `historico/medicao_0f67cf5.md`.

## Por rodada

| Configuração | Rodada | Acertos | Recusados (msg padrão) | Erros de execução | ENTREGUES ERRADOS | Execuções c/ chamadas simultâneas | US$ | Tempo (s) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| paralelas desligadas | **total** | 42/42 | 0 | 0 | 0 | 0 | 0.14756 | 353.3 |
| paralelas desligadas | 1 | 14/14 | 0 | 0 | 0 | 0 | 0.04830 | 118.1 |
| paralelas desligadas | 2 | 14/14 | 0 | 0 | 0 | 0 | 0.05121 | 121.5 |
| paralelas desligadas | 3 | 14/14 | 0 | 0 | 0 | 0 | 0.04805 | 113.7 |
| paralelas ligadas | **total** | 42/42 | 0 | 0 | 0 | 0 | 0.14579 | 336.0 |
| paralelas ligadas | 1 | 14/14 | 0 | 0 | 0 | 0 | 0.04852 | 116.1 |
| paralelas ligadas | 2 | 14/14 | 0 | 0 | 0 | 0 | 0.04840 | 111.3 |
| paralelas ligadas | 3 | 14/14 | 0 | 0 | 0 | 0 | 0.04887 | 108.6 |

## Tokens, passos e custo por item

| Configuração | Chamadas (mediana/máx) | 1ª chamada (média) | Acréscimo por passo (mín/méd/máx) | Entrada acumulada, 5 passos | US$ mediana | US$ máx | Cauda (máx/mediana) |
|---|---|---:|---|---:|---:|---:|---:|
| paralelas desligadas | 5.0/9 | 2713 | [73, 128, 219] | 14543 | 0.003667 | 0.006600 | 1.8× |
| paralelas ligadas | 5.0/6 | 2715 | [72, 129, 219] | 14538 | 0.003656 | 0.004582 | 1.25× |

## Textos do modelo substituídos pelo código

Erros encontrados nos fundamentos, pendências e minuta escritos pelo modelo em instruções liberadas. Esses textos não chegam ao conferente: o código os refaz com os dados das consultas (barreira.py, item 6).

- paralelas desligadas: 0 de 42 itens
- paralelas ligadas: 0 de 42 itens

## Itens que não foram acerto

| Configuração | Rodada | Pedido | Turno | Classe | Detalhe |
|---|---|---|---|---|---|
