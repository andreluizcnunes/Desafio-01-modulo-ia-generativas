# Correções das revisões

## Reauditoria do B1 (base `519f1f9`): contrato de confirmação dos campos

**Caso reprovado.** «O retorno foi remarcado para 2026-11-20. Essa nova data foi
cancelada por causa de um compromisso anterior.» Nesse caso, a data cancelada
alimentou as quatro ferramentas e a minuta.

**Causa raiz.** A leitura falhava aberta. Quando uma ressalva não podia ser resolvida
com segurança, ela era **descartada**, e a data afirmada continuava valendo. No caso
reprovado, a palavra «anterior», que descrevia o compromisso, foi tomada como
referência ao valor substituído. O ramo correspondente descartava a ressalva porque o
campo vinha de uma remarcação. O mesmo defeito estrutural aparecia por outra via:
uma oração sobre a data com verbo fora do vocabulário («Essa nova data caiu.») era
tratada como neutra. O vocabulário decidia o que **invalidava** a data, e o que ele
não reconhecia deixava a data confirmada.

**Desenho da solução** (`barreira.ler_complementacao`, comentário do contrato):

1. **Contrato explícito.** Cada campo tocado termina CONFIRMADO, PENDENTE ou AMBÍGUO,
   com o valor vigente só no primeiro. `pedido_vigente` preenche o campo CONFIRMADO,
   esvazia o PENDENTE (diligência) e esvazia o AMBÍGUO e o registra como problema
   (análise manual). A guarda das ferramentas e a barreira usam esse pedido vigente,
   e o cálculo, o histórico e o saldo só executam com um campo CONFIRMADO.
2. **Complementação inteira.** O estado de cada campo só é lido depois de todas as
   orações. Uma oração posterior pode cancelar, substituir ou tornar ambíguo o que
   veio antes. AMBÍGUO não volta a CONFIRMADO pelo texto.
3. **Falha fechada.** Uma oração ligada ao campo (pelo rótulo, valor, expressão
   referencial, nome que abrange as datas ou elipse) que não seja atribuição,
   ressalva ou reafirmação reconhecida deixa o campo AMBÍGUO. O vocabulário só
   escolhe entre PENDENTE e CONFIRMADO, e o que ele não reconhece nunca confirma.
4. **Antecedentes, e não palavras.** Uma ressalva sem valor recai sobre os
   antecedentes do texto: os valores citados para o campo e o valor anterior que um
   verbo de substituição pressupõe. Com um antecedente, o campo fica PENDENTE; com
   mais de um, AMBÍGUO. A palavra «anterior» deixou de ter efeito. Uma ressalva com
   valor vale para aquele valor.
5. **Outro evento.** Uma oração sem vínculo com os campos («A reunião com a
   prefeitura foi cancelada», «O compromisso anterior foi desmarcado») não muda a data.
6. **Confirmação explícita do campo.** Para o que o texto livre não resolve, o
   formulário da complementação aceita o campo e o valor confirmados, enviados junto
   com o texto, no mesmo fluxo e na mesma sessão. O modelo recebe o campo na
   mensagem. O valor explícito não vale se o texto o cancelou, o deixou ambíguo ou
   confirmou outro.

| Critério de aceite | Evidência |
|---|---|
| O caso reprovado fica fora das ferramentas de mérito, dos fundamentos e da minuta | `teste_bloqueio.py`, parte 6, com o Agno real e as requisições interceptadas, nos dois modos: só `consultar_servidor` executa; as três funções de mérito são barradas; nem as mensagens nem o SQLite recebem dado de mérito; o resultado vai à análise manual, também com a resposta de diligência. `teste_app.py`, passos A3b e A3d: mensagem padrão na tela, com a resposta simulada e com o Agno interceptado. O comando de reprodução de `AUDITORIA_FINAL.md` mostra só a mensagem padrão, sem métricas nem minuta. |
| Regra geral, além dos exemplos conhecidos | `teste_complementacao.py`, parte 2: 9.072 complementações geradas (6 formas de atribuição × 14 formas de referência × 18 predicados, 8 deles fora do vocabulário do detector, × 6 complementos de frase, entre eles «por causa de um compromisso anterior»). Nenhuma termina com a data confirmada (3.600 pendentes, 5.472 ambíguas). A guarda barrou `calcular_diarias` com a data antes de executar nas 9.072. |
| Data afirmada e depois cancelada; remarcada e depois cancelada; referência indireta; negada ou condicional | `teste_complementacao.py`, parte 1, por categoria; `teste_bloqueio.py`, parte 6 (sete complementações, nos dois modos) |
| Substituição por outra data confirmada | `teste_complementacao.py`, partes 1 e 3: seis formas confirmam só a nova data, e a guarda aceita a nova e barra a antiga. `teste_bloqueio.py`, parte 6b: com o Agno real, as quatro consultas executam com 2026-11-21, e a instrução sai apta com 4,5 diárias e R$ 1.260,00, sem 2026-11-20 nos textos. Com 2026-11-20 nos argumentos, o cálculo é barrado. |
| Cancelamento de outro evento sem invalidar o retorno | `teste_complementacao.py`, parte 3: 1.944 complementações com outro evento cancelado, negado, condicionado ou com predicado fora do vocabulário mantêm o retorno confirmado. |
| Complementações oficiais | `teste_complementacao.py`, parte 1 (0111 e 0112); `teste_barreira.py`, parte 6; `teste_bloqueio.py`, partes 2 e 7 (acervo em seis rodadas roteirizadas, 42/42 por configuração); `teste_app.py`, passo A3. As complementações oficiais não mudam de leitura, e a mensagem ao modelo só ganha a linha da confirmação explícita quando ela é informada. |
| Confirmação explícita | `teste_complementacao.py`, parte 4; `teste_app.py`, passo A3c, pela tela: o texto sem confirmação, com o campo informado, resulta em apto. O campo explícito com a data que o texto deixou ambígua vai à análise manual. |

