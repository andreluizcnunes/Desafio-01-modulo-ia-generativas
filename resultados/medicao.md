# Medição contra o gabarito

3 rodadas × (12 pedidos + 2 complementações) por configuração, gpt-5.6-luna, banco novo a cada rodada.

## Por rodada

| Configuração | Rodada | Acertos | Recusados (msg padrão) | Erros de execução | ENTREGUES ERRADOS | Execuções c/ chamadas simultâneas | US$ | Tempo (s) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| paralelas desligadas | **total** | 41/42 | 1 | 0 | 0 | 0 | 0.15808 | 371.8 |
| paralelas desligadas | 1 | 14/14 | 0 | 0 | 0 | 0 | 0.05181 | 123.1 |
| paralelas desligadas | 2 | 13/14 | 1 | 0 | 0 | 0 | 0.05430 | 125.9 |
| paralelas desligadas | 3 | 14/14 | 0 | 0 | 0 | 0 | 0.05196 | 122.8 |
| paralelas ligadas | **total** | 42/42 | 0 | 0 | 0 | 0 | 0.15935 | 445.1 |
| paralelas ligadas | 1 | 14/14 | 0 | 0 | 0 | 0 | 0.05542 | 149.9 |
| paralelas ligadas | 2 | 14/14 | 0 | 0 | 0 | 0 | 0.05242 | 151.8 |
| paralelas ligadas | 3 | 14/14 | 0 | 0 | 0 | 0 | 0.05150 | 143.4 |

## Tokens, passos e custo por item

| Configuração | Chamadas (mediana/máx) | 1ª chamada (média) | Acréscimo por passo (mín/méd/máx) | Entrada acumulada, 5 passos | US$ mediana | US$ máx | Cauda (máx/mediana) |
|---|---|---:|---|---:|---:|---:|---:|
| paralelas desligadas | 5.0/8 | 2746 | [72, 128, 219] | 14616 | 0.003897 | 0.007182 | 1.84× |
| paralelas ligadas | 5.0/9 | 2743 | [72, 129, 219] | 14616 | 0.003923 | 0.006876 | 1.75× |

## Itens que não foram acerto

| Configuração | Rodada | Pedido | Turno | Classe | Detalhe |
|---|---|---|---|---|---|
| paralelas desligadas | 2 | DIA-2026-0106 | pedido | recusado | antecedencia: a instrução declara 'nao_atende', as consultas sustentam 'atende' |
