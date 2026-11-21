# Custo da memória por turno (Etapa 4)

Entrada em tokens. T1 = turno do pedido; T2 = turno da complementação, na mesma sessão.

| Configuração | Pedido | T1 1ª chamada | T1 total | T2 1ª chamada | T2 total | T2 recomendação | Aplicada ao pedido certo | US$ T1+T2 |
|---|---|---:|---:|---:|---:|---|---|---:|
| A · sem memória | DIA-2026-0111 | 2625 | 5347 | 2548 | 5220 | diligencia | NÃO | 0.00310 |
| A · sem memória | DIA-2026-0112 | 2625 | 5374 | 2551 | 5221 | diligencia | NÃO | 0.00317 |
| B · histórico da sessão (teto 4) | DIA-2026-0111 | 2625 | 5347 | 3156 | 17066 | apto_para_autorizacao | sim | 0.00569 |
| B · histórico da sessão (teto 4) | DIA-2026-0112 | 2625 | 5374 | 3190 | 17216 | apto_para_autorizacao | sim | 0.00566 |
| C · histórico + memórias do usuário | DIA-2026-0111 | 2650 | 6620 | 3264 | 18924 | apto_para_autorizacao | sim | 0.00660 |
| C · histórico + memórias do usuário | DIA-2026-0112 | 2650 | 6648 | 3340 | 19301 | apto_para_autorizacao | sim | 0.00670 |
