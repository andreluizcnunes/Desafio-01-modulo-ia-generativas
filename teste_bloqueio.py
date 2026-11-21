"""Teste de integração da guarda das consultas de mérito, com o Agno real e sem chave.

O agente é o de `construir_agente`, com as ferramentas, o gancho de ferramenta,
o filtro de dados pessoais e o banco SQLite de verdade. Só as requisições ao
modelo são interceptadas localmente (`httpx.MockTransport`): um roteiro
devolve as chamadas de ferramenta e a resposta final, como a API devolveria,
nos dois modos que a aplicação usa (resposta direta e fluxo de eventos).

O que se confere, em cada cenário:
- o ponto de execução: cada função de negócio é contada quando realmente roda;
- as mensagens enviadas ao modelo, interceptadas: nenhum resultado de mérito
  depois de um cadastro DIVERGE ou de um pedido sem data de retorno;
- o banco temporário, tabela por tabela;
- o resultado que a tela recebe.

Cenários (art. 9º): DIA-2026-0112 inicial com tentativa de cálculo, histórico
e saldo depois do DIVERGE; DIA-2026-0111 inicial com tentativa de cálculo sem
retorno; as duas diligências legítimas e as complementações na mesma sessão
(0112 com a matrícula 207418, 0111 com o retorno informado); e o pedido
regular DIA-2026-0101 como controle, com as quatro ferramentas executando.

Execução: python teste_bloqueio.py
Saída: resultados/teste_bloqueio.txt
"""
import functools
import json
import pathlib
import re
import sqlite3
import tempfile
from collections.abc import Callable

import httpx
from agno.guardrails import PIIDetectionGuardrail
from agno.run.agent import RunInput

import instrutor
from ferramentas import FERRAMENTAS
from instrutor import apagar_banco, construir_agente, instruir, texto_do_pedido
from medir import CONFIGURACOES, RODADAS, classificar
from simulacao import consultas_corretas, esperado, instrucao_correta
from verificar_etapa3 import AGENCIA, CONTA, CPF

BASE = pathlib.Path(__file__).parent
SAIDA = BASE / "resultados" / "teste_bloqueio.txt"
PEDIDOS = {p["numero"]: p for p in json.loads((BASE / "dados" / "pedidos.json").read_text("utf-8"))}
COMPLEMENTOS = {c["numero"]: c for c in
                json.loads((BASE / "dados" / "complementacoes.json").read_text("utf-8"))}
# Trechos que só aparecem no resultado de uma consulta de mérito executada
# (a instrução de sistema, guardada no banco, cita os critérios sem números).
MARCAS_DE_MERITO = (r"Valor unitário: R\$", r"Quantidade: \d", r"Antecedência: \d",
                    r"Mês da partida \d", r"Prestação de contas(?: do|: nenhuma)",
                    r"Saldo da unidade [A-Z]+: R\$")


def com_merito(texto: str) -> list[str]:
    return [m for m in MARCAS_DE_MERITO if re.search(m, texto)]
MERITO = ("calcular_diarias", "consultar_historico_diarias", "consultar_saldo_diarias")
linhas: list[str] = []


def log(texto: str = "") -> None:
    print(texto)
    linhas.append(texto)


# ----------------------------------------------------------------------
# O modelo interceptado.
# ----------------------------------------------------------------------
class ModeloRoteirizado:
    """Responde às requisições do Agno com os passos do roteiro, na ordem."""

    def __init__(self):
        self.passos: list = []
        self.requisicoes: list[dict] = []

    def __call__(self, requisicao: httpx.Request) -> httpx.Response:
        corpo = json.loads(requisicao.content)
        self.requisicoes.append(corpo)
        tipo, conteudo = self.passos.pop(0)
        if tipo == "ferramentas":
            chamadas = [{"id": f"call_{len(self.requisicoes)}_{n}", "type": "function",
                         "function": {"name": nome, "arguments": json.dumps(args)}}
                        for n, (nome, args) in enumerate(conteudo)]
            mensagem, fim = {"role": "assistant", "content": None, "tool_calls": chamadas}, \
                "tool_calls"
        else:
            mensagem, fim = {"role": "assistant", "content": conteudo}, "stop"
        uso = {"prompt_tokens": 100, "completion_tokens": 10, "total_tokens": 110}
        if not corpo.get("stream"):
            return httpx.Response(200, json={
                "id": "chatcmpl-teste", "object": "chat.completion", "created": 0,
                "model": corpo["model"], "usage": uso,
                "choices": [{"index": 0, "message": mensagem, "finish_reason": fim}]})
        delta = dict(mensagem)
        if "tool_calls" in delta:
            delta["tool_calls"] = [dict(c, index=n) for n, c in enumerate(delta["tool_calls"])]
        pedacos = [{"choices": [{"index": 0, "delta": delta, "finish_reason": None}]},
                   {"choices": [{"index": 0, "delta": {}, "finish_reason": fim}]},
                   {"choices": [], "usage": uso}]
        sse = "".join("data: " + json.dumps(dict(p, id="chatcmpl-teste",
                                                 object="chat.completion.chunk", created=0,
                                                 model=corpo["model"])) + "\n\n"
                      for p in pedacos) + "data: [DONE]\n\n"
        return httpx.Response(200, content=sse.encode(),
                              headers={"content-type": "text/event-stream"})


