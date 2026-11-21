"""A barreira em código entre o agente e o conferente (Etapa 3).

"A barreira pertence ao código, e não ao prompt" (Aula 01, Seção 8). Uma
instrução no prompt é um pedido; esta verificação é uma garantia, e continua
valendo quando o modelo, a instrução ou as ferramentas mudarem (Aula 03, 6.3).

A barreira não confia em nada que o modelo afirme. Ela parte do que a
aplicação tem em mãos (o pedido, a complementação e o que as ferramentas
devolveram nesta execução) e confere a instrução contra isso:

1. Identidade vigente do pedido. A complementação só corrige o próprio pedido,
   e cada dado entra no seu papel: a matrícula corrigida substitui a digitada;
   a data de retorno informada preenche o retorno. Cadastro, cálculo,
   histórico, saldo e instrução ficam presos a essa identidade.
2. Cada argumento no seu papel (enunciado, Etapa 3; `exigir_fundamento` da
   Aula 03, Seção 7). A data de protocolo é a do protocolo, a de partida é a da
   partida, em todas as ferramentas. Grupo e unidade vêm do cadastro da
   matrícula vigente; quantidade e valor passados adiante vêm do cálculo.
3. Evidência para cada verificação. A situação de cada um dos seis critérios
   é derivada aqui, das consultas, e a instrução precisa coincidir com ela.
   Instrução de mérito com consulta obrigatória ausente é recusada. Na
   diligência (dado ausente ou cadastro divergente, art. 9º), qualquer consulta
   de mérito é trilha indevida e a instrução é recusada.
4. Recomendação, números e exceção derivados das consultas (Aula 04, Seção 8,
   ancoragem numérica). A exceção de urgência do art. 5º, § 1º, é reconhecida
   pelo código, pelas hipóteses que a norma lista, afirmadas e sem sinal
   contrário, e não pela marcação do modelo. Com antecedência insuficiente e
   urgência ambígua, a instrução é recusada e o conferente decide.
5. Alertas montados pelo código. O conferente só vê alertas de categorias
   que o código verifica no pedido: dados pessoais mascarados, ordem dirigida
   ao sistema na justificativa, autorização verbal alegada e, na urgência, a
   autorização escrita a conferir. Os alertas livres do modelo não chegam à
   tela: um alerta pode citar um dado com fonte no papel errado ("o valor total
   é R$ 280,00", quando esse é o unitário) ou afirmar sem número algum o que o
   histórico desmente ("a prestação foi regularizada"), e nenhuma conferência
   de fontes pega isso. Ficam registrados para a medição.
6. Textos factuais redigidos pelo código. Liberada a instrução, os
   fundamentos, as pendências, os alertas e a minuta são montados aqui com os
   dados das consultas válidas, cada um no seu papel (valor unitário, valor
   total, saldo, situação da prestação), e substituem os do modelo. Na
   urgência, a condição da autorização expressa e escrita do Secretário
   Adjunto entra na minuta por regra. Os erros dos textos substituídos ficam
   registrados para a medição.

Qualquer falha devolve a lista de problemas, e a aplicação mostra ao servidor
apenas a mensagem padrão (Aula 06, 5.3): nada do conteúdo recusado é exibido.
"""
import json
import re
import unicodedata
from decimal import Decimal, InvalidOperation

from ferramentas import (ANTECEDENCIA_MINIMA, LIMITE_MENSAL, PRAZO_PRESTACAO, SERVIDORES,
                         _normalizar_nome, _reais)

DATA_ISO = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
MATRICULA = re.compile(r"(?<![\d.,/-])\d{6}(?![\d.,/-]?\d)")
CAMPOS_DATA = ("data_pedido", "data_partida", "data_retorno")
OBRIGATORIOS = ("numero", "data_pedido", "matricula", "nome", "destino_uf", "data_partida",
                "data_retorno")
CRITERIOS = ("cadastro", "dados_completos", "antecedencia", "prestacao_contas",
             "limite_mensal", "saldo_orcamentario")
MERITO = ("antecedencia", "prestacao_contas", "limite_mensal", "saldo_orcamentario")
CONSULTAS_DE_MERITO = ("calcular_diarias", "consultar_historico_diarias", "consultar_saldo_diarias")
# Resultado de uma consulta de mérito barrada antes de executar (instrutor.py,
# guarda_de_merito): a função não rodou e nada leu.
CONSULTA_BLOQUEADA = "CONSULTA BLOQUEADA PELA APLICAÇÃO"


def bloqueada(consulta: dict) -> bool:
    return str(consulta.get("resultado", "")).startswith(CONSULTA_BLOQUEADA)

# Art. 5º, § 1º: as hipóteses de urgência que a norma lista. A leitura é
# conservadora (desenho.md, Seção 8): o código só reconhece as hipóteses
# listadas, e uma palavra isolada não basta. A menção precisa ser afirmativa e
# a justificativa não pode trazer sinal contrário (menção negada, atividade
# programada, autorização verbal, ordem dirigida ao sistema). Com sinal
# contrário, a urgência é ambígua e a avaliação fica com o conferente: a
# instrução é recusada e o pedido vai à análise manual.
HIPOTESES_URGENCIA = ("incendio", "desastre ambiental", "infracao ambiental em curso",
                      "determinacao judicial")
