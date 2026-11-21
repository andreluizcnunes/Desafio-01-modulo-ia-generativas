"""Contrato de confirmação dos campos da complementação, sem modelo e sem chave.

Regra geral (barreira.ler_complementacao): nenhuma consulta de mérito executa
com data cancelada, negada, indefinida ou ambígua. Só um campo CONFIRMADO
alimenta o pedido vigente, e a guarda das ferramentas confere os argumentos
contra esse pedido vigente.

O teste tem quatro partes:
1. Casos nomeados, por categoria, com o estado e o valor esperados.
2. Regra geral por combinação: milhares de complementações geradas (forma da
   atribuição × forma da referência × predicado × complemento da frase),
   inclusive com predicados fora do vocabulário do detector. Nenhuma termina
   com a data confirmada, e a guarda barra `calcular_diarias` com essa data em
   todas, sem executar a função.
3. Controles: cancelamento de outro evento não invalida o retorno; substituição
   legítima confirma só a nova data, e a guarda aceita a nova e barra a antiga.
4. Confirmação explícita do campo, para o que o texto livre não resolve.

Execução: python teste_complementacao.py
Saída: resultados/teste_complementacao.txt
"""
import itertools
import json
import pathlib
import uuid
from types import SimpleNamespace

from barreira import AMBIGUO, CONFIRMADO, PENDENTE, CONSULTA_BLOQUEADA, ler_complementacao, pedido_vigente
import ferramentas
from instrutor import _encerrar_execucao, _registrar_execucao, guarda_de_merito

BASE = pathlib.Path(__file__).parent
SAIDA = BASE / "resultados" / "teste_complementacao.txt"
PEDIDOS = {p["numero"]: p for p in json.loads((BASE / "dados" / "pedidos.json").read_text("utf-8"))}
COMPLEMENTOS = {c["numero"]: c for c in
                json.loads((BASE / "dados" / "complementacoes.json").read_text("utf-8"))}
P111, C111 = PEDIDOS["DIA-2026-0111"], COMPLEMENTOS["DIA-2026-0111"]
P112, C112 = PEDIDOS["DIA-2026-0112"], COMPLEMENTOS["DIA-2026-0112"]
linhas: list[str] = []


def log(texto: str = "") -> None:
    print(texto)
    linhas.append(texto)


def estado_do_retorno(texto: str, campos: dict | None = None) -> tuple[str | None, str | None, list]:
    leitura, _ = ler_complementacao(texto, P111, campos)
    vigente, problemas = pedido_vigente(P111, dict(C111, texto=texto, campos=campos))
    lido = leitura.get("data_retorno", {})
    assert vigente["data_retorno"] == (lido.get("valor") if lido.get("estado") == CONFIRMADO else None)
    return lido.get("estado"), vigente["data_retorno"], problemas


def guarda_calcula(texto: str, retorno: str, campos: dict | None = None) -> bool:
    """A guarda deixaria `calcular_diarias` executar com este retorno?"""
    execucao = str(uuid.uuid4())
    contexto = SimpleNamespace(run_id=execucao)
    executou = []

    def calcular(**argumentos):
        executou.append(argumentos)
        return ferramentas.calcular_diarias(**argumentos)

    _registrar_execucao(execucao, P111, dict(C111, texto=texto, campos=campos))
    try:
        guarda_de_merito("consultar_servidor", ferramentas.consultar_servidor,
                         {"matricula": P111["matricula"], "nome_informado": P111["nome"]}, contexto)
        resposta = guarda_de_merito(
            "calcular_diarias", calcular,
            {"grupo": "B", "destino_uf": P111["destino_uf"], "data_pedido": P111["data_pedido"],
             "data_partida": P111["data_partida"], "data_retorno": retorno}, contexto)
    finally:
        _encerrar_execucao(execucao)
    barrada = str(resposta).startswith(CONSULTA_BLOQUEADA)
    assert barrada != bool(executou), (texto, resposta)
    return bool(executou)