EXECUTADAS: list[str] = []


def contar(funcao):
    """A função de negócio, contada no momento em que realmente executa."""
    @functools.wraps(funcao)
    def contada(*args, **kwargs):
        EXECUTADAS.append(funcao.__name__)
        return funcao(*args, **kwargs)
    return contada


def agente_interceptado(banco: pathlib.Path, modelo: Callable[[httpx.Request], httpx.Response], fabrica=None):
    agente = (fabrica or construir_agente)(memoria="historico", banco=banco)
    agente.model.api_key = "sk-teste-local"
    agente.model.http_client = httpx.Client(transport=httpx.MockTransport(modelo))
    agente.tools = [contar(f) for f in FERRAMENTAS]
    return agente


def _textos(valor) -> list[str]:
    """Todas as cadeias de um valor do banco, abrindo o JSON guardado dentro de JSON."""
    if isinstance(valor, (bytes, bytearray)):
        valor = valor.decode("utf-8", errors="ignore")
    if isinstance(valor, str):
        try:
            aberto = json.loads(valor)
        except (ValueError, TypeError):
            return [valor]
        return [valor] + (_textos(aberto) if aberto != valor else [])
    if isinstance(valor, dict):
        return [t for v in valor.values() for t in _textos(v)]
    if isinstance(valor, (list, tuple)):
        return [t for v in valor for t in _textos(v)]
    return [str(valor)]


def conteudo_do_banco(banco: pathlib.Path) -> str:
    """O texto de todas as tabelas, célula por célula, com o JSON aberto."""
    conexao = sqlite3.connect(banco)
    partes = []
    for (tabela,) in conexao.execute("SELECT name FROM sqlite_master WHERE type='table'"):
        for linha in conexao.execute(f"SELECT * FROM {tabela}").fetchall():
            partes += _textos(list(linha))
    conexao.close()
    return "\n".join(partes)


# ----------------------------------------------------------------------
# Roteiros.
# ----------------------------------------------------------------------
def final(numero: str, complementacao: bool = False) -> tuple:
    item = esperado(numero, complementacao)
    return ("final", instrucao_correta(item, consultas_corretas(item)).model_dump_json())


def trilha(numero: str, complementacao: bool = False) -> list:
    item = esperado(numero, complementacao)
    ordem = ("consultar_servidor", "calcular_diarias", "consultar_historico_diarias",
             "consultar_saldo_diarias")
    return [("ferramentas", [(f, item["trilha"][f])]) for f in ordem if f in item["trilha"]]


MERITO_207481 = [
    ("ferramentas", [("calcular_diarias", {"grupo": "B", "destino_uf": "MT",
                                           "data_pedido": "2026-10-09",
                                           "data_partida": "2026-11-24",
                                           "data_retorno": "2026-11-27"})]),
    ("ferramentas", [("consultar_historico_diarias", {"matricula": "207481",
                                                      "data_partida": "2026-11-24",
                                                      "quantidade_pedida": 3.5})]),
    ("ferramentas", [("consultar_saldo_diarias", {"unidade": "CFA", "valor": 980.0})]),
]
CALCULO_SEM_RETORNO = [
    ("ferramentas", [("calcular_diarias", {"grupo": "A", "destino_uf": "MT",
                                           "data_pedido": "2026-10-09",
                                           "data_partida": "2026-11-17",
                                           "data_retorno": None})]),
]


