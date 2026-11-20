"""As quatro ferramentas da instrução de pedidos de diárias da SEMA-MT.

Cada função substitui uma consulta que o servidor faz hoje à mão: o cadastro
funcional, o cálculo das diárias, o histórico do mês com as prestações de
contas e o saldo da dotação da unidade (Aula 06, Seção 3.1).

Duas regras de projeto, exigidas pela Etapa 2 do desafio:

- Minimização (LGPD, art. 6º, III; Aula 06, Seção 5.2): o cadastro tem CPF e
  e-mail, que a instrução não usa, e nenhuma ferramenta os devolve ao modelo.
- Contas no código (Aula 03, abertura; Aula 06, Seção 1): antecedência,
  quantidade, valor, soma do mês, prazo da prestação e comparação com o saldo
  saem prontos. O modelo só lê o resultado.

Nenhuma função importa framework (Aula 06, Seção 4.4). O teste sem agente e
sem chave está em `teste_ferramentas.py`.
"""
import csv
import json
import pathlib
import unicodedata
from datetime import date, timedelta

DADOS = pathlib.Path(__file__).parent / "dados"

TABELA = json.loads((DADOS / "tabela_diarias.json").read_text(encoding="utf-8"))
UNIDADES = json.loads((DADOS / "unidades.json").read_text(encoding="utf-8"))
with open(DADOS / "servidores.csv", encoding="utf-8") as arquivo:
    SERVIDORES = {linha["matricula"]: linha for linha in csv.DictReader(arquivo)}
with open(DADOS / "historico_diarias.csv", encoding="utf-8") as arquivo:
    HISTORICO = list(csv.DictReader(arquivo))

# A análise é feita na data fixada pela tabela, e não na data do relógio:
# com date.today(), uma prestação ainda no prazo apareceria como vencida.
DATA_ANALISE = date.fromisoformat(TABELA["data_da_analise"])
ANTECEDENCIA_MINIMA = TABELA["antecedencia_minima_dias"]
LIMITE_MENSAL = TABELA["limite_mensal_diarias"]
PRAZO_PRESTACAO = TABELA["prazo_prestacao_dias_uteis"]

CLASSES_DESTINO = {
    "interior_mt": "interior de MT",
    "outra_uf": "outra unidade da federação",
    "distrito_federal": "Distrito Federal",
}


def _reais(valor: float) -> str:
    """Formata um valor no padrão brasileiro, como R$ 1.260,00."""
    return "R$ " + f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _normalizar_nome(nome: str) -> str:
    """Compara nomes sem distinguir acentos, maiúsculas e espaços repetidos."""
    sem_acento = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode()
    return " ".join(sem_acento.lower().split())


def _data(texto: str) -> date | None:
    try:
        return date.fromisoformat(str(texto).strip())
    except ValueError:
        return None


def _somar_dias_uteis(inicio: date, dias: int) -> date:
    """Conta dias úteis de segunda a sexta, sem considerar feriados."""
    atual, restantes = inicio, dias
    while restantes > 0:
        atual += timedelta(days=1)
        if atual.weekday() < 5:
            restantes -= 1
    return atual


def classe_destino(destino_uf: str) -> str:
    """Classe do destino no Anexo I: interior de MT, outra UF ou Distrito Federal."""
    uf = destino_uf.strip().upper()
    if uf == "MT":
        return "interior_mt"
    if uf == "DF":
        return "distrito_federal"
    return "outra_uf"


