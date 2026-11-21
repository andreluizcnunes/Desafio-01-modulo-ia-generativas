"""Teste local da barreira e da medição com respostas controladas, sem modelo e sem chave.

As consultas são feitas pelas ferramentas reais e só a resposta do modelo é
simulada (simulacao.py). Cada caso diz se a barreira deve liberar ou recusar.
Os casos de recusa reproduzem os achados da auditoria: matrícula errada no
histórico após a complementação, datas trocadas de papel, consulta obrigatória
omitida, exceção de urgência marcada pelo modelo, fatos inventados nos textos.
Os de liberação são o controle positivo (pedido regular), as duas diligências,
o pedido urgente e as duas complementações.

Depois, os mesmos casos passam por `instruir` com o agente simulado e pelo
classificador da medição: a instrução recusada não chega à tela (situação
"recusada") e não conta como acerto; e as falhas do fluxo (status de erro,
fluxo sem resposta, resposta de outra execução, exceção, fluxo sem evento
inicial com uma execução anterior válida no banco) viram erro de execução,
sem reaproveitar a instrução anterior.

Por fim, confere que nenhum módulo do agente nem a tela leem o gabarito.

Execução: python teste_barreira.py
Saída: resultados/teste_barreira.txt
"""
import json
import pathlib

from barreira import verificar
from instrutor import instruir
from medir import classificar
from simulacao import (AgenteSimulado, alterar, consulta, consultas_corretas, esperado,
                       instrucao_correta)

BASE = pathlib.Path(__file__).parent
SAIDA = BASE / "resultados" / "teste_barreira.txt"
PEDIDOS = {p["numero"]: p for p in json.loads((BASE / "dados" / "pedidos.json").read_text("utf-8"))}
COMPLEMENTOS = {c["numero"]: c for c in
                json.loads((BASE / "dados" / "complementacoes.json").read_text("utf-8"))}
linhas: list[str] = []


def log(texto: str = "") -> None:
    print(texto)
    linhas.append(texto)


def caso_correto(numero: str, complementacao: bool = False):
    item = esperado(numero, complementacao)
    consultas = consultas_corretas(item)
    return item, consultas, instrucao_correta(item, consultas)


