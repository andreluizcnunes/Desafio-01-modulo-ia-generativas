# Medição contra o gabarito

3 rodadas × (12 pedidos + 2 complementações) por configuração, gpt-5.6-luna, banco novo a cada rodada.

## Por rodada

| Configuração | Rodada | Acertos | Recusados (msg padrão) | Erros de execução | ENTREGUES ERRADOS | Execuções c/ chamadas simultâneas | US$ | Tempo (s) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| paralelas desligadas | **total** | 38/42 | 1 | 0 | 3 | 0 | 0.14419 | 361.1 |
| paralelas desligadas | 1 | 13/14 | 1 | 0 | 0 | 0 | 0.04686 | 120.8 |
| paralelas desligadas | 2 | 13/14 | 0 | 0 | 1 | 0 | 0.04735 | 119.5 |
| paralelas desligadas | 3 | 12/14 | 0 | 0 | 2 | 0 | 0.04999 | 120.8 |
| paralelas ligadas | **total** | 38/42 | 0 | 0 | 4 | 0 | 0.14302 | 373.9 |
| paralelas ligadas | 1 | 13/14 | 0 | 0 | 1 | 0 | 0.04738 | 126.1 |
| paralelas ligadas | 2 | 13/14 | 0 | 0 | 1 | 0 | 0.04743 | 120.4 |
| paralelas ligadas | 3 | 12/14 | 0 | 0 | 2 | 0 | 0.04821 | 127.4 |

## Tokens, passos e custo por item

| Configuração | Chamadas (mediana/máx) | 1ª chamada (média) | Acréscimo por passo (mín/méd/máx) | Entrada acumulada, 5 passos | US$ mediana | US$ máx | Cauda (máx/mediana) |
|---|---|---:|---|---:|---:|---:|---:|
| paralelas desligadas | 5.0/8 | 2460 | [72, 129, 219] | 13186 | 0.003544 | 0.006746 | 1.9× |
| paralelas ligadas | 5.0/6 | 2465 | [72, 129, 219] | 13184 | 0.003556 | 0.004452 | 1.25× |

## Itens que não foram acerto

| Configuração | Rodada | Pedido | Turno | Classe | Detalhe |
|---|---|---|---|---|---|
| paralelas desligadas | 1 | DIA-2026-0111 | pedido | recusado | matrícula 206689 da instrução não foi consultada no cadastro |
| paralelas desligadas | 2 | DIA-2026-0106 | pedido | entregue_errado | recomendacao: 'nao_recomendado' ≠ 'apto_para_autorizacao' |
| paralelas desligadas | 3 | DIA-2026-0106 | pedido | entregue_errado | recomendacao: 'nao_recomendado' ≠ 'apto_para_autorizacao' |
| paralelas desligadas | 3 | DIA-2026-0107 | pedido | entregue_errado | exige_autorizacao_superior: True ≠ False |
| paralelas ligadas | 1 | DIA-2026-0106 | pedido | entregue_errado | recomendacao: 'nao_recomendado' ≠ 'apto_para_autorizacao' |
| paralelas ligadas | 2 | DIA-2026-0106 | pedido | entregue_errado | recomendacao: 'nao_recomendado' ≠ 'apto_para_autorizacao' |
| paralelas ligadas | 3 | DIA-2026-0106 | pedido | entregue_errado | recomendacao: 'nao_recomendado' ≠ 'apto_para_autorizacao' |
| paralelas ligadas | 3 | DIA-2026-0107 | pedido | entregue_errado | exige_autorizacao_superior: True ≠ False |
