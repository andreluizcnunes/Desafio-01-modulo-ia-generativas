# Custo da memória por turno (Etapa 4)

Entrada em tokens. T1 = turno do pedido; T2 = turno da complementação, na mesma sessão.

Versão do código executada: `6f4d2fa` · provedor real (OpenAI).

| Configuração | Pedido | T1 1ª chamada | T1 total | T2 1ª chamada | T2 total | T2 recomendação | Aplicada ao pedido certo | US$ T1+T2 |
|---|---|---:|---:|---:|---:|---|---|---:|
| A · sem memória | DIA-2026-0111 | 2655 | 5407 | 2578 | 5240 | diligencia | NÃO | 0.00303 |
| A · sem memória | DIA-2026-0112 | 2655 | 5434 | 2581 | 5234 | diligencia | NÃO | 0.00300 |
| B · histórico da sessão (teto 4) | DIA-2026-0111 | 2655 | 5407 | 3159 | 20848 | apto_para_autorizacao | sim | 0.00643 |
| B · histórico da sessão (teto 4) | DIA-2026-0112 | 2655 | 5434 | 3187 | 17201 | apto_para_autorizacao | sim | 0.00565 |
| C · histórico + memórias do usuário | DIA-2026-0111 | 2680 | 6681 | 3319 | 19193 | apto_para_autorizacao | sim | 0.00666 |
| C · histórico + memórias do usuário | DIA-2026-0112 | 2680 | 6711 | 3332 | 19253 | apto_para_autorizacao | sim | 0.00677 |
