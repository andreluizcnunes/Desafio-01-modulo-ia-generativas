"""Custo da memória por turno, com as duas complementações (Etapa 4).

Cada pedido é uma sessão (`session_id` = número do pedido) e o `user_id` é a
matrícula do pedido como foi protocolado, ambos informados em cada `run`
(Aula 07, 2). Três configurações, como pede o enunciado e como no experimento
da Aula 07, 3.1:

    A · sem memória                      nada guardado entre os turnos
    B · histórico da sessão              add_history_to_context, teto de 4 execuções
    C · histórico + memórias do usuário  B + update_memory_on_run

Para cada complementação registra-se a entrada do primeiro turno (o pedido) e a
do turno da complementação, e se a complementação foi aplicada ao pedido certo:
mesmo número, matrícula e valores do gabarito, e instrução liberada pela
barreira.

Execução: python memoria.py
Saída: resultados/memoria.json e resultados/memoria.md
"""
import json
import pathlib

from instrutor import construir_agente, instruir

BASE = pathlib.Path(__file__).parent
RESULTADOS = BASE / "resultados"
PEDIDOS = {p["numero"]: p for p in json.loads((BASE / "dados" / "pedidos.json").read_text("utf-8"))}
COMPLEMENTOS = json.loads((BASE / "dados" / "complementacoes.json").read_text("utf-8"))
GABARITO = {g["numero_pedido"]: g for g in
            json.loads((BASE / "gabarito.json").read_text("utf-8"))["complementacoes"]}

CONFIGURACOES = [
    ("A · sem memória", "nenhuma"),
    ("B · histórico da sessão (teto 4)", "historico"),
    ("C · histórico + memórias do usuário", "usuario"),
]


def aplicada_ao_pedido_certo(resultado, numero: str) -> bool:
    esperado = GABARITO[numero]
    i = resultado.instrucao
    return (resultado.situacao == "entregue" and i is not None
            and i.numero_pedido == numero and i.matricula == esperado["matricula"]
            and i.recomendacao == esperado["recomendacao"]
            and i.quantidade_diarias == esperado["quantidade_diarias"]
            and i.valor_total == esperado["valor_total"])


def resumo_turno(r) -> dict:
    m = r.medidas
    return {"situacao": r.situacao,
            "recomendacao": r.instrucao.recomendacao if r.instrucao else None,
            "matricula": r.instrucao.matricula if r.instrucao else None,
            "valor_total": r.instrucao.valor_total if r.instrucao else None,
            "entrada_1a_chamada": (m.get("entrada_por_chamada") or [None])[0],
            "entrada_total": m.get("tokens_entrada"), "saida_total": m.get("tokens_saida"),
            "chamadas": m.get("chamadas"), "custo": round(m.get("custo", 0), 6),
            "motivo_recusa": r.motivo}


def main() -> None:
    registros = []
    for rotulo, memoria in CONFIGURACOES:
        banco = RESULTADOS / f"memoria_{memoria}.db"
        banco.unlink(missing_ok=True)  # nenhuma configuração herda a anterior
        agente = construir_agente(memoria=memoria, banco=banco)
        for c in COMPLEMENTOS:
            pedido = PEDIDOS[c["numero"]]
            t1 = instruir(pedido, agente)
            t2 = instruir(pedido, agente, complemento=c)
            registro = {"configuracao": rotulo, "pedido": c["numero"],
                        "turno_pedido": resumo_turno(t1), "turno_complementacao": resumo_turno(t2),
                        "aplicada_ao_pedido_certo": aplicada_ao_pedido_certo(t2, c["numero"])}
            registros.append(registro)
            print(f"{rotulo:38} {c['numero']}  T1 1ª chamada {registro['turno_pedido']['entrada_1a_chamada']}"
                  f" · T2 1ª chamada {registro['turno_complementacao']['entrada_1a_chamada']}"
                  f" · T2 total {registro['turno_complementacao']['entrada_total']}"
                  f" · aplicada certo: {registro['aplicada_ao_pedido_certo']}")
        banco.unlink(missing_ok=True)  # cópia de trabalho com dados pessoais: não fica

    (RESULTADOS / "memoria.json").write_text(
        json.dumps(registros, ensure_ascii=False, indent=2), encoding="utf-8")

    linhas = ["# Custo da memória por turno (Etapa 4)", "",
              "Entrada em tokens. T1 = turno do pedido; T2 = turno da complementação, "
              "na mesma sessão.", "",
              "| Configuração | Pedido | T1 1ª chamada | T1 total | T2 1ª chamada | T2 total "
              "| T2 recomendação | Aplicada ao pedido certo | US$ T1+T2 |",
              "|---|---|---:|---:|---:|---:|---|---|---:|"]
    for r in registros:
        a, b = r["turno_pedido"], r["turno_complementacao"]
        linhas.append(f"| {r['configuracao']} | {r['pedido']} | {a['entrada_1a_chamada']} | "
                      f"{a['entrada_total']} | {b['entrada_1a_chamada']} | {b['entrada_total']} | "
                      f"{b['recomendacao'] or b['situacao']} | "
                      f"{'sim' if r['aplicada_ao_pedido_certo'] else 'NÃO'} | "
                      f"{a['custo'] + b['custo']:.5f} |")
    (RESULTADOS / "memoria.md").write_text("\n".join(linhas) + "\n", encoding="utf-8")
    print("\n".join(linhas))


if __name__ == "__main__":
    main()