def montar_casos() -> list[tuple]:
    """(rótulo, pedido, complemento, consultas, instrução, deve_recusar, gabarito)."""
    casos = []
    p101, p106, p107, p108 = (PEDIDOS[n] for n in ("DIA-2026-0101", "DIA-2026-0106",
                                                   "DIA-2026-0107", "DIA-2026-0108"))
    p111, p112 = PEDIDOS["DIA-2026-0111"], PEDIDOS["DIA-2026-0112"]
    c111, c112 = COMPLEMENTOS["DIA-2026-0111"], COMPLEMENTOS["DIA-2026-0112"]

    # Controle positivo.
    g, k, i = caso_correto("DIA-2026-0101")
    casos.append(("0101 regular, instrução correta (controle positivo)", p101, None, k, i, False, g))

    # Datas trocadas de papel.
    trocadas = [k[0],
                consulta("calcular_diarias", grupo="B", destino_uf="MT", data_pedido="2026-11-09",
                         data_partida="2026-10-08", data_retorno="2026-11-12"),
                consulta("consultar_historico_diarias", matricula="204317",
                         data_partida="2026-10-08", quantidade_pedida=35.5),
                consulta("consultar_saldo_diarias", unidade="CFF", valor=9940.0)]
    casos.append(("0101 com protocolo e partida trocados (35,5 diárias, R$ 9.940,00)", p101, None,
                  trocadas, alterar(i, quantidade_diarias=35.5, valor_total=9940.0), True, g))
    so_historico = [k[0], k[1],
                    consulta("consultar_historico_diarias", matricula="204317",
                             data_partida="2026-10-08", quantidade_pedida=3.5), k[3]]
    casos.append(("0101 com a data de protocolo no lugar da partida, só no histórico", p101, None,
                  so_historico, i, True, g))

    # Fatos inventados nos textos, com os números principais certos.
    inventado = alterar(i)
    inventado.verificacoes[-1].detalhe = "Saldo da unidade CFF: R$ 50.000,00, suficiente."
    casos.append(("0101 com saldo inventado no fundamento", p101, None, k, inventado, True, g))
    casos.append(("0101 com valor inventado na minuta", p101, None, k,
                  alterar(i, minuta_despacho=i.minuta_despacho + " Valor de referência: "
                                                                  "R$ 1.200,00."), True, g))

    # Consulta obrigatória omitida.
    g, k, i = caso_correto("DIA-2026-0108")
    sem_historico = [c for c in k if c["ferramenta"] != "consultar_historico_diarias"]
    apto = alterar(i, recomendacao="apto_para_autorizacao",
                   situacoes={"prestacao_contas": "atende"})
    casos.append(("0108 sem a consulta de histórico, marcado apto", p108, None, sem_historico,
                  apto, True, g))
    casos.append(("0108 com todas as consultas, marcado apto apesar da VENCIDA", p108, None, k,
                  apto, True, g))
    casos.append(("0108 correto: não recomendado pela prestação vencida", p108, None, k, i, False, g))

    # A exceção de urgência não vem da marcação do modelo.
    g, k, i = caso_correto("DIA-2026-0107")
    casos.append(("0107 com autorização verbal, marcado apto com exige_autorizacao_superior",
                  p107, None, k,
                  alterar(i, recomendacao="apto_para_autorizacao", exige_autorizacao_superior=True,
                          situacoes={"antecedencia": "atende"}), True, g))
    casos.append(("0107 não recomendado, mas com exige_autorizacao_superior=true", p107, None, k,
                  alterar(i, exige_autorizacao_superior=True), True, g))
    casos.append(("0107 correto: não recomendado, sem exceção", p107, None, k, i, False, g))
    g, k, i = caso_correto("DIA-2026-0106")
    casos.append(("0106 urgente correto: apto, autorização escrita na minuta", p106, None, k, i,
                  False, g))
    casos.append(("0106 urgente sem a condição da autorização escrita na minuta", p106, None, k,
                  alterar(i, minuta_despacho="Ao ordenador de despesa. Pedido DIA-2026-0106: "
                                             "apto para autorização."), True, g))
    casos.append(("0106 urgente marcado não recomendado", p106, None, k,
                  alterar(i, recomendacao="nao_recomendado", exige_autorizacao_superior=False,
                          situacoes={"antecedencia": "nao_atende"}), True, g))

    # Diligências.
    g, k, i = caso_correto("DIA-2026-0111")
    casos.append(("0111 diligência correta (falta o retorno)", p111, None, k, i, False, g))
    casos.append(("0111 diligência com quantidade e valor", p111, None, k,
                  alterar(i, quantidade_diarias=4.5, valor_total=1260.0), True, g))
    g, k, i = caso_correto("DIA-2026-0112")
    casos.append(("0112 diligência correta (nome diverge do cadastro)", p112, None, k, i, False, g))
    casos.append(("0112 calculado para o servidor da matrícula digitada", p112, None,
                  k + [consulta("calcular_diarias", grupo="B", destino_uf="MT",
                                data_pedido="2026-10-09", data_partida="2026-11-24",
                                data_retorno="2026-11-27")],
                  alterar(i, recomendacao="apto_para_autorizacao", quantidade_diarias=3.5,
                          valor_total=980.0), True, g))

    # Complementações.
    g, k, i = caso_correto("DIA-2026-0111", complementacao=True)
    casos.append(("0111 complementação correta (retorno 2026-11-20)", p111, c111, k, i, False, g))
    casos.append(("complementação do 0111 aplicada ao 0112", p112, c111, k, i, True,
                  esperado("DIA-2026-0112")))
    g, k, i = caso_correto("DIA-2026-0112", complementacao=True)
    casos.append(("0112 complementação correta (matrícula 207418)", p112, c112, k, i, False, g))
    historico_errado = [c if c["ferramenta"] != "consultar_historico_diarias" else
                        consulta("consultar_historico_diarias", matricula="207481",
                                 data_partida="2026-11-24", quantidade_pedida=3.5) for c in k]
    casos.append(("0112 complementação com o histórico da matrícula digitada 207481", p112, c112,
                  historico_errado, i, True, g))
    return casos


