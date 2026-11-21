"""Evidências da Etapa 3: o filtro de dados pessoais e a barreira em código.

Parte 1 (sem API): aplica o filtro a todos os pedidos e complementações e
confere que só o CPF e a conta/agência do DIA-2026-0104 são mascarados, e que
nenhuma matrícula, data ou número de pedido é tocado (enunciado, Etapa 3).

Parte 2 (sem API): entrega à barreira as respostas controladas de
teste_barreira.py, instruções adulteradas de propósito como o dossiê adulterado
da Aula 04, Seção 7.3, e confere que cada uma é recusada, e que as corretas
passam.

Parte 3 (com API): instrui o DIA-2026-0104 de verdade e procura o CPF e a
conta no que foi enviado ao modelo e em cada tabela do banco (Aula 07, 6.1).

Execução: python verificar_etapa3.py
Saída: resultados/etapa3_filtro_e_barreira.txt
"""
import json
import pathlib
import re
import sqlite3

from agno.run.agent import RunInput

from barreira import verificar
from instrutor import (FILTRO_DADOS_PESSOAIS, apagar_banco, construir_agente, instruir,
                       texto_da_complementacao, texto_do_pedido)
from teste_barreira import montar_casos

BASE = pathlib.Path(__file__).parent
SAIDA = BASE / "resultados" / "etapa3_filtro_e_barreira.txt"
PEDIDOS = json.loads((BASE / "dados" / "pedidos.json").read_text(encoding="utf-8"))
COMPLEMENTOS = json.loads((BASE / "dados" / "complementacoes.json").read_text(encoding="utf-8"))
POR_NUMERO = {p["numero"]: p for p in PEDIDOS}
CPF, CONTA, AGENCIA = "052.318.947-20", "98765-4", "1234-5"
linhas: list[str] = []


def log(texto: str = "") -> None:
    print(texto)
    linhas.append(texto)


def parte1_filtro() -> None:
    log("[1] Filtro de dados pessoais, sem API")
    textos = ([(p["numero"], texto_do_pedido(p)) for p in PEDIDOS]
              + [(f"{c['numero']} (compl.)", texto_da_complementacao(c)) for c in COMPLEMENTOS])
    for rotulo, original in textos:
        entrada = RunInput(input_content=original)
        FILTRO_DADOS_PESSOAIS.check(entrada)
        filtrado = entrada.input_content_string()
        # Tudo que é identificador do processo precisa sobreviver ao filtro.
        identificadores = (set(re.findall(r"\b\d{6}\b", original))
                           | set(re.findall(r"\b\d{4}-\d{2}-\d{2}\b", original))
                           | set(re.findall(r"DIA-\d{4}-\d{4}", original)))
        perdidos = [i for i in identificadores if i not in filtrado]
        mascarados = original != filtrado
        assert not perdidos, f"{rotulo}: identificadores mascarados {perdidos}"
        if rotulo == "DIA-2026-0104":
            assert CPF not in filtrado and CONTA not in filtrado and AGENCIA not in filtrado
        else:
            assert not mascarados, f"{rotulo}: mascarou algo indevidamente"
        log(f"    {rotulo:24} mascarado: {'SIM' if mascarados else 'não':3} · "
            f"identificadores preservados: {len(identificadores)}")
    trecho = FILTRO_DADOS_PESSOAIS
    entrada = RunInput(input_content=POR_NUMERO["DIA-2026-0104"]["justificativa"])
    trecho.check(entrada)
    log(f"    justificativa do 0104 como chega ao modelo: {entrada.input_content_string()}")


def parte2_barreira() -> None:
    log("\n[2] Barreira em código, com respostas controladas, sem API")
    log("    (os casos estão em teste_barreira.py, que também os passa pela medição)")
    for rotulo, pedido, compl, consultas, instrucao, deve_recusar, _ in montar_casos():
        problemas = verificar(instrucao, consultas, pedido, compl)
        assert bool(problemas) == deve_recusar, (rotulo, problemas)
        log(f"    {rotulo:78} -> {'RECUSADA' if problemas else 'liberada'}")
        for p in problemas:
            log(f"        · {p}")


def parte3_api() -> None:
    log("\n[3] DIA-2026-0104 instruído de verdade: o CPF chega ao modelo ou ao banco?")
    banco = BASE / "resultados" / "etapa3_verificacao.db"
    apagar_banco(banco)
    resultado = instruir(POR_NUMERO["DIA-2026-0104"], construir_agente(banco=banco))
    log(f"    situação: {resultado.situacao} · recomendação: "
        f"{resultado.instrucao.recomendacao if resultado.instrucao else '-'}")
    log(f"    entrada enviada ao modelo contém CPF? "
        f"{'SIM' if CPF in resultado.entrada_enviada else 'não'} · conta? "
        f"{'SIM' if CONTA in resultado.entrada_enviada else 'não'} · matrícula 200941 intacta? "
        f"{'sim' if '200941' in resultado.entrada_enviada else 'NÃO'}")
    conexao = sqlite3.connect(banco)
    for (tabela,) in conexao.execute("SELECT name FROM sqlite_master WHERE type='table'"):
        linhas_tabela = conexao.execute(f"SELECT * FROM {tabela}").fetchall()
        achou = [d for d in (CPF, CONTA, AGENCIA) if any(d in str(l) for l in linhas_tabela)]
        log(f"    tabela {tabela:22} {len(linhas_tabela):>3} registro(s) · "
            f"dado pessoal encontrado: {achou or 'nenhum'}")
        assert not achou
    conexao.close()
    apagar_banco(banco)
    if resultado.instrucao:
        log(f"    alertas do agente: {resultado.instrucao.alertas}")


if __name__ == "__main__":
    parte1_filtro()
    parte2_barreira()
    parte3_api()
    log("\nTodas as verificações da Etapa 3 passaram.")
    SAIDA.write_text("\n".join(linhas) + "\n", encoding="utf-8")
