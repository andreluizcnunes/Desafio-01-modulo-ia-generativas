"""Medição do agente contra o gabarito: acertos, tokens, tempo e custo.

Três rodadas dos 12 pedidos e das 2 complementações, em duas configurações:
chamadas paralelas desligadas (a escolhida, Aula 06, 4.3) e ligadas (a
comparação pedida nos critérios de avaliação). Cada rodada começa com banco
novo, para que nenhuma herde a memória da anterior (Aula 07, 3.1).

Classificação de cada item, na ordem de gravidade do enunciado:
- acerto: entregue ao conferente e igual ao gabarito em recomendação,
  matrícula, quantidade, valor e exigência de autorização superior;
- recusado: a barreira recusou e o servidor viu a mensagem padrão (erro visível);
- erro de execução: status de erro ou saída fora do contrato (erro visível);
- ENTREGUE ERRADO: chegou ao conferente diferente do gabarito (o que mais pesa).

O custo é lido por item, para ver a cauda e não só a média (Aula 03, 5.4).

Execução: python medir.py
Saída: resultados/medicao.json e resultados/medicao.md
"""
import json
import pathlib
import statistics
import time

from instrutor import apagar_banco, construir_agente, instruir

BASE = pathlib.Path(__file__).parent
RESULTADOS = BASE / "resultados"
PEDIDOS = json.loads((BASE / "dados" / "pedidos.json").read_text("utf-8"))
POR_NUMERO = {p["numero"]: p for p in PEDIDOS}
COMPLEMENTOS = json.loads((BASE / "dados" / "complementacoes.json").read_text("utf-8"))
GAB = json.loads((BASE / "gabarito.json").read_text("utf-8"))
GAB_PEDIDOS = {g["numero_pedido"]: g for g in GAB["pedidos"]}
GAB_COMPL = {g["numero_pedido"]: g for g in GAB["complementacoes"]}
RODADAS = 3
CONFIGURACOES = [("paralelas desligadas", False), ("paralelas ligadas", True)]
CAMPOS = ("recomendacao", "matricula", "quantidade_diarias", "valor_total",
          "exige_autorizacao_superior")


def classificar(resultado, esperado: dict) -> tuple[str, list]:
    if resultado.situacao == "erro":
        return "erro_execucao", []
    if resultado.situacao == "recusada":
        return "recusado", []
    i = resultado.instrucao
    diferencas = [f"{c}: {getattr(i, c)!r} ≠ {esperado[c]!r}" for c in CAMPOS
                  if getattr(i, c) != esperado[c]]
    return ("acerto" if not diferencas else "entregue_errado"), diferencas


def item(rodada, config, numero, turno, resultado, esperado) -> dict:
    classe, diferencas = classificar(resultado, esperado)
    m = resultado.medidas
    return {"rodada": rodada, "configuracao": config, "pedido": numero, "turno": turno,
            "classe": classe, "diferencas": diferencas, "motivo_recusa": resultado.motivo,
            "recomendacao": resultado.instrucao.recomendacao if resultado.instrucao else None,
            "esperado": esperado["recomendacao"],
            "chamadas": m.get("chamadas"), "entrada_por_chamada": m.get("entrada_por_chamada"),
            "max_simultaneas": m.get("max_ferramentas_simultaneas"),
            "tokens_entrada": m.get("tokens_entrada"), "tokens_saida": m.get("tokens_saida"),
            "custo": m.get("custo", 0), "segundos": m.get("segundos")}


def resumir(itens: list[dict]) -> dict:
    custos = sorted(i["custo"] for i in itens)
    mediana = statistics.median(custos)
    primeiras = [i["entrada_por_chamada"][0] for i in itens if i["entrada_por_chamada"]]
    acrescimos = [b - a for i in itens if i["turno"] == "pedido"
                  for a, b in zip(i["entrada_por_chamada"], i["entrada_por_chamada"][1:])]
    cinco = [i["tokens_entrada"] for i in itens if i["chamadas"] == 5 and i["turno"] == "pedido"]
    return {
        "itens": len(itens),
        "acertos": sum(i["classe"] == "acerto" for i in itens),
        "recusados": sum(i["classe"] == "recusado" for i in itens),
        "erros_execucao": sum(i["classe"] == "erro_execucao" for i in itens),
        "entregues_errados": sum(i["classe"] == "entregue_errado" for i in itens),
        "execucoes_com_chamadas_simultaneas": sum((i["max_simultaneas"] or 0) > 1 for i in itens),
        "chamadas_mediana": statistics.median(i["chamadas"] or 0 for i in itens),
        "chamadas_max": max(i["chamadas"] or 0 for i in itens),
        "entrada_1a_chamada_media": round(statistics.mean(primeiras)) if primeiras else None,
        "acrescimo_por_passo_min_med_max": ([min(acrescimos), round(statistics.mean(acrescimos)),
                                             max(acrescimos)] if acrescimos else None),
        "entrada_acumulada_media_5_passos": round(statistics.mean(cinco)) if cinco else None,
        "tokens_entrada": sum(i["tokens_entrada"] or 0 for i in itens),
        "tokens_saida": sum(i["tokens_saida"] or 0 for i in itens),
        "custo_total": round(sum(custos), 5),
        "custo_mediana": round(mediana, 6), "custo_max": round(custos[-1], 6),
        "razao_cauda": round(custos[-1] / mediana, 2) if mediana else None,
        "segundos_total": round(sum(i["segundos"] or 0 for i in itens), 1),
        "segundos_mediana": statistics.median(i["segundos"] or 0 for i in itens),
    }


