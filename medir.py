"""Medição do agente contra o gabarito: acertos, tokens, tempo e custo.

Três rodadas dos 12 pedidos e das 2 complementações, em duas configurações:
chamadas paralelas desligadas (a escolhida, Aula 06, 4.3) e ligadas (a
comparação pedida nos critérios de avaliação). Cada rodada começa com banco
novo, para que nenhuma herde a memória da anterior (Aula 07, 3.1).

Classificação de cada item, na ordem de gravidade do enunciado:
- acerto: entregue ao conferente e igual ao gabarito em recomendação,
  matrícula, quantidade, valor e exigência de autorização superior, nas
  situações dos seis critérios, na trilha de consultas (cada argumento no seu
  papel, sem consulta ausente nem fora da etapa), nos dados factuais dos
  fundamentos, pendências, alertas e minuta, no papel de cada dado (o
  fundamento diz o que a situação diz; a minuta traz o valor total, o
  unitário e o encaminhamento esperados), nos alertas (exatamente as
  categorias esperadas, sem alerta fora delas, sem valor no papel errado e
  sem afirmação que contradiga a situação de um critério) e sem número por
  extenso;
- recusado: a barreira recusou e o servidor viu a mensagem padrão (erro visível);
- erro de execução: status de erro ou saída fora do contrato (erro visível);
- ENTREGUE ERRADO: chegou ao conferente diferente do gabarito (o que mais pesa).

A conferência dos textos e da trilha é implementada aqui, e não importada da
barreira: a medição precisa poder falhar de forma independente do sistema
medido (Aula 03, 5.2). O gabarito só é lido pela avaliação.

O custo é lido por item, para ver a cauda e não só a média (Aula 03, 5.4).

Execução: python medir.py
Saída: resultados/medicao.json e resultados/medicao.md
"""
import json
import pathlib
import re
import statistics
import time
import unicodedata

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


MESES = ["janeiro", "fevereiro", "marco", "abril", "maio", "junho", "julho", "agosto",
         "setembro", "outubro", "novembro", "dezembro"]


def _num(texto: str) -> float:
    """'1.260,00' -> 1260.0; '3,5' -> 3.5; '980.00' -> 980.0; '18400' -> 18400.0."""
    if "," in texto:
        return round(float(texto.replace(".", "").replace(",", ".")), 2)
    if re.fullmatch(r"\d{1,3}(\.\d{3})+", texto):
        return float(texto.replace(".", ""))
    return round(float(texto), 2)


def _plano(texto: str) -> str:
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()


