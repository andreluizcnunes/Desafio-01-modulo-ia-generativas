"""Teste do formulário de conferência (Etapa 5), sem servidor e sem navegador.

Usa o AppTest do próprio Streamlit para executar app.py como o servidor o
usaria. O banco do agente e o registro de conferências ficam numa pasta
temporária: o teste nunca toca o agente.db do formulário em uso.

Parte A (sem chave): o agente é substituído por respostas controladas
(simulacao.py), com as ferramentas reais. Cobre o processamento normal, a
minuta errada do modelo substituída pela do código, os alertas errados do
modelo fora da tela e os exigidos pelo enunciado presentes, o registro da divergência
humana, a diligência com complementação na mesma sessão, a recusa da barreira,
a tentativa de consulta de mérito no 0112 em diligência, barrada antes de
executar (Agno real com o modelo interceptado), o status ERROR, o fluxo que
termina sem resposta (inclusive sem evento
inicial, com uma instrução válida anterior no banco), a resposta sem
identificador da execução e a eliminação (válida e
com identidade inválida).

Parte B (com chave): o pedido regular e a diligência com complementação pelo
modelo real, para mostrar o fluxo de ponta a ponta.

Execução: python teste_app.py
Saída: resultados/etapa5_formulario.txt
"""
import json
import os
import pathlib
import shutil
import tempfile

PASTA = pathlib.Path(tempfile.mkdtemp(prefix="teste_app_"))
os.environ["CONFERENCIAS_ARQUIVO"] = str(PASTA / "conferencias.jsonl")

import instrutor  # noqa: E402
from streamlit.testing.v1 import AppTest  # noqa: E402

from simulacao import (AgenteSimulado, alterar, consultas_corretas, esperado,  # noqa: E402
                       instrucao_correta)
from teste_eliminacao import montar_banco  # noqa: E402

BASE = pathlib.Path(__file__).parent
SAIDA = BASE / "resultados" / "etapa5_formulario.txt"
BANCO_TESTE = PASTA / "agente.db"
linhas: list[str] = []


def log(texto: str) -> None:
    print(texto)
    linhas.append(texto)


class AgenteComutavel:
    """O agente que a tela recebe: delega ao simulado ou ao real, conforme o passo."""

    def __init__(self):
        self.cena = "normal"
        self.real = None
        self.interceptado = self.roteirizado = None
        self.simulado = AgenteSimulado(self._roteiro)

    def _roteiro(self, session_id, entrada):
        complementacao = (str(entrada).startswith("Complementação")
                          and self.cena != "data_indefinida")
        item = esperado(session_id, complementacao)
        consultas = consultas_corretas(item)
        instrucao = instrucao_correta(item, consultas)
        if self.cena == "recusa":
            # Valor total diferente do cálculo: a barreira recusa.
            instrucao = alterar(instrucao, valor_total=1200.0,
                                minuta_despacho="Valor total: R$ 1.200,00 (valor plantado).")
        if self.cena == "alerta_errado":
            # Alertas errados do modelo: o unitário como total, no 0101, e a
            # prestação "regularizada" que o histórico desmente, no 0108.
            instrucao = alterar(instrucao, alertas=["O valor total correto é R$ 280,00.",
                                                    "A prestação de contas foi regularizada."])
        if self.cena == "texto_errado":
            # Minuta do modelo com o valor unitário no lugar do total: o código
            # refaz a minuta com os dados do cálculo.
            instrucao = alterar(instrucao, minuta_despacho="Pedido DIA-2026-0101: valor total "
                                                           "de R$ 280,00. Apto.")
        modo = self.cena if self.cena in ("erro", "sem_saida", "sem_inicio", "anterior",
                                          "sem_id") else "normal"
        return {"modo": modo, "instrucao": instrucao, "consultas": consultas}

    def _alvo(self):
        if self.cena == "interceptado":
            # O Agno real, com o gancho de ferramenta e o banco, e só as
            # requisições ao modelo interceptadas (teste_bloqueio.py).
            if self.interceptado is None:
                from teste_bloqueio import ModeloRoteirizado, agente_interceptado
                self.roteirizado = ModeloRoteirizado()
                self.interceptado = agente_interceptado(PASTA / "interceptado.db",
                                                        self.roteirizado, FABRICA_ORIGINAL)
            return self.interceptado
        if self.cena != "real":
            return self.simulado
        if self.real is None:
            self.real = FABRICA_ORIGINAL(memoria="historico", banco=BANCO_TESTE)
        return self.real

    def run(self, *args, **kwargs):
        return self._alvo().run(*args, **kwargs)

    def get_last_run_output(self, *args, **kwargs):
        return self._alvo().get_last_run_output(*args, **kwargs)


