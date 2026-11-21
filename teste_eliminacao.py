"""Teste local da rotina de eliminação, sem modelo e sem chave.

Monta um banco do agente em SQLite temporário com a própria API do Agno
(sessões, execuções e memórias) e confere os casos da auditoria:

1. A sessão do 0112 gravada sob a matrícula digitada (207481), com o nome da
   titular em minúsculas no pedido e numa memória, sem a matrícula correta.
   A rotina precisa encontrá-la e apagar sessão, execução e memória.
2. Matrícula parcial ("20") com nome fictício: nada pode ser apagado.
3. Matrícula válida com nome de outra pessoa: nada pode ser apagado.
4. Arquivo que não é o banco do agente: recusado.
5. Tabela que não pode ser lida: aparece como falha de verificação, e a rotina
   não declara que nada restou.

Em todos os casos, os registros de controle (Ana Paula, 204317, e Beatriz,
206689) continuam no banco.

Execução: python teste_eliminacao.py
Saída: resultados/teste_eliminacao.txt
"""
import json
import pathlib
import sqlite3
import tempfile
import warnings

warnings.filterwarnings("ignore")

from agno.db.schemas.memory import UserMemory
from agno.db.sqlite import SqliteDb
from agno.run.agent import RunInput, RunOutput
from agno.run.base import RunStatus
from agno.session import AgentSession

from eliminacao import eliminar_titular, ocorrencias
from instrutor import texto_do_pedido

BASE = pathlib.Path(__file__).parent
SAIDA = BASE / "resultados" / "teste_eliminacao.txt"
PEDIDOS = {p["numero"]: p for p in json.loads((BASE / "dados" / "pedidos.json").read_text("utf-8"))}
CONTROLES = [("204317", "Ana Paula Figueiredo"), ("206689", "Beatriz Moraes Cunha")]
linhas: list[str] = []


def log(texto: str = "") -> None:
    print(texto)
    linhas.append(texto)


def gravar(db: SqliteDb, pedido: dict, user_id: str, memoria: str | None = None) -> None:
    sessao = pedido["numero"]
    db.upsert_session(AgentSession(session_id=sessao, user_id=user_id, agent_id="instrutor"))
    db.upsert_run(RunOutput(run_id=f"run-{sessao}", agent_id="instrutor", session_id=sessao,
                            user_id=user_id, status=RunStatus.completed,
                            input=RunInput(input_content=texto_do_pedido(pedido)),
                            content=f"Instrução do pedido {sessao}."),
                  session_id=sessao, user_id=user_id)
    if memoria:
        db.upsert_user_memory(UserMemory(memory=memoria, user_id=user_id))


def montar_banco(banco: pathlib.Path) -> None:
    db = SqliteDb(db_file=str(banco))
    gravar(db, PEDIDOS["DIA-2026-0101"], "204317", "Ana Paula Figueiredo viaja a Sinop.")
    gravar(db, PEDIDOS["DIA-2026-0111"], "206689")
    # 0112 sob a matrícula digitada, com o nome em minúsculas e sem a matrícula correta.
    p112 = dict(PEDIDOS["DIA-2026-0112"], nome="carla regina souza")
    gravar(db, p112, "207481", "a servidora carla regina souza vai a Alta Floresta em novembro.")


def contagem(banco: pathlib.Path) -> dict:
    conexao = sqlite3.connect(banco)
    total = {t: conexao.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
             for (t,) in conexao.execute("SELECT name FROM sqlite_master WHERE type='table'")
             if t != "agno_schema_versions"}
    conexao.close()
    return total


def controles_intactos(banco: pathlib.Path) -> None:
    for matricula, nome in CONTROLES:
        achado, falhas = ocorrencias(banco, [matricula, nome])
        assert achado.get("agno_sessions") and achado.get("agno_runs"), (nome, achado, falhas)
    log(f"      controles intactos: {', '.join(n for _, n in CONTROLES)}")


def main() -> None:
    with tempfile.TemporaryDirectory() as pasta:
        banco = pathlib.Path(pasta) / "agente.db"
        montar_banco(banco)
        log(f"[0] Banco montado: {contagem(banco)}")

        log("\n[1] Carla (207418): sessão sob 207481, nome em minúsculas, sem a matrícula correta")
        achado, _ = ocorrencias(banco, ["207418", "Carla Regina Souza"])
        log(f"    antes, a busca normalizada encontra: {achado} (a linha da sessão só tem o user_id 207481)")
        assert achado == {"agno_runs": 1, "agno_memories": 1}, achado  # a sessão guarda só o user_id 207481
        r = eliminar_titular(banco, "207418", "Carla Regina Souza")
        log(f"    sessões apagadas: {r['etapa1_sessoes_apagadas']}")
        log(f"    memórias apagadas: {r['etapa2_memorias_apagadas']}")
        log(f"    depois: {r['depois'] or 'nenhuma tabela'} · falhas de verificação: "
            f"{r['falhas_de_verificacao'] or 'nenhuma'} · nada restou: {r['nada_restou']}")
        assert r["nada_restou"] and r["etapa1_sessoes_apagadas"]["por_mencao_sob_outro_user_id"] \
            == ["DIA-2026-0112"] and len(r["etapa2_memorias_apagadas"]) == 1, r
        log(f"    banco: {contagem(banco)}")
        controles_intactos(banco)

        for rotulo, matricula, nome in (
                ("[2] Matrícula parcial '20' com nome fictício", "20", "Fulano de Tal"),
                ("[3] Matrícula de Ana Paula com o nome de outra pessoa", "204317",
                 "Carla Regina Souza"),
                ("[3b] Matrícula inexistente", "999999", "Fulano de Tal")):
            antes = contagem(banco)
            r = eliminar_titular(banco, matricula, nome)
            log(f"\n{rotulo}")
            log(f"    recusada: {r['recusada']}")
            assert r["recusada"] and contagem(banco) == antes, r
            log(f"    nada apagado: {contagem(banco)}")
            controles_intactos(banco)

        log("\n[4] Arquivo que não é o banco do agente")
        r = eliminar_titular(BASE / "dados" / "pedidos.json", "206689", "Beatriz Moraes Cunha")
        log(f"    recusada: {r['recusada']}")
        assert r["recusada"]

        log("\n[5] Tabela que não pode ser lida")
        conexao = sqlite3.connect(banco)
        conexao.execute("CREATE TABLE anexo_corrompido (conteudo TEXT)")
        conexao.execute("INSERT INTO anexo_corrompido VALUES (CAST(X'FFFE' AS TEXT))")
        conexao.commit()
        conexao.close()
        r = eliminar_titular(banco, "206689", "Beatriz Moraes Cunha")
        log(f"    falhas de verificação: {r['falhas_de_verificacao']}")
        log(f"    nada restou: {r['nada_restou']}")
        assert r["falhas_de_verificacao"] and not r["nada_restou"], r
        controles_intactos_ana = ocorrencias(banco, list(CONTROLES[0]))[0]
        assert controles_intactos_ana.get("agno_sessions"), controles_intactos_ana
        log("      controle Ana Paula intacto")

    log("\nTodos os casos de eliminação passaram.")
    SAIDA.write_text("\n".join(linhas) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
