"""Formulário de conferência da instrução de pedidos de diárias (Etapa 5).

Padrão de formulário da Aula 06, Seção 6: um envio, uma devolução, o resultado
em campos. A aplicação não conversa com o Agno: importa `instruir` do
instrutor.py e desenha o objeto `Instrucao` campo a campo (Aula 06, 6.1).

- Progresso visível: cada consulta é anunciada quando começa (Aula 06, 6.3). Só
  o NOME da consulta aparece durante a execução; os argumentos aparecem depois
  que a barreira libera a instrução, porque nada do conteúdo recusado pode
  chegar ao servidor.
- A minuta fica em campo editável, e o servidor registra o encaminhamento que
  decidiu ao lado do sugerido, com o motivo quando divergem: esse registro é o
  lugar físico da conferência humana (Aula 01, 5; Aula 05, 5; Aula 06, 6.2) e
  fica em resultados/conferencias.jsonl, para medir com que frequência o
  servidor discorda do agente.
- Na diligência, a complementação é enviada na mesma sessão do pedido.
- Em área separada, a rotina de eliminação e o que restou no banco.
- Falha da execução (inclusive fluxo sem resposta) ou recusa da barreira:
  mensagem padrão e devolução à análise manual (Aula 06, 5.3). O progresso, a
  instrução, a minuta, as consultas e as medidas da execução recusada não
  aparecem.
- Eliminação: a identidade é validada antes (matrícula de seis algarismos e
  nome do cadastro), e só o banco de trabalho do agente é tocado.

Execução: streamlit run app.py
"""
import json
import os
import pathlib
from datetime import datetime

import streamlit as st

from eliminacao import eliminar_titular, validar_titular
from instrutor import BANCO_PADRAO, MENSAGEM_PADRAO, Resultado, construir_agente, instruir

BASE = pathlib.Path(__file__).parent
PEDIDOS = json.loads((BASE / "dados" / "pedidos.json").read_text(encoding="utf-8"))
COMPLEMENTOS = {c["numero"]: c for c in
                json.loads((BASE / "dados" / "complementacoes.json").read_text(encoding="utf-8"))}
# Onde as conferências são registradas; configurável para que os testes não
# misturem registros simulados aos da operação.
REGISTRO = pathlib.Path(os.environ.get("CONFERENCIAS_ARQUIVO",
                                       BASE / "resultados" / "conferencias.jsonl"))

ROTULOS = {
    "consultar_servidor": "Consultando o cadastro funcional",
    "calcular_diarias": "Calculando quantidade, valor e antecedência",
    "consultar_historico_diarias": "Consultando o histórico do mês e as prestações de contas",
    "consultar_saldo_diarias": "Consultando o saldo da unidade",
}
RECOMENDACOES = {
    "apto_para_autorizacao": "Apto para autorização",
    "nao_recomendado": "Não recomendado",
    "diligencia": "Diligência",
}
SITUACOES = {"atende": "✅ atende", "nao_atende": "❌ não atende", "nao_verificado": "➖ não verificado"}

st.set_page_config(page_title="Instrução de diárias · SEMA-MT", page_icon="📋", layout="wide")


@st.cache_resource
def agente_em_cache():
    """Um único agente para todos os pedidos.

    Ele tem histórico, mas não mistura pedidos: `session_id` (número do pedido)
    e `user_id` (matrícula) são informados em cada execução, e o histórico fica
    separado por sessão (Aula 06, 6.5; Aula 07, 2).
    """
    return construir_agente(memoria="historico", banco=BANCO_PADRAO)


def executar(pedido: dict, complemento: dict | None) -> None:
    rotulo = "Aplicando a complementação" if complemento else "Instruindo o pedido"
    with st.status(f"{rotulo} {pedido['numero']}", expanded=True) as status:
        # O progresso fica num espaço próprio, apagado se a instrução não for
        # entregue: da execução recusada, nada além da mensagem padrão fica na tela.
        progresso, etapas = st.empty(), []

        def anunciar(nome, _args):
            etapas.append(f"- {ROTULOS.get(nome, nome)}")
            progresso.markdown("\n".join(etapas))

        try:
            resultado = instruir(pedido, agente_em_cache(), complemento=complemento,
                                 ao_chamar_ferramenta=anunciar)
        except Exception as erro:  # nenhuma falha pode derrubar a tela
            resultado = Resultado("erro", motivo=[f"{type(erro).__name__}: {erro}"])
        if resultado.situacao == "entregue":
            status.update(label=f"Instrução concluída em {resultado.medidas['segundos']} s",
                          state="complete")
        else:
            progresso.empty()
            status.update(label="Instrução não concluída", state="error", expanded=False)
    st.session_state["atual"] = {"pedido": pedido, "complemento": complemento,
                                 "resultado": resultado}