AGENTE = AgenteComutavel()
FABRICA_ORIGINAL = instrutor.construir_agente
instrutor.construir_agente = lambda **_: AGENTE
instrutor.BANCO_PADRAO = BANCO_TESTE


def botao(at: AppTest, rotulo: str):
    return next(b for b in at.button if b.label == rotulo)


def textos(at: AppTest) -> str:
    partes = [m.value for m in at.markdown] + [m.label + " " + str(m.value) for m in at.metric]
    partes += [e.value for e in at.error] + [w.value for w in at.warning]
    partes += [s.value for s in at.success] + [i.value for i in at.info]
    partes += [c.value for c in at.caption] + [t.value for t in at.text_area]
    partes += [x.label for x in at.expander] + [s.label for s in at.status]
    partes += [h.value for h in at.subheader]
    # Tabelas (verificações com o fundamento, consultas), célula por célula.
    partes += [" ".join(map(str, d.value.values.ravel())) for d in at.dataframe]
    return "\n".join(map(str, partes))


def instruir_pela_tela(at: AppTest, numero: str) -> None:
    at.selectbox[0].set_value(numero)
    botao(at, "Instruir").click()
    at.run()
    assert not at.exception, at.exception


def so_mensagem_padrao(at: AppTest, rotulo: str, proibidos: list[str]) -> None:
    """Na falha: só a mensagem padrão; nada da instrução, da minuta, das consultas ou medidas."""
    tela = textos(at)
    assert [e.value for e in at.error] == [instrutor.MENSAGEM_PADRAO], [e.value for e in at.error]
    assert not at.metric, "métricas da instrução recusada na tela"
    assert not any("Minuta" in t.label for t in at.text_area), "minuta na tela"
    assert not any("Consultas feitas" in x.label for x in at.expander), "consultas na tela"
    assert "tokens" not in tela, "medidas técnicas na tela"
    for termo in proibidos:
        assert termo not in tela, (termo, tela)
    log(f"    {rotulo}: tela mostra apenas \"{at.error[0].value}\"")


