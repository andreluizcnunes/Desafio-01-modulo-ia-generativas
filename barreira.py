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
   pelo código, pelas hipóteses que a norma lista, e não pela marcação do
   modelo. Na urgência, a minuta precisa condicionar a autorização à
   autorização escrita do Secretário Adjunto (§ 2º).
5. Dados factuais dos textos. Valores, datas, matrículas, números de pedido,
   quantidades e prazos citados nos fundamentos, nas pendências, nos alertas e
   na minuta precisam constar do pedido, da complementação, das consultas
   desta execução ou das constantes da norma.

Qualquer falha devolve a lista de problemas, e a aplicação mostra ao servidor
apenas a mensagem padrão (Aula 06, 5.3): nada do conteúdo recusado é exibido.
"""
import json
import re
import unicodedata
from decimal import Decimal, InvalidOperation

from ferramentas import ANTECEDENCIA_MINIMA, LIMITE_MENSAL, PRAZO_PRESTACAO, SERVIDORES, _normalizar_nome

DATA_ISO = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
MATRICULA = re.compile(r"(?<![\d.,/-])\d{6}(?![\d.,/-]?\d)")
CAMPOS_DATA = ("data_pedido", "data_partida", "data_retorno")
OBRIGATORIOS = ("numero", "data_pedido", "matricula", "nome", "destino_uf", "data_partida",
                "data_retorno")
CRITERIOS = ("cadastro", "dados_completos", "antecedencia", "prestacao_contas",
             "limite_mensal", "saldo_orcamentario")
MERITO = ("antecedencia", "prestacao_contas", "limite_mensal", "saldo_orcamentario")
CONSULTAS_DE_MERITO = ("calcular_diarias", "consultar_historico_diarias", "consultar_saldo_diarias")

# Art. 5º, § 1º: as hipóteses de urgência que a norma lista. A leitura é
# conservadora: o código só reconhece as hipóteses listadas; qualquer outra
# alegação de urgência fica com a antecedência "não atende" e o conferente
# decide (desenho.md, Seção 8).
HIPOTESES_URGENCIA = ("incendio", "desastre ambiental", "infracao ambiental em curso",
                      "determinacao judicial")

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


def urgencia_legitima(pedido: dict) -> bool:
    """A justificativa descreve uma das hipóteses do art. 5º, § 1º?"""
    justificativa = _sem_acento(pedido.get("justificativa") or "")
    return any(h in justificativa for h in HIPOTESES_URGENCIA)


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
            "antecedencia_atende": "NÃO ATENDE" not in resultado}


def _conferir_consultas(consultas: list[dict], pedido: dict, vigente: dict) -> tuple[list, dict]:
    """Confere os argumentos de cada consulta e devolve as evidências válidas."""
    problemas: list[str] = []
    matricula = _texto(vigente.get("matricula"))
    servidor = SERVIDORES.get(matricula)
    evidencias: dict = {"servidor": None, "calculo": None, "historico": None, "saldo": None}

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
    urgente = urgencia_legitima(pedido)
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
                "valor": None, "exige": False, "sem_evidencia": []}
    sem_evidencia = [c for c in ("cadastro",) + MERITO if sit[c] == "nao_verificado"]
    recomendacao = "nao_recomendado" if "nao_atende" in sit.values() else "apto_para_autorizacao"
    exige = bool(calculo and not calculo["antecedencia_atende"] and urgente)
    return {"situacoes": sit, "recomendacao": recomendacao,
            "quantidade": calculo["quantidade"] if calculo else None,
            "valor": calculo["valor"] if calculo else None,
            "exige": exige, "sem_evidencia": sem_evidencia}


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


def _textos_da_instrucao(instrucao) -> list[tuple[str, str]]:
    textos = [(f"fundamento de {v.criterio}", v.detalhe) for v in instrucao.verificacoes]
    textos += [("pendência", p) for p in instrucao.pendencias]
    textos += [("alerta", a) for a in instrucao.alertas]
    textos.append(("minuta", instrucao.minuta_despacho))
    return textos


# ----------------------------------------------------------------------
# A verificação.
# ----------------------------------------------------------------------
def verificar(instrucao, consultas: list[dict], pedido: dict,
              complemento: dict | None = None) -> list[str]:
    """Devolve a lista de problemas; lista vazia significa instrução liberada."""
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
    # saldo feitos nesse cenário (inclusive para o servidor da matrícula
    # digitada, quando o cadastro diverge) são trilha indevida, e nada dela
    # pode chegar ao formulário.
    if alvo["recomendacao"] == "diligencia":
        indevidas = [c["ferramenta"] for c in consultas if c["ferramenta"] in CONSULTAS_DE_MERITO]
        if indevidas:
            problemas.append(f"consultas de mérito em pedido que exige diligência (art. 9º): "
                             f"{', '.join(indevidas)}")

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
    if alvo["exige"]:
        minuta = _sem_acento(instrucao.minuta_despacho)
        if not ("autoriza" in minuta and "escrita" in minuta):
            problemas.append("pedido urgente sem a condição da autorização escrita do "
                             "Secretário Adjunto na minuta (art. 5º, § 2º)")

    # Dados factuais dos textos.
    permitidos = fatos_das_fontes(pedido, vigente, complemento, consultas)
    for rotulo, texto in _textos_da_instrucao(instrucao):
        citados = fatos_citados(texto or "")
        for tipo, descricao in (("valores", "valor"), ("datas", "data"),
                                ("matriculas", "matrícula"), ("pedidos", "pedido"),
                                ("numeros", "número")):
            sem_fonte = citados[tipo] - permitidos[tipo]
            if sem_fonte:
                problemas.append(f"{rotulo}: {descricao} sem fonte no pedido ou nas consultas: "
                                 f"{sorted(map(str, sem_fonte))}")
    return problemas
