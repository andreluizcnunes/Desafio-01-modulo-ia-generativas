# Custo da memória por turno (Etapa 4)

Entrada em tokens. T1 = turno do pedido; T2 = turno da complementação, na mesma sessão.

| Configuração | Pedido | T1 1ª chamada | T1 total | T2 1ª chamada | T2 total | T2 recomendação | Aplicada ao pedido certo | US$ T1+T2 |
|---|---|---:|---:|---:|---:|---|---|---:|
| A · sem memória | DIA-2026-0111 | 2640 | 5377 | 2563 | 5256 | diligencia | NÃO | 0.00342 |
| A · sem memória | DIA-2026-0112 | 2640 | 5404 | 2566 | 5249 | diligencia | NÃO | 0.00340 |
| B · histórico da sessão (teto 4) | DIA-2026-0111 | 2640 | 5377 | 3269 | 17631 | apto_para_autorizacao | sim | 0.00607 |
| B · histórico da sessão (teto 4) | DIA-2026-0112 | 2640 | 5404 | 3378 | 18156 | apto_para_autorizacao | sim | 0.00632 |
| C · histórico + memórias do usuário | DIA-2026-0111 | 2665 | 6653 | 3468 | 19937 | apto_para_autorizacao | sim | 0.00728 |
| C · histórico + memórias do usuário | DIA-2026-0112 | 2665 | 6667 | 3446 | 19796 | apto_para_autorizacao | sim | 0.00720 |