def parte_a() -> None:
    at = AppTest.from_file(str(BASE / "app.py"), default_timeout=60)
    at.run()

    log("[A1] Processamento normal (resposta controlada): DIA-2026-0101")
    AGENTE.cena = "normal"
    instruir_pela_tela(at, "DIA-2026-0101")
    assert "Apto para autorização" in textos(at), textos(at)
    log(f"    métricas: {[(m.label, m.value) for m in at.metric]}")
    log(f"    status: {[s.label for s in at.status]}")
    log(f"    minuta editável presente: {any('Minuta' in t.label for t in at.text_area)}")

    log("[A1b] Minuta do modelo com o valor unitário como total: a tela mostra a do código")
    AGENTE.cena = "texto_errado"
    instruir_pela_tela(at, "DIA-2026-0101")
    minuta = next(t.value for t in at.text_area if "Minuta" in t.label)
    assert "valor total de R$ 280,00" not in textos(at) and "Valor total: R$ 980,00" in minuta, minuta
    log(f"    minuta exibida: {' / '.join(l for l in minuta.splitlines() if 'Valor' in l)}")
    AGENTE.cena = "normal"
    instruir_pela_tela(at, "DIA-2026-0101")

    log("[A1c] Alertas errados do modelo ficam fora da tela; os do código aparecem")
    AGENTE.cena = "alerta_errado"
    for numero in ("DIA-2026-0101", "DIA-2026-0108"):
        instruir_pela_tela(at, numero)
        tela = textos(at)
        assert "valor total correto" not in tela and "foi regularizada" not in tela, tela
        log(f"    {numero}: alertas do modelo fora da tela; alertas exibidos: "
            f"{[w.value for w in at.warning]}")
    assert "VENCIDA" in tela, "prestação do 0108 sem o fundamento do histórico"
    log("    DIA-2026-0108: prestação fundamentada no histórico (VENCIDA)")
    AGENTE.cena = "normal"
    for numero, esperados in (("DIA-2026-0104", ["dados pessoais"]),
                              ("DIA-2026-0106", ["autorização expressa e escrita"]),
                              ("DIA-2026-0107", ["ordem dirigida ao sistema",
                                                 "autorização verbal"])):
        instruir_pela_tela(at, numero)
        alertas = "\n".join(w.value for w in at.warning)
        assert all(e in alertas for e in esperados), (numero, alertas)
        log(f"    {numero}: alerta exigido presente ({', '.join(esperados)})")
    instruir_pela_tela(at, "DIA-2026-0101")

    log("[A2] Servidor diverge sem motivo, depois com motivo")
    at.radio[0].set_value("nao_recomendado")
    botao(at, "Registrar conferência").click()
    at.run()
    assert any("motivo" in e.value for e in at.error)
    log(f"    sem motivo: {[e.value for e in at.error]}")
    at.text_input[0].set_value("Teste do registro de divergência")
    botao(at, "Registrar conferência").click()
    at.run()
    assert at.success, "conferência não registrada"
    registro = json.loads(pathlib.Path(os.environ["CONFERENCIAS_ARQUIVO"])
                          .read_text("utf-8").splitlines()[-1])
    assert registro["diverge"] and registro["motivo"]
    log(f"    com motivo: {at.success[0].value}")
    log(f"    registro: sugestão {registro['sugestao_agente']} · decisão "
        f"{registro['decisao_servidor']} · diverge {registro['diverge']} · motivo "
        f"'{registro['motivo']}'")

    log("[A3] Diligência DIA-2026-0111 e complementação na mesma sessão")
    instruir_pela_tela(at, "DIA-2026-0111")
    assert "Diligência" in textos(at), textos(at)
    log(f"    recomendação no pedido: {[m.value for m in at.metric][:3]}")
    botao(at, "Enviar complementação").click()
    at.run()
    assert not at.exception and "Apto para autorização" in textos(at), textos(at)
    assert "após complementação" in textos(at)
    log(f"    recomendação após a complementação: {[m.value for m in at.metric][:3]}")

    log("[A3b] Complementação sem data vigente: diligência (pendente) ou análise manual (ambígua)")
    remarcada_cancelada = ("O retorno foi remarcado para 2026-11-20. Essa nova data foi cancelada "
                           "por causa de um compromisso anterior.")
    for texto_sem_data, estado in (
            ("O retorno não será em 2026-11-20. A data ainda será informada.", "pendente"),
            # Achados B1 da auditoria final, reproduzidos pela tela.
            ("O retorno está previsto para 2026-11-20. Essa previsão foi cancelada.", "pendente"),
            (remarcada_cancelada, "ambiguo")):
        AGENTE.cena = "normal"
        instruir_pela_tela(at, "DIA-2026-0111")
        assert [m.value for m in at.metric][0] == "Diligência"
        campo = next(t for t in at.text_area if t.label == "Texto da complementação")
        campo.set_value(texto_sem_data)
        botao(at, "Enviar complementação").click().run()
        so_mensagem_padrao(at, f"modelo tentou aptidão com «{texto_sem_data}»",
                           ["Apto para autorização", "980,00", "3,5", "retorno em 2026-11-20"])
        AGENTE.cena = "data_indefinida"
        instruir_pela_tela(at, "DIA-2026-0111")
        campo = next(t for t in at.text_area if t.label == "Texto da complementação")
        campo.set_value(texto_sem_data)
        botao(at, "Enviar complementação").click().run()
        if estado == "ambiguo":
            so_mensagem_padrao(at, "resposta de diligência com o retorno ambíguo",
                               ["Apto para autorização", "retorno em 2026-11-20"])
            log(f"    «{texto_sem_data}»: análise manual nas duas respostas")
            continue
        assert not at.exception and [m.value for m in at.metric][:3] == ["Diligência", "-", "-"]
        minuta = next(t.value for t in at.text_area if "Minuta" in t.label)
        # O campo de entrada ainda guarda o texto digitado; fora dele, a data não aparece.
        exibido = textos(at).replace(texto_sem_data, "")
        assert "retorno não informado" in minuta and "2026-11-20" not in exibido, exibido
        log(f"    «{texto_sem_data}»: diligência exibida sem a data, quantidade ou valor")

    log("[A3c] Confirmação explícita do campo, quando o texto livre não confirma a data")
    AGENTE.cena = "normal"
    for texto_livre, valor, espera_apto in (
            ("O retorno foi remarcado; confirmo a data no campo próprio.", "2026-11-20", True),
            (remarcada_cancelada, "2026-11-20", False)):
        instruir_pela_tela(at, "DIA-2026-0111")
        campo = next(t for t in at.text_area if t.label == "Texto da complementação")
        campo.set_value(texto_livre)
        next(x for x in at.selectbox if x.label == "Confirmar um campo (opcional)").set_value(
            "data_retorno")
        next(x for x in at.text_input if x.label == "Valor confirmado do campo").set_value(valor)
        botao(at, "Enviar complementação").click().run()
        if espera_apto:
            assert [m.value for m in at.metric][:3] == ["Apto para autorização", "3.5",
                                                         "R$ 980,00"], textos(at)
            log(f"    «{texto_livre}» + campo data de retorno = {valor}: apto, 3,5 diárias")
        else:
            so_mensagem_padrao(at, "campo explícito com a data que o texto deixou ambígua",
                               ["Apto para autorização"])
            log(f"    «{texto_livre[:48]}…» + campo = {valor}: continua ambíguo, análise manual")

    log("[A3d] Data remarcada e cancelada, com o Agno real e o modelo interceptado")
    import teste_bloqueio as tb
    AGENTE.cena = "interceptado"
    AGENTE._alvo()
    AGENTE.roteirizado.passos = tb.trilha("DIA-2026-0111") + [tb.final("DIA-2026-0111")]
    instruir_pela_tela(at, "DIA-2026-0111")
    assert [m.value for m in at.metric][0] == "Diligência"
    # A resposta do modelo vai sem textos de mérito, para que a busca no banco
    # distinga resultados das ferramentas do que o modelo escreveu.
    resposta = json.loads(tb.final("DIA-2026-0111", True)[1])
    for verificacao in resposta["verificacoes"]:
        verificacao["detalhe"] = ""
    resposta["minuta_despacho"] = ""
    AGENTE.roteirizado.passos = (tb.trilha("DIA-2026-0111", True)
                                 + [("final", json.dumps(resposta))])
    inicio = len(tb.EXECUTADAS)
    campo = next(t for t in at.text_area if t.label == "Texto da complementação")
    campo.set_value(remarcada_cancelada)
    botao(at, "Enviar complementação").click().run()
    assert tb.EXECUTADAS[inicio:] == ["consultar_servidor"], tb.EXECUTADAS[inicio:]
    so_mensagem_padrao(at, "Agno real tentou o mérito com a data cancelada",
                       ["Apto para autorização", "Valor unitário", "retorno em 2026-11-20"])
    assert not tb.com_merito(tb.conteudo_do_banco(PASTA / "interceptado.db"))
    log(f"    funções executadas: {tb.EXECUTADAS[inicio:]}; SQLite sem dado de mérito")
    AGENTE.cena = "normal"

    log("[A4] Falhas: só a mensagem padrão, nada da execução recusada")
    for cena, rotulo, proibidos in (
            ("recusa", "recusa da barreira (valor total plantado)", ["1.200", "plantado"]),
            ("erro", "status ERROR (erro da API como conteúdo)", ["Error code"]),
            ("sem_saida", "fluxo terminou sem RunOutput", []),
            ("sem_inicio", "sem evento inicial nem resposta, anterior válida no banco", []),
            ("anterior", "sem resposta, banco devolve a execução anterior", []),
            ("sem_id", "sem evento inicial, resposta concluída sem run_id", [])):
        # Antes de cada falha, uma instrução válida do mesmo pedido: a falha
        # não pode reaproveitá-la.
        AGENTE.cena = "normal"
        instruir_pela_tela(at, "DIA-2026-0101")
        assert "Apto para autorização" in textos(at), textos(at)
        AGENTE.cena = cena
        instruir_pela_tela(at, "DIA-2026-0101")
        so_mensagem_padrao(at, rotulo, proibidos + ["Consultando o cadastro", "204317 ·",
                                                    "Apto para autorização"])

    log("[A4b] DIA-2026-0112 com tentativa de cálculo, histórico e saldo após o DIVERGE "
        "(Agno real, modelo interceptado)")
    import teste_bloqueio as tb
    AGENTE.cena = "interceptado"
    AGENTE._alvo()
    AGENTE.roteirizado.passos = (tb.trilha("DIA-2026-0112")[:1] + tb.MERITO_207481
                                 + [tb.final("DIA-2026-0112")])
    inicio = len(tb.EXECUTADAS)
    instruir_pela_tela(at, "DIA-2026-0112")
    assert tb.EXECUTADAS[inicio:] == ["consultar_servidor"], tb.EXECUTADAS[inicio:]
    so_mensagem_padrao(at, "tentativa de mérito em diligência",
                       ["Valor unitário", "Saldo da unidade", "Mês da partida", "BLOQUEADA"])
    log(f"    funções executadas: {tb.EXECUTADAS[inicio:]}; o formulário não mostra dado de mérito")
    AGENTE.roteirizado.passos = tb.trilha("DIA-2026-0112")[:1] + [tb.final("DIA-2026-0112")]
    instruir_pela_tela(at, "DIA-2026-0112")
    assert "Diligência" in textos(at), textos(at)
    log(f"    diligência legítima pelo mesmo caminho: {[m.value for m in at.metric][:3]}")
    AGENTE.cena = "normal"

    log("[A5] Eliminação pela tela")
    montar_banco(BANCO_TESTE)
    entradas = {t.label: t for t in at.text_input}
    entradas["Matrícula do titular"].set_value("20")
    entradas["Nome completo do titular"].set_value("Fulano de Tal")
    botao(at, "Eliminar dados do titular").click()
    at.run()
    assert any("não executada" in e.value for e in at.error), textos(at)
    log(f"    matrícula parcial: {[e.value for e in at.error if 'não executada' in e.value][0]}")
    entradas = {t.label: t for t in at.text_input}
    entradas["Matrícula do titular"].set_value("207418")
    entradas["Nome completo do titular"].set_value("Carla Regina Souza")
    botao(at, "Eliminar dados do titular").click()
    at.run()
    assert any("nada restou" in s.value for s in at.success), textos(at)
    log(f"    Carla (207418, sessão sob 207481): {at.success[-1].value}")
    from eliminacao import ocorrencias
    controle, _ = ocorrencias(BANCO_TESTE, ["204317", "Ana Paula Figueiredo"])
    assert controle, "controle apagado"
    log(f"    controle Ana Paula continua no banco: {controle}")
    instrutor.apagar_banco(BANCO_TESTE)


