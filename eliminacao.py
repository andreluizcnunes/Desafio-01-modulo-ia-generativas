"""Rotina de eliminação dos dados do servidor guardados pelo agente (Etapa 4).

LGPD, art. 18: o titular tem direito à eliminação dos seus dados. A Aula 07,
Seção 6.2, mostrou que a eliminação no Agno exige etapas em objetos diferentes,
e que só a conferência direta no banco prova que nada restou. O DIA-2026-0112
acrescenta um caso que a busca pelo identificador não alcança: a matrícula
digitada pertence a outro servidor, a sessão fica gravada sob o `user_id`
dele, e a busca pelo `user_id` da titular não a encontra. Por isso a rotina
procura também pela matrícula e pelo nome do titular em todas as tabelas.

Etapas da rotina:
1. Sessões do titular: as que têm o `user_id` dele e as que mencionam a
   matrícula ou o nome sob outro identificador. `delete_sessions` leva junto
   as execuções (tabela de runs).
2. Memórias do usuário: lista com `get_user_memories` e apaga com
   `delete_user_memories`, que recebe os identificadores das memórias e não o
   usuário (Aula 07, 6.2), inclusive memórias gravadas sob outro `user_id` que
   mencionem o titular.
3. Conferência tabela por tabela: procura a matrícula e o nome em cada linha
   de cada tabela, como o `ocorrencias_do_titular` da Aula 07.

Alcance: esta rotina apaga somente o banco do agente, que é cópia de
trabalho. O processo de diárias é registro de despesa pública, sujeito à
transparência e à guarda das normas de prestação de contas, e não é tocado.

Execução do teste: python eliminacao.py
Saída: resultados/eliminacao.txt
"""
import json
import pathlib
import sqlite3
import warnings

warnings.filterwarnings("ignore")

from agno.db.sqlite import SqliteDb

BASE = pathlib.Path(__file__).parent


def ocorrencias(banco: pathlib.Path, termos: list[str]) -> dict:
    """Conta, em cada tabela, as linhas que contêm algum dos termos."""
    if not banco.exists():
        return {}
    conexao = sqlite3.connect(banco)
    encontrado = {}
    for (tabela,) in conexao.execute("SELECT name FROM sqlite_master WHERE type='table'"):
        try:
            linhas = conexao.execute(f"SELECT * FROM {tabela}").fetchall()
        except sqlite3.Error:
            continue
        total = sum(1 for linha in linhas if any(t in str(linha) for t in termos))
        if total:
            encontrado[tabela] = total
    conexao.close()
    return encontrado