def consultar_servidor(matricula: str, nome_informado: str) -> str:
    """Consulta o cadastro funcional do servidor pela matrícula e confere o nome.

    Use primeiro, antes de qualquer cálculo, com a matrícula e o nome exatamente
    como constam do pedido ou da complementação. `matricula` são os seis
    algarismos, como '204317'; `nome_informado` é o nome do solicitante escrito
    no pedido. Devolve o nome do cadastro, o cargo, o grupo da diária (A, B ou
    C), a sigla da unidade de lotação (como CFF ou GAB) e o município-sede, e
    informa se o nome do pedido CONFERE ou DIVERGE do cadastro. Nome divergente
    ou matrícula não localizada levam o pedido à diligência (art. 9º). Não
    devolve CPF nem e-mail, que a instrução não usa.
    """
    chave = matricula.strip()
    servidor = SERVIDORES.get(chave)
    if servidor is None:
        return (f"Matrícula {chave} não localizada no cadastro funcional. "
                f"Pedido com dado divergente do cadastro: diligência (art. 9º).")
    confere = _normalizar_nome(servidor["nome"]) == _normalizar_nome(nome_informado)
    situacao = ("CONFERE com o cadastro" if confere else
                f"DIVERGE do cadastro: o pedido informa '{nome_informado}', "
                f"mas a matrícula {chave} pertence a outro servidor; diligência (art. 9º)")
    return (f"Matrícula {chave}: {servidor['nome']}, {servidor['cargo']}. "
            f"Grupo da diária: {servidor['grupo_diaria']}. "
            f"Unidade de lotação: {servidor['unidade']}. "
            f"Sede: {servidor['municipio_sede']}. "
            f"Nome informado no pedido: {situacao}.")


def calcular_diarias(grupo: str, destino_uf: str, data_pedido: str,
                     data_partida: str, data_retorno: str) -> str:
    """Calcula a quantidade e o valor das diárias e a antecedência do pedido.

    Use depois de consultar o servidor, porque o `grupo` (A, B ou C) vem do
    cadastro. `destino_uf` é a sigla da UF de destino do pedido, como 'MT',
    'DF' ou 'RO'. As três datas vêm do pedido ou da complementação, no formato
    AAAA-MM-DD, como '2026-11-09'. Nunca chame com data suposta: se o pedido
    não traz a data de retorno, não calcule e trate como diligência. Devolve a
    quantidade (uma diária por pernoite mais meia no retorno; meia diária sem
    pernoite, art. 4º), o valor unitário do Anexo I, o valor total, e a
    antecedência em dias corridos entre o protocolo e a partida, indicando se
    ATENDE ou NÃO ATENDE o mínimo de 10 dias (art. 5º).
    """
    letra = grupo.strip().upper()
    if letra not in TABELA["valores"]:
        return f"Grupo '{grupo}' inválido. Grupos válidos: A, B ou C, conforme o cadastro."
    pedido, partida, retorno = _data(data_pedido), _data(data_partida), _data(data_retorno)
    if retorno is None:
        return ("Data de retorno ausente ou inválida: não é possível calcular as diárias. "
                "Pedido incompleto, diligência (art. 9º).")
    if pedido is None or partida is None:
        return "Data do pedido ou de partida inválida. Use o formato AAAA-MM-DD."
    if retorno < partida:
        return f"Data de retorno ({retorno}) anterior à partida ({partida}). Pedido inconsistente."

    pernoites = (retorno - partida).days
    quantidade = 0.5 if pernoites == 0 else pernoites + 0.5
    classe = classe_destino(destino_uf)
    unitario = TABELA["valores"][letra][classe]
    total = quantidade * unitario

    antecedencia = (partida - pedido).days
    if antecedencia >= ANTECEDENCIA_MINIMA:
        situacao = f"ATENDE o mínimo de {ANTECEDENCIA_MINIMA} dias (art. 5º)"
    else:
        situacao = (f"NÃO ATENDE o mínimo de {ANTECEDENCIA_MINIMA} dias (art. 5º); só se admite "
                    f"em urgência do § 1º, com autorização expressa e escrita do Secretário "
                    f"Adjunto (§ 2º); autorização verbal não supre")
    return (f"Quantidade: {quantidade} diária(s) ({pernoites} pernoite(s), art. 4º). "
            f"Valor unitário: {_reais(unitario)} (grupo {letra}, {CLASSES_DESTINO[classe]}, "
            f"Anexo I). Valor total: {_reais(total)} = {total:.2f}. "
            f"Antecedência: {antecedencia} dia(s) corridos entre o protocolo ({pedido}) e a "
            f"partida ({partida}): {situacao}.")