def registrar_conferencia(pedido, complemento, instrucao, decisao, motivo, minuta, medidas):
    registro = {
        "data_hora": datetime.now().isoformat(timespec="seconds"),
        "numero_pedido": pedido["numero"],
        "turno": "complementacao" if complemento else "pedido",
        "sugestao_agente": instrucao.recomendacao,
        "decisao_servidor": decisao,
        "diverge": decisao != instrucao.recomendacao,
        "motivo": motivo,
        "minuta_editada": minuta.strip() != instrucao.minuta_despacho.strip(),
        "minuta_final": minuta,
        "custo_usd": round(medidas.get("custo", 0), 6),
    }
    REGISTRO.parent.mkdir(exist_ok=True)
    with REGISTRO.open("a", encoding="utf-8") as arquivo:
        arquivo.write(json.dumps(registro, ensure_ascii=False) + "\n")


st.title("Instrução de pedidos de diárias")
st.caption("SEMA-MT · Coordenadoria de Diárias e Passagens · IN SEMA nº 07/2026 (hipotética). "
           "A instrução é uma sugestão para conferência: a decisão é do ordenador de despesa (art. 10).")

aba_instrucao, aba_eliminacao = st.tabs(["Instrução e conferência", "Eliminação de dados (LGPD)"])

with aba_instrucao:
    with st.form("formulario_pedido"):
        coluna_pedido, coluna_botao = st.columns([3, 1])
        with coluna_pedido:
            numero = st.selectbox(
                "Pedido protocolado", [p["numero"] for p in PEDIDOS],
                format_func=lambda n: next(f"{p['numero']} · {p['nome']} · "
                                           f"{p['destino_municipio']}/{p['destino_uf']}"
                                           for p in PEDIDOS if p["numero"] == n))
        with coluna_botao:
            st.markdown("&nbsp;", unsafe_allow_html=True)
            enviado = st.form_submit_button("Instruir", type="primary", width="stretch")
    pedido_escolhido = next(p for p in PEDIDOS if p["numero"] == numero)
    with st.expander("Pedido como foi protocolado"):
        st.json(pedido_escolhido)

    if enviado:
        executar(pedido_escolhido, None)

    atual = st.session_state.get("atual")
    if atual:
        pedido, complemento, resultado = atual["pedido"], atual["complemento"], atual["resultado"]
        if resultado.situacao != "entregue":
            # Nada do conteúdo recusado aparece ao servidor (enunciado, Etapa 5).
            st.error(MENSAGEM_PADRAO)
        else:
            i = resultado.instrucao
            st.subheader(f"{i.numero_pedido} · matrícula {i.matricula}"
                         + (" · após complementação" if complemento else ""))
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Recomendação do agente", RECOMENDACOES[i.recomendacao])
            c2.metric("Diárias", "-" if i.quantidade_diarias is None else f"{i.quantidade_diarias}")
            c3.metric("Valor total", "-" if i.valor_total is None else
                      "R$ " + f"{i.valor_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            c4.metric("Autorização superior escrita", "exigida" if i.exige_autorizacao_superior
                      else "não exigida")

            st.markdown("**Verificações exigidas pela norma**")
            st.dataframe([{"Critério": v.criterio, "Situação": SITUACOES[v.situacao],
                           "Fundamento": v.detalhe} for v in i.verificacoes],
                         hide_index=True, width="stretch")
            if i.alertas:
                st.warning("**Alertas para o conferente**\n\n" + "\n".join(f"- {a}" for a in i.alertas))
            if i.pendencias:
                st.info("**Pendências do solicitante**\n\n" + "\n".join(f"- {p}" for p in i.pendencias))
            with st.expander(f"Consultas feitas pelo agente ({len(resultado.consultas)})"):
                st.dataframe([{"Ferramenta": c["ferramenta"], "Argumentos": json.dumps(
                    c["argumentos"], ensure_ascii=False), "Resultado": c["resultado"]}
                    for c in resultado.consultas], hide_index=True, width="stretch")

            # A conferência humana: minuta editável e decisão registrada.
            st.markdown("**Conferência do servidor**")
            with st.form(f"conferencia_{i.numero_pedido}_{'c' if complemento else 'p'}"):
                minuta = st.text_area("Minuta do despacho (editável)", value=i.minuta_despacho,
                                      height=200)
                opcoes = list(RECOMENDACOES)
                decisao = st.radio("Encaminhamento decidido pelo servidor", opcoes,
                                   index=opcoes.index(i.recomendacao),
                                   format_func=RECOMENDACOES.get, horizontal=True)
                motivo = st.text_input("Motivo (obrigatório quando diverge do agente)")
                registrar = st.form_submit_button("Registrar conferência")
            if registrar:
                if decisao != i.recomendacao and not motivo.strip():
                    st.error("Informe o motivo da divergência antes de registrar.")
                else:
                    registrar_conferencia(pedido, complemento, i, decisao, motivo, minuta,
                                          resultado.medidas)
                    st.success(f"Conferência registrada: agente sugeriu "
                               f"'{RECOMENDACOES[i.recomendacao]}', servidor decidiu "
                               f"'{RECOMENDACOES[decisao]}'.")
                    st.download_button("Baixar a minuta conferida", minuta,
                                       file_name=f"despacho-{i.numero_pedido}.txt")

            if i.recomendacao == "diligencia":
                st.markdown("**Complementação do solicitante** (enviada na mesma sessão do pedido)")
                with st.form(f"complementacao_{i.numero_pedido}"):
                    sugerido = COMPLEMENTOS.get(i.numero_pedido, {})
                    texto = st.text_area("Texto da complementação", value=sugerido.get("texto", ""))
                    data = st.text_input("Data de recebimento (AAAA-MM-DD)",
                                         value=sugerido.get("data", ""))
                    enviar = st.form_submit_button("Enviar complementação", type="primary")
                if enviar and texto.strip():
                    executar(pedido, {"numero": pedido["numero"], "data": data, "texto": texto})
                    st.rerun()

        m = resultado.medidas
        if resultado.situacao == "entregue" and m.get("chamadas") is not None:
            st.caption(f"{m.get('chamadas', 0)} chamadas ao modelo · "
                       f"{len(m.get('ferramentas', []))} consultas · "
                       f"{m.get('tokens_entrada', 0)} tokens de entrada · "
                       f"{m.get('tokens_saida', 0)} de saída · "
                       f"US$ {m.get('custo', 0):.5f} · {m.get('segundos', 0)} s")

