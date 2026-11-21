"""Gera o gabarito.json aplicando a IN SEMA nº 07/2026 por código, sem modelo algum.

O enunciado descreve o gabarito original como calculado pelo gerar_dados.py,
"que aplica a norma por código, sem modelo algum". Esse arquivo não acompanha
o acervo, e este script refaz o cálculo, **independente de ferramentas.py**,
para que um erro nas ferramentas não se repita no gabarito (Aula 03, 5.2: a
medição pode falhar tanto quanto o sistema medido).

O gabarito é escrito antes de qualquer execução do agente (Aula 02, Mini LAB;
Aula 03, 5.1) e **nunca é entregue ao agente**: nenhum módulo do agente o
importa, porque um agente que lê a resposta esperada não está sendo medido.

Duas informações vêm do cenário e não de cálculo, como no gerar_dados.py:
- quais justificativas descrevem urgência legítima do art. 5º, § 1º (só o
  DIA-2026-0106, incêndio florestal em curso; o 0107 alega autorização verbal
  para uma capacitação, o que o § 2º não admite);
- a decisão do desenho.md, Seção 8, para o pedido urgente: apto para
  autorização, com exigência de autorização superior escrita.

Execução: python gabarito.py
"""
import csv
import json
import pathlib
import re
from datetime import date, timedelta

BASE = pathlib.Path(__file__).parent
DADOS = BASE / "dados"

URGENCIA_LEGITIMA = {"DIA-2026-0106"}


def carregar():
    tabela = json.loads((DADOS / "tabela_diarias.json").read_text(encoding="utf-8"))
    unidades = json.loads((DADOS / "unidades.json").read_text(encoding="utf-8"))
    pedidos = json.loads((DADOS / "pedidos.json").read_text(encoding="utf-8"))
    complementos = json.loads((DADOS / "complementacoes.json").read_text(encoding="utf-8"))
    with open(DADOS / "servidores.csv", encoding="utf-8") as f:
        servidores = {s["matricula"]: s for s in csv.DictReader(f)}
    with open(DADOS / "historico_diarias.csv", encoding="utf-8") as f:
        historico = list(csv.DictReader(f))
    return tabela, unidades, pedidos, complementos, servidores, historico


def uteis_depois(inicio: date, n: int) -> date:
    d = inicio
    while n:
        d += timedelta(days=1)
        if d.weekday() < 5:
            n -= 1
    return d


CRITERIOS = ("cadastro", "dados_completos", "antecedencia", "prestacao_contas",
             "limite_mensal", "saldo_orcamentario")