def rodar(rotulo, banco, modelo, agente, numero, passos, progresso, complemento=None):
    modelo.passos = list(passos)
    inicio_req, inicio_exec = len(modelo.requisicoes), len(EXECUTADAS)
    r = instruir(PEDIDOS[numero], agente, complemento=complemento,
                 ao_chamar_ferramenta=(lambda *_: None) if progresso else None)
    assert not modelo.passos, f"{rotulo}: roteiro não consumido ({len(modelo.passos)} passos)"
    executadas = EXECUTADAS[inicio_exec:]
    mensagens = [str(m.get("content")) for corpo in modelo.requisicoes[inicio_req:]
                 for m in corpo.get("messages", []) if m.get("role") == "tool"]
    return r, executadas, mensagens


def cenario_tentativa(numero: str, passos_indevidos: list, progresso: bool) -> None:
    modo = "fluxo de eventos" if progresso else "resposta direta"
    banco = pathlib.Path(tempfile.mkdtemp(prefix="bloqueio_")) / "agente.db"
    modelo = ModeloRoteirizado()
    agente = agente_interceptado(banco, modelo)
    passos = trilha(numero)[:1] + passos_indevidos + [final(numero)]
    r, executadas, mensagens = rodar(numero, banco, modelo, agente, numero, passos, progresso)
    tentadas = [nome for _, chamadas in passos_indevidos for nome, _ in chamadas]

    assert not [f for f in executadas if f in MERITO], (numero, executadas)
    assert executadas == ["consultar_servidor"], executadas
    assert r.consultas_bloqueadas == tentadas, r.consultas_bloqueadas
    vazou = [m for m in mensagens if com_merito(m)]
    assert not vazou, vazou
    # Cada requisição reenvia a conversa: a última traz todos os resultados.
    ultima = [str(m.get("content")) for m in modelo.requisicoes[-1]["messages"]
              if m.get("role") == "tool"]
    assert sum(instrutor.CONSULTA_BLOQUEADA in m for m in ultima) == len(tentadas), ultima
    no_banco = com_merito(conteudo_do_banco(banco))
    assert not no_banco, no_banco
    assert r.situacao == "recusada" and r.instrucao is not None, r.situacao
    assert any("bloqueada antes de executar" in m for m in r.motivo), r.motivo
    log(f"    {numero} ({modo}): tentou {', '.join(tentadas)}")
    log(f"        funções executadas: {executadas} · bloqueadas antes de executar: "
        f"{r.consultas_bloqueadas}")
    log(f"        mensagens ao modelo com dado de mérito: 0 · resposta da guarda: "
        f"{next(m for m in mensagens if instrutor.CONSULTA_BLOQUEADA in m)[:110]}...")
    log(f"        banco temporário com dado de mérito: nenhum · formulário: {r.situacao} "
        f"(mensagem padrão; tentativa registrada: {r.motivo[0][:70]}...)")
    apagar_banco(banco)


def cenario_diligencia_e_complemento(numero: str, progresso: bool) -> None:
    modo = "fluxo de eventos" if progresso else "resposta direta"
    banco = pathlib.Path(tempfile.mkdtemp(prefix="bloqueio_")) / "agente.db"
    modelo = ModeloRoteirizado()
    agente = agente_interceptado(banco, modelo)

    r, executadas, mensagens = rodar(numero, banco, modelo, agente, numero,
                                     trilha(numero) + [final(numero)], progresso)
    assert r.situacao == "entregue", r.motivo
    assert r.instrucao.recomendacao == "diligencia"
    assert r.instrucao.quantidade_diarias is None and r.instrucao.valor_total is None
    assert executadas == ["consultar_servidor"] and not r.consultas_bloqueadas, executadas
    log(f"    {numero} ({modo}): diligência entregue, quantidade e valor nulos; executou "
        f"{executadas}")

    c = COMPLEMENTOS[numero]
    r, executadas, mensagens = rodar(numero, banco, modelo, agente, numero,
                                     trilha(numero, True) + [final(numero, True)], progresso,
                                     complemento=c)
    assert r.situacao == "entregue", r.motivo
    assert r.instrucao.recomendacao == esperado(numero, True)["recomendacao"]
    assert executadas == ["consultar_servidor"] + list(MERITO), executadas
    assert not r.consultas_bloqueadas
    historico = next(x for x in r.consultas if x["ferramenta"] == "consultar_historico_diarias")
    calculo = next(x for x in r.consultas if x["ferramenta"] == "calcular_diarias")
    conexao = sqlite3.connect(banco)
    sessoes = conexao.execute("SELECT DISTINCT session_id FROM agno_sessions").fetchall()
    conexao.close()
    assert sessoes == [(numero,)], sessoes
    log(f"        complementação na mesma sessão ({sessoes[0][0]}): "
        f"{r.instrucao.recomendacao}; executou {executadas}")
    log(f"        histórico com a matrícula {historico['argumentos']['matricula']}; cálculo "
        f"com retorno {calculo['argumentos']['data_retorno']}")
    apagar_banco(banco)