**Limites do reconhecimento textual.** A leitura é conservadora por construção. O que
ela não entende vai à diligência ou à análise manual, e não ao cálculo. O preço é
devolver alguns textos legítimos:

- «O retorno foi alterado para 2026-11-21. A data anterior foi cancelada.» fica
  AMBÍGUO, porque «a data» tem dois antecedentes possíveis. Citar o valor antigo («A
  data anterior, 2026-11-20, foi cancelada») ou usar a confirmação explícita resolve.
- «Essa nova data foi cancelada», depois de uma remarcação, vai à análise manual, e
  não à diligência: a leitura não usa «nova» para escolher o antecedente.
- Uma frase curta sem conteúdo reconhecível depois de uma data («Caiu.», «Obrigada.»)
  deixa a data AMBÍGUA.
- Uma oração que cita o campo sem ser atribuição, ressalva ou reafirmação reconhecida
  («Na volta, a servidora passará por Sinop») deixa o campo AMBÍGUO.
- Um cancelamento da «viagem» deixa todas as datas pendentes.
- Uma oração sobre outro evento que não cite o campo, uma data dele ou uma expressão
  referencial não muda a data. Uma ressalva sobre o campo escrita sem nenhum desses
  vínculos, com um sujeito que o detector não liga às datas, também não muda a data.
  É o limite que resta da leitura de texto livre, e por isso a conferência humana de
  toda instrução continua (`relatorio.md`, Seção 8).
- As medições reais (B2, versão `6f4d2fa`) não foram refeitas. As complementações
  oficiais têm a mesma leitura, e a mensagem ao modelo não muda para elas.

As evidências simuladas desta correção estão em `resultados/teste_complementacao.txt`,
`resultados/teste_bloqueio.txt`, `resultados/teste_barreira.txt` e
`resultados/etapa5_formulario_b1.txt` (parte A do formulário, sem o modelo real). O
`resultados/etapa5_formulario.txt` continua sendo a evidência real da versão `6f4d2fa`.

## Auditoria final (base `d2c4cf7`): bloqueadores B1 e B2

### B1 — Data cancelada na complementação

**Causa raiz.** Cada oração era lida isoladamente. Uma oração afirmativa
(«O retorno está previsto para 2026-11-20») virava candidata, e o cancelamento na
oração seguinte só a invalidava se repetisse o rótulo do campo ou a palavra "data".
Uma referência anafórica («Essa previsão foi cancelada», «Ela foi cancelada») não
alcançava a candidata. A guarda das ferramentas e a barreira conferem contra o mesmo
pedido vigente, e por isso as duas liberavam a data cancelada.

**Correção.** `barreira.ler_complementacao` lê as orações em ordem e mantém a situação
de cada campo: confirmada, substituída, cancelada, negada, condicional, indefinida ou
conflitante. Uma oração se liga a um campo pelo rótulo, pelo valor citado ou por
referência anafórica, que recai sobre os campos da última oração que tratou de algum
campo. Só a data confirmada e a substituída preenchem o campo. Sem substituição
confirmada, o campo fica pendente, e o pedido segue em diligência, com as consultas de
mérito barradas antes de executar. Uma ressalva que não se consegue atribuir a um
campo vai para a análise manual. Na diligência, a pendência diz que a complementação
deixou a data cancelada, negada, condicional ou indefinida (`desenho.md`, Seção 2).

| Critério de encerramento | Evidência |
|---|---|
| A data cancelada fica fora das consultas de mérito, dos fundamentos e da minuta | `teste_bloqueio.py`, parte 6: com o Agno real e as requisições ao modelo interceptadas, a frase do achado e mais três variantes (cancelada por anáfora, negada e condicional), nos dois modos. A aptidão com a data do texto é recusada. Só `consultar_servidor` executa, as três funções de mérito são barradas, e nem as mensagens ao modelo nem o SQLite recebem dado de mérito. A diligência é entregue sem a data nos fundamentos, nas pendências e na minuta. Com a `barreira.py` de `d2c4cf7`, o mesmo cenário executa as quatro funções. |
| Reprodução pela tela | `teste_app.py`, passo A3b, com a frase do achado. O comando de reprodução de `AUDITORIA_FINAL.md` agora mostra só a mensagem padrão, sem «Apto», 3,5 diárias ou R$ 980,00. Com a resposta de diligência, a tela mostra quantidade e valor nulos e a minuta com «retorno não informado». |
| Construções positivas e negativas | `teste_barreira.py`, parte 6: 41 construções com situação definida. Positivas: 7 confirmadas e 7 substituídas. Negativas: 11 canceladas, 2 negadas, 5 condicionais e 9 indefinidas. Somam-se uma data sem campo, duas ressalvas sem campo (análise manual), o cancelamento da partida original e o cancelamento da matrícula corrigida do 0112. |
| Complementações legítimas do 0111 e do 0112 | `teste_barreira.py`, parte 6; `teste_bloqueio.py`, parte 2 (mesma sessão, nos dois modos); `teste_app.py`, passo A3; e a medição real (B2). |