def parte1_barreira(casos) -> None:
    log("[1] Barreira com respostas controladas (ferramentas reais, modelo simulado)")
    for rotulo, pedido, compl, consultas, instrucao, deve_recusar, _ in casos:
        problemas = verificar(instrucao, consultas, pedido, compl)
        assert bool(problemas) == deve_recusar, (rotulo, problemas)
        log(f"    {rotulo:78} -> {'RECUSADA' if problemas else 'liberada'}")
        for p in problemas:
            log(f"        · {p}")


def parte2_instruir_e_medir(casos) -> None:
    log("\n[2] Os mesmos casos por instruir() e pelo classificador da medição")
    for rotulo, pedido, compl, consultas, instrucao, deve_recusar, gab in casos:
        agente = AgenteSimulado(lambda *_: {"modo": "normal", "instrucao": instrucao,
                                            "consultas": consultas})
        r = instruir(pedido, agente, complemento=compl)
        classe, diferencas = classificar(r, gab)
        assert r.situacao == ("recusada" if deve_recusar else "entregue"), (rotulo, r.motivo)
        if deve_recusar:
            assert classe == "recusado", (rotulo, classe)
        elif compl is None or pedido["numero"] == compl["numero"]:
            assert classe == "acerto", (rotulo, diferencas)
        log(f"    {rotulo:78} -> {r.situacao:9} · medição: {classe}")

    log("\n[3] Falhas do fluxo: nada é lido do conteúdo, a medição conta erro de execução")
    g, k, i = caso_correto("DIA-2026-0101")
    for modo, rotulo in (("erro", "status ERROR (erro da API como conteúdo)"),
                         ("sem_saida", "fluxo terminou sem RunOutput e sem última execução"),
                         ("outra_execucao", "resposta de outra execução"),
                         ("excecao", "exceção durante a execução"),
                         ("sem_inicio", "sem evento inicial nem resposta; anterior válida no banco"),
                         ("anterior", "sem resposta; banco devolve a execução anterior")):
        for progresso in (False, True):
            cenas = [modo]
            if modo in ("sem_inicio", "anterior"):
                cenas = ["normal", modo]  # primeiro uma execução válida da mesma sessão
            roteiro = iter(cenas)
            agente = AgenteSimulado(lambda *_: {"modo": next(roteiro), "instrucao": i,
                                                "consultas": k})
            if len(cenas) == 2:
                anterior = instruir(PEDIDOS["DIA-2026-0101"], agente)
                assert anterior.situacao == "entregue", anterior.motivo
            r = instruir(PEDIDOS["DIA-2026-0101"], agente,
                         ao_chamar_ferramenta=(lambda *_: None) if progresso else None)
            classe, _ = classificar(r, g)
            assert r.situacao == "erro" and classe == "erro_execucao", (modo, progresso, r)
            assert r.instrucao is None, (modo, progresso)
            if modo != "erro":  # nada da resposta foi lido
                assert not r.consultas, (modo, progresso)
            log(f"    {rotulo:58} {'(com progresso)' if progresso else '(sem progresso)':16} "
                f"-> {r.situacao} · {r.motivo[0][:60]}")


def parte3_gabarito_isolado() -> None:
    log("\n[4] O gabarito só é lido pela avaliação")
    for modulo in ("ferramentas.py", "instrutor.py", "barreira.py", "app.py"):
        texto = (BASE / modulo).read_text(encoding="utf-8")
        assert "gabarito" not in texto.lower(), modulo
        log(f"    {modulo:16} não lê o gabarito")


if __name__ == "__main__":
    casos = montar_casos()
    parte1_barreira(casos)
    parte2_instruir_e_medir(casos)
    parte3_gabarito_isolado()
    log(f"\nTodos os {len(casos)} casos controlados e as 12 falhas do fluxo passaram.")
    SAIDA.write_text("\n".join(linhas) + "\n", encoding="utf-8")