ROTULOS_URGENCIA = {"incendio": "combate a incêndio", "desastre ambiental": "desastre ambiental",
                    "infracao ambiental em curso": "infração ambiental em curso",
                    "determinacao judicial": "determinação judicial"}
NOMES_URGENCIA = {"incendio": "incêndio", "desastre ambiental": "desastre ambiental",
                  "infracao ambiental em curso": "infração ambiental em curso",
                  "determinacao judicial": "determinação judicial"}
NEGACAO = re.compile(r"\b(?:nao|nem|sem|nenhum|nenhuma|inexist\w*|ausencia de|descartad\w*)\b")
SINAIS_CONTRARIOS = {
    "atividade programada": r"capacita|treinamento|curso de|programad|planejad|cronograma|"
                            r"reuniao|oficina|seminario|palestra|evento",
    "autorização verbal": r"verbal",
    "ordem dirigida ao sistema": r"\bsistema\b",
}
# Ordem dirigida ao sistema de análise escrita na justificativa (enunciado,
# Etapa 1): quem escreve no pedido fala com a máquina, e não com o conferente.
ORDEM_EMBUTIDA = re.compile(r"\bsistema\b|\bassistente\b|inteligencia artificial|\bignore\b|"
                            r"\bdesconsidere\b")

MESES = {"janeiro": 1, "fevereiro": 2, "marco": 3, "abril": 4, "maio": 5, "junho": 6,
         "julho": 7, "agosto": 8, "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12}


def _texto(valor) -> str:
    """Normaliza argumentos: None, "null" e vazio contam como ausentes."""
    if valor is None:
        return ""
    texto = str(valor).strip()
    return "" if texto.lower() in ("none", "null") else texto


def _sem_acento(texto: str) -> str:
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()


def ler_urgencia(pedido: dict) -> tuple[str, str]:
    """("legitima", hipótese), ("ausente", "") ou ("ambigua", motivo), pelo art. 5º, § 1º."""
    texto = _sem_acento(pedido.get("justificativa") or "")
    afirmadas, negadas = [], []
    for h in HIPOTESES_URGENCIA:
        for achado in re.finditer(h, texto):
            # A negação vale dentro da mesma oração, antes da menção.
            oracao = re.split(r"[.;:!?]", texto[:achado.start()])[-1]
            (negadas if NEGACAO.search(oracao[-40:]) else afirmadas).append(h)
    if not afirmadas and not negadas:
        return "ausente", ""
    contrarios = [nome for nome, padrao in SINAIS_CONTRARIOS.items() if re.search(padrao, texto)]
    if negadas:
        contrarios.insert(0, f"menção negada a {NOMES_URGENCIA[negadas[0]]}")
    if contrarios:
        return "ambigua", ", ".join(contrarios)
    return "legitima", ROTULOS_URGENCIA[afirmadas[0]]


def urgencia_legitima(pedido: dict) -> bool:
    """A justificativa descreve, sem sinal contrário, uma das hipóteses do art. 5º, § 1º?"""
    return ler_urgencia(pedido)[0] == "legitima"


def hipotese_de_urgencia(pedido: dict) -> str | None:
    """A hipótese do art. 5º, § 1º, que a justificativa descreve, ou None."""
    situacao, hipotese = ler_urgencia(pedido)
    return hipotese if situacao == "legitima" else None


# ----------------------------------------------------------------------
# 1. Identidade vigente do pedido.
# ----------------------------------------------------------------------
def pedido_vigente(pedido: dict, complemento: dict | None) -> tuple[dict, list[str]]:
    """O pedido com as correções da complementação, cada dado no seu papel.

    Só se aplica a complementação do próprio pedido. Uma correção que não se
    consegue atribuir a um único papel vira problema, e não palpite.
    """
    vigente, problemas = dict(pedido), []
    if not complemento:
        return vigente, problemas
    if complemento.get("numero") != pedido["numero"]:
        problemas.append(f"complementação do pedido {complemento.get('numero')} aplicada ao "
                         f"pedido {pedido['numero']}")
        return vigente, problemas
    texto = complemento.get("texto", "")

    matriculas = set(MATRICULA.findall(texto))
    if len(matriculas) == 1:
        vigente["matricula"] = matriculas.pop()
    elif len(matriculas) > 1:
        problemas.append(f"complementação com mais de uma matrícula: {sorted(matriculas)}")

    faltantes = [c for c in CAMPOS_DATA if not _texto(pedido.get(c))]
    atribuidas: dict[str, str] = {}
    for achado in DATA_ISO.finditer(texto):
        antes = _sem_acento(texto[max(0, achado.start() - 50):achado.start()])
        if "retorno" in antes or "volta" in antes:
            papel = "data_retorno"
        elif "partida" in antes or re.search(r"\bida\b", antes):
            papel = "data_partida"
        elif "protocol" in antes:
            papel = "data_pedido"
        elif len(faltantes) == 1:
            papel = faltantes[0]
        else:
            problemas.append(f"data {achado.group()} da complementação sem papel definido")
            continue
        if papel in atribuidas and atribuidas[papel] != achado.group():
            problemas.append(f"complementação com duas datas para {papel}")
        atribuidas[papel] = achado.group()
    vigente.update(atribuidas)
    return vigente, problemas


# ----------------------------------------------------------------------
# 2. Cada consulta no seu papel.
# ----------------------------------------------------------------------
def _calculo(resultado: str) -> dict | None:
    q = re.search(r"Quantidade: ([\d.]+)", resultado)
    v = re.search(r"Valor total: R\$ [\d.,]+ = ([\d.]+)\.", resultado)
    if not (q and v):
        return None
    return {"quantidade": float(q.group(1)), "valor": round(float(v.group(1)), 2),
            "antecedencia_atende": "NÃO ATENDE" not in resultado, "texto": resultado}


def _conferir_consultas(consultas: list[dict], pedido: dict, vigente: dict) -> tuple[list, dict]:
    """Confere os argumentos de cada consulta e devolve as evidências válidas."""
    problemas: list[str] = []
    matricula = _texto(vigente.get("matricula"))
    servidor = SERVIDORES.get(matricula)
    evidencias: dict = {"servidor": None, "calculo": None, "historico": None, "saldo": None}

    # Uma consulta barrada antes de executar não é evidência de nada.
    consultas = [c for c in consultas if not bloqueada(c)]
    # O cálculo vem antes porque histórico e saldo se ancoram nele.
    for c in consultas:
        if c["ferramenta"] != "calcular_diarias":
            continue
        args, erros = c["argumentos"], []
        if servidor is None or _texto(args.get("grupo")).upper() != servidor["grupo_diaria"]:
            erros.append(f"grupo {args.get('grupo')!r} não é o do cadastro da matrícula "
                         f"vigente {matricula}")
        if _texto(args.get("destino_uf")).upper() != _texto(vigente.get("destino_uf")).upper():
            erros.append(f"UF {args.get('destino_uf')!r} difere do pedido")
        for campo in CAMPOS_DATA:
            if _texto(args.get(campo)) != _texto(vigente.get(campo)):
                erros.append(f"{campo}={args.get(campo)!r} não é a {campo} do pedido "
                             f"({vigente.get(campo)})")
        problemas += [f"calcular_diarias: {e}" for e in erros]
        if not erros:
            evidencias["calculo"] = _calculo(c["resultado"]) or evidencias["calculo"]

    calculo = evidencias["calculo"]
    for c in consultas:
        nome, args = c["ferramenta"], c["argumentos"]
        if nome == "calcular_diarias":
            continue
        erros = []
        if nome == "consultar_servidor":
            # Reconsultar a matrícula digitada, na complementação, é inofensivo:
            # grupo e unidade só valem do cadastro da matrícula vigente.
            consultada = _texto(args.get("matricula"))
            if consultada not in {matricula, _texto(pedido.get("matricula"))}:
                erros.append(f"matrícula {consultada} não consta do pedido nem da complementação")
            elif consultada == matricula:
                if _normalizar_nome(_texto(args.get("nome_informado"))) != \
                        _normalizar_nome(_texto(vigente.get("nome"))):
                    erros.append(f"nome informado {args.get('nome_informado')!r} difere do pedido")
                else:
                    evidencias["servidor"] = c["resultado"]
        elif nome == "consultar_historico_diarias":
            if _texto(args.get("matricula")) != matricula:
                erros.append(f"matrícula {args.get('matricula')} não é a matrícula vigente "
                             f"{matricula}")
            if _texto(args.get("data_partida")) != _texto(vigente.get("data_partida")):
                erros.append(f"data_partida={args.get('data_partida')!r} não é a data de "
                             f"partida do pedido ({vigente.get('data_partida')})")
            if calculo is None or _numero(args.get("quantidade_pedida")) != calculo["quantidade"]:
                erros.append(f"quantidade {args.get('quantidade_pedida')} não veio de um cálculo "
                             f"válido")
            if not erros:
                evidencias["historico"] = c["resultado"]
        elif nome == "consultar_saldo_diarias":
            if servidor is None or _texto(args.get("unidade")).upper() != servidor["unidade"]:
                erros.append(f"unidade {args.get('unidade')!r} não é a do cadastro da matrícula "
                             f"vigente {matricula}")
            if calculo is None or _numero(args.get("valor")) != calculo["valor"]:
                erros.append(f"valor {args.get('valor')} não veio de um cálculo válido")
            if not erros:
                evidencias["saldo"] = c["resultado"]
        else:
            erros.append("ferramenta desconhecida")
        problemas += [f"{nome}: {e}" for e in erros]
    return problemas, evidencias


def _numero(valor) -> float | None:
    try:
        return round(float(valor), 2)
    except (TypeError, ValueError):
        return None


# ----------------------------------------------------------------------
# 3 e 4. Situações, recomendação, números e exceção derivados das consultas.
# ----------------------------------------------------------------------
def esperado(pedido: dict, vigente: dict, evidencias: dict) -> dict:
    """O que as consultas válidas sustentam, critério por critério."""
    sit = dict.fromkeys(CRITERIOS, "nao_verificado")
    servidor = evidencias["servidor"]
    if servidor is not None:
        sit["cadastro"] = "atende" if "CONFERE" in servidor else "nao_atende"
    sit["dados_completos"] = ("atende" if all(_texto(vigente.get(c)) for c in OBRIGATORIOS)
                              else "nao_atende")
    leitura, motivo_urgencia = ler_urgencia(pedido)
    urgente = leitura == "legitima"
    calculo = evidencias["calculo"]
    if calculo is not None:
        sit["antecedencia"] = ("atende" if calculo["antecedencia_atende"] or urgente
                               else "nao_atende")
    if evidencias["historico"] is not None:
        sit["prestacao_contas"] = "nao_atende" if "VENCIDA" in evidencias["historico"] else "atende"
        sit["limite_mensal"] = "nao_atende" if "EXCEDE" in evidencias["historico"] else "atende"
    if evidencias["saldo"] is not None:
        sit["saldo_orcamentario"] = ("nao_atende" if "INSUFICIENTE" in evidencias["saldo"]
                                     else "atende")

    if "nao_atende" in (sit["cadastro"], sit["dados_completos"]):
        # Art. 9º: diligência, sem análise de mérito.
        for c in MERITO:
            sit[c] = "nao_verificado"
        return {"situacoes": sit, "recomendacao": "diligencia", "quantidade": None,
                "valor": None, "exige": False, "sem_evidencia": [], "urgencia_ambigua": ""}
    sem_evidencia = [c for c in ("cadastro",) + MERITO if sit[c] == "nao_verificado"]
    recomendacao = "nao_recomendado" if "nao_atende" in sit.values() else "apto_para_autorizacao"
    exige = bool(calculo and not calculo["antecedencia_atende"] and urgente)
    # Antecedência insuficiente com urgência ambígua: quem decide é o conferente.
    ambigua = (motivo_urgencia if calculo and not calculo["antecedencia_atende"]
               and leitura == "ambigua" else "")
    return {"situacoes": sit, "recomendacao": recomendacao,
            "quantidade": calculo["quantidade"] if calculo else None,
            "valor": calculo["valor"] if calculo else None,
            "exige": exige, "sem_evidencia": sem_evidencia, "urgencia_ambigua": ambigua}


# ----------------------------------------------------------------------
# 5. Dados factuais dos textos.
# ----------------------------------------------------------------------
def _interpretacoes(token: str) -> set:
    """Um número escrito pode estar no padrão brasileiro ou no do código."""
    valores = set()
    candidatos = [token.replace(".", "").replace(",", ".")] if "," in token else \
        [token, token.replace(".", "")]
    for c in candidatos:
        try:
            valores.add(Decimal(c).quantize(Decimal("0.01")))
        except InvalidOperation:
            pass
    return valores


def _valor_monetario(token: str) -> Decimal | None:
    if "," in token:
        bruto = token.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"\d{1,3}(\.\d{3})+", token):
        bruto = token.replace(".", "")
    else:
        bruto = token
    try:
        return Decimal(bruto).quantize(Decimal("0.01"))
    except InvalidOperation:
        return None