def fatos_do_texto(texto: str) -> dict:
    """Extração própria da medição: valores, datas, matrículas, pedidos e números com unidade."""
    plano = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()
    datas = set(re.findall(r"\d{4}-\d{2}-\d{2}", texto))
    datas |= {f"{a}-{int(m):02d}-{int(d):02d}" for d, m, a in
              re.findall(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b", texto)}
    datas |= {f"{a}-{MESES.index(m) + 1:02d}-{int(d):02d}" for d, m, a in
              re.findall(r"\b(\d{1,2})o? de ([a-z]+) de (\d{4})", plano) if m in MESES}
    limpo = re.sub(r"\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4}", " ", texto)
    valores = {_num(v) for v in re.findall(r"R\$\s*(\d+(?:[.,]\d+)*)", limpo)}
    valores |= {_num(v) for v in re.findall(r"(?<![\d.,])\d{1,3}(?:\.\d{3})*,\d{2}(?![\d,])",
                                            limpo)}
    numeros = {_num(n) for n in re.findall(r"(\d+(?:[.,]\d+)?)\s*(?:dias?\b|dia\(s\)|di[aá]ria)",
                                           limpo)}
    return {"valores": valores, "datas": datas,
            "matriculas": set(re.findall(r"(?<![\d.,/-])\d{6}(?![\d.,/-]?\d)", limpo)),
            "pedidos": set(re.findall(r"DIA-\d{4}-\d{4}", texto)), "numeros": numeros}


def _igual(a, b) -> bool:
    try:
        return round(float(a), 2) == round(float(b), 2)
    except (TypeError, ValueError):
        return str(a or "").strip().upper() == str(b or "").strip().upper()


def conferir(instrucao, consultas: list[dict], esperado: dict) -> list[str]:
    """Diferenças entre a instrução entregue e o gabarito."""
    dif = [f"{c}: {getattr(instrucao, c)!r} ≠ {esperado[c]!r}" for c in CAMPOS
           if getattr(instrucao, c) != esperado[c]]
    declaradas = {v.criterio: v.situacao for v in instrucao.verificacoes}
    dif += [f"situação de {c}: {declaradas.get(c)!r} ≠ {s!r}"
            for c, s in esperado["situacoes"].items() if declaradas.get(c) != s]
    # Trilha: cada ferramenta esperada foi chamada com os argumentos esperados,
    # nenhuma chamada usou argumento fora do papel e nenhuma ferramenta fora da
    # etapa foi chamada (na diligência, só o cadastro).
    extras = sorted({c["ferramenta"] for c in consultas} - set(esperado["trilha"]))
    if extras:
        dif.append(f"trilha: consultas fora da etapa: {', '.join(extras)}")
    for ferramenta, args in esperado["trilha"].items():
        feitas = [c["argumentos"] for c in consultas if c["ferramenta"] == ferramenta]
        if not any(all(_igual(f.get(k), v) for k, v in args.items()) for f in feitas):
            dif.append(f"trilha: {ferramenta} não chamada com {args}")
        for f in feitas:
            if ferramenta == "consultar_servidor" and \
                    str(f.get("matricula", "")).strip() in esperado["fatos"]["matriculas"]:
                continue
            if not all(_igual(f.get(k), v) for k, v in args.items()):
                dif.append(f"trilha: {ferramenta} chamada fora do papel com {f}")
    # Papel de cada dado: o fundamento de cada critério diz o que a situação diz,
    # e a minuta traz o valor total, o unitário e o encaminhamento esperados.
    for v in instrucao.verificacoes:
        dif += [f"fundamento de {v.criterio}: {d}"
                for d in _fundamento_incoerente(v.criterio, esperado["situacoes"].get(v.criterio),
                                                _plano(v.detalhe or ""))]
    dif += _minuta_fora_do_papel(_plano(instrucao.minuta_despacho or ""), esperado)
    dif += _alertas_fora_do_papel([_plano(a or "") for a in instrucao.alertas], esperado)
    # Urgência: a minuta preserva a condição da autorização escrita (art. 5º, § 2º).
    minuta = _plano(instrucao.minuta_despacho or "")
    if esperado["exige_autorizacao_superior"] and not (
            "autorizacao expressa e escrita" in minuta and "dispens" not in minuta):
        dif.append("minuta do pedido urgente sem a condição da autorização expressa e escrita")
    for texto in [instrucao.minuta_despacho] + list(instrucao.alertas):
        plano = _plano(texto or "")
        if "autoriza" in plano and re.search(r"dispens|desnecessari", plano):
            dif.append(f"texto afirma que a autorização é dispensável: {texto[:60]!r}")
    # Fatos citados nos textos.
    permitidos = {k: set(v) for k, v in esperado["fatos"].items()}
    textos = [v.detalhe for v in instrucao.verificacoes] + list(instrucao.pendencias) + \
        list(instrucao.alertas) + [instrucao.minuta_despacho]
    for texto in textos:
        for tipo, achados in fatos_do_texto(texto or "").items():
            fora = {a for a in achados if a not in permitidos[tipo]}
            if fora:
                dif.append(f"texto cita {tipo} sem fonte: {sorted(map(str, fora))}")
        if POR_EXTENSO.search(_plano(texto or "")):
            dif.append(f"texto com número por extenso: {texto[:60]!r}")
    return dif


# Palavras da norma que cada situação exige (+) ou proíbe (-) no fundamento.
TERMOS = {
    ("cadastro", "atende"): (["confere"], ["diverge", "nao localizada"]),
    ("cadastro", "nao_atende"): (["diverge|nao localizada"], []),
    ("dados_completos", "nao_atende"): (["falta|ausente|nao informad"], []),
    ("antecedencia", "atende"): (["atende o minimo|urgencia"], []),
    ("antecedencia", "nao_atende"): (["nao atende"], ["admitida"]),
    ("prestacao_contas", "atende"): (["nenhuma pendente|no prazo"],
                                     ["vencida", "regularizada", "aprovada"]),
    ("prestacao_contas", "nao_atende"): (["vencida"],
                                         ["nao (?:esta |ha |consta )?(?:prestacao )?vencida",
                                          "regularizada", "aprovada", "nenhuma pendente"]),
    ("limite_mensal", "atende"): (["atende"], ["excede"]),
    ("limite_mensal", "nao_atende"): (["excede"], []),
    ("saldo_orcamentario", "atende"): (["suficiente"], ["insuficiente"]),
    ("saldo_orcamentario", "nao_atende"): (["insuficiente"], []),
}
POR_EXTENSO = re.compile(
    r"\b(?:dois|duas|tres|quatro|cinco|seis|sete|oito|nove|dez|onze|doze|quinze|vinte|trinta|"
    r"quarenta|cinquenta|sessenta|setenta|oitenta|noventa|cem|cento|duzentos|trezentos|"
    r"quinhentos|mil|milhao|milhoes|meia|uma?)\b(?:\s+\w+){0,4}?\s+(?:reais|diarias?|dias?)\b")


def _fundamento_incoerente(criterio: str, situacao: str | None, texto: str) -> list[str]:
    if situacao == "nao_verificado":
        return [] if "nao verificado" in texto else ["critério não verificado sem dizê-lo"]
    exige, proibe = TERMOS.get((criterio, situacao), ([], []))
    falhas = [f"falta '{t}'" for t in exige if not re.search(t, texto)]
    return falhas + [f"contradiz a situação com '{t}'" for t in proibe if re.search(t, texto)]


def _minuta_fora_do_papel(minuta: str, esperado: dict) -> list[str]:
    dif = []
    rotulados = {rotulo: _num(v) for rotulo, v in
                 re.findall(r"valor (total|unitario)[^\d\n]{0,15}?r\$\s*(\d+(?:[.,]\d+)*)", minuta)}
    pares = (("total", esperado["valor_total"]), ("unitario", esperado["papeis"]["valor_unitario"]))
    for rotulo, valor in pares:
        if valor is None and rotulo in rotulados:
            dif.append(f"minuta com valor {rotulo} em pedido sem análise de mérito")
        elif valor is not None and rotulados.get(rotulo) != round(valor, 2):
            dif.append(f"minuta: valor {rotulo} {rotulados.get(rotulo)} ≠ {valor}")
    encaminhamento = {"apto_para_autorizacao": "apto para autorizacao",
                      "nao_recomendado": "nao recomendado",
                      "diligencia": "diligencia"}.get(esperado["recomendacao"], "-")
    sugerido = re.search(r"encaminhamento sugerido: ([a-z ]+)", minuta)
    if not sugerido or not sugerido.group(1).startswith(encaminhamento):
        dif.append(f"minuta sem o encaminhamento '{encaminhamento}'")
    return dif


# Categorias de alerta que o enunciado descreve, reconhecidas pela própria
# medição. A ordem importa: o alerta da autorização verbal também cita a
# autorização escrita que ela não supre.
CATEGORIAS_ALERTA = (("dados_pessoais", r"dados pessoais|\bcpf\b|conta (?:corrente|bancaria)"),
                     ("ordem_embutida", r"\bordem\b|dirigida ao sistema"),
                     ("autorizacao_verbal", r"verbal"),
                     ("autorizacao_escrita", r"autorizacao expressa e escrita"))
# Assunto de cada critério, para conferir o que um alerta afirma sobre ele.
ASSUNTOS = {"prestacao_contas": r"prestac", "limite_mensal": r"limite",
            "saldo_orcamentario": r"saldo", "cadastro": r"cadastro|matricula",
            "antecedencia": r"antecedencia"}


def _alertas_fora_do_papel(alertas: list[str], esperado: dict) -> list[str]:
    dif, achadas = [], []
    for alerta in alertas:
        categoria = next((c for c, padrao in CATEGORIAS_ALERTA if re.search(padrao, alerta)), None)
        if categoria is None:
            dif.append(f"alerta fora das categorias esperadas: {alerta[:60]!r}")
        else:
            achadas.append(categoria)
        # Um valor rotulado no alerta precisa ser o daquele papel.
        for rotulo, valor in re.findall(r"valor (total|unitario)[^\d\n]{0,25}?r\$\s*(\d+(?:[.,]\d+)*)",
                                        alerta):
            certo = (esperado["valor_total"] if rotulo == "total"
                     else esperado["papeis"]["valor_unitario"])
            if certo is None or _num(valor) != round(certo, 2):
                dif.append(f"alerta: valor {rotulo} {_num(valor)} ≠ {certo}")
        # O que o alerta afirma sobre um critério não pode contradizer a situação.
        for criterio, assunto in ASSUNTOS.items():
            situacao = esperado["situacoes"].get(criterio)
            if re.search(assunto, alerta) and situacao != "nao_verificado":
                proibidos = TERMOS.get((criterio, situacao), ([], []))[1]
                dif += [f"alerta sobre {criterio} contradiz a situação com '{t}'"
                        for t in proibidos if re.search(t, alerta)]
    if sorted(achadas) != sorted(esperado.get("alertas", [])):
        dif.append(f"alertas: categorias {sorted(achadas)} ≠ {sorted(esperado.get('alertas', []))}")
    return dif


def classificar(resultado, esperado: dict) -> tuple[str, list]:
    if resultado.situacao == "erro":
        return "erro_execucao", []
    if resultado.situacao == "recusada":
        return "recusado", []
    diferencas = conferir(resultado.instrucao, resultado.consultas, esperado)
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
            "custo": m.get("custo", 0), "segundos": m.get("segundos"),
            # Erros nos textos do modelo que o código substituiu antes da entrega.
            "textos_do_modelo_substituidos": resultado.textos_substituidos,
            # Alertas escritos pelo modelo, registrados e não exibidos.
            "alertas_do_modelo": resultado.alertas_do_modelo}


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
        "entregues_com_erro_no_texto_do_modelo": sum(bool(i["textos_do_modelo_substituidos"])
                                                     for i in itens),
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
         "Critério de acerto: os cinco campos, as situações dos seis critérios, a trilha "
         "(argumentos no papel, sem consulta ausente nem fora da etapa), os dados factuais dos "
         "textos com fonte, o papel de cada dado (fundamento coerente com a situação; valor "
         "total, unitário e encaminhamento da minuta), os alertas (exatamente as categorias "
         "esperadas, sem valor no papel errado nem afirmação que contradiga um critério), a "
         "condição da autorização escrita na urgência e nenhum número por extenso. As medições "
         "anteriores, com o critério de cada versão, estão em `historico/`.", "",
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
    l += ["", "## Textos do modelo substituídos pelo código", "",
          "Erros encontrados nos fundamentos, pendências e minuta escritos pelo modelo em "
          "instruções liberadas. Esses textos não chegam ao conferente: o código os refaz "
          "com os dados das consultas (barreira.py, item 6).", ""]
    for config, blocos in resumo.items():
        l.append(f"- {config}: {blocos['geral']['entregues_com_erro_no_texto_do_modelo']} de "
                 f"{blocos['geral']['itens']} itens")
    exemplos = [(i["configuracao"], i["rodada"], i["pedido"], t) for i in itens
                for t in i["textos_do_modelo_substituidos"]]
    for config, rodada, pedido, texto in exemplos[:10]:
        l.append(f"  - {config}, rodada {rodada}, {pedido}: {texto[:160]}")
    l += ["", "## Alertas escritos pelo modelo (registrados, não exibidos)", "",
          "A tela mostra os alertas montados pelo código (barreira.py, item 5). Os do modelo "
          "ficam no resultado para comparação.", ""]
    for config, _ in resumo.items():
        com = [i for i in itens if i["configuracao"] == config and i["alertas_do_modelo"]]
        l.append(f"- {config}: {len(com)} itens com alerta do modelo")
    vistos = set()
    for i in itens:
        for a in i["alertas_do_modelo"]:
            if (i["pedido"], a) not in vistos and len(vistos) < 8:
                vistos.add((i["pedido"], a))
                l.append(f"  - {i['pedido']}: {a[:160]}")
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