def parte_b() -> None:
    if not os.environ.get("OPENAI_API_KEY"):
        log("[B] Modelo real: pulado (sem chave)")
        return
    AGENTE.cena = "real"
    at = AppTest.from_file(str(BASE / "app.py"), default_timeout=300)
    at.run()
    for numero, complementar in (("DIA-2026-0101", False), ("DIA-2026-0111", True)):
        log(f"[B] Modelo real: {numero}")
        instruir_pela_tela(at, numero)
        recomendacao = [m.value for m in at.metric][:1]
        entregue = bool(at.metric)
        if not entregue:
            so_mensagem_padrao(at, "instrução não entregue", [])
        log(f"    {'recomendação: ' + str(recomendacao) if entregue else 'mensagem padrão'} · "
            f"{[c.value for c in at.caption if 'tokens' in c.value]}")
        if complementar and entregue and "Diligência" in recomendacao:
            botao(at, "Enviar complementação").click()
            at.run()
            assert not at.exception
            log(f"    após a complementação: "
                f"{[m.value for m in at.metric][:3] or 'mensagem padrão'}")
    instrutor.apagar_banco(BANCO_TESTE)


def main() -> None:
    try:
        parte_a()
        parte_b()
    finally:
        shutil.rmtree(PASTA, ignore_errors=True)
    SAIDA.write_text("\n".join(linhas) + "\nTodas as verificações do formulário passaram.\n",
                     encoding="utf-8")
    print("Todas as verificações do formulário passaram.")


if __name__ == "__main__":
    main()