def _sessoes_que_mencionam(banco: pathlib.Path, termos: list[str]) -> set:
    """Sessões cujo registro menciona o titular, sob qualquer `user_id`."""
    conexao = sqlite3.connect(banco)
    ids = set()
    tabelas = {t for (t,) in conexao.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    for tabela in tabelas:
        colunas = [c[1] for c in conexao.execute(f"PRAGMA table_info({tabela})")]
        if "session_id" not in colunas:
            continue
        for linha in conexao.execute(f"SELECT * FROM {tabela}"):
            if any(t in str(linha) for t in termos):
                ids.add(linha[colunas.index("session_id")])
    conexao.close()
    return ids


def eliminar_titular(banco: pathlib.Path, matricula: str, nome: str) -> dict:
    """Apaga sessões, execuções e memórias do titular e confere o banco."""
    termos = [matricula, nome]
    relatorio = {"titular": f"{nome} ({matricula})", "antes": ocorrencias(banco, termos)}
    db = SqliteDb(db_file=str(banco))

    # Etapa 1 — sessões (e, em cascata, as execuções).
    proprias = {s.session_id for s in (db.get_sessions(user_id=matricula) or [])}
    mencionam = _sessoes_que_mencionam(banco, termos)
    sessoes = sorted(proprias | mencionam)
    if sessoes:
        db.delete_sessions(session_ids=sessoes)
    relatorio["etapa1_sessoes_apagadas"] = {"pelo_user_id": sorted(proprias),
                                            "por_mencao_sob_outro_user_id": sorted(mencionam - proprias)}
    relatorio["apos_etapa1"] = ocorrencias(banco, termos)

    # Etapa 2 — memórias do usuário: listar para apagar.
    memorias = list(db.get_user_memories(user_id=matricula) or [])
    memorias += [m for m in (db.get_user_memories() or [])
                 if m.user_id != matricula and any(t in str(m.memory) for t in termos)]
    ids = [m.memory_id for m in memorias if m.memory_id]
    if ids:
        db.delete_user_memories(memory_ids=ids)
    relatorio["etapa2_memorias_apagadas"] = [str(m.memory)[:80] for m in memorias]

    # Etapa 3 — conferência tabela por tabela.
    relatorio["depois"] = ocorrencias(banco, termos)
    relatorio["nada_restou"] = not relatorio["depois"]
    return relatorio


# ----------------------------------------------------------------------
# Teste com as duas servidoras que passaram por diligência.
# ----------------------------------------------------------------------
def main() -> None:
    from instrutor import apagar_banco, construir_agente, instruir

    pedidos = {p["numero"]: p for p in json.loads((BASE / "dados" / "pedidos.json").read_text("utf-8"))}
    complementos = json.loads((BASE / "dados" / "complementacoes.json").read_text("utf-8"))
    banco = BASE / "resultados" / "eliminacao_teste.db"
    apagar_banco(banco)
    saida: list[str] = []

    def log(texto: str = "") -> None:
        print(texto)
        saida.append(texto)

    # Memórias do usuário ligadas de propósito, para que a rotina tenha as três
    # tabelas a limpar (sessões, execuções e memórias), como na Aula 07, 6.1.
    agente = construir_agente(memoria="usuario", banco=banco)
    log("[1] Atendimentos gravados no banco do agente")
    instruir(pedidos["DIA-2026-0101"], agente)  # outra servidora: não pode ser apagada
    for c in complementos:
        instruir(pedidos[c["numero"]], agente)
        instruir(pedidos[c["numero"]], agente, complemento=c)
    for numero in ("DIA-2026-0101", "DIA-2026-0111", "DIA-2026-0112"):
        log(f"    sessão {numero} · user_id {pedidos[numero]['matricula']}")

    titulares = [("206689", "Beatriz Moraes Cunha"), ("207418", "Carla Regina Souza")]
    controle = ["204317", "Ana Paula Figueiredo"]

    log("\n[2] Busca só pelo user_id da titular (o caminho intuitivo)")
    db = SqliteDb(db_file=str(banco))
    for matricula, nome in titulares:
        achadas = [s.session_id for s in (db.get_sessions(user_id=matricula) or [])]
        log(f"    {nome} ({matricula}): sessões pelo user_id = {achadas or 'nenhuma'} · "
            f"mas o titular aparece em {ocorrencias(banco, [matricula, nome])}")

    log("\n[3] Rotina de eliminação completa")
    for matricula, nome in titulares:
        r = eliminar_titular(banco, matricula, nome)
        log(f"    titular: {r['titular']}")
        log(f"      antes            : {r['antes']}")
        log(f"      etapa 1 sessões  : {r['etapa1_sessoes_apagadas']}")
        log(f"      após a etapa 1   : {r['apos_etapa1'] or 'nenhuma tabela'}")
        log(f"      etapa 2 memórias : {len(r['etapa2_memorias_apagadas'])} apagada(s) "
            f"{r['etapa2_memorias_apagadas']}")
        log(f"      depois (tabela por tabela): {r['depois'] or 'nenhuma tabela'} · "
            f"nada restou: {'SIM' if r['nada_restou'] else 'NÃO'}")
        assert r["nada_restou"], r

    restante = ocorrencias(banco, controle)
    log(f"\n[4] Controle: a outra servidora (Ana Paula, 204317) continua no banco? "
        f"{'sim' if restante else 'NÃO'} {restante}")
    assert restante, "a rotina apagou dados de quem não pediu"

    (BASE / "resultados" / "eliminacao.txt").write_text("\n".join(saida) + "\n", encoding="utf-8")
    apagar_banco(banco)


if __name__ == "__main__":
    main()
