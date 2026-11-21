"""Respostas controladas do agente, para testar sem modelo e sem chave.

As consultas são feitas pelas ferramentas reais; só a resposta do modelo é
simulada. Assim, a barreira, a medição e o formulário são testados contra
instruções escritas de propósito, certas e erradas, como o dossiê adulterado
da Aula 04, Seção 7.3, e contra falhas do fluxo que o modelo real não produz
quando se quer (Aula 06, 5.3).

Usado por teste_barreira.py e teste_app.py. A aplicação não importa este
módulo.
"""
import json
import pathlib
import uuid

from agno.models.response import ToolExecution
from agno.run.agent import RunOutput, RunStartedEvent, ToolCallStartedEvent
from agno.run.base import RunStatus

from ferramentas import FERRAMENTAS, _reais
from instrutor import Instrucao, Verificacao

BASE = pathlib.Path(__file__).parent
FUNCOES = {f.__name__: f for f in FERRAMENTAS}
GAB = json.loads((BASE / "gabarito.json").read_text(encoding="utf-8"))
ORDEM = ("consultar_servidor", "calcular_diarias", "consultar_historico_diarias",
         "consultar_saldo_diarias")
FONTE_DO_CRITERIO = {"cadastro": "consultar_servidor", "antecedencia": "calcular_diarias",
                     "prestacao_contas": "consultar_historico_diarias",
                     "limite_mensal": "consultar_historico_diarias",
                     "saldo_orcamentario": "consultar_saldo_diarias"}


def esperado(numero: str, complementacao: bool = False) -> dict:
    lista = GAB["complementacoes"] if complementacao else GAB["pedidos"]
    return next(g for g in lista if g["numero_pedido"] == numero)


def consulta(ferramenta: str, **argumentos) -> dict:
    """Uma consulta feita pela ferramenta real."""
    return {"ferramenta": ferramenta, "argumentos": argumentos,
            "resultado": FUNCOES[ferramenta](**argumentos)}


def consultas_corretas(item: dict) -> list[dict]:
    """A trilha esperada, executada pelas ferramentas reais, na ordem."""
    return [consulta(f, **item["trilha"][f]) for f in ORDEM if f in item["trilha"]]


def instrucao_correta(item: dict, consultas: list[dict]) -> Instrucao:
    """A instrução que um modelo correto devolveria, com os textos tirados das consultas."""
    resultados = {c["ferramenta"]: c["resultado"] for c in consultas}
    verificacoes = []
    for criterio, situacao in item["situacoes"].items():
        if criterio == "dados_completos":
            detalhe = ("Pedido com todos os dados e datas." if situacao == "atende"
                       else "Falta a data de retorno (art. 9º).")
        else:
            detalhe = resultados.get(FONTE_DO_CRITERIO[criterio], "Não consultado.")
        verificacoes.append(Verificacao(criterio=criterio, situacao=situacao, detalhe=detalhe))
    numero, matricula = item["numero_pedido"], item["matricula"]
    if item["recomendacao"] == "diligencia":
        minuta = (f"Ao ordenador de despesa. Pedido {numero}, matrícula {matricula}: "
                  f"sugere-se diligência ao solicitante para correção (art. 9º).")
    else:
        minuta = (f"Ao ordenador de despesa. Pedido {numero}, matrícula {matricula}: "
                  f"{item['quantidade_diarias']} diária(s), valor total "
                  f"{_reais(item['valor_total'])}. Encaminhamento sugerido: "
                  f"{item['recomendacao'].replace('_', ' ')}.")
        if item["exige_autorizacao_superior"]:
            minuta += (" Pedido urgente (art. 5º, § 1º): a autorização fica condicionada à "
                       "autorização expressa e escrita do Secretário Adjunto, registrada no "
                       "processo (art. 5º, § 2º).")
    return Instrucao(numero_pedido=numero, matricula=matricula,
                     quantidade_diarias=item["quantidade_diarias"],
                     valor_total=item["valor_total"], verificacoes=verificacoes,
                     recomendacao=item["recomendacao"],
                     exige_autorizacao_superior=item["exige_autorizacao_superior"],
                     pendencias=[], alertas=[], minuta_despacho=minuta)


def alterar(instrucao: Instrucao, situacoes: dict | None = None, **campos) -> Instrucao:
    """Cópia da instrução com campos e situações trocados."""
    nova = instrucao.model_copy(deep=True, update=campos)
    for v in nova.verificacoes:
        if situacoes and v.criterio in situacoes:
            v.situacao = situacoes[v.criterio]
    return nova


class AgenteSimulado:
    """Imita o `Agent` do Agno no que `instruir` usa: `run` e `get_last_run_output`.

    `roteiro(session_id, entrada)` devolve a cena: um dicionário com `modo`
    ("normal", "erro", "sem_saida", "outra_execucao", "excecao", "sem_inicio" ou
    "anterior"), e, no modo normal, `instrucao` e `consultas`.

    - "sem_saida": o fluxo anuncia o início e termina sem resposta, e o banco não
      tem execução.
    - "sem_inicio": o fluxo termina sem evento inicial e sem resposta; o banco
      guarda a execução anterior da mesma sessão, válida e tipada.
    - "anterior": o fluxo anuncia o início e termina sem resposta; o banco guarda
      a execução anterior da mesma sessão, com outro identificador.
    """

    def __init__(self, roteiro):
        self.roteiro = roteiro
        self.ultima = None

    def _saida(self, cena: dict, session_id: str, user_id: str) -> RunOutput:
        status = RunStatus.error if cena["modo"] == "erro" else RunStatus.completed
        conteudo = ("Error code: 400 - simulação de erro da API" if cena["modo"] == "erro"
                    else cena.get("instrucao"))
        ferramentas = [ToolExecution(tool_name=c["ferramenta"], tool_args=c["argumentos"],
                                     result=c["resultado"]) for c in cena.get("consultas", [])]
        return RunOutput(run_id=str(uuid.uuid4()), session_id=session_id, user_id=user_id,
                         content=conteudo, status=status, tools=ferramentas, messages=[])

    def run(self, entrada, session_id=None, user_id=None, stream=False, **_):
        cena = self.roteiro(session_id, entrada)
        if cena["modo"] == "excecao":
            raise RuntimeError("simulação de falha de conexão")
        saida = self._saida(cena, session_id, user_id)
        if cena["modo"] == "sem_saida":
            self.ultima = None
        elif cena["modo"] not in ("sem_inicio", "anterior"):
            self.ultima = saida  # nos dois outros, o banco fica com a execução anterior
        if not stream:
            if cena["modo"] == "outra_execucao":
                saida.session_id = "DIA-2026-0000"
            return None if cena["modo"] in ("sem_saida", "sem_inicio", "anterior") else saida

        def eventos():
            if cena["modo"] != "sem_inicio":
                yield RunStartedEvent(run_id=saida.run_id, session_id=session_id)
            for t in saida.tools or []:
                yield ToolCallStartedEvent(run_id=saida.run_id, session_id=session_id, tool=t)
            if cena["modo"] in ("sem_saida", "sem_inicio", "anterior"):
                return
            if cena["modo"] == "outra_execucao":
                saida.run_id = str(uuid.uuid4())
            yield saida
        return eventos()

    def get_last_run_output(self, session_id=None):
        if self.ultima is not None and self.ultima.session_id == session_id:
            return self.ultima
        return None
