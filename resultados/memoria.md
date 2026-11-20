# Custo da memória por turno (Etapa 4)

Entrada em tokens. T1 = turno do pedido; T2 = turno da complementação, na mesma sessão.

| Configuração | Pedido | T1 1ª chamada | T1 total | T2 1ª chamada | T2 total | T2 recomendação | Aplicada ao pedido certo | US$ T1+T2 |
|---|---|---:|---:|---:|---:|---|---|---:|
| A · sem memória | DIA-2026-0111 | 2354 | 4805 | 2277 | 4621 | diligencia | NÃO | 0.00330 |
| A · sem memória | DIA-2026-0112 | 2354 | 4832 | 2280 | 4683 | diligencia | NÃO | 0.00306 |
| B · histórico da sessão (teto 4) | DIA-2026-0111 | 2354 | 4805 | 3075 | 16659 | apto_para_autorizacao | sim | 0.00588 |
| B · histórico da sessão (teto 4) | DIA-2026-0112 | 2354 | 4832 | 3029 | 16411 | apto_para_autorizacao | sim | 0.00579 |
| C · histórico + memórias do usuário | DIA-2026-0111 | 2379 | 5967 | 3045 | 17546 | apto_para_autorizacao | sim | 0.00624 |
| C · histórico + memórias do usuário | DIA-2026-0112 | 2379 | 6103 | 3185 | 18527 | apto_para_autorizacao | sim | 0.00695 |