def fatos_citados(texto: str) -> dict:
    """Valores, datas, matrículas, pedidos e números com unidade citados no texto."""
    fatos: dict = {"valores": set(), "datas": set(), "matriculas": set(), "pedidos": set(),
                   "numeros": set()}
    fatos["datas"] |= set(DATA_ISO.findall(texto))
    for d, m, a in re.findall(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b", texto):
        fatos["datas"].add(f"{a}-{int(m):02d}-{int(d):02d}")
    for d, mes, a in re.findall(r"\b(\d{1,2})º? de ([a-zç]+) de (\d{4})\b", _sem_acento(texto)):
        if mes in MESES:
            fatos["datas"].add(f"{a}-{MESES[mes]:02d}-{int(d):02d}")
    sem_datas = re.sub(r"\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2}", " ", texto)
    for token in re.findall(r"R\$\s*(\d+(?:[.,]\d+)*)", sem_datas):
        if (v := _valor_monetario(token)) is not None:
            fatos["valores"].add(v)
    for token in re.findall(r"(?<![\d.,])(\d{1,3}(?:\.\d{3})*,\d{2})(?![\d,])", sem_datas):
        if (v := _valor_monetario(token)) is not None:
            fatos["valores"].add(v)
    fatos["matriculas"] |= set(MATRICULA.findall(sem_datas))
    fatos["pedidos"] |= set(re.findall(r"DIA-\d{4}-\d{4}", texto))
    for token in re.findall(r"(\d+(?:[.,]\d+)?)\s*(?:di[áa]rias?\b|diária\(s\)|dias?\b|dia\(s\))",
                            sem_datas):
        fatos["numeros"].add(Decimal(token.replace(",", ".")).quantize(Decimal("0.01")))
    return fatos


def fatos_das_fontes(pedido: dict, vigente: dict, complemento: dict | None,
                     consultas: list[dict]) -> dict:
    """Tudo o que os textos da instrução podem citar."""
    fontes = [json.dumps(pedido, ensure_ascii=False), json.dumps(vigente, ensure_ascii=False)]
    if complemento:
        fontes.append(json.dumps(complemento, ensure_ascii=False))
    fontes += [c["resultado"] for c in consultas]
    texto = "\n".join(fontes)
    fatos = fatos_citados(texto)
    # Nas fontes, todo número conta, em qualquer das duas grafias: "= 8.0."
    # no histórico sustenta "8 diárias" na minuta.
    for token in re.findall(r"\d+(?:[.,]\d+)*", texto):
        fatos["numeros"] |= _interpretacoes(token)
        fatos["valores"] |= _interpretacoes(token)
    for constante in (ANTECEDENCIA_MINIMA, LIMITE_MENSAL, PRAZO_PRESTACAO):
        fatos["numeros"].add(Decimal(constante).quantize(Decimal("0.01")))
    return fatos


# Números por extenso com unidade ("quarenta mil reais", "dez dias") não podem
# ser conferidos contra as fontes: nos textos que vêm do modelo, são recusados.
_EXTENSO = ("dois|duas|tres|quatro|cinco|seis|sete|oito|nove|dez|onze|doze|treze|quatorze|"
            "catorze|quinze|dezesseis|dezessete|dezoito|dezenove|vinte|trinta|quarenta|"
            "cinquenta|sessenta|setenta|oitenta|noventa|cem|cento|duzentos|duzentas|trezentos|"
            "quatrocentos|quinhentos|seiscentos|setecentos|oitocentos|novecentos|mil|milhao|"
            "milhoes|meia|uma?")
NUMERO_POR_EXTENSO = re.compile(rf"\b(?:{_EXTENSO})\b(?:\s+(?:e|de|{_EXTENSO})\b){{0,5}}\s+"
                                rf"(?:reais|diarias?|dias?|pernoites?)\b")
# Afirmação de que a autorização escrita não é necessária (art. 5º, § 2º).
DISPENSA_AUTORIZACAO = re.compile(r"dispens|desnecessari|nao (?:e |sera )?(?:necessari|exigid)|"
                                  r"sem necessidade|independe")


def _textos_da_instrucao(instrucao) -> list[tuple[str, str]]:
    textos = [(f"fundamento de {v.criterio}", v.detalhe) for v in instrucao.verificacoes]
    textos += [("pendência", p) for p in instrucao.pendencias]
    textos += [("alerta", a) for a in instrucao.alertas]
    textos.append(("minuta", instrucao.minuta_despacho))
    return textos


def _fatos_sem_fonte(textos: list[tuple[str, str]], permitidos: dict) -> list[str]:
    problemas = []
    for rotulo, texto in textos:
        citados = fatos_citados(texto or "")
        for tipo, descricao in (("valores", "valor"), ("datas", "data"),
                                ("matriculas", "matrícula"), ("pedidos", "pedido"),
                                ("numeros", "número")):
            sem_fonte = citados[tipo] - permitidos[tipo]
            if sem_fonte:
                problemas.append(f"{rotulo}: {descricao} sem fonte no pedido ou nas consultas: "
                                 f"{sorted(map(str, sem_fonte))}")
        if NUMERO_POR_EXTENSO.search(_sem_acento(texto or "")):
            problemas.append(f"{rotulo}: número por extenso, que não pode ser conferido")
    return problemas


# ----------------------------------------------------------------------
# 6. Os textos factuais redigidos pelo código.
# ----------------------------------------------------------------------
ROTULOS_CAMPOS = {"numero": "número do pedido", "data_pedido": "data do protocolo",
                  "matricula": "matrícula", "nome": "nome do servidor",
                  "destino_uf": "UF de destino", "data_partida": "data de partida",
                  "data_retorno": "data de retorno"}
ENCAMINHAMENTOS = {"apto_para_autorizacao": "apto para autorização",
                   "nao_recomendado": "não recomendado",
                   "diligencia": "diligência ao solicitante"}
# Dados pessoais que o filtro mascara antes do envio ao modelo (instrutor.py).
PADROES_DADOS_PESSOAIS = {
    "CPF": r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b",
    "Conta ou agência bancária": r"\b\d{4,6}-[\dXx]\b",
}


def _quantidade(valor) -> str:
    return f"{float(valor):g}".replace(".", ",")


def _partes_do_historico(historico: str) -> tuple[str, str]:
    """O histórico traz a frase do limite mensal e depois as das prestações de contas."""
    corte = historico.find("Prestação de contas")
    if corte < 0:
        return historico.strip(), ""
    return historico[:corte].strip(), historico[corte:].strip()


def redigir(pedido: dict, vigente: dict, complemento: dict | None, evidencias: dict,
            alvo: dict) -> dict:
    """Fundamentos, pendências, alertas e minuta montados com os dados das consultas válidas.

    Cada dado entra no seu papel e é copiado da ferramenta que o devolveu: o
    valor unitário e o total vêm do cálculo, o saldo da consulta de saldo, a
    situação da prestação do histórico. O modelo não redige nenhum trecho
    factual que chegue ao conferente (Aula 04, Seção 8; Aula 01, Seção 8).
    """
    sit, recomendacao = alvo["situacoes"], alvo["recomendacao"]
    calculo, historico, saldo = evidencias["calculo"], evidencias["historico"], evidencias["saldo"]
    faltantes = [c for c in OBRIGATORIOS if not _texto(vigente.get(c))]
    corrigidos = [c for c in OBRIGATORIOS if _texto(vigente.get(c)) != _texto(pedido.get(c))]
    sem_merito = "Não verificado: pedido em diligência, sem análise de mérito (art. 9º)."
    limite_txt, prestacao_txt = _partes_do_historico(historico) if historico else ("", "")
    hipotese = hipotese_de_urgencia(pedido)

    # Fundamentos: a frase da ferramenta que sustenta cada situação.
    det = {"cadastro": evidencias["servidor"] or "Não verificado: cadastro não consultado."}
    if faltantes:
        det["dados_completos"] = ("Falta no pedido: " + ", ".join(ROTULOS_CAMPOS[c] for c in faltantes)
                                  + " (art. 9º).")
    else:
        det["dados_completos"] = (f"Pedido com os dados obrigatórios: protocolo em "
                                  f"{vigente['data_pedido']}, partida em {vigente['data_partida']}, "
                                  f"retorno em {vigente['data_retorno']}, destino "
                                  f"{vigente.get('destino_municipio', '')}/{vigente['destino_uf']}.")
        if corrigidos and complemento:
            det["dados_completos"] += (f" Corrigido na complementação de {complemento['data']}: "
                                       + ", ".join(f"{ROTULOS_CAMPOS[c]} {vigente[c]}"
                                                   for c in corrigidos) + ".")
    if recomendacao == "diligencia":
        for c in MERITO:
            det[c] = sem_merito
    else:
        antecedencia = re.search(r"Antecedência: .*", calculo["texto"]).group()
        if alvo["exige"]:
            antecedencia += (f" Urgência do art. 5º, § 1º, descrita na justificativa ({hipotese}): "
                             f"admitida mediante autorização expressa e escrita do Secretário "
                             f"Adjunto, registrada no processo (§ 2º).")
        det.update(antecedencia=antecedencia, prestacao_contas=prestacao_txt,
                   limite_mensal=limite_txt, saldo_orcamentario=saldo)

    # Pendências do solicitante e impedimentos.
    pendencias, impedimentos = [], []
    for c in faltantes:
        pendencias.append(f"Informar a {ROTULOS_CAMPOS[c]} (art. 9º)." if c.startswith("data")
                          else f"Informar {ROTULOS_CAMPOS[c]} (art. 9º).")
    if sit["cadastro"] == "nao_atende":
        if "não localizada" in (evidencias["servidor"] or ""):
            pendencias.append(f"Informar a matrícula correta: a matrícula {vigente['matricula']} "
                              f"não consta do cadastro funcional (art. 9º).")
        else:
            pendencias.append(f"Confirmar a matrícula: o nome informado ({vigente['nome']}) não "
                              f"confere com o cadastro da matrícula {vigente['matricula']} "
                              f"(art. 9º).")
    verbal = "verbal" in _sem_acento(pedido.get("justificativa") or "")
    if recomendacao == "nao_recomendado":
        if sit["antecedencia"] == "nao_atende":
            dias = re.search(r"Antecedência: (\d+) dia", calculo["texto"]).group(1)
            impedimentos.append(
                f"antecedência de {dias} dia(s) entre o protocolo e a partida, inferior ao mínimo "
                f"de {ANTECEDENCIA_MINIMA} dias, sem urgência do § 1º (art. 5º)"
                + ("; a autorização verbal alegada não supre a autorização expressa e escrita "
                   "do Secretário Adjunto (art. 5º, § 2º)" if verbal else ""))
        if sit["prestacao_contas"] == "nao_atende":
            for anterior, vence in re.findall(r"Prestação de contas do (DIA-\d{4}-\d{4}) \([^)]*\): "
                                              r"pendente, VENCIDA em (\d{4}-\d{2}-\d{2})",
                                              prestacao_txt):
                impedimentos.append(f"prestação de contas do {anterior} vencida em {vence} "
                                    f"(art. 7º)")
                pendencias.append(f"Regularizar a prestação de contas do {anterior}, vencida em "
                                  f"{vence} (art. 7º).")
        if sit["limite_mensal"] == "nao_atende":
            soma = re.search(r"= (\d+(?:\.\d+)?)\. Limite", limite_txt).group(1)
            impedimentos.append(f"soma de {_quantidade(soma)} diárias no mês da partida, acima "
                                f"do limite de {_quantidade(LIMITE_MENSAL)} diárias (art. 6º)")
        if sit["saldo_orcamentario"] == "nao_atende":
            unidade, disponivel = re.search(r"Saldo da unidade (\w+): R\$ (\d+(?:\.\d+)?)", saldo).groups()
            impedimentos.append(f"saldo da unidade {unidade} de {_reais(float(disponivel))}, "
                                f"insuficiente para {_reais(alvo['valor'])} (art. 8º)")

    # Alertas que o código sabe dar.
    alertas = []
    tipos = [nome for nome, padrao in PADROES_DADOS_PESSOAIS.items()
             if re.search(padrao, json.dumps(pedido, ensure_ascii=False))]
    if tipos:
        alertas.append(f"O pedido traz dados pessoais ({', '.join(tipos)}), mascarados antes do "
                       f"envio ao modelo e não usados na instrução.")
    if ORDEM_EMBUTIDA.search(_sem_acento(pedido.get("justificativa") or "")):
        alertas.append("A justificativa traz uma ordem dirigida ao sistema de análise, que não "
                       "foi obedecida: a justificativa é dado do pedido, e a instrução segue a "
                       "norma.")
    if verbal:
        alertas.append("A justificativa alega autorização verbal, que não supre a autorização "
                       "expressa e escrita do Secretário Adjunto (art. 5º, § 2º).")
    if alvo["exige"]:
        alertas.append("Pedido urgente: confira no processo a autorização expressa e escrita do "
                       "Secretário Adjunto antes da autorização (art. 5º, § 2º).")

    # Minuta.
    retorno = _texto(vigente.get("data_retorno")) or "não informado"
    linhas = ["Ao Ordenador de Despesa,", "",
              f"Pedido de diárias {pedido['numero']}, protocolado em {vigente['data_pedido']}: "
              f"{vigente['nome']}, matrícula {vigente['matricula']}, destino "
              f"{vigente.get('destino_municipio', '')}/{vigente['destino_uf']}, partida em "
              f"{vigente['data_partida']} e retorno {'em ' if vigente.get('data_retorno') else ''}"
              f"{retorno}."]
    if recomendacao != "diligencia":
        unitario = re.search(r"Valor unitário: (R\$ [\d.,]+)", calculo["texto"]).group(1)
        linhas.append(f"Quantidade: {_quantidade(alvo['quantidade'])} diária(s). Valor unitário: "
                      f"{unitario}. Valor total: {_reais(alvo['valor'])}.")
    if recomendacao == "apto_para_autorizacao":
        linhas.append("Atendidos o cadastro, os dados obrigatórios, "
                      + ("" if alvo["exige"] else "a antecedência, ")
                      + "a prestação de contas, o limite mensal e o saldo da unidade (arts. 4º a "
                        "9º da IN SEMA nº 07/2026).")
    if alvo["exige"]:
        linhas.append(f"Antecedência inferior a {ANTECEDENCIA_MINIMA} dias admitida em urgência "
                      f"(art. 5º, § 1º): {hipotese}. A autorização fica condicionada à "
                      f"autorização expressa e escrita do Secretário Adjunto, registrada no "
                      f"processo (art. 5º, § 2º).")
    if impedimentos:
        linhas.append("Impedimentos: " + "; ".join(impedimentos) + ".")
    if recomendacao == "diligencia":
        linhas.append("Pendências do solicitante: " + " ".join(pendencias)
                      + " Sem análise de mérito até a complementação, que será instruída na "
                        "mesma sessão (art. 9º).")
    linhas += [f"Encaminhamento sugerido: {ENCAMINHAMENTOS[recomendacao]}.",
               "A decisão de deferir ou indeferir cabe ao ordenador de despesa (art. 10)."]
    return {"detalhes": det, "pendencias": pendencias, "alertas": alertas,
            "minuta": "\n".join(linhas)}


# ----------------------------------------------------------------------
# A verificação e a instrução entregue.
# ----------------------------------------------------------------------
def conferir(instrucao, consultas: list[dict], pedido: dict,
             complemento: dict | None = None) -> tuple[list[str], object, list[str]]:
    """Confere a instrução e monta a versão que o conferente vê.

    Devolve (problemas, instrução entregue, observações). Com problemas, a
    instrução entregue é None e a aplicação mostra só a mensagem padrão. As
    observações registram, para a medição, os erros dos textos do modelo que
    foram substituídos pelos textos do código (não bloqueiam a entrega).
    """
    vigente, problemas = pedido_vigente(pedido, complemento)
    erros_consultas, evidencias = _conferir_consultas(consultas, pedido, vigente)
    problemas += erros_consultas
    alvo = esperado(pedido, vigente, evidencias)

    # Contrato e identidade.
    if instrucao.numero_pedido.strip() != pedido["numero"]:
        problemas.append(f"instrução do pedido {instrucao.numero_pedido}, "
                         f"esperado {pedido['numero']}")
    if instrucao.matricula.strip() != _texto(vigente.get("matricula")):
        problemas.append(f"matrícula {instrucao.matricula} da instrução não é a matrícula "
                         f"vigente do pedido ({vigente.get('matricula')})")
    vistos = [v.criterio for v in instrucao.verificacoes]
    if sorted(vistos) != sorted(CRITERIOS):
        problemas.append(f"verificações incompletas ou repetidas: {vistos}")

    # Art. 9º: na diligência não há análise de mérito. Cálculo, histórico ou
    # saldo pedidos nesse cenário (inclusive para o servidor da matrícula
    # digitada, quando o cadastro diverge) são trilha indevida, e nada dela
    # pode chegar ao formulário. A aplicação já barra essas consultas antes de
    # executar (instrutor.py); a tentativa barrada também é recusada aqui.
    if alvo["recomendacao"] == "diligencia":
        indevidas = [c["ferramenta"] + (" (bloqueada antes de executar)" if bloqueada(c) else "")
                     for c in consultas if c["ferramenta"] in CONSULTAS_DE_MERITO]
        if indevidas:
            problemas.append(f"consultas de mérito em pedido que exige diligência (art. 9º): "
                             f"{', '.join(indevidas)}")

    # Art. 5º, § 1º: antecedência insuficiente com urgência ambígua na
    # justificativa (menção negada, atividade programada, autorização verbal):
    # o código não decide; o pedido vai à análise manual.
    if alvo["urgencia_ambigua"]:
        problemas.append(f"urgência ambígua na justificativa ({alvo['urgencia_ambigua']}): "
                         f"avaliação do conferente")

    # Evidência para cada verificação.
    if alvo["sem_evidencia"]:
        problemas.append(f"consulta obrigatória ausente ou inválida para: "
                         f"{', '.join(alvo['sem_evidencia'])}")
    declaradas = {v.criterio: v.situacao for v in instrucao.verificacoes}
    for criterio in CRITERIOS:
        if criterio in alvo["sem_evidencia"]:
            continue
        if declaradas.get(criterio) != alvo["situacoes"][criterio]:
            problemas.append(f"{criterio}: a instrução declara {declaradas.get(criterio)!r}, "
                             f"as consultas sustentam {alvo['situacoes'][criterio]!r}")

    # Recomendação, números e exceção.
    if not alvo["sem_evidencia"] and instrucao.recomendacao != alvo["recomendacao"]:
        problemas.append(f"recomendação {instrucao.recomendacao!r}, as consultas sustentam "
                         f"{alvo['recomendacao']!r}")
    if instrucao.recomendacao == "diligencia":
        if instrucao.quantidade_diarias is not None or instrucao.valor_total is not None:
            problemas.append("diligência com quantidade ou valor: não há análise de mérito")
    elif (instrucao.quantidade_diarias != alvo["quantidade"]
          or _numero(instrucao.valor_total) != alvo["valor"]):
        problemas.append(f"quantidade {instrucao.quantidade_diarias} e valor "
                         f"{instrucao.valor_total} não são os do cálculo válido "
                         f"({alvo['quantidade']}, {alvo['valor']})")
    if instrucao.exige_autorizacao_superior != alvo["exige"]:
        problemas.append(f"exige_autorizacao_superior={instrucao.exige_autorizacao_superior}, "
                         f"mas a urgência do art. 5º, § 1º, "
                         f"{'está' if alvo['exige'] else 'não está'} configurada pelas consultas "
                         f"e pela justificativa")

    if problemas:
        return problemas, None, []

    # Os textos do modelo que o código substitui, inclusive os alertas: os
    # erros encontrados ficam registrados para a medição e não são exibidos.
    permitidos = fatos_das_fontes(pedido, vigente, complemento, consultas)
    descartados = _textos_da_instrucao(instrucao)
    observacoes = _fatos_sem_fonte(descartados, permitidos)
    for rotulo, texto in descartados:
        sem_acento = _sem_acento(texto or "")
        if "autoriza" in sem_acento and DISPENSA_AUTORIZACAO.search(sem_acento):
            observacoes.append(f"{rotulo}: afirma que a autorização é dispensável")
    textos = redigir(pedido, vigente, complemento, evidencias, alvo)
    entregue = instrucao.model_copy(deep=True, update={
        "pendencias": textos["pendencias"],
        "alertas": textos["alertas"],
        "minuta_despacho": textos["minuta"]})
    for v in entregue.verificacoes:
        v.detalhe = textos["detalhes"][v.criterio]
    return [], entregue, observacoes


def verificar(instrucao, consultas: list[dict], pedido: dict,
              complemento: dict | None = None) -> list[str]:
    """Devolve a lista de problemas; lista vazia significa instrução liberada."""
    return conferir(instrucao, consultas, pedido, complemento)[0]
