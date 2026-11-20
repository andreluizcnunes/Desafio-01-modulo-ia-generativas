"""Teste do formulário de conferência (Etapa 5), sem servidor e sem navegador.

Usa o AppTest do próprio Streamlit para executar app.py como o servidor o
usaria: escolhe o pedido, instrui, confere, registra a decisão, envia a
complementação na mesma sessão, confere a mensagem padrão no erro e aciona a
rotina de eliminação.

Execução: python teste_app.py
Saída: resultados/etapa5_formulario.txt e registros em resultados/conferencias.jsonl
"""
import pathlib

from streamlit.testing.v1 import AppTest

from instrutor import BANCO_PADRAO, MENSAGEM_PADRAO, Resultado, apagar_banco

BASE = pathlib.Path(__file__).parent
SAIDA = BASE / "resultados" / "etapa5_formulario.txt"
linhas: list[str] = []


def log(texto: str) -> None:
    print(texto)
    linhas.append(texto)


def botao(at: AppTest, rotulo: str):
    return next(b for b in at.button if b.label == rotulo)


def textos(at: AppTest) -> str:
    partes = [m.value for m in at.markdown] + [m.label + " " + str(m.value) for m in at.metric]
    partes += [e.value for e in at.error] + [w.value for w in at.warning]
    partes += [s.value for s in at.success] + [i.value for i in at.info]
    return "\n".join(map(str, partes))


def main() -> None:
    apagar_banco(BANCO_PADRAO)
    at = AppTest.from_file(str(BASE / "app.py"), default_timeout=240)
    at.run()

    log("[1] Pedido regular DIA-2026-0101")
    at.selectbox[0].set_value("DIA-2026-0101")
    botao(at, "Instruir").click()
    at.run()
    tela = textos(at)
    assert "Apto para autorização" in tela, tela
    log(f"    métricas: {[(m.label, m.value) for m in at.metric]}")
    log(f"    status: {[s.label for s in at.status]}")
    log(f"    minuta editável presente: {any('Minuta' in t.label for t in at.text_area)}")

    log("[2] Servidor diverge sem motivo, depois com motivo")
    at.radio[0].set_value("nao_recomendado")
    botao(at, "Registrar conferência").click()
    at.run()
    assert any("motivo" in e.value for e in at.error)
    log(f"    sem motivo: {[e.value for e in at.error]}")
    at.text_input[0].set_value("Teste do registro de divergência")
    botao(at, "Registrar conferência").click()
    at.run()
    assert at.success, "conferência não registrada"
    log(f"    com motivo: {at.success[0].value}")

    log("[3] Diligência DIA-2026-0111 e complementação na mesma sessão")
    at.selectbox[0].set_value("DIA-2026-0111")
    botao(at, "Instruir").click()
    at.run()
    assert "Diligência" in textos(at), textos(at)
    log(f"    recomendação no pedido: {[m.value for m in at.metric][:3]}")
    botao(at, "Enviar complementação").click()
    at.run()
    assert "Apto para autorização" in textos(at), textos(at)
    log(f"    recomendação após a complementação: {[m.value for m in at.metric][:3]}")

    log("[4] Execução com erro: mensagem padrão, nada do conteúdo")
    at.session_state["atual"] = {
        "pedido": {"numero": "DIA-2026-0105"}, "complemento": None,
        "resultado": Resultado("recusada", motivo=["simulação de recusa da barreira"]),
    }
    at.run()
    assert [e.value for e in at.error] == [MENSAGEM_PADRAO], [e.value for e in at.error]
    assert "simulação" not in textos(at)
    log(f"    tela mostra apenas: {at.error[0].value}")

    log("[5] Eliminação dos dados de Beatriz (206689)")
    entradas = {t.label: t for t in at.text_input}
    entradas["Matrícula do titular"].set_value("206689")
    entradas["Nome completo do titular"].set_value("Beatriz Moraes Cunha")
    botao(at, "Eliminar dados do titular").click()
    at.run()
    assert any("nada restou" in s.value for s in at.success), textos(at)
    log(f"    {at.success[-1].value}")

    SAIDA.write_text("\n".join(linhas) + "\nTodas as verificações do formulário passaram.\n",
                     encoding="utf-8")
    apagar_banco(BANCO_PADRAO)
    print("Todas as verificações do formulário passaram.")


if __name__ == "__main__":
    main()