def main() -> None:
    itens = []
    for config, paralelas in CONFIGURACOES:
        for rodada in range(1, RODADAS + 1):
            banco = RESULTADOS / f"medicao_{'ligadas' if paralelas else 'desligadas'}_{rodada}.db"
            apagar_banco(banco)
            agente = construir_agente(memoria="historico", paralelas=paralelas, banco=banco)
            inicio = time.perf_counter()
            for p in PEDIDOS:
                r = instruir(p, agente)
                itens.append(item(rodada, config, p["numero"], "pedido", r, GAB_PEDIDOS[p["numero"]]))
                print(f"{config:22} r{rodada} {p['numero']} {itens[-1]['classe']:16} "
                      f"{itens[-1]['recomendacao']} {itens[-1]['diferencas'] or ''}"
                      f"{itens[-1]['motivo_recusa'] or ''}", flush=True)
            for c in COMPLEMENTOS:
                r = instruir(POR_NUMERO[c["numero"]], agente, complemento=c)
                itens.append(item(rodada, config, c["numero"], "complementacao", r,
                                  GAB_COMPL[c["numero"]]))
                print(f"{config:22} r{rodada} {c['numero']}+c {itens[-1]['classe']:16} "
                      f"{itens[-1]['recomendacao']} {itens[-1]['diferencas'] or ''}"
                      f"{itens[-1]['motivo_recusa'] or ''}", flush=True)
            print(f"   rodada concluída em {time.perf_counter() - inicio:.0f} s", flush=True)
            apagar_banco(banco)

    resumo = {}
    for config, _ in CONFIGURACOES:
        resumo[config] = {"geral": resumir([i for i in itens if i["configuracao"] == config])}
        for rodada in range(1, RODADAS + 1):
            resumo[config][f"rodada_{rodada}"] = resumir(
                [i for i in itens if i["configuracao"] == config and i["rodada"] == rodada])
    (RESULTADOS / "medicao.json").write_text(
        json.dumps({"resumo": resumo, "itens": itens}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    escrever_md(resumo, itens)


def escrever_md(resumo: dict, itens: list[dict]) -> None:
    l = ["# Medição contra o gabarito", "",
         f"{RODADAS} rodadas × (12 pedidos + 2 complementações) por configuração, "
         "gpt-5.6-luna, banco novo a cada rodada.", "",
         "## Por rodada", "",
         "| Configuração | Rodada | Acertos | Recusados (msg padrão) | Erros de execução "
         "| ENTREGUES ERRADOS | Execuções c/ chamadas simultâneas | US$ | Tempo (s) |",
         "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    for config, blocos in resumo.items():
        for nome, r in blocos.items():
            rot = "**total**" if nome == "geral" else nome.replace("rodada_", "")
            l.append(f"| {config} | {rot} | {r['acertos']}/{r['itens']} | {r['recusados']} | "
                     f"{r['erros_execucao']} | {r['entregues_errados']} | "
                     f"{r['execucoes_com_chamadas_simultaneas']} | {r['custo_total']:.5f} | "
                     f"{r['segundos_total']} |")
    l += ["", "## Tokens, passos e custo por item", "",
          "| Configuração | Chamadas (mediana/máx) | 1ª chamada (média) | Acréscimo por passo "
          "(mín/méd/máx) | Entrada acumulada, 5 passos | US$ mediana | US$ máx | Cauda (máx/mediana) |",
          "|---|---|---:|---|---:|---:|---:|---:|"]
    for config, blocos in resumo.items():
        r = blocos["geral"]
        l.append(f"| {config} | {r['chamadas_mediana']}/{r['chamadas_max']} | "
                 f"{r['entrada_1a_chamada_media']} | {r['acrescimo_por_passo_min_med_max']} | "
                 f"{r['entrada_acumulada_media_5_passos']} | {r['custo_mediana']:.6f} | "
                 f"{r['custo_max']:.6f} | {r['razao_cauda']}× |")
    l += ["", "## Itens que não foram acerto", "",
          "| Configuração | Rodada | Pedido | Turno | Classe | Detalhe |", "|---|---|---|---|---|---|"]
    for i in itens:
        if i["classe"] != "acerto":
            detalhe = "; ".join(i["diferencas"] or i["motivo_recusa"] or ["-"])
            l.append(f"| {i['configuracao']} | {i['rodada']} | {i['pedido']} | {i['turno']} | "
                     f"{i['classe']} | {detalhe[:220]} |")
    (RESULTADOS / "medicao.md").write_text("\n".join(l) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