# ----------------------------------------------------------------------
# 1. Casos nomeados.
# ----------------------------------------------------------------------
D, N = "2026-11-20", "2026-11-22"
CASOS = {
    "Complementação oficial": [
        (C111["texto"], CONFIRMADO, D),
    ],
    "Data afirmada e depois cancelada": [
        (f"O retorno está previsto para {D}. Essa previsão foi cancelada.", PENDENTE, None),
        (f"Retorno: {D}. Desconsiderem essa data.", PENDENTE, None),
        (f"O retorno está previsto para {D}, mas foi cancelado.", PENDENTE, None),
        (f"O retorno está previsto para {D}. Cancelado.", PENDENTE, None),
        (f"O retorno está previsto para {D}. A viagem foi cancelada.", PENDENTE, None),
    ],
    "Data remarcada e depois cancelada": [
        (f"O retorno foi remarcado para {D}. Essa nova data foi cancelada por causa de um "
         f"compromisso anterior.", AMBIGUO, None),
        (f"O retorno foi remarcado para {D}. Essa nova data foi cancelada.", AMBIGUO, None),
        (f"A volta foi alterada para {D}. Ela foi cancelada.", AMBIGUO, None),
        (f"O retorno foi remarcado para {D}. O retorno em {D} foi cancelado.", PENDENTE, None),
        (f"O retorno foi remarcado para {D}. A data {D} foi cancelada.", PENDENTE, None),
    ],
    "Cancelamento por referência indireta": [
        (f"O retorno está previsto para {D}. Ela foi cancelada.", PENDENTE, None),
        (f"O retorno está previsto para {D}. Isso não vale mais.", PENDENTE, None),
        (f"O retorno está previsto para {D}. A data informada acima ficou sem efeito.",
         PENDENTE, None),
        (f"O retorno está previsto para {D}. A referida previsão foi revogada pela chefia.",
         PENDENTE, None),
        (f"O retorno está previsto para {D}. Essa nova data caiu.", AMBIGUO, None),
        (f"O retorno está previsto para {D}. Caiu.", AMBIGUO, None),
    ],
    "Data negada ou condicional": [
        (f"O retorno não será em {D}. A data ainda será informada.", PENDENTE, None),
        (f"Retorno: {D}. Não será nessa data.", PENDENTE, None),
        (f"O retorno não está previsto para {D}.", PENDENTE, None),
        (f"O retorno será em {D}, se houver transporte.", PENDENTE, None),
        (f"Retorno: {D}. Isso só vale desde que haja veículo.", PENDENTE, None),
        (f"O retorno está previsto para {D}. Essa previsão mudou.", PENDENTE, None),
        (f"Não confirmo a data de retorno. Retorno: {D}.", AMBIGUO, None),
    ],
    "Data substituída por outra confirmada": [
        (f"O retorno em {D} foi cancelado. O retorno foi remarcado para {N}.", CONFIRMADO, N),
        (f"O retorno está previsto para {D}. Essa previsão foi cancelada. O retorno foi "
         f"remarcado para {N}.", CONFIRMADO, N),
        (f"Retorno: {D}. Essa data foi cancelada. Retorno: {N}.", CONFIRMADO, N),
        (f"O retorno não será em {D}. O retorno será em {N}.", CONFIRMADO, N),
        (f"O retorno foi alterado para {N}. A data anterior, {D}, foi cancelada.", CONFIRMADO, N),
        (f"A volta foi remarcada para {N}.", CONFIRMADO, N),
    ],
    "Cancelamento de outro evento, sem invalidar o retorno": [
        (f"O retorno está previsto para {D}. A reunião com a prefeitura foi cancelada.",
         CONFIRMADO, D),
        (f"O retorno está previsto para {D}. O compromisso anterior foi desmarcado.",
         CONFIRMADO, D),
        (f"O retorno está previsto para {D}. A vistoria de 2026-11-18 foi suspensa.",
         CONFIRMADO, D),
        (f"O retorno está previsto para {D}. Não há outras alterações.", CONFIRMADO, D),
        (f"O retorno está previsto para {D}. Essa data está confirmada.", CONFIRMADO, D),
        (f"O retorno está previsto para {D}. A data de partida não muda.", CONFIRMADO, D),
    ],
    "Conflito e valor inválido": [
        (f"Retorno: {D}; retorno: 2026-11-21.", AMBIGUO, None),
        (f"O retorno está previsto para {D}. Essa previsão foi cancelada. Retorno: {D}.",
         AMBIGUO, None),
        (f"O retorno está previsto para {D}. A data 2026-11-19 foi cancelada.", AMBIGUO, None),
        ("Retorno previsto para 2026-02-30.", PENDENTE, None),
    ],
}


