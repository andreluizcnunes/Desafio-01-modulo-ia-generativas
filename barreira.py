"""A barreira em código entre o agente e o conferente (Etapa 3).

"A barreira pertence ao código, e não ao prompt" (Aula 01, Seção 8). Uma
instrução no prompt é um pedido; esta verificação é uma garantia, e continua
valendo quando o modelo, a instrução ou as ferramentas mudarem (Aula 03, 6.3).

Ela confere o que o agente fez contra o que a aplicação tem em mãos:

1. Argumentos ancorados no pedido (enunciado, Etapa 3): toda matrícula
   consultada e toda data usada no cálculo constam do pedido ou da
   complementação. É a regra do `exigir_fundamento` da Aula 03, Seção 7,
   aplicada a matrícula e datas.
2. Argumentos ancorados nas ferramentas: grupo e unidade vêm do cadastro da
   matrícula consultada; quantidade e valor passados adiante vêm do cálculo.
3. Números da instrução ancorados (Aula 04, Seção 8, ancoragem numérica):
   quantidade e valor devolvidos ao conferente são exatamente os que o
   `calcular_diarias` produziu nesta execução, para o grupo do servidor cuja
   matrícula está na instrução, e o nome desse servidor confere com o pedido.
   É o que impede a instrução "calculada para o servidor errado".
4. Coerência mínima do contrato: número do pedido igual, e recomendação de
   aptidão só com os seis critérios atendidos.

Qualquer falha devolve a lista de problemas, e a aplicação mostra ao servidor
apenas a mensagem padrão (Aula 06, 5.3): nada do conteúdo recusado é exibido.
"""
import re

from ferramentas import SERVIDORES, _normalizar_nome

DATA = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
MATRICULA = re.compile(r"\b\d{6}\b")
CRITERIOS = {"cadastro", "dados_completos", "antecedencia", "prestacao_contas",
             "limite_mensal", "saldo_orcamentario"}


def permitidos(pedido: dict, complemento: dict | None) -> tuple[set, set]:
    """Matrículas e datas que constam do pedido ou da complementação."""
    matriculas = {str(pedido["matricula"]).strip()}
    datas = {str(pedido.get(c)) for c in ("data_pedido", "data_partida", "data_retorno")
             if pedido.get(c)}
    if complemento:
        matriculas |= set(MATRICULA.findall(complemento["texto"]))
        datas |= set(DATA.findall(complemento["texto"]))
    return matriculas, datas


def _calculos(consultas: list[dict]) -> list[dict]:
    """Quantidade e valor que o calcular_diarias efetivamente devolveu."""
    achados = []
    for c in consultas:
        if c["ferramenta"] != "calcular_diarias":
            continue
        q = re.search(r"Quantidade: ([\d.]+)", c["resultado"])
        v = re.search(r"Valor total: R\$ [\d.,]+ = ([\d.]+)\.", c["resultado"])
        if q and v:
            achados.append({"grupo": str(c["argumentos"].get("grupo", "")).strip().upper(),
                            "quantidade": float(q.group(1)), "valor": float(v.group(1))})
    return achados