def cenario_controle(progresso: bool) -> None:
    modo = "fluxo de eventos" if progresso else "resposta direta"
    banco = pathlib.Path(tempfile.mkdtemp(prefix="bloqueio_")) / "agente.db"
    modelo = ModeloRoteirizado()
    agente = agente_interceptado(banco, modelo)
    numero = "DIA-2026-0101"
    r, executadas, _ = rodar(numero, banco, modelo, agente, numero,
                             trilha(numero) + [final(numero)], progresso)
    assert r.situacao == "entregue" and r.instrucao.recomendacao == "apto_para_autorizacao", \
        r.motivo
    assert executadas == ["consultar_servidor"] + list(MERITO) and not r.consultas_bloqueadas
    # Controle das marcas: com o mérito executado, o banco tem os resultados.
    assert len(com_merito(conteudo_do_banco(banco))) == len(MARCAS_DE_MERITO), \
        com_merito(conteudo_do_banco(banco))
    log(f"    {numero} ({modo}): {r.instrucao.recomendacao}; as quatro funções executaram: "
        f"{executadas}; o banco tem as {len(MARCAS_DE_MERITO)} marcas de mérito (controle "
        f"da busca)")
    apagar_banco(banco)


def cenario_argumentos(progresso: bool, variacao: int) -> None:
    """Argumentos indevidos não executam mesmo com o pedido completo e cadastro válido."""
    numero = "DIA-2026-0101"
    passos_validos = trilha(numero)
    outro = PEDIDOS["DIA-2026-0108"]
    incorretos = (
        ({"matricula": outro["matricula"], "nome_informado": outro["nome"]},
         {"data_retorno": "2026-11-13"}, {"matricula": outro["matricula"]}, {"valor": 980.01}),
        ({"nome_informado": outro["nome"]}, {"destino_uf": "DF", "grupo": "A"},
         {"data_partida": PEDIDOS[numero]["data_pedido"], "quantidade_pedida": 1.0},
         {"unidade": "GAB"}),
    )[variacao]
    passos = []
    nomes = []
    for (tipo, chamadas), alteracoes in zip(passos_validos, incorretos):
        nome, argumentos = chamadas[0]
        nomes.append(nome)
        passos.extend([(tipo, [(nome, dict(argumentos, **alteracoes))]), (tipo, chamadas)])
    banco = pathlib.Path(tempfile.mkdtemp(prefix="argumentos_")) / "agente.db"
    modelo = ModeloRoteirizado()
    agente = agente_interceptado(banco, modelo)
    r, executadas, mensagens = rodar("argumentos fora do pedido", banco, modelo, agente,
                                    numero, passos + [final(numero)], progresso)
    assert r.situacao == "entregue", (r.situacao, r.motivo)
    assert executadas == nomes and r.consultas_bloqueadas == nomes, (executadas, r.consultas_bloqueadas)
    assert [c["ferramenta"] for c in r.consultas] == nomes
    assert any(instrutor.CONSULTA_BLOQUEADA in m for m in mensagens)
    dados_externos = (f"Matrícula {outro['matricula']}:", "Valor total: R$ 1.260,00", "980.01")
    # O registro pode conter argumentos tentados. A busca abaixo cobre trechos de resultado.
    assert all(dado not in "\n".join(mensagens) for dado in dados_externos)
    assert dados_externos[0] not in conteudo_do_banco(banco)
    log(f"    {'eventos' if progresso else 'direto'}, variante {variacao + 1}: "
        f"{len(nomes)} tentativas barradas e {len(executadas)} consultas válidas entregues.")
    apagar_banco(banco)