def parte1_casos() -> None:
    log("[1] Casos nomeados: estado do retorno, valor vigente e guarda do cálculo")
    for categoria, casos in CASOS.items():
        log(f"  {categoria}")
        for texto, estado, valor in casos:
            lido, vigente, problemas = estado_do_retorno(texto)
            assert (lido, vigente) == (estado, valor), (texto, lido, vigente, problemas)
            assert bool(problemas) == (estado == AMBIGUO), (texto, problemas)
            # A guarda só calcula com a data confirmada; com qualquer data do
            # texto que não seja a vigente, barra antes de executar.
            for data in {D, N, "2026-11-21"}:
                assert guarda_calcula(texto, data) == (data == valor), (texto, data)
            destino = {CONFIRMADO: "mérito com " + str(valor), PENDENTE: "diligência",
                       AMBIGUO: "análise manual"}[estado]
            log(f"    {estado:10} -> {destino:22} | {texto}")
    numero_112 = (
        (C112["texto"], CONFIRMADO, "207418"),
        ("A minha matrícula correta é 207418. Essa informação está errada.", PENDENTE, None),
        ("A referência do ofício é 207418.", None, P112["matricula"]),
    )
    log("  Complementação oficial do 0112 e variantes")
    for texto, estado, valor in numero_112:
        leitura, _ = ler_complementacao(texto, P112)
        vigente, problemas = pedido_vigente(P112, dict(C112, texto=texto))
        assert leitura.get("matricula", {}).get("estado") == estado and not problemas, texto
        assert vigente["matricula"] == valor, (texto, vigente["matricula"])
        log(f"    {str(estado):10} -> matrícula {str(valor):8} | {texto}")


# ----------------------------------------------------------------------
# 2. Regra geral por combinação.
# ----------------------------------------------------------------------
ATRIBUICOES = (f"O retorno está previsto para {D}.", f"Retorno: {D}.",
               f"Confirmo o retorno para {D}.", f"O retorno foi remarcado para {D}.",
               f"A volta foi alterada para {D}.", "Data do retorno: 20/11/2026.")
REFERENCIAS = ("Essa data", "Essa nova data", "Essa previsão", "Ela", "Isso",
               "A data informada acima", "A referida data", "Tal data", "A mesma",
               "O retorno", "A volta", "A data de retorno", f"A data {D}", f"O dia {D}")
PREDICADOS_DO_VOCABULARIO = ("foi cancelada", "não vale mais", "ficou sem efeito",
                             "não será mantida", "depende de confirmação da chefia",
                             "ainda será confirmada", "foi revogada", "foi desmarcada",
                             "está sujeita a alteração", "foi adiada")
PREDICADOS_FORA_DO_VOCABULARIO = ("caiu", "foi trocada", "perdeu a validade",
                                  "deixou de existir", "virou outra", "foi derrubada",
                                  "furou", "já era")
COMPLEMENTOS_DA_FRASE = ("", " por causa de um compromisso anterior",
                         " conforme o ofício original", " em razão da reunião inicial",
                         " segundo a nova orientação", ", infelizmente")


def parte2_regra_geral() -> None:
    log("\n[2] Regra geral: a data citada depois de afirmada nunca fica confirmada")
    total = barradas = 0
    por_estado = {PENDENTE: 0, AMBIGUO: 0}
    for atribuicao, referencia, predicado, complemento in itertools.product(
            ATRIBUICOES, REFERENCIAS, PREDICADOS_DO_VOCABULARIO + PREDICADOS_FORA_DO_VOCABULARIO,
            COMPLEMENTOS_DA_FRASE):
        texto = f"{atribuicao} {referencia} {predicado}{complemento}."
        estado, vigente, _ = estado_do_retorno(texto)
        assert estado in (PENDENTE, AMBIGUO) and vigente is None, (texto, estado, vigente)
        por_estado[estado] += 1
        total += 1
        if not guarda_calcula(texto, D):
            barradas += 1
    assert barradas == total
    log(f"    {total} complementações = {len(ATRIBUICOES)} atribuições × {len(REFERENCIAS)} "
        f"referências × {len(PREDICADOS_DO_VOCABULARIO) + len(PREDICADOS_FORA_DO_VOCABULARIO)} "
        f"predicados ({len(PREDICADOS_FORA_DO_VOCABULARIO)} fora do vocabulário) × "
        f"{len(COMPLEMENTOS_DA_FRASE)} complementos da frase")
    log(f"    pendente (diligência): {por_estado[PENDENTE]} · ambíguo (análise manual): "
        f"{por_estado[AMBIGUO]} · confirmado: 0")
    log(f"    guarda: calcular_diarias com {D} barrado antes de executar em {barradas} de {total}")
    # O mesmo vale para os predicados fora do vocabulário: o que o detector não
    # reconhece deixa o campo ambíguo, e nunca confirmado.
    for predicado in PREDICADOS_FORA_DO_VOCABULARIO:
        estado, _, _ = estado_do_retorno(f"O retorno está previsto para {D}. Essa data {predicado}.")
        assert estado == AMBIGUO, predicado
    log(f"    predicados fora do vocabulário ({', '.join(PREDICADOS_FORA_DO_VOCABULARIO)}): "
        "ambíguo em todas as combinações")


