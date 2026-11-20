"""Testa as quatro ferramentas sem agente e sem chave de API (Etapa 2).

Um erro dentro da função aparece depois como resposta estranha do agente,
difícil de localizar (Aula 06, Seção 3.2). Por isso cada ferramenta é chamada
aqui com casos tirados dos próprios pedidos, e cada resultado é conferido com
`assert` contra o valor que a norma determina. A saída é gravada em
resultados/teste_ferramentas.txt como evidência de que as contas estão certas
antes de o modelo entrar.

Execução: python teste_ferramentas.py
"""
import pathlib

from ferramentas import (FERRAMENTAS, SERVIDORES, calcular_diarias, consultar_historico_diarias,
                         consultar_saldo_diarias, consultar_servidor)

SAIDA = pathlib.Path(__file__).parent / "resultados" / "teste_ferramentas.txt"
linhas: list[str] = []


def registrar(titulo: str, resultado: str) -> str:
    linhas.append(f"\n[{titulo}]\n  {resultado}")
    return resultado


def main() -> None:
    linhas.append("Ferramentas e a primeira linha da docstring de cada uma:")
    for funcao in FERRAMENTAS:
        linhas.append(f"  {funcao.__name__:30} {funcao.__doc__.splitlines()[0]}")

    # DIA-2026-0112 — matrícula de outro servidor, por troca de dois algarismos.
    r = registrar("DIA-2026-0112 · matrícula digitada 207481",
                  consultar_servidor("207481", "Carla Regina Souza"))
    assert "Rafael Lima Antunes" in r and "DIVERGE" in r
    r = registrar("DIA-2026-0112 · matrícula corrigida 207418 (complementação)",
                  consultar_servidor("207418", "Carla Regina Souza"))
    assert "CONFERE" in r and "Grupo da diária: C" in r and "Unidade de lotação: CUC" in r
    r = registrar("Complementação DIA-2026-0112 · cálculo com o grupo C de Carla",
                  calcular_diarias("C", "MT", "2026-10-09", "2026-11-24", "2026-11-27"))
    assert "Quantidade: 3.5" in r and "= 770.00" in r

    # DIA-2026-0108 — prestação de contas vencida.
    r = registrar("DIA-2026-0108 · prestação do DIA-2026-0023",
                  consultar_historico_diarias("203648", "2026-11-03", 3.5))
    assert "VENCIDA em 2026-09-25" in r

    # DIA-2026-0102 — pendente, mas ainda no prazo.
    r = registrar("DIA-2026-0102 · prestação do DIA-2026-0041",
                  consultar_historico_diarias("205882", "2026-11-09", 3.5))
    assert "NO PRAZO até 2026-10-13" in r and "VENCIDA" not in r

    # DIA-2026-0103 — ida e volta no mesmo dia: meia diária.
    r = registrar("DIA-2026-0103 · meia diária",
                  calcular_diarias("B", "MT", "2026-10-07", "2026-11-05", "2026-11-05"))
    assert "Quantidade: 0.5" in r and "= 140.00" in r and "ATENDE o mínimo" in r

    # DIA-2026-0104 — Distrito Federal, grupo A.
    r = registrar("DIA-2026-0104 · Distrito Federal",
                  calcular_diarias("A", "DF", "2026-10-06", "2026-11-16", "2026-11-18"))
    assert "Quantidade: 2.5" in r and "= 1500.00" in r

    # DIA-2026-0105 — antecedência de 5 dias.
    r = registrar("DIA-2026-0105 · antecedência insuficiente",
                  calcular_diarias("B", "MT", "2026-10-08", "2026-10-13", "2026-10-15"))
    assert "Antecedência: 5 dia(s)" in r and "NÃO ATENDE" in r

    # DIA-2026-0109 — limite mensal: 8 já concedidas em novembro + 3,5.
    r = registrar("DIA-2026-0109 · limite mensal",
                  consultar_historico_diarias("208114", "2026-11-23", 3.5))
    assert "= 11.5" in r and "EXCEDE" in r

    # DIA-2026-0110 — outra UF e saldo insuficiente.
    r = registrar("DIA-2026-0110 · cálculo para outra UF",
                  calcular_diarias("B", "RO", "2026-10-02", "2026-11-10", "2026-11-14"))
    assert "Quantidade: 4.5" in r and "= 1800.00" in r and "outra unidade" in r
    r = registrar("DIA-2026-0110 · saldo da CRH",
                  consultar_saldo_diarias("CRH", 1800.0))
    assert "INSUFICIENTE" in r

    # DIA-2026-0111 — data de retorno ausente: a ferramenta recusa calcular.
    r = registrar("DIA-2026-0111 · retorno ausente",
                  calcular_diarias("B", "MT", "2026-10-09", "2026-11-17", ""))
    assert "não é possível calcular" in r

    # Minimização: nenhum CPF nem e-mail sai do cadastro, para os 40 servidores.
    for matricula, servidor in SERVIDORES.items():
        r = consultar_servidor(matricula, servidor["nome"])
        assert servidor["cpf"] not in r and servidor["email"] not in r and "@" not in r
    linhas.append(f"\n[Minimização] {len(SERVIDORES)} servidores consultados: "
                  f"nenhum CPF nem e-mail devolvido ao modelo.")

    linhas.append("\nTodas as verificações passaram.")
    texto = "\n".join(linhas)
    print(texto)
    SAIDA.parent.mkdir(exist_ok=True)
    SAIDA.write_text(texto + "\n", encoding="utf-8")
    print(f"\nEvidência gravada em {SAIDA.relative_to(SAIDA.parents[1])}")


if __name__ == "__main__":
    main()