def verificar(instrucao, consultas: list[dict], pedido: dict,
              complemento: dict | None = None) -> list[str]:
    """Devolve a lista de problemas; lista vazia significa instrução liberada."""
    problemas: list[str] = []
    matriculas_ok, datas_ok = permitidos(pedido, complemento)
    consultadas = {str(c["argumentos"].get("matricula", "")).strip()
                   for c in consultas if c["ferramenta"] == "consultar_servidor"}
    grupos = {SERVIDORES[m]["grupo_diaria"] for m in consultadas & matriculas_ok if m in SERVIDORES}
    unidades = {SERVIDORES[m]["unidade"] for m in consultadas & matriculas_ok if m in SERVIDORES}
    calculos = _calculos(consultas)

    # 1 e 2. Argumentos de cada consulta.
    for c in consultas:
        nome, args = c["ferramenta"], c["argumentos"]
        if "matricula" in args and str(args["matricula"]).strip() not in matriculas_ok:
            problemas.append(f"{nome}: matrícula {args['matricula']} não consta do pedido "
                             f"nem da complementação")
        for campo in ("data_pedido", "data_partida", "data_retorno"):
            if campo in args and str(args[campo]).strip() not in datas_ok:
                problemas.append(f"{nome}: {campo}={args[campo]!r} não consta do pedido "
                                 f"nem da complementação")
        if nome == "calcular_diarias":
            if str(args.get("grupo", "")).strip().upper() not in grupos:
                problemas.append(f"calcular_diarias: grupo {args.get('grupo')!r} não veio do "
                                 f"cadastro de uma matrícula do pedido")
            if str(args.get("destino_uf", "")).strip().upper() != str(pedido["destino_uf"]).upper():
                problemas.append(f"calcular_diarias: UF {args.get('destino_uf')!r} difere do pedido")
        if nome == "consultar_historico_diarias":
            if float(args.get("quantidade_pedida", -1)) not in {k["quantidade"] for k in calculos}:
                problemas.append(f"consultar_historico_diarias: quantidade "
                                 f"{args.get('quantidade_pedida')} não veio do cálculo")
        if nome == "consultar_saldo_diarias":
            if str(args.get("unidade", "")).strip().upper() not in unidades:
                problemas.append(f"consultar_saldo_diarias: unidade {args.get('unidade')!r} "
                                 f"não veio do cadastro")
            if round(float(args.get("valor", -1)), 2) not in {round(k["valor"], 2) for k in calculos}:
                problemas.append(f"consultar_saldo_diarias: valor {args.get('valor')} "
                                 f"não veio do cálculo")

    # 3. A instrução que chegaria ao conferente.
    if instrucao.numero_pedido.strip() != pedido["numero"]:
        problemas.append(f"instrução do pedido {instrucao.numero_pedido}, "
                         f"esperado {pedido['numero']}")
    matricula = instrucao.matricula.strip()
    if matricula not in matriculas_ok:
        problemas.append(f"matrícula {matricula} da instrução não consta do pedido "
                         f"nem da complementação")
    elif matricula not in consultadas:
        problemas.append(f"matrícula {matricula} da instrução não foi consultada no cadastro")

    tem_numeros = instrucao.quantidade_diarias is not None or instrucao.valor_total is not None
    if instrucao.recomendacao != "diligencia" and not tem_numeros:
        problemas.append("instrução de mérito sem quantidade e valor")
    if tem_numeros:
        servidor = SERVIDORES.get(matricula)
        if servidor is None:
            problemas.append(f"quantidade e valor para matrícula {matricula} sem cadastro")
        else:
            if _normalizar_nome(servidor["nome"]) != _normalizar_nome(pedido["nome"]):
                problemas.append(f"quantidade e valor calculados para {matricula}, cujo cadastro "
                                 f"não confere com o nome do pedido")
            ancorado = any(k["grupo"] == servidor["grupo_diaria"]
                           and k["quantidade"] == instrucao.quantidade_diarias
                           and round(k["valor"], 2) == round(instrucao.valor_total or -1, 2)
                           for k in calculos)
            if not ancorado:
                problemas.append(f"quantidade {instrucao.quantidade_diarias} e valor "
                                 f"{instrucao.valor_total} não foram produzidos pelo cálculo "
                                 f"para o grupo do servidor {matricula}")

    # 4. Coerência do contrato.
    vistos = {v.criterio for v in instrucao.verificacoes}
    if vistos != CRITERIOS:
        problemas.append(f"verificações incompletas: faltam {sorted(CRITERIOS - vistos)}")
    if instrucao.recomendacao == "apto_para_autorizacao" and any(
            v.situacao != "atende" for v in instrucao.verificacoes):
        problemas.append("recomendação de aptidão com critério não atendido ou não verificado")
    return problemas