### B2 — Medições reais

**Diagnóstico da conexão.** A credencial não foi exibida. Neste ambiente, com a mesma
configuração, foram verificados quatro pontos:

- **Configuração:** `OPENAI_API_KEY` presente no `.env`, e nenhuma URL base ou variável
  de proxy definida.
- **Rede:** o DNS de `api.openai.com` resolveu.
- **Autenticação:** `GET /v1/models` respondeu 200 em 0,7 s.
- **Disponibilidade:** o `gpt-5.6-luna` constava da lista de modelos.

O `Connection error` da auditoria, com zero tokens, veio da rede do ambiente do
auditor. Nada foi alterado na configuração.

**Medições reais da versão candidata (`6f4d2fa`, 21/11/2026).** A versão inclui a
correção do B1. O cabeçalho de `medicao.md`, `memoria.md` e `falhas.md` registra a
versão executada. A medição anterior está em `resultados/historico/medicao_067e97b.md`.

| Medição | Resultado real | Evidência |
|---|---|---|
| 12 pedidos e duas complementações, 3 rodadas × 2 configurações | 42/42 e 42/42 (14/14 em cada rodada); 0 recusados, 0 erros, 0 entregues errados; nenhuma consulta barrada pela guarda | `resultados/medicao.md` |
| Tokens (desligadas / ligadas) | entrada 576.462 / 575.896; saída 24.065 / 23.828; E₁ médio 2.741; acumulado de 5 passos 14.690 | `resultados/medicao.md` |
| Tempo e custo (desligadas / ligadas) | 292,5 s / 295,5 s; US$ 0,14417 / 0,14377; mediana de US$ 0,00367 por pedido; US$ 1,74 por mês | `resultados/medicao.md`; `relatorio.md`, Seção 3 |
| Chamadas paralelas | 0 execuções com chamadas simultâneas nas duas configurações; no máximo 5 chamadas por item | `resultados/medicao.md` |
| Memória por turno, nas três configurações, para as duas complementações | A: 0/2 aplicadas; B: 2/2, com +504 / +532 tokens na 1ª chamada do turno; C: 2/2, custando 4% a 20% mais que B | `resultados/memoria.md` |
| Quatro falhas provocadas | (1) resistiu e alertou 6/6; (2) `status=error` e mensagem padrão; (3) fábrica deixa CPF e conta passarem, configurado mascara; (4) diligência nas 6, todas recusadas | `resultados/falhas.md` |
| Formulário com o modelo real | 0101 apto; 0111 diligência e apto após a complementação | `resultados/etapa5_formulario.txt`, parte B |
| Etapa 3, parte 3, e eliminação com o modelo real | sem CPF ou conta nas mensagens e no banco; nada restou das duas titulares, controle preservado | `resultados/etapa3_filtro_e_barreira.txt`; `resultados/eliminacao.txt` |

O confronto com o desenho e a justificativa da conferência humana estão no
`relatorio.md`, Seções 3 e 8. E₁ ficou 33% acima do estimado, a saída ficou igual ao
estimado e o custo mensal, 18% acima. Com 0 erros em 84, o limite superior de 95% de
erro ainda é de cerca de 3,6%. Por isso, a conferência de toda instrução continua.

**Resultados simulados, registrados à parte.** As respostas roteirizadas e o HTTP
interceptado (`teste_barreira.py`, `teste_bloqueio.py`, `teste_eliminacao.py` e
`teste_app.py`, parte A) verificam o código. Os números deles não entram nas medidas
acima.

**Impedimentos remanescentes.** Nenhum para B1 e B2. Os achados E1 e E2 da auditoria
não eram bloqueadores e ficaram fora do escopo desta correção. O log de eliminação
desta execução registra 0 memórias da Carla, e o relatório agora descreve isso
(Seção 6). O falso alerta de E2 continua sem correção.

## Quarta revisão (base `067e97b`)

| Falha | Causa estrutural | Correção e evidência |
|---|---|---|
| Retorno negado na complementação do 0111 usado como data confirmada | A mera presença de uma data podia preencher o campo ausente. | `pedido_vigente` aplica atribuições afirmativas e explícitas ao campo correspondente. Datas negadas, condicionais, indefinidas ou inválidas deixam o campo pendente. Atribuições incompatíveis seguem para análise manual. `teste_barreira.py` cobre os formatos e casos equivalentes. `teste_bloqueio.py` cobre as funções executadas e o SQLite. `teste_app.py` cobre a minuta e a diligência na tela. |
| Cadastro e histórico de outra matrícula e cálculo com retorno indevido executavam | O gancho verificava os pré-requisitos do mérito. Os argumentos de cada chamada só eram verificados na saída. | A mesma validação de argumentos serve ao gancho e à conferência final, cobrindo as quatro ferramentas. Histórico e saldo exigem resultados de um cálculo autorizado da mesma execução. Tentativas barradas ficam separadas das consultas executadas. `teste_bloqueio.py` cobre matrículas, nomes, datas, grupo, UF, quantidade, unidade e valor indevidos, com respostas diretas e eventos. |
| Uma menção descritiva a um sistema gerava alerta de ordem | O alerta e a leitura de urgência reagiam à presença de certas palavras. | `ordem_dirigida_ao_agente` reconhece instruções pelo destinatário e pelo conteúdo da oração, incluindo comandos de análise sem vocativo. O alerta e a urgência usam o mesmo detector. Há controles para o 0107, ordens equivalentes, referências descritivas e urgência legítima que cita um sistema de monitoramento. |