# ----------------------------------------------------------------------
# 3. Controles.
# ----------------------------------------------------------------------
EVENTOS = ("A reunião com a prefeitura", "O compromisso anterior", "A vistoria de 2026-11-18",
           "O curso de capacitação", "A audiência inicial", "O voo de conexão")
SUBSTITUICOES = (
    f"O retorno em {D} foi cancelado. O retorno foi remarcado para {N}.",
    f"O retorno está previsto para {D}. Essa previsão foi cancelada. O retorno foi remarcado "
    f"para {N}.",
    f"O retorno está previsto para {D}. Ela foi cancelada. Retorno: {N}.",
    f"O retorno não será em {D}. O retorno será em {N}.",
    f"O retorno foi alterado para {N}. A data anterior, {D}, foi cancelada.",
    f"Retorno: {D}. Essa data foi cancelada. Retorno: {N}.",
)


def parte3_controles() -> None:
    log("\n[3] Controles: outro evento não invalida o retorno; substituição confirma a nova data")
    total = 0
    for atribuicao, evento, predicado, complemento in itertools.product(
            ATRIBUICOES[:3], EVENTOS, PREDICADOS_DO_VOCABULARIO + PREDICADOS_FORA_DO_VOCABULARIO,
            COMPLEMENTOS_DA_FRASE):
        texto = f"{atribuicao} {evento} {predicado}{complemento}."
        estado, vigente, problemas = estado_do_retorno(texto)
        assert (estado, vigente, problemas) == (CONFIRMADO, D, []), (texto, estado, problemas)
        total += 1
    for texto in (f"O retorno está previsto para {D}. A reunião com a prefeitura foi cancelada.",
                  f"O retorno está previsto para {D}. O compromisso anterior caiu."):
        assert guarda_calcula(texto, D)
    log(f"    {total} complementações com outro evento cancelado, negado, condicionado ou com "
        f"predicado fora do vocabulário: retorno confirmado em {D} em todas")
    for texto in SUBSTITUICOES:
        estado, vigente, problemas = estado_do_retorno(texto)
        assert (estado, vigente, problemas) == (CONFIRMADO, N, []), (texto, estado, vigente)
        assert guarda_calcula(texto, N) and not guarda_calcula(texto, D), texto
        log(f"    substituída -> {N}; guarda aceita {N} e barra {D} | {texto}")


# ----------------------------------------------------------------------
# 4. Confirmação explícita do campo.
# ----------------------------------------------------------------------
def parte4_confirmacao_explicita() -> None:
    log("\n[4] Confirmação explícita do campo, informada com a complementação")
    ambiguo = (f"O retorno foi remarcado para {D}. Essa nova data foi cancelada por causa de um "
               f"compromisso anterior.")
    casos = (
        (ambiguo, {"data_retorno": N}, CONFIRMADO, N),
        (ambiguo, {"data_retorno": "22/11/2026"}, CONFIRMADO, N),
        (ambiguo, {"data_retorno": D}, AMBIGUO, None),
        (f"O retorno está previsto para {D}. Essa previsão foi cancelada.", {"data_retorno": D},
         AMBIGUO, None),
        (f"O retorno está previsto para {D}. Essa previsão foi cancelada.", {"data_retorno": N},
         CONFIRMADO, N),
        (C111["texto"], {"data_retorno": D}, CONFIRMADO, D),
        (C111["texto"], {"data_retorno": N}, AMBIGUO, None),
        (ambiguo, {"data_retorno": "2026-02-30"}, AMBIGUO, None),
    )
    for texto, campos, estado, valor in casos:
        lido, vigente, _ = estado_do_retorno(texto, campos)
        assert (lido, vigente) == (estado, valor), (texto, campos, lido, vigente)
        assert guarda_calcula(texto, N, campos) == (valor == N)
        log(f"    {estado:10} -> {str(valor):10} | campo {campos['data_retorno']} | {texto}")


if __name__ == "__main__":
    parte1_casos()
    parte2_regra_geral()
    parte3_controles()
    parte4_confirmacao_explicita()
    log("\nTodas as verificações do contrato de confirmação passaram.")
    SAIDA.write_text("\n".join(linhas) + "\n", encoding="utf-8")
