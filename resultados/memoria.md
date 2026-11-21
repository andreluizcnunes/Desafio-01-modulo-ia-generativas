# Custo da memória por turno (Etapa 4)

Entrada em tokens. T1 = turno do pedido; T2 = turno da complementação, na mesma sessão.

| Configuração | Pedido | T1 1ª chamada | T1 total | T2 1ª chamada | T2 total | T2 recomendação | Aplicada ao pedido certo | US$ T1+T2 |
|---|---|---:|---:|---:|---:|---|---|---:|
| A · sem memória | DIA-2026-0111 | 2597 | 5291 | 2520 | 5166 | diligencia | NÃO | 0.00298 |
| A · sem memória | DIA-2026-0112 | 2597 | 5318 | 2523 | 5169 | diligencia | NÃO | 0.00303 |
| B · histórico da sessão (teto 4) | DIA-2026-0111 | 2597 | 5291 | 3139 | 16981 | apto_para_autorizacao | sim | 0.00563 |
| B · histórico da sessão (teto 4) | DIA-2026-0112 | 2597 | 5318 | 3132 | 16926 | apto_para_autorizacao | sim | 0.00555 |
| C · histórico + memórias do usuário | DIA-2026-0111 | 2622 | 6453 | 3105 | 17846 | apto_para_autorizacao | sim | 0.00609 |
| C · histórico + memórias do usuário | DIA-2026-0112 | 2622 | 6480 | 3182 | 18212 | apto_para_autorizacao | sim | 0.00617 |