with aba_eliminacao:
    st.markdown("A rotina apaga as sessões, as execuções e as memórias do titular no banco do "
                "agente e confere o banco tabela por tabela, procurando a matrícula e o nome. "
                "Ela alcança **somente o banco do agente**, que é cópia de trabalho: o processo "
                "de diárias é registro de despesa pública e não é tocado.")
    with st.form("formulario_eliminacao"):
        col_m, col_n = st.columns(2)
        matricula_titular = col_m.text_input("Matrícula do titular", placeholder="207418")
        nome_titular = col_n.text_input("Nome completo do titular", placeholder="Carla Regina Souza")
        eliminar = st.form_submit_button("Eliminar dados do titular", type="primary")
    if eliminar:
        problemas = validar_titular(matricula_titular, nome_titular)
        if problemas:
            # Identidade não confere: nada é apagado (matrícula parcial, nome de outra pessoa).
            st.error("Eliminação não executada: " + "; ".join(problemas) + ".")
        elif not BANCO_PADRAO.exists():
            st.info("O banco do agente ainda não existe: não há dados a eliminar.")
        else:
            r = eliminar_titular(BANCO_PADRAO, matricula_titular, nome_titular)
            if r["recusada"]:
                st.error("Eliminação não executada: " + "; ".join(r["recusada"]) + ".")
            else:
                st.write(f"**Antes:** {r['antes'] or 'o titular não aparece em nenhuma tabela'}")
                st.write(f"**Sessões apagadas:** {r['etapa1_sessoes_apagadas']}")
                st.write(f"**Memórias apagadas:** {len(r['etapa2_memorias_apagadas'])}")
                if r["falhas_de_verificacao"]:
                    st.error("Falha de verificação: tabelas que não puderam ser conferidas: "
                             + "; ".join(r["falhas_de_verificacao"]))
                if r["nada_restou"]:
                    st.success("Conferência tabela por tabela: nada restou do titular no banco "
                               "do agente.")
                elif r["depois"]:
                    st.error(f"Ainda restam registros: {r['depois']}")
    if BANCO_PADRAO.exists():
        st.caption("O que há no banco agora (registros por tabela):")
        import sqlite3
        conexao = sqlite3.connect(BANCO_PADRAO)
        st.dataframe([{"Tabela": t, "Registros": conexao.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]}
                      for (t,) in conexao.execute("SELECT name FROM sqlite_master WHERE type='table'")],
                     hide_index=True)
        conexao.close()