A verificação local com Agno, ferramentas reais, SQLite temporário e HTTP
interceptado cobriu os 12 pedidos e as duas complementações em três rodadas por
configuração, com 42/42 em cada uma. As quatro falhas também foram provocadas com
respostas e erros controlados. A evidência está em `resultados/teste_bloqueio.txt`. A revisão
também reexecutou os testes da barreira, das ferramentas, do filtro, da eliminação
e do formulário. A evidência atual do formulário está em
`resultados/etapa5_formulario_revisao4.txt`.

A tentativa de instrução no provedor terminou em erro de conexão neste ambiente.
As medições com o modelo real, incluindo as rodadas de `medir.py`, a memória e as
falhas que dependem do modelo, ficaram pendentes para esta revisão. Os números
históricos de tokens, tempo e custo permanecem identificados como da terceira
revisão. O transporte simulado só mede a compatibilidade funcional com o gabarito.
As regras de texto aceitam construções suportadas e encaminham ambiguidades para
confirmação. O detector de ordens tem cobertura linguística delimitada. O acervo
original, a cópia usada pela aplicação e o gabarito foram preservados.

Três revisões apontaram falhas. A primeira, da versão `8b61395`, em quatro frentes; a
segunda, da versão `0f67cf5`, em cinco; a terceira, da versão `fb61dd9`, em quatro. Este
arquivo registra cada critério de aceite, onde está a evidência e o que ficou
pendente. A revisão mais recente vem primeiro.

# Terceira revisão (versão fb61dd9)

Testes e medições executados em 21/11/2026.

## 1. Alertas contraditórios na tela e na medição

| Critério de aceite | Situação | Onde está a evidência |
|---|---|---|
| 0101 com o alerta «O valor total correto é R$ 280,00»: a afirmação fica fora da tela e a saída aceita só tem fatos corretos | executado | `teste_barreira.py`, caso "0101 com alerta: o valor unitário como total": entregue com os alertas do código, sem o do modelo; `teste_app.py`, passo A1c, pela tela |
| 0108 com o alerta «A prestação de contas foi regularizada»: fora da tela, prestação fundamentada no histórico | executado | caso "0108 com alerta sem número": entregue sem o alerta; o fundamento é a frase do histórico ("VENCIDA"); `teste_app.py`, passo A1c, confere "VENCIDA" na tabela de verificações |
| As duas saídas incorretas, entregues como vieram, são entrega divergente; a intervenção do código é registrada à parte | executado | parte 2b: `entregue_errado` pelos dois motivos, categoria ("alerta fora das categorias esperadas") e papel ("alerta: valor total 280.0 ≠ 980.0"; "alerta sobre prestacao_contas contradiz a situação com 'regularizada'"); os alertas do modelo ficam em `Resultado.alertas_do_modelo` e na medição (`alertas_do_modelo`) |
| Streamlit com os dois casos e com os alertas legítimos do enunciado | executado | `teste_app.py`, passo A1c: os dois alertas errados fora da tela; dados pessoais no 0104, ordem dirigida ao sistema e autorização verbal no 0107, autorização escrita a conferir no 0106 |

**O que mudou.** O conferente só vê alertas montados pelo código, pelas categorias que
o enunciado pede e que o código verifica no pedido (`barreira.redigir`): dados pessoais
mascarados, ordem dirigida ao sistema, autorização verbal e, na urgência, a autorização
escrita a conferir. Os alertas do modelo saem da tela e ficam registrados. A medição
passou a conferir os alertas por categoria (o gabarito traz as categorias esperadas,
definidas pelo enunciado), o valor rotulado e o que o alerta afirma sobre cada
critério.

## 2. Consultas de mérito bloqueadas antes de executar

| Critério de aceite | Situação | Onde está a evidência |
|---|---|---|
| 0112 inicial: o modelo tenta as três funções após DIVERGE; nenhuma executa, nenhum resultado de mérito entra nas mensagens ao modelo, no SQLite ou no formulário; a tentativa é registrada e recusada | executado | `teste_bloqueio.py` (Agno real, requisições ao modelo interceptadas localmente), parte 1, nos dois modos: funções executadas só `consultar_servidor`; as três barradas; mensagens interceptadas e banco temporário sem dado de mérito; resultado recusado; `teste_app.py`, passo A4b, pela tela |
| 0111 inicial: a falta do retorno também bloqueia; as diligências legítimas seguem, com quantidade e valor nulos | executado | `teste_bloqueio.py`, partes 1 e 2 |
| 0112 após a complementação, na mesma sessão, consulta o histórico com 207418; 0111 retoma o cálculo com o retorno informado; pedido regular com as quatro ferramentas | executado | `teste_bloqueio.py`, partes 2 e 3; a parte 3 é o controle da própria busca (o banco do 0101 tem as seis marcas de mérito) |
| Agente compartilhado pela tela isola cada execução | executado | `teste_bloqueio.py`, parte 4: o cadastro conferido do 0101 não libera o mérito do 0112 no mesmo agente |