def cenario_complementacao_negada(progresso: bool) -> None:
    numero = "DIA-2026-0111"
    complemento = dict(COMPLEMENTOS[numero],
                       texto="O retorno não será em 2026-11-20. A data ainda será informada.")
    banco = pathlib.Path(tempfile.mkdtemp(prefix="complementacao_")) / "agente.db"
    modelo = ModeloRoteirizado()
    agente = agente_interceptado(banco, modelo)
    r, _, _ = rodar("diligência inicial", banco, modelo, agente, numero,
                    trilha(numero) + [final(numero)], progresso)
    assert r.situacao == "entregue" and r.instrucao.recomendacao == "diligencia"
    # O modelo tenta entregar aptidão sem redigir valores, para que a busca no
    # banco distinga resultados das ferramentas do texto que o modelo escreveu.
    resposta = json.loads(final(numero, True)[1])
    for verificacao in resposta["verificacoes"]:
        verificacao["detalhe"] = ""
    resposta["minuta_despacho"] = ""
    r, executadas, mensagens = rodar("complementação negada", banco, modelo, agente, numero,
                                    trilha(numero, True) + [("final", json.dumps(resposta))], progresso,
                                    complemento=complemento)
    assert r.situacao == "recusada" and executadas == ["consultar_servidor"], (r.motivo, executadas)
    assert r.consultas_bloqueadas == list(MERITO) and not any(com_merito(m) for m in mensagens)
    assert not com_merito(conteudo_do_banco(banco))
    r, executadas, _ = rodar("diligência mantida", banco, modelo, agente, numero,
                            trilha(numero) + [final(numero)], progresso, complemento=complemento)
    assert r.situacao == "entregue" and r.instrucao.recomendacao == "diligencia"
    assert executadas == ["consultar_servidor"] and r.instrucao.valor_total is None
    log(f"    {'eventos' if progresso else 'direto'}: data negada mantida pendente; "
        "tentativa de mérito barrada e diligência regular entregue.")
    apagar_banco(banco)


def cenario_isolamento() -> None:
    """Um pedido em diligência e um regular no mesmo agente: o estado não se mistura."""
    banco = pathlib.Path(tempfile.mkdtemp(prefix="bloqueio_")) / "agente.db"
    modelo = ModeloRoteirizado()
    agente = agente_interceptado(banco, modelo)
    r1, ex1, _ = rodar("0101", banco, modelo, agente, "DIA-2026-0101",
                       trilha("DIA-2026-0101") + [final("DIA-2026-0101")], True)
    r2, ex2, _ = rodar("0112", banco, modelo, agente, "DIA-2026-0112",
                       trilha("DIA-2026-0112")[:1] + MERITO_207481 + [final("DIA-2026-0112")],
                       True)
    assert r1.situacao == "entregue" and not [f for f in ex2 if f in MERITO], ex2
    assert not instrutor._EXECUCOES, instrutor._EXECUCOES
    log(f"    mesmo agente, 0101 e depois 0112: o cadastro conferido do 0101 não libera o "
        f"mérito do 0112 (executadas no 0112: {ex2}); estado das execuções vazio ao final")
    apagar_banco(banco)


def cenario_acervo() -> None:
    """Repete as rodadas contra o gabarito com HTTP interceptado e ferramentas reais."""
    log("\n[7] Cobertura local de 12 pedidos e duas complementações, sem uso do provedor")
    itens = [(numero, None) for numero in PEDIDOS] + list(COMPLEMENTOS.items())
    for rotulo, paralelas in CONFIGURACOES:
        for rodada in range(1, RODADAS + 1):
            with tempfile.TemporaryDirectory(prefix="acervo_") as pasta:
                banco = pathlib.Path(pasta) / "agente.db"
                modelo = ModeloRoteirizado()
                agente = agente_interceptado(
                    banco, modelo, lambda **kw: construir_agente(paralelas=paralelas, **kw))
                for numero, complemento in itens:
                    segundo_turno = complemento is not None
                    r, _, _ = rodar(rotulo, banco, modelo, agente, numero,
                                    trilha(numero, segundo_turno) + [final(numero, segundo_turno)],
                                    False, complemento=complemento)
                    classe, diferencas = classificar(r, esperado(numero, segundo_turno))
                    assert classe == "acerto" and not r.consultas_bloqueadas, (
                        rotulo, rodada, numero, classe, diferencas, r.motivo)
                log(f"    {rotulo}, rodada {rodada}: {len(itens)}/{len(itens)}.")
    log("    Respostas roteirizadas. Tokens, tempo e custo do provedor não foram medidos.")


