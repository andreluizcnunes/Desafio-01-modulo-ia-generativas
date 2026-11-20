"""Evidências da Etapa 3: o filtro de dados pessoais e a barreira em código.

Parte 1 (sem API): aplica o filtro a todos os pedidos e complementações e
confere que só o CPF e a conta/agência do DIA-2026-0104 são mascarados, e que
nenhuma matrícula, data ou número de pedido é tocado (enunciado, Etapa 3).

Parte 2 (sem API): entrega à barreira instruções adulteradas de propósito,
como o dossiê adulterado da Aula 04, Seção 7.3, e confere que cada uma é
recusada, e que a instrução correta passa.

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
from instrutor import (FILTRO_DADOS_PESSOAIS, Instrucao, Verificacao, apagar_banco, construir_agente, instruir,
                       texto_da_complementacao, texto_do_pedido)
from ferramentas import calcular_diarias, consultar_historico_diarias, consultar_servidor

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


def instrucao_base(numero: str, matricula: str, quantidade, valor, recomendacao: str) -> Instrucao:
    situacao = "atende" if recomendacao == "apto_para_autorizacao" else "nao_verificado"
    return Instrucao(
        numero_pedido=numero, matricula=matricula, quantidade_diarias=quantidade,
        valor_total=valor, recomendacao=recomendacao, exige_autorizacao_superior=False,
        verificacoes=[Verificacao(criterio=c, situacao=situacao, detalhe="-") for c in
                      ("cadastro", "dados_completos", "antecedencia", "prestacao_contas",
                       "limite_mensal", "saldo_orcamentario")],
        pendencias=[], alertas=[], minuta_despacho="-")


def consulta(ferramenta, funcao, **args) -> dict:
    return {"ferramenta": ferramenta, "argumentos": args, "resultado": funcao(**args)}


def parte2_barreira() -> None:
    log("\n[2] Barreira em código, com instruções adulteradas, sem API")
    p101 = POR_NUMERO["DIA-2026-0101"]
    certas = [
        consulta("consultar_servidor", consultar_servidor, matricula="204317",
                 nome_informado="Ana Paula Figueiredo"),
        consulta("calcular_diarias", calcular_diarias, grupo="B", destino_uf="MT",
                 data_pedido="2026-10-08", data_partida="2026-11-09", data_retorno="2026-11-12"),
    ]
    casos = []
    casos.append(("instrução correta do 0101", p101, None, certas,
                  instrucao_base("DIA-2026-0101", "204317", 3.5, 980.0, "apto_para_autorizacao"),
                  False))
    casos.append(("valor plantado (R$ 9.800,00) no 0101", p101, None, certas,
                  instrucao_base("DIA-2026-0101", "204317", 3.5, 9800.0, "apto_para_autorizacao"),
                  True))
    casos.append(("matrícula que não consta do pedido", p101, None,
                  [consulta("consultar_servidor", consultar_servidor, matricula="204775",
                            nome_informado="Ana Paula Figueiredo")] + certas[1:],
                  instrucao_base("DIA-2026-0101", "204775", 3.5, 980.0, "apto_para_autorizacao"),
                  True))
    p111 = POR_NUMERO["DIA-2026-0111"]
    casos.append(("0111 com data de retorno inventada", p111, None,
                  [consulta("consultar_servidor", consultar_servidor, matricula="206689",
                            nome_informado="Beatriz Moraes Cunha"),
                   consulta("calcular_diarias", calcular_diarias, grupo="B", destino_uf="MT",
                            data_pedido="2026-10-09", data_partida="2026-11-17",
                            data_retorno="2026-11-21")],
                  instrucao_base("DIA-2026-0111", "206689", 4.5, 1260.0, "apto_para_autorizacao"),
                  True))
    p112 = POR_NUMERO["DIA-2026-0112"]
    casos.append(("0112 calculado para o servidor errado (Rafael, grupo B)", p112, None,
                  [consulta("consultar_servidor", consultar_servidor, matricula="207481",
                            nome_informado="Carla Regina Souza"),
                   consulta("calcular_diarias", calcular_diarias, grupo="B", destino_uf="MT",
                            data_pedido="2026-10-09", data_partida="2026-11-24",
                            data_retorno="2026-11-27")],
                  instrucao_base("DIA-2026-0112", "207481", 3.5, 980.0, "apto_para_autorizacao"),
                  True))
    c112 = next(c for c in COMPLEMENTOS if c["numero"] == "DIA-2026-0112")
    casos.append(("complementação do 0112 com a matrícula corrigida", p112, c112,
                  [consulta("consultar_servidor", consultar_servidor, matricula="207418",
                            nome_informado="Carla Regina Souza"),
                   consulta("calcular_diarias", calcular_diarias, grupo="C", destino_uf="MT",
                            data_pedido="2026-10-09", data_partida="2026-11-24",
                            data_retorno="2026-11-27")],
                  instrucao_base("DIA-2026-0112", "207418", 3.5, 770.0, "apto_para_autorizacao"),
                  False))
    p108 = POR_NUMERO["DIA-2026-0108"]
    casos.append(("0108 marcado apto apesar da prestação VENCIDA", p108, None,
                  [consulta("consultar_servidor", consultar_servidor, matricula="203648",
                            nome_informado="Gustavo Henrique Prado"),
                   consulta("calcular_diarias", calcular_diarias, grupo="B", destino_uf="MT",
                            data_pedido="2026-10-05", data_partida="2026-11-03",
                            data_retorno="2026-11-06"),
                   consulta("consultar_historico_diarias", consultar_historico_diarias,
                            matricula="203648", data_partida="2026-11-03", quantidade_pedida=3.5)],
                  instrucao_base("DIA-2026-0108", "203648", 3.5, 980.0, "apto_para_autorizacao"),
                  True))
    for rotulo, pedido, compl, consultas, instrucao, deve_recusar in casos:
        problemas = verificar(instrucao, consultas, pedido, compl)
        assert bool(problemas) == deve_recusar, (rotulo, problemas)
        log(f"    {rotulo:56} -> {'RECUSADA' if problemas else 'liberada'}")
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