**O que mudou.** Um gancho de ferramenta (`tool_hooks`, o equivalente no Agno do
`wrap_tool_call` da Aula 03, 4.2) decide antes de a função rodar: cálculo, histórico e
saldo só executam com o pedido vigente completo e o cadastro da matrícula vigente
CONFERE nesta execução. Barrada, a consulta devolve ao modelo só o motivo. O estado
fica preso ao identificador que `instruir` gera para cada execução. A barreira final
continua e recusa a tentativa barrada. Sem o gancho, o teste falha: as três funções
executam.

## 3. Contexto afirmativo para a exceção de urgência

| Critério de aceite | Situação | Onde está a evidência |
|---|---|---|
| «Incêndio.» e «O incêndio foi extinto. A viagem é para vistoria de rotina.», com as datas do 0106, ficam fora de aptidão automática mesmo com o modelo marcando apto; expectativas próprias, fora do gabarito | executado | `teste_barreira.py`, casos "variante do 0106 'Incêndio.'" e "'O incêndio foi extinto…'": recusados (urgência ambígua: menção isolada; ocorrência encerrada; finalidade de rotina); expectativa "análise manual" definida no teste; parte 2b: `entregue_errado`; parte 5 |
| 0106 original apto condicionado à autorização escrita; 0107 não recomendado, com o alerta da autorização verbal | executado | casos "0106 urgente correto" e "0107 correto"; `teste_app.py`, passo A1c; medição (`resultados/medicao.md`) |

**O que mudou.** `barreira.ler_urgencia` exige contexto afirmativo de situação
emergencial em curso na frase da menção e trata como sinal contrário a ocorrência
encerrada, o contexto passado e a finalidade de rotina (`desenho.md`, Seção 8).

## 4. Resultado sem identificador no fluxo do formulário

| Critério de aceite | Situação | Onde está a evidência |
|---|---|---|
| Identificador válido da execução atual e correspondência com o retorno e a sessão, na saída direta e na recuperada do banco | executado | `instrutor.instruir` gera o identificador e o entrega ao Agno; `teste_bloqueio.py` confirma, com o Agno real, que a resposta traz esse identificador nos dois modos |
| Caso sem evento inicial e com RunOutput sem run_id: mensagem padrão, sem a instrução | executado | `teste_barreira.py`, parte 3 ("resposta concluída sem run_id"), nos dois modos; `teste_app.py`, passo A4; na versão anterior, o mesmo caso era entregue |
| Controles: execução atual concluída, fluxo sem resposta, resultado anterior da mesma sessão, erro da API e complementação legítima | executado | `teste_barreira.py`, partes 3 e 3b; `teste_app.py`, passos A1, A3 e A4 |

## 5. Evidências da revisão

| Critério de aceite | Situação | Onde está a evidência |
|---|---|---|
| Testes locais de ferramentas, barreira, eliminação e formulário; bloqueio de mérito com as requisições do Agno interceptadas e o banco temporário inspecionado; ponto de execução das funções conferido | executado | `teste_ferramentas.py`, `teste_barreira.py` (50 casos, 14 falhas do fluxo, 4 controles do vínculo), `teste_eliminacao.py`, `teste_bloqueio.py`, `teste_app.py` parte A (`resultados/`) |
| `medir.py` e os testes do classificador nunca contam como acerto alertas incorretos nem consultas de mérito fora da etapa; gabarito independente; casos adicionais com expectativas próprias | executado | `medir.conferir` (alertas por categoria, valor rotulado, afirmação contra a situação; consultas fora da etapa); `gabarito.json` com `alertas`, definidos pelo enunciado; parte 2b: as 29 instruções erradas são `entregue_errado`, as 20 corretas são acerto; as variantes da urgência têm expectativa "análise manual" definida no teste |
| Três rodadas de 14 itens por configuração e as quatro falhas provocadas; acertos, recusas, erros, entregas divergentes, tokens, tempo e custo; execuções que dependem do modelo | executado | 84/84 acertos (42/42 em cada configuração), 0 recusados, 0 erros, 0 entregues errados; 565.104 e 576.004 tokens de entrada, 23.615 e 24.078 de saída; US$ 0,1414 e 0,1441; 313 s e 355 s (`resultados/medicao.md`); `resultados/falhas.md`; dependem do modelo e foram executados em 21/11: `medir.py`, `falhas.py`, `memoria.py`, `eliminacao.py`, `verificar_etapa3.py` (parte 3) e `teste_app.py` (parte B) |
| Medição anterior identificada pelo critério que aplicou | executado | `resultados/historico/medicao_fb61dd9.md` |
| `resultados/`, `CORRECOES.md`, `relatorio.md` e `LEIA-ME.md` atualizados; acervo e chave fora das alterações | executado | `dados/` sem alteração; só `.env.example` versionado |

## Pendências e limites da terceira revisão