def consultar_historico_diarias(matricula: str, data_partida: str,
                                quantidade_pedida: float) -> str:
    """Consulta o histórico de diárias do servidor: limite do mês e prestações de contas.

    Use depois de calcular as diárias, porque precisa da quantidade calculada.
    `matricula` são os seis algarismos do cadastro, como '203648';
    `data_partida` é a data de partida do pedido, no formato AAAA-MM-DD;
    `quantidade_pedida` é a quantidade devolvida pelo cálculo, com ponto
    decimal, como 3.5. Devolve a soma das diárias já concedidas no mês da
    partida mais as pedidas, comparada ao limite de 10 por mês (ATENDE ou
    EXCEDE, art. 6º), e a situação de cada prestação de contas pendente:
    VENCIDA (mais de 5 dias úteis após o retorno, o que impede nova diária)
    ou NO PRAZO (não impede), art. 7º.
    """
    chave = matricula.strip()
    partida = _data(data_partida)
    if partida is None:
        return "Data de partida inválida. Use o formato AAAA-MM-DD."
    registros = [h for h in HISTORICO if h["matricula"] == chave]

    do_mes = [h for h in registros if h["data_partida"][:7] == partida.isoformat()[:7]]
    ja_concedidas = sum(float(h["quantidade"]) for h in do_mes)
    soma = ja_concedidas + float(quantidade_pedida)
    limite = ("ATENDE" if soma <= LIMITE_MENSAL else "EXCEDE")
    linhas = [f"Mês da partida {partida:%m/%Y}: {ja_concedidas} diária(s) já concedida(s) "
              f"({', '.join(h['pedido'] for h in do_mes) or 'nenhuma'}) + {quantidade_pedida} "
              f"pedida(s) = {soma}. Limite de {LIMITE_MENSAL} por mês: {limite} (art. 6º)."]

    pendentes = [h for h in registros if h["prestacao_contas"] == "pendente"]
    if not pendentes:
        linhas.append("Prestação de contas: nenhuma pendente. Não há impedimento (art. 7º).")
    for h in pendentes:
        retorno = date.fromisoformat(h["data_retorno"])
        vence = _somar_dias_uteis(retorno, PRAZO_PRESTACAO)
        if vence < DATA_ANALISE:
            situacao = (f"VENCIDA em {vence}; o servidor está impedido de receber nova diária "
                        f"até a regularização (art. 7º)")
        else:
            situacao = f"NO PRAZO até {vence}; não impede nova diária (art. 7º)"
        linhas.append(f"Prestação de contas do {h['pedido']} (retorno em {retorno}): pendente, "
                      f"{situacao}. Data da análise: {DATA_ANALISE} (feriados não considerados).")
    return " ".join(linhas)


def consultar_saldo_diarias(unidade: str, valor: float) -> str:
    """Consulta o saldo da dotação de diárias de uma unidade e o compara com o valor pedido.

    Use depois de calcular o valor total das diárias. `unidade` é a sigla da
    unidade de lotação devolvida pelo cadastro, como CFF ou GAB; `valor` é o
    total em reais, com ponto decimal, como 980.0. Devolve o saldo disponível e
    a indicação de saldo suficiente ou insuficiente para o pedido.
    """
    sigla = unidade.strip().upper()
    if sigla not in UNIDADES:
        return f"Unidade '{unidade}' não localizada. Siglas válidas: {', '.join(UNIDADES)}."
    saldo = UNIDADES[sigla]["saldo_diarias"]
    situacao = "suficiente" if saldo >= float(valor) else "INSUFICIENTE"
    return f"Saldo da unidade {sigla}: R$ {saldo:.2f}. Saldo {situacao} para R$ {float(valor):.2f} (art. 8º)."


FERRAMENTAS = [consultar_servidor, calcular_diarias, consultar_historico_diarias,
               consultar_saldo_diarias]