def cenario_falhas_controladas() -> None:
    """Exercita as defesas das quatro falhas com respostas e erros controlados."""
    log("\n[8] Quatro falhas provocadas com HTTP local")
    with tempfile.TemporaryDirectory(prefix="falhas_") as pasta:
        base = pathlib.Path(pasta)
        banco = base / "ordem.db"
        modelo = ModeloRoteirizado()
        agente = agente_interceptado(banco, modelo)
        numero = "DIA-2026-0107"
        obedeceu = json.loads(final(numero)[1])
        obedeceu["recomendacao"] = "apto_para_autorizacao"
        r, _, _ = rodar("ordem embutida", banco, modelo, agente, numero,
                        trilha(numero) + [("final", json.dumps(obedeceu))], False)
        assert r.situacao == "recusada" and any("recomendação" in m for m in r.motivo)
        log("    1. Ordem embutida: a aptidão simulada foi recusada pela barreira.")

        def erro_api(_):
            return httpx.Response(400, json={"error": {"message": "Erro controlado da API",
                                                        "type": "invalid_request_error"}})

        agente = agente_interceptado(base / "erro.db", erro_api)
        r = instruir(PEDIDOS["DIA-2026-0101"], agente)
        assert r.situacao == "erro" and r.instrucao is None
        log("    2. HTTP 400: a resposta de erro ficou fora do contrato entregue.")

        numero = "DIA-2026-0104"
        entrada = RunInput(input_content=texto_do_pedido(PEDIDOS[numero]))
        PIIDetectionGuardrail(mask_pii=True).check(entrada)
        dados_pessoais = (CPF, CONTA, AGENCIA)
        assert all(d in entrada.input_content_string() for d in dados_pessoais)
        banco = base / "filtro.db"
        modelo = ModeloRoteirizado()
        agente = agente_interceptado(banco, modelo)
        r, _, _ = rodar("filtro configurado", banco, modelo, agente, numero,
                        trilha(numero) + [final(numero)], False)
        assert r.situacao == "entregue" and all(d not in conteudo_do_banco(banco) for d in dados_pessoais)
        assert all(d not in str(modelo.requisicoes) for d in dados_pessoais)
        log("    3. Padrões de fábrica deixam CPF, conta e agência no texto. O filtro do projeto "
            "os remove das requisições e do SQLite.")

        numero = "DIA-2026-0101"
        banco = base / "sem_ferramentas.db"
        modelo = ModeloRoteirizado()
        agente = agente_interceptado(banco, modelo)
        agente.tools = []
        r, executadas, _ = rodar("sem ferramentas", banco, modelo, agente, numero, [final(numero)], False)
        assert not executadas and r.situacao == "recusada"
        assert any("consulta obrigatória ausente" in m for m in r.motivo)
        log("    4. Resposta de mérito sem ferramentas: recusada por falta de consultas obrigatórias.")


def main() -> None:
    log("[1] Tentativas de consulta de mérito em pedido que exige diligência (art. 9º)")
    for progresso in (False, True):
        cenario_tentativa("DIA-2026-0112", MERITO_207481, progresso)
        cenario_tentativa("DIA-2026-0111", CALCULO_SEM_RETORNO, progresso)
    log("\n[2] Diligências legítimas e complementações na mesma sessão")
    for progresso in (False, True):
        cenario_diligencia_e_complemento("DIA-2026-0112", progresso)
        cenario_diligencia_e_complemento("DIA-2026-0111", progresso)
    log("\n[3] Controle: pedido regular com as quatro ferramentas")
    for progresso in (False, True):
        cenario_controle(progresso)
    log("\n[4] Agente compartilhado")
    cenario_isolamento()
    log("\n[5] Argumentos fora do pedido barrados antes de cada ferramenta")
    for progresso in (False, True):
        for variacao in (0, 1):
            cenario_argumentos(progresso, variacao)
    log("\n[6] Complementação negada pela entrada normal do agente")
    for progresso in (False, True):
        cenario_complementacao_negada(progresso)
    cenario_acervo()
    cenario_falhas_controladas()
    log("\nTodas as verificações da guarda das ferramentas passaram.")
    SAIDA.write_text("\n".join(linhas) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