- **Alertas só do código:** o conferente vê os alertas das categorias que o código sabe
  verificar. Um alerta útil do modelo fora delas fica só no registro. Na falha 1, a
  variante sutil do 0108 ("prestação já regularizada", sem dirigir-se ao sistema) foi
  alertada pelo modelo nas 3 execuções, mas esses alertas não vão mais à tela; o
  conferente vê "não recomendado" com a prestação VENCIDA no fundamento.
- **Urgência por palavras:** a leitura exige contexto afirmativo e recusa os sinais
  contrários conhecidos, mas continua sendo leitura de palavras. Uma justificativa que
  descreva, com essas palavras, uma emergência inexistente ainda abre a exceção; a
  autorização escrita e a leitura da justificativa ficam com o conferente.
- **Tentativa barrada recusa a instrução:** se o modelo tenta uma consulta de mérito
  numa diligência, a guarda impede a execução e a barreira recusa a instrução, mesmo que
  a diligência devolvida esteja correta. Nesta medição, isso não ocorreu (0 recusas).
- **Contagem corrigida:** o registro da segunda revisão dizia que o 0106 e o 0107 foram
  corretos em "12 de 12" execuções; eram 6 de 6 de cada (3 rodadas × 2 configurações).
- **Falha 4:** nesta execução, com a tabela, o modelo calculou e errou nas 3; sem a
  tabela, pediu diligência nas 3. A barreira recusou as 6.
- **Gabarito reconstruído e expurgo automático:** como nas revisões anteriores.

# Segunda revisão (versão 0f67cf5)

Testes e medições executados em 21/11/2026.

## 1. Fundamentação das instruções

| Critério de aceite | Situação | Onde está a evidência |
|---|---|---|
| 0101 com campos estruturados corretos e minuta com total de R$ 280,00: a saída exibida tem o total de R$ 980,00 ou vai à análise manual; a versão incorreta nunca conta como acerto | executado | `teste_barreira.py`, caso "0101 com o valor unitário como total": a instrução entregue traz a minuta do código, com "Valor total: R$ 980,00"; parte 2b: a minuta do modelo, entregue sem a barreira, é `entregue_errado` ("valor total 280.0 ≠ 980.0"); `teste_app.py`, passo A1b, pela tela |
| 0108 com prestação vencida e fundamento "regularizada": a versão exibida reflete o histórico ou vai à análise manual | executado | caso "0108 com situação vencida e fundamento dizendo 'regularizada e aprovada'": o fundamento entregue é a frase do histórico ("VENCIDA em 2026-09-25"); parte 2b: a versão do modelo é `entregue_errado` |
| 0101 com valor por extenso na minuta: o trecho fica fora da instrução entregue e da contagem de acertos | executado | caso "0101 com valor por extenso na minuta"; nos alertas, que vão à tela como o modelo escreve, o valor por extenso é recusado (caso "0101 com alerta citando valor por extenso") |
| Controle positivo com fundamentos e minuta coerentes com as consultas | executado | os 12 pedidos e as 2 complementações com a instrução correta são liberados e contam como acerto (`teste_barreira.py`, partes 1, 2 e 2b) |

**O que mudou.** Liberada a instrução, `barreira.redigir` monta os fundamentos, as
pendências e a minuta com os dados das consultas válidas, cada um no seu papel, e
substitui os textos do modelo (`desenho.md`, Seção 2, passo 7b). Os alertas do modelo
continuam na tela e são conferidos. Os erros dos textos substituídos ficam registrados
(`Resultado.textos_substituidos`) e aparecem na medição.

## 2. Diligência sem análise de mérito

| Critério de aceite | Situação | Onde está a evidência |
|---|---|---|
| 0112 inicial com cálculo, histórico e saldo de 207481 após a divergência: recusado, fora da tela e do acerto | executado | caso "0112 diligência correta, mas com cálculo, histórico e saldo de 207481": recusado; parte 2b: `entregue_errado` ("consultas fora da etapa") |
| 0112 inicial regular: diligência com o motivo cadastral e sem consultas de mérito; após a complementação, mesma sessão e consultas da matrícula 207418 | executado | casos "0112 diligência correta" e "0112 complementação correta"; "0112 complementação com o histórico da matrícula digitada 207481": recusado; `teste_app.py` e medição com a sessão do pedido |
| 0111: falta de retorno gera diligência; a complementação na mesma sessão volta ao mérito | executado | casos "0111 diligência correta", "0111 … tentativa de cálculo sem retorno" (recusado) e "0111 complementação correta"; `teste_app.py`, passo A3 |
| A medição confere ferramentas extras e fora da etapa, além das ausentes | executado | `medir.conferir`: "consultas fora da etapa" |

## 3. Urgência com condição de autorização escrita

| Critério de aceite | Situação | Onde está a evidência |
|---|---|---|
| 0106 com minuta que dispensa a autorização escrita: recusar ou gerar a minuta com a condição | executado | caso "0106 urgente com minuta que dispensa a autorização escrita": a minuta entregue é a do código, com a condição; o alerta que afirma a dispensa é recusado |
| Variante do 0106 com capacitação programada, incêndio negado e autorização verbal: a menção a incêndio não produz aptidão | executado | casos "variante do 0106 …": urgência ambígua, recusada nas duas respostas do modelo (apto ou não recomendado) e encaminhada à análise manual; `teste_barreira.py`, parte 5 |
| 0106 original com a condição escrita explícita; 0107 não recomendado | executado | casos "0106 urgente correto" e "0107 correto"; medição: 0106 correto em 6 de 6 execuções e 0107 em 6 de 6 (`resultados/historico/medicao_fb61dd9.md`; o registro original dizia "12 de 12", contagem corrigida na terceira revisão) |