def instruir(pedido: dict, dados, original: dict | None = None,
             complemento: dict | None = None) -> dict:
    """Aplica os arts. 3º a 9º e devolve a instrução esperada.

    Além da recomendação e dos números, registra o que a medição precisa para
    conferir a instrução inteira: a situação de cada critério, a trilha de
    consultas que a instrução deveria ter feito (cada argumento no seu papel) e
    os fatos que os textos podem citar.
    """
    tabela, unidades, _, _, servidores, historico = dados
    original = original or pedido
    analise = date.fromisoformat(tabela["data_da_analise"])
    s = servidores.get(pedido["matricula"])
    esperado = {"numero_pedido": pedido["numero"], "matricula": pedido["matricula"],
                "quantidade_diarias": None, "valor_total": None,
                "exige_autorizacao_superior": False, "nao_atende": [],
                "situacoes": dict.fromkeys(CRITERIOS, "nao_verificado"),
                "trilha": {"consultar_servidor": {"matricula": pedido["matricula"],
                                                  "nome_informado": pedido["nome"]}}}
    fatos = {"valores": set(), "numeros": {10.0, 5.0},
             "datas": {d for d in (original.get("data_pedido"), original.get("data_partida"),
                                   original.get("data_retorno"), pedido.get("data_retorno"),
                                   tabela["data_da_analise"]) if d},
             "matriculas": {original["matricula"], pedido["matricula"]},
             "pedidos": {pedido["numero"]} | set(re.findall(r"DIA-\d{4}-\d{4}",
                                                            pedido.get("justificativa", "")))}
    if complemento:
        fatos["datas"] |= {complemento["data"]} | set(re.findall(r"\d{4}-\d{2}-\d{2}",
                                                                 complemento["texto"]))

    def fechar(resultado: dict) -> dict:
        resultado["fatos"] = {k: sorted(v) for k, v in fatos.items()}
        return resultado

    # Art. 9º: incompleto ou divergente do cadastro -> diligência, sem análise de mérito.
    divergente = s is None or s["nome"].strip().lower() != pedido["nome"].strip().lower()
    incompleto = not pedido.get("data_retorno")
    if divergente or incompleto:
        esperado["situacoes"].update(cadastro="nao_atende" if divergente else "atende",
                                     dados_completos="nao_atende" if incompleto else "atende")
        esperado.update(recomendacao="diligencia",
                        nao_atende=(["cadastro"] if divergente else []) +
                                   (["dados_completos"] if incompleto else []))
        return fechar(esperado)

    partida = date.fromisoformat(pedido["data_partida"])
    retorno = date.fromisoformat(pedido["data_retorno"])
    protocolo = date.fromisoformat(pedido["data_pedido"])

    # Arts. 3º e 4º.
    pernoites = (retorno - partida).days
    quantidade = 0.5 if pernoites == 0 else pernoites + 0.5
    uf = pedido["destino_uf"].upper()
    classe = "interior_mt" if uf == "MT" else "distrito_federal" if uf == "DF" else "outra_uf"
    unitario = tabela["valores"][s["grupo_diaria"]][classe]
    valor = quantidade * unitario
    esperado.update(quantidade_diarias=quantidade, valor_total=valor)
    esperado["trilha"].update({
        "calcular_diarias": {"grupo": s["grupo_diaria"], "destino_uf": uf,
                             "data_pedido": pedido["data_pedido"],
                             "data_partida": pedido["data_partida"],
                             "data_retorno": pedido["data_retorno"]},
        "consultar_historico_diarias": {"matricula": s["matricula"],
                                        "data_partida": pedido["data_partida"],
                                        "quantidade_pedida": quantidade},
        "consultar_saldo_diarias": {"unidade": s["unidade"], "valor": valor}})
    saldo = unidades[s["unidade"]]["saldo_diarias"]
    fatos["valores"] |= {unitario, valor, saldo}

    falhas = []
    # Art. 5º.
    antecedencia = (partida - protocolo).days
    if antecedencia < tabela["antecedencia_minima_dias"]:
        if pedido["numero"] in URGENCIA_LEGITIMA:
            esperado["exige_autorizacao_superior"] = True
        else:
            falhas.append("antecedencia")
    # Art. 7º.
    for h in historico:
        if h["matricula"] == s["matricula"]:
            fatos["datas"] |= {h["data_partida"], h["data_retorno"]}
            fatos["pedidos"].add(h["pedido"])
            if h["prestacao_contas"] == "pendente":
                vence = uteis_depois(date.fromisoformat(h["data_retorno"]),
                                     tabela["prazo_prestacao_dias_uteis"])
                fatos["datas"].add(vence.isoformat())
                if vence < analise:
                    falhas.append("prestacao_contas")
    # Art. 6º.
    mes = sum(float(h["quantidade"]) for h in historico
              if h["matricula"] == s["matricula"] and h["data_partida"][:7] == pedido["data_partida"][:7])
    if mes + quantidade > tabela["limite_mensal_diarias"]:
        falhas.append("limite_mensal")
    fatos["numeros"] |= {quantidade, float(pernoites), float(antecedencia), mes,
                         mes + quantidade, float(tabela["limite_mensal_diarias"]),
                         float(tabela["antecedencia_minima_dias"]),
                         float(tabela["prazo_prestacao_dias_uteis"])}
    # Art. 8º.
    if saldo < valor:
        falhas.append("saldo_orcamentario")

    esperado["nao_atende"] = sorted(set(falhas))
    esperado["situacoes"] = {c: ("nao_atende" if c in falhas else "atende") for c in CRITERIOS}
    esperado["recomendacao"] = "nao_recomendado" if falhas else "apto_para_autorizacao"
    return fechar(esperado)


def complementar(pedido: dict, complemento: dict) -> dict:
    """Aplica a complementação ao pedido, como o servidor faria ao reconstituir o caso."""
    texto = complemento["texto"]
    novo = dict(pedido)
    if pedido["numero"] == "DIA-2026-0111":
        novo["data_retorno"] = texto.split("previsto para ")[1].rstrip(".")
    if pedido["numero"] == "DIA-2026-0112":
        novo["matricula"] = texto.split("correta é ")[1].rstrip(".")
    return novo


def main() -> None:
    dados = carregar()
    _, _, pedidos, complementos, _, _ = dados
    por_numero = {p["numero"]: p for p in pedidos}
    gabarito = {"pedidos": [instruir(p, dados) for p in pedidos], "complementacoes": []}
    for c in complementos:
        resultado = instruir(complementar(por_numero[c["numero"]], c), dados,
                             original=por_numero[c["numero"]], complemento=c)
        gabarito["complementacoes"].append(resultado)

    destino = BASE / "gabarito.json"
    destino.write_text(json.dumps(gabarito, ensure_ascii=False, indent=2), encoding="utf-8")
    for item in gabarito["pedidos"] + gabarito["complementacoes"]:
        print(f"{item['numero_pedido']}  mat {item['matricula']}  {item['recomendacao']:22} "
              f"{str(item['quantidade_diarias']):>4}  {str(item['valor_total']):>7}  "
              f"autorização superior: {item['exige_autorizacao_superior']!s:5}  "
              f"não atende: {', '.join(item['nao_atende']) or '-'}")
    print(f"\ngravado em {destino.name}")


if __name__ == "__main__":
    main()