**O que mudou.** `barreira.ler_urgencia` só reconhece a hipótese do § 1º afirmada e sem
sinal contrário (menção negada, atividade programada, autorização verbal, ordem ao
sistema). Com antecedência insuficiente e urgência ambígua, a barreira recusa e o
conferente decide. A condição da autorização escrita entra na minuta por regra do
código (`desenho.md`, Seção 8).

## 4. Resultado pertencente à execução atual

| Critério de aceite | Situação | Onde está a evidência |
|---|---|---|
| Fluxo sem evento inicial e sem resposta final, com execução anterior válida da mesma sessão no banco: mensagem padrão, sem reutilizar a anterior | executado | `teste_barreira.py`, parte 3 ("sem evento inicial nem resposta; anterior válida no banco"), que falha na versão 0f67cf5; `teste_app.py`, passo A4 |
| Resposta ausente, status de erro, execução diferente e fluxo normal pelo formulário; complementação e registro da decisão preservados | executado | `teste_app.py`, passos A1 a A5 e parte B (`resultados/etapa5_formulario.txt`) |

**O que mudou.** Em `instrutor.instruir`, o banco só é consultado quando o
identificador da execução atual é conhecido, e a resposta recuperada precisa ter o
mesmo identificador e a mesma sessão e status concluído.

## 5. Medição e evidências

| Critério de aceite | Situação | Onde está a evidência |
|---|---|---|
| Medição confere cada situação e seu fundamento, o papel dos dados exibidos e a presença, identidade e pertinência das consultas; gabarito independente | executado | `medir.conferir` (fundamento coerente com a situação, total e unitário da minuta, encaminhamento, consultas fora da etapa, número por extenso, condição da autorização escrita); `gabarito.json` com `papeis`; parte 2b de `teste_barreira.py` |
| Testes locais de barreira, ferramentas, eliminação e formulário, com bancos temporários e controles positivos e negativos | executado | `teste_barreira.py` (44 casos, 12 falhas do fluxo), `teste_ferramentas.py`, `teste_eliminacao.py`, `teste_app.py` parte A |
| Três rodadas de 12 pedidos e 2 complementações em cada configuração; quatro falhas provocadas; acertos, recusas, erros, entregas divergentes, tokens, tempo e custo | executado | 84/84 acertos (42/42 com paralelas desligadas e 42/42 ligadas), 0 recusados, 0 erros, 0 entregues errados, US$ 0,1476 e 0,1458, 353 s e 336 s (`resultados/medicao.md`); `resultados/falhas.md` |
| Resultados anteriores identificados pelo critério que mediram | executado | `resultados/historico/medicao_0f67cf5.md`, com o critério daquela versão no cabeçalho |
| `resultados/`, `relatorio.md`, `LEIA-ME.md` e `CORRECOES.md` atualizados; acervo intacto; chave fora do Git | executado | `dados/` sem alteração (`git log -- dados`); só `.env.example` versionado |

## Pendências e limites da segunda revisão

- **Alertas do modelo:** são o único texto do modelo que vai à tela. A barreira confere
  as fontes dos dados citados, números por extenso e a afirmação de dispensa da
  autorização escrita; um alerta errado que não cite dado algum não é detectado.
- **Leitura da urgência:** continua por palavras da justificativa. Uma hipótese do § 1º
  afirmada sem sinal contrário e sem emergência real ainda abre a exceção; a autorização
  escrita e a leitura da justificativa ficam com o conferente (`relatorio.md`, Seção 10).
- **Diagnóstico dos textos substituídos:** os textos do modelo que o código refaz são
  conferidos só pelas fontes. Em 84 itens, nenhum citou dado sem fonte; esse número não
  mede o papel dos dados nos textos do modelo.
- **Falha 4:** nesta execução, o modelo sem ferramentas pediu diligência nas 6 em vez de
  calcular; o erro de cálculo citado (3,0 diárias em vez de 3,5) é da execução de
  20/11. Nas duas, a barreira recusou as 6.
- **Gabarito reconstruído e expurgo automático:** como na primeira revisão.

# Primeira revisão (versão 8b61395)

Testes e medições executados em 20/11/2026.

## 1. Barreira de validação em código

| Critério de aceite | Situação | Onde está a evidência |
|---|---|---|
| 0112 após a complementação: recusar o histórico de 207481 para a instrução de 207418, liberar com as consultas corretas | executado | `teste_barreira.py`, casos "0112 complementação…" → `resultados/teste_barreira.txt` |
| 0101 com protocolo e partida trocados (35,5 diárias, R$ 9.940,00): validar cada data pelo seu papel, inclusive a partida usada no histórico; aplicar só correções do próprio pedido | executado | casos "0101 com protocolo e partida trocados", "…só no histórico" e "complementação do 0111 aplicada ao 0112" |
| 0108 sem a consulta de histórico: exigir evidência para cada verificação de mérito; preservar a diligência (sem mérito, quantidade e valor nulos) | executado | casos "0108 sem a consulta de histórico", "0111 diligência…", "0112 diligência…" |
| 0107 marcado apto com `exige_autorizacao_superior=true`: a marcação do modelo não justifica a exceção; o 0107 fica não recomendado; o 0106 trata a urgência de forma consistente e explicita a condição da autorização escrita | executado | casos "0107…" e "0106…"; medição: 0107 correto 6/6, 0106 correto 5/6 e recusado 1/6 (`resultados/medicao.md`) |
| 0101 com saldo inventado no fundamento e valor inventado na minuta: dados factuais dos textos com fonte no pedido ou nas ferramentas | executado | casos "0101 com saldo inventado…" e "…valor inventado na minuta" |

**O que mudou.** `barreira.py` foi reescrita. O agente (`instrutor.py`) teve a instrução
de sistema ajustada na regra da urgência, nas situações da diligência e na proibição de
contas nos textos. A urgência do § 1º passou a ser reconhecida por código (`desenho.md`,
Seção 8).

## 2. Medição e evidências

| Critério de aceite | Situação | Onde está a evidência |
|---|---|---|
| Acerto confere situações dos seis critérios, fundamentos, fatos da minuta e trilha de consultas; mantidas as quatro classes | executado | `medir.py` (`conferir`, `classificar`); `gabarito.json` com `situacoes`, `trilha` e `fatos` |
| Gabarito independente da implementação e lido só pela avaliação | executado | `gabarito.py` não importa as ferramentas; `teste_barreira.py`, parte 4, confere que agente e tela não o leem |
| Casos da seção 1 nos testes locais com respostas controladas, com controle positivo, diligência e as duas complementações; fundamentação inválida fora da tela e da contagem de acertos | executado | `simulacao.py`, `teste_barreira.py` (22 casos, partes 1 e 2); `teste_app.py`, passo A4 |
| Três rodadas com 12 pedidos e 2 complementações por configuração de paralelas; acertos, recusas, erros, tokens, tempo, custo | executado | `resultados/medicao.json` e `resultados/medicao.md`: 41/42 (desligadas) e 42/42 (ligadas), 0 entregues errados |
| Evidências das quatro falhas provocadas e justificativa do ponto de conferência humana | executado | `resultados/falhas.md`; `relatorio.md`, Seções 7 e 8 |
| Declarar a cobertura medida e o que depende de acesso ao modelo | executado | `relatorio.md`, Seção 9 |

## 3. Eliminação e conferência no SQLite

| Critério de aceite | Situação | Onde está a evidência |
|---|---|---|
| Titular sob a matrícula errada do 0112, com o nome em minúsculas: encontrar e comprovar a remoção de sessão, execução e memória, tabela por tabela | executado | `teste_eliminacao.py`, caso 1 → `resultados/teste_eliminacao.txt` |
| Tabela que não pôde ser conferida aparece como falha de verificação | executado | `teste_eliminacao.py`, caso 5 |
| Matrícula parcial "20" com nome fictício: validar identidade e formato antes de excluir; preservar os controles com dados inválidos e ao excluir titular válida | executado | `teste_eliminacao.py`, casos 1 a 3; `teste_app.py`, passo A5 |
| Exclusão restrita ao banco de trabalho do agente; `teste_app.py` isolado em banco temporário | executado | `eliminacao._banco_do_agente` (`teste_eliminacao.py`, caso 4); `teste_app.py` usa pasta temporária para banco e registro |

## 4. Mensagem padrão em falhas de execução

| Critério de aceite | Situação | Onde está a evidência |
|---|---|---|
| Retorno ausente ou execução não concluída é falha antes de ler o conteúdo; a resposta precisa pertencer à execução atual | executado | `instrutor.instruir`; `teste_barreira.py`, parte 3 (status ERROR, sem `RunOutput`, outra execução, exceção; com e sem progresso) |
| Na tela: mensagem padrão; sem instrução, minuta, argumentos ou detalhes técnicos da execução recusada | executado | `app.py` (`executar` limpa o progresso; medidas só para instrução entregue); `teste_app.py`, passo A4 |
| Teste pelo formulário: falha do fluxo simulado, status ERROR, recusa da barreira e processamento normal; divergência humana e complementação na mesma sessão | executado | `teste_app.py`, passos A1 a A4, e parte B com o modelo real → `resultados/etapa5_formulario.txt` |

## Pendências e limites da primeira revisão

- **Leitura da urgência:** o código reconhece só as hipóteses listadas no § 1º e por
  palavras da justificativa. É uma leitura conservadora, e a decisão sobre emergência
  fora da lista fica com o conferente (`relatorio.md`, Seção 10).
- **Fatos dos textos:** números por extenso, ou sem "R$", centavos ou unidade, não são
  conferidos.
- **Gabarito reconstruído:** o `gabarito.json` e o `gerar_dados.py` originais do enunciado
  não estavam no material entregue. A medição usa o gabarito reconstruído por
  `gabarito.py`.
- **Expurgo automático por prazo:** continua não implementado (opcional da Aula 07).

O acervo do desafio (`dados/`) não foi alterado. A chave fica só no `.env` local; o
repositório guarda apenas o `.env.example`.
