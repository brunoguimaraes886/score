---
tipo: decisoes
atualizado: 2026-10-07
tags: [contexto, bootcamp, decisoes]
---

# Decisões

> [[00 - Comece aqui|← Índice]] · porquê, ganhos, perdas e texto para a RFC: [[04 - Decisões explicadas]] · ordem de construção e etapas: [[09 - Plano de trabalho]] · modelo: [[Modelo - Decisão]]

Todas as regras e decisões do projeto, uma por linha: o **código** e a regra. O porquê de cada uma está em [[04 - Decisões explicadas]], na mesma ordem e com os mesmos códigos.

**Situação (07/10):** 45 fixas · 129 decididas · 2 a decidir (nenhuma toca o banco nem o código): o `database.sql` está liberado.

**Como ler**

- **Fixa** vem de fora (enunciado, rubrica, base, aulas ou resposta da organização) e não se vota; **decidida** é escolha do Bruno ou do time.
- O código é tópico + número e nunca muda (ex.: `MOV-12` = "Dinheiro em movimento", nº 12). As decisões de segurança ficam juntas em [[#11. Segurança]], com o código do tópico de origem.
- `[banco]` = muda tabela ou coluna.
- Para responder uma decisão aberta: escreva na linha **Escolha** dela, em [[04 - Decisões explicadas#A decidir]], a letra ou a sua resposta (ou `?`, para pedir explicação).
- Decisão nova: entra em "A decidir", nos dois arquivos, com o próximo número do tópico; ao fechar, vai para o tópico.

**Tópicos:** [[#A decidir|A decidir]] · [[#0. Regras do jogo|Regras]] · [[#1. Escopo — ESC|ESC]] · [[#2. Time e processo — TIM|TIM]] · [[#3. Arquitetura e ambiente — ARQ|ARQ]] · [[#4. Modelo de dados — DAD|DAD]] · [[#5. Cliente e conta — CLI|CLI]] · [[#6. Dinheiro em movimento — MOV|MOV]] · [[#7. Cofrinho — COF|COF]] · [[#8. Gamificação — GAM|GAM]] · [[#9. Virada do dia — DIA|DIA]] · [[#10. Rotas, contrato e erros — API|API]] · [[#11. Segurança|Segurança]] · [[#12. Produção (Aula 4) — PRD|PRD]] · [[#13. Testes — TST|TST]] · [[#14. RFC e entrega — RFC|RFC]]

---

## A decidir

As opções estão em [[04 - Decisões explicadas#A decidir]].

- **RFC-06** Qual é o principal desafio da RFC. *Sugestão:* decidir depois dos fluxos; os mais fortes são a concorrência no saldo e a virada do dia.
- **ESC-07** Nome do banco (opcional). Decidir quando quiser.

---

## 0. Regras do jogo

A rubrica, deduzida (o texto oficial não está na pasta). R1 e R2 são hipóteses do Plano do time; o Bruno decidiu não perguntar.

- **R1** *(hipótese)* Os testes são só black box: falam com a API por HTTP e não importam código de `src/`. Não se sabe se teste unitário é proibido.
- **R2** *(hipótese)* Tudo sobe com um comando num Linux limpo, sem passo escondido.
- **R3** Cada falha tem um código próprio (ex.: `QIT001004`), além do status HTTP. Nunca 200 com erro; nunca 500 por regra de negócio.
- **R4** Append-only: nada que entrou deixa de existir. Correção é linha nova; encerrar ou excluir é mudar o estado e registrar o evento. Soft delete não conta.
- **R6** Nada de float para dinheiro: banco, JSON, schema, testes e exemplos da RFC.
- **R7** A RFC mostra as decisões tomadas e as descartadas, com o preço de cada uma e quando ganhariam, inclusive "não fazer nada".

*R5 (o `id` interno nunca sai) e R8 (recurso de outro dono → 404) estão em [[#11. Segurança]].*

---

## 1. Escopo — ESC

O que entra na entrega e o que fica de fora.

**Fixas**

- **ESC-01** Cinco obrigatórios: cadastro de cliente, conta vinculada a um cliente, transação com controle de saldo, tarifa na transferência e extrato paginado.
- **ESC-02** Seis itens são livres, e é a defesa deles que a banca cobra: entidades (DAD-05), controle do saldo (DAD-07, MOV-11), tarifa (MOV-06, MOV-09, GAM-09), representação do dinheiro (DAD-08), rotas e formato (API) e quantidade de testes (TST-05).
- **ESC-08** A banca pontua a funcionalidade extra.

**Decididas**

- **ESC-03** A funcionalidade extra é a gamificação.
- **ESC-04** Vale a versão 2.1 da gamificação: tarifa que cai com pontos, um cofrinho único que sobe de ranque e chance de não pagar transferências de até R$ 100. As regras estão em COF e GAM.
- **ESC-05** Tudo da 2.1 entra na entrega, sem cortes. A ordem de construção está em [[09 - Plano de trabalho#Ordem de construção]].
- **ESC-06** Fora do escopo: login de clientes, PIX e TED com outros bancos, cheque especial, cartão, boleto, notificações, alterar dados do cliente, agência e número de conta, calendário de feriados e frontend. O saque entra (MOV-07).

---

## 2. Time e processo — TIM

Como o time trabalha até a entrega.

**Fixas**

- **TIM-01** Time de até 3 pessoas: João, Ana e Bruno.
- **TIM-02** "A ferramenta é livre · a defesa é obrigatória." Não há política escrita sobre uso de IA (o Bruno decidiu não perguntar).

**Decididas**

- **TIM-03** IA: Codex dentro do repositório (escreve e roda código e testes no Docker local); Claude Cowork nas regras, na RFC, na revisão e nas notas. Falta um `AGENTS.md` dentro do repositório.
- **TIM-04** Git: repositório novo do zero, privado no GitHub até a publicação (RFC-07); poucas branches grandes, uma por fase, com merge nos marcos.
- **TIM-05** Só o Bruno mexe no código, com Codex e Claude. João e Ana também defendem o projeto na banca e precisam conhecer as decisões.
- **TIM-06** Comunicação concentrada nestas notas e nas conversas com a IA.
- **TIM-07** As decisões moram nestas notas; quando o repositório novo existir, `docs/decisoes.md` as espelha, com os mesmos códigos.
- **TIM-08** Git automático pelo Codex: ele cria a branch da fase (`fase/NN-nome`, NN = etapa do [[09 - Plano de trabalho]]); a cada passo do plano, com a suíte inteira verde, faz o commit e o push; no fim da fase, com o banco recriado (`down -v`) e a suíte verde, faz o merge na `main` com `--no-ff`, a tag `fase-NN` e o push. Mensagens em Conventional Commits em português (ex.: `feat(conta): abre conta para cliente existente`). Nunca: force push, amend, rebase, reset, commit com teste vermelho ou com `.env`. Se não ficar verde, para e relata, sem merge.

---

## 3. Arquitetura e ambiente — ARQ

Quantas peças, o que roda no compose e como a banca sobe tudo. Detalhes do código: [[03 - Stack e repositórios]].

**Fixas**

- **ARQ-01** Stack do base: Python 3.11, FastAPI, SQLAlchemy 2, PostgreSQL 16, jsonschema, pytest e Docker.
- **ARQ-02** Camadas: middlewares → schemas → resources → controllers (regras; `commit` por último) → repositories → models → DTOs. O resource não guarda nada no `self`.
- **ARQ-03** As tabelas são escritas à mão em `database/database.sql`, que só roda com o volume vazio: mudou o arquivo, `docker compose down -v`.
- **ARQ-04** Tudo sobe com um `docker compose up`, sem criar `.env`: os valores padrão ficam no compose.
- **ARQ-05** Worker, mock ou outro serviço vira mais um serviço no compose e aparece na RFC; serviço de fora é testado com Mockserver.
- **ARQ-11** Pode apagar o `sample_entity` e mudar a estrutura do base.

**Decididas**

- **ARQ-06** Três peças: API, PostgreSQL e Mockserver (no papel do Banco Central). Sem worker: a virada do dia é uma rota interna (DIA-02). nginx na frente da API só se sobrar tempo (PRD-10).
- **ARQ-07** O único serviço de fora é a taxa do CDI do Banco Central, por um connector com timeout. Nos testes e na entrega, o Mockserver responde no lugar dele, carregado com 10 anos de CDI real. Plano B: CDI fixo em configuração.
- **ARQ-08** Ambiente de entrega: o compose do base + Mockserver, `.env` opcional, `./src` montado e `--reload`; sem volume nomeado e sem dados de demonstração.
- **ARQ-09** `/docs` desligada, como no base: o contrato são os schemas JSON e a tabela de rotas da RFC.
- **ARQ-10** O teste de fogo (RFC-03) roda no GitHub Codespaces: o mesmo Linux para os três.
- **ARQ-12** O Banco Central só é chamado pelo script que baixa o CDI, uma vez, no desenvolvimento; os dados são conferidos ali e gravados no arquivo do Mockserver. Na entrega (`docker compose up`), o Mockserver já sobe com os valores, e nem a API nem os testes falam com o Banco Central.

---

## 4. Modelo de dados — DAD

As tabelas. O banco nasce inteiro (DAD-15); mudar depois exige `docker compose down -v`.

**Fixas**

- **DAD-01** Toda tabela tem `id` interno (inteiro) e `<entidade>_key` pública (UUID), única.
- **DAD-04** Método: entidade, estado e relação, nesta ordem. "A modelagem decide onde o saldo mora."

**Decididas**

- **DAD-05** Entidades: cliente, conta (de cliente, cofrinho ou do sistema), operação, lançamento (partidas dobradas), depósito (quem depositou) e as tabelas de estado e de eventos de estado, como no base; além delas, categorias, lotes, eventos da gamificação, relógio do banco e logs (mapa das tabelas na explicada).
- **DAD-06** Uma tabela de operações com `type` (depósito, saque, transferência, guardar, resgatar, rendimento…). As pernas de cada operação ficam nos lançamentos.
- **DAD-07** Saldo em dois lugares: coluna `balance` na conta, atualizada sob trava, e a soma dos lançamentos, com teste de reconciliação.
- **DAD-08** Dinheiro em centavos inteiros: `BIGINT` no banco e inteiro no JSON (`5050` = R$ 50,50).
- **DAD-09** Duas contas do sistema, criadas pelo `database.sql`: a do banco (recebe tarifas; paga rendimentos e prêmios) e uma "mundo de fora" para todos os clientes (origem dos depósitos, destino dos saques). Elas não travam e não têm saldo em coluna: o saldo delas é a soma dos lançamentos.
- **DAD-10** Só as contas do sistema podem ficar negativas; conta de cliente e cofrinho, nunca.
- **DAD-11** Append-only pela disciplina do código: nenhuma rota apaga ou altera movimentação. Trigger que barra `UPDATE` e `DELETE` nessas tabelas, se sobrar tempo.
- **DAD-12** A key é UUID v4, gerada no repository, como no base.
- **DAD-13** Operação síncrona: nasce concluída no mesmo commit. Se uma regra falha, nada é gravado (só o log da tentativa, PRD-06). Única exceção: o bloqueio automático (CLI-08).
- **DAD-14** Gamificação: eventos (XP, nível, ranque, pontos) + valores atuais em colunas da conta.
- **DAD-15** O `database.sql` nasce completo, com todas as tabelas, antes do código.
- **DAD-16** A tarifa é um lançamento dentro da transferência: um pedido = uma operação + quatro lançamentos (quem envia −valor e −tarifa; quem recebe +valor; banco +tarifa), que somam zero.
- **DAD-17** Toda operação guarda duas datas: `created_at` (data e hora reais) e `accounting_date` (a data contábil, do relógio do banco, DIA-01).

---

## 5. Cliente e conta — CLI

Quem é o cliente, quantas contas ele tem e por quais estados a conta passa.

**Fixas**

- **CLI-01** Conta só existe ligada a um cliente que existe: conta para cliente inexistente → 404, e nenhuma conta é criada.

**Decididas**

- **CLI-02** Dados do cliente, como no `sample_entity` do base: nome, CPF (válido e único), e-mail (único) e data de nascimento.
- **CLI-03** Idade mínima de 18 anos (abaixo → 422, `QIT001006`), sem máximo; conferida só no cadastro.
- **CLI-04** Uma conta não encerrada por cliente, aberta por rota própria; nasce `ACTIVE`, com saldo 0. Depois de encerrar, o cliente pode abrir outra, que começa do zero.
- **CLI-05** O cliente não tem estado. A conta vai de `ACTIVE` a `BLOCKED` e volta, e de `ACTIVE` a `CLOSED` (final; a bloqueada precisa ser desbloqueada antes). Toda mudança grava um evento. Bloqueada: lê, mas não envia nem recebe dinheiro (409). Encerrada: só lê. Só o banco bloqueia e desbloqueia (rota interna, com motivo); só o dono encerra.
- **CLI-06** O dono encerra a conta só com saldo e cofrinho zerados; depois disso, qualquer operação nela → 409.
- **CLI-07** Conta bloqueada não muda nada na virada: o cofrinho rende, o recorde dá XP e o ranque segue.
- **CLI-09** Conta bloqueada não mexe em dinheiro: depósito, saque, transferência enviada ou recebida, guardar e resgatar → 409; também não encerra. Leitura, pontos e categorias continuam liberados.

*CLI-08 (bloqueio automático) está em [[#11. Segurança]].*

---

## 6. Dinheiro em movimento — MOV

Depósito, saque, transferência, tarifa, concorrência, idempotência e extrato da conta. Cofrinho em COF; desconto e sorteio em GAM.

**Fixas**

- **MOV-01** Transferência sem saldo é barrada, e os dois saldos ficam como estavam.
- **MOV-02** O saldo precisa cobrir valor + tarifa.
- **MOV-03** Toda transferência passa pela tarifa.
- **MOV-04** Extrato paginado no envelope do base: `data`, `limit`, `page`, `is_last_page` (`limit` padrão 10 e máximo 100; `page` começa em 0).
- **MOV-05** Ler o saldo e gravar com base nele acontecem na mesma transação, com a linha travada (`with_for_update()`, como a biblioteca).

**Decididas**

- **MOV-06** Tarifa de 1% do valor da transferência; os pontos podem reduzi-la (GAM-09).
- **MOV-07** Operações de dinheiro: depósito (vem do mundo de fora), saque (volta para ele) e transferência; no cofrinho, guardar e resgatar.
- **MOV-08** O que barra uma operação: valor que não é inteiro ≥ 1 centavo (400, API-18), saldo que não cobre valor + tarifa (422), conta que não está ativa (409) e origem igual ao destino (422). Não há valor máximo.
- **MOV-09** Só a transferência tem tarifa, e quem paga é quem envia, num lançamento próprio (DAD-16). Depósito, saque, guardar e resgatar não têm tarifa.
- **MOV-10** Tarifa arredondada para cima ao centavo (1% de R$ 12,34 = 12,34 centavos → 13): nunca sai mais barato dividir a transferência. Tarifa zero não gera lançamento.
- **MOV-11** Concorrência: trava as duas contas com `SELECT … FOR UPDATE`, sempre na mesma ordem (menor `id` primeiro), para não haver deadlock.
- **MOV-12** Idempotência: `request_control_key` (UUID) no corpo de depósito, saque, transferência, guardar e resgatar, com `UNIQUE` na tabela de operações, para sempre. Mesma chave e mesmo corpo → a resposta da primeira vez; corpo diferente → 409; pedido barrado não guarda a chave.
- **MOV-13** Sem estorno; a RFC explica como seria: uma operação nova apontando para a original.
- **MOV-14** Extrato da conta: mais recentes primeiro (`created_at` decrescente, desempate por `id`), com o saldo depois de cada lançamento.
- **MOV-15** Depósito: qualquer um com o `INTERNAL-TOKEN` deposita em qualquer conta, informando nome e CPF ou CNPJ de quem deposita; não precisa ser cliente. Saque: só o dono, com o token da conta.
- **MOV-16** Detalhes do depósito: rota `POST /accounts/{key}/deposits`; corpo validado por schema (nome, CPF ou CNPJ formatado, valor inteiro ≥ 1 e chave de idempotência); dígito verificador errado → 422; quem depositou fica na tabela `deposits`; a resposta traz só a key da operação.
- **MOV-17** O extrato mostra a outra ponta de cada lançamento (`counterparty`): na transferência, o nome do outro cliente e o CPF mascarado; no depósito, quem depositou; na tarifa, no rendimento e no prêmio, o banco; em guardar e resgatar, o cofrinho e a categoria; no saque, nada.
- **MOV-18** Cada item do extrato mostra as duas datas: `created_at` (quando aconteceu) e `accounting_date` (em que dia do banco contou).
- **MOV-19** Idempotência na prática: a operação guarda o `request_hash` (SHA-256 do corpo) e cada lançamento guarda o `balance_after`; a resposta repetida é remontada deles. Na corrida com a mesma chave, o `IntegrityError` do `UNIQUE` é tratado como repetição, nunca 500.

---

## 7. Cofrinho — COF

O produto de poupança da gamificação: um cofrinho por conta, dividido em categorias e lotes, com rendimento diário. Ranque e XP em GAM; a rotina diária em DIA.

- **COF-01** Um cofrinho por conta (GAM-01), que muda de ranque com o saldo (padrão → bronze → … → diamante), em vez de um cofrinho especial separado.
- **COF-02** Rendimento diário em % do CDI, pelo ranque: padrão 100%, bronze 102,5%, prata 105%, ouro 110%, platina 115% e diamante 120%. A conta principal não rende.
- **COF-03** Todo dinheiro do cofrinho está numa categoria: "economias" é a padrão, e o dono cria as suas (ex.: "carro"). A categoria não muda o rendimento.
- **COF-04** Excluir categoria: "economias" nunca; categoria com dinheiro, não; categoria zerada não some sozinha, mas pode ser excluída.
- **COF-05** Saldo e extrato do cofrinho por categoria e no total, com a categoria de cada movimento.
- **COF-06** Cada vez que se guarda, nasce um lote com a sua data. O resgate sai da categoria escolhida, do lote mais antigo dela até zerar, e depois do seguinte.
- **COF-07** Resgate maior que o saldo da categoria é negado (422), mesmo que o cofrinho todo tenha o dinheiro.
- **COF-08** O resgate desconta IOF e IR, e o dono sempre vê o rendimento bruto e o líquido.
- **COF-10** Guardar e resgatar só entre a conta e o próprio cofrinho; o resgate é livre, a qualquer hora, e o dinheiro volta para a conta.
- **COF-11** Sem limite para guardar: o valor de cada ranque é o mínimo para alcançá-lo.
- **COF-12** IR e IOF reais, por lote: IR regressivo pelo prazo do lote (22,5% até 180 dias, 20% até 360, 17,5% até 720, 15% acima) e IOF regressivo nos resgates com menos de 30 dias. O imposto é arredondado uma vez, no total do resgate, para cima.
- **COF-13** O rendimento é contado em cada lote (para o IR por prazo); o dono vê só o total bruto e o líquido.
- **COF-14** O cofrinho é uma conta (mesma tabela, tipo "cofrinho") ligada à conta principal; categorias e lotes ficam em tabelas próprias. Nasce com a conta, já com "economias".
- **COF-15** O rendimento diário guarda a fração de centavo: taxa diária com 8 casas e resíduo em `NUMERIC` com 8 casas, em cada lote. Os centavos inteiros viram lançamento no dia; a fração fica para o dia seguinte.
- **COF-16** Só rendem os dias com taxa do CDI publicada pelo Banco Central (dias úteis); dia sem taxa, sem rendimento.
- **COF-17** A taxa de cada dia é o CDI real (série 12 do SGS do Banco Central), pedido pelo connector da ARQ-07.
- **COF-18** Nome da categoria único entre as ativas da conta; sem limite de quantidade; sem renomear; excluída não volta (cria-se outra).
- **COF-19** Não existe mover dinheiro entre categorias: resgata e guarda de novo (perde a data dos lotes e paga imposto).
- **COF-20** Se o Banco Central (o Mockserver) não responder na virada em 5 s, a virada responde 503 com código próprio, nada é gravado e o dia não avança.
- **COF-21** A taxa usada em cada virada não ganha tabela própria: tudo se reconstrói dos lançamentos, do arquivo do Mockserver e dos eventos de ranque.
- **COF-22** Dinheiro guardado antes da virada rende o dia inteiro, a qualquer hora; resgatado antes da virada não rende o dia.
- **COF-23** Cada lote guarda em colunas o principal e o rendimento que restam e o resíduo, atualizados sob a trava do cofrinho; os lançamentos do cofrinho são por categoria (um de rendimento por categoria por dia). Prova: soma dos lotes = saldo da categoria = soma dos lançamentos.
- **COF-24** No resgate de parte de um lote, principal e rendimento saem na proporção do lote; o imposto incide só sobre a parte de rendimento.
- **COF-25** `[banco]` O IOF e o IR do resgate são creditados na conta do banco, em lançamentos de tipo `IOF` e `IR`; o repasse ao governo fica fora (só na RFC).

---

## 8. Gamificação — GAM

XP, nível, pontos, benefícios e ranque. Tudo é da conta (GAM-01).

- **GAM-01** A gamificação é por conta: XP, nível, pontos, ranque e cofrinho são da conta. Conta nova, aberta depois de encerrar a anterior, começa do zero.
- **GAM-02** As peças: XP sobe com o uso → nível → pontos para dois benefícios (tarifa menor ou chance de não debitar). À parte, o ranque, pelo saldo do cofrinho, define quanto ele rende.
- **GAM-04** O cofrinho só dá XP quando o saldo total dele passa do maior valor que já teve (o recorde); o rendimento conta. Tirar e pôr de volta não dá XP.
- **GAM-05** O nível nunca cai, e nenhum XP se perde: ao subir, a sobra passa adiante (GAM-24).
- **GAM-06** Pontos ganhos ao subir de nível ficam livres até o dono aplicá-los.
- **GAM-07** Os pontos se dividem entre Tarifa e Chance e podem ser redistribuídos a qualquer hora; cada mudança é um evento.
- **GAM-09** Cada ponto em tarifa tira 0,1 p.p. dos 1%; com os 10 pontos em tarifa (nível 10), a tarifa é 0%.
- **GAM-10** Chance de não debitar: o sorteio só acontece depois de conferir o saldo; quando sai, a transferência acontece e a conta do banco devolve valor + tarifa num lançamento de prêmio. Cada ponto em chance soma 0,1 p.p. (máximo de 1%).
- **GAM-11** Um ponto em chance vale o mesmo que um em tarifa, calibrado para transferências de até R$ 100.
- **GAM-12** O ranque (bronze, prata, ouro, platina, diamante) é dado só pelo saldo do cofrinho.
- **GAM-13** Mínimo de cada ranque: padrão R$ 0, bronze R$ 2 mil, prata R$ 5 mil, ouro R$ 10 mil, platina R$ 30 mil e diamante R$ 50 mil.
- **GAM-14** Carência: o ranque vale enquanto o cofrinho tiver o mínimo, mais 30 dias contados da queda. Voltou ao mínimo nesses 30 dias, mantém; passados os 30, cai direto para o ranque que o saldo dá. Durante a carência, rende no ranque.
- **GAM-15** 10 níveis e 1 ponto por nível (10 pontos no máximo). Todos os números da gamificação são constantes ajustáveis.
- **GAM-16** Fórmulas de XP: cofrinho = n XP por R$ 1 de novo recorde; transferência = (x/4)·log(n·10), com x = valor em reais. n = próximo nível (nível 0 → 1; nível 9 → 10; no nível 10, n continua 10 e o XP segue sem teto).
- **GAM-17** Transferência dá XP para quem envia e para quem recebe, cada um com o seu n. Depósito, saque, guardar e resgatar não dão XP de movimentação.
- **GAM-18** x = centavos ÷ 100 (R$ 12,34 → 12,34); XP sempre inteiro, truncado; log na base 10.
- **GAM-19** O ranque sobe na hora, ao guardar, e a virada também confere a subida; queda e carência só na virada. O rendimento do dia usa o ranque do início do dia. O XP de recorde sai na hora (ao guardar) e na virada (pelo rendimento).
- **GAM-21** Pontos na API: "aplicar +Y" (soma Y pontos livres a um benefício; faltou ponto livre → 422) e "zerar tudo" (todos voltam a livres). Não existe tirar um ponto só. Sem chave de idempotência.
- **GAM-22** Concorre ao sorteio a transferência com valor até R$ 100,00 (10.000 centavos), sem contar a tarifa.
- **GAM-23** O prêmio do sorteio não dá XP.
- **GAM-24** Cada nível custa 1.000 × n² de XP (0→1 = 1.000 … 9→10 = 100.000; 385.000 no total); ao subir, o XP zera e a sobra passa adiante. Se subir no meio de uma operação, o resto do valor rende com o n novo.
- **GAM-25** O XP do recorde conta reais inteiros: XP = n × (reais inteiros do novo saldo − reais inteiros do recorde). Os centavos do rendimento não se perdem; viram XP quando completam um real.

---

## 9. Virada do dia — DIA

A rotina que fecha o dia: rendimento, XP de recorde, ranques e carência.

- **DIA-01** O relógio do banco é uma data contábil guardada numa tabela de uma linha: é o "hoje" de toda regra que depende do dia (rendimento, recorde, carência, limite diário). Só avança quando a virada roda.
- **DIA-02** A virada é uma rota interna (`/internal`), sem worker, e fechar o mesmo dia duas vezes não paga duas vezes. Em produção, um agendador a chamaria todo dia.
- **DIA-03** A virada roda numa transação só (tudo ou nada), nesta ordem: pede a taxa do CDI → rendimento por lote → XP de recorde → ranques (subir; abrir ou encerrar carência; cair) → guarda o ranque que rende amanhã → avança a data.
- **DIA-04** O relógio começa em 01/06/2026 (segunda, dia útil), data fixa escrita no `database.sql`.
- **DIA-05** A rota da virada recebe a data a fechar (`accounting_date`): igual ao relógio → fecha e avança; já fechada → 409 e nada muda; no futuro → 422.

---

## 10. Rotas, contrato e erros — API

Rotas, formato das respostas e erros.

**Fixas**

- **API-01** Erro sempre no formato `{title, description, translation, code}`. `QIT000xxx` são genéricos; `QIT001xxx` são do projeto, a partir de `QIT001008` (o base usa até `QIT001007`).
- **API-02** O status de sucesso sai do resource: 201 criou, 202 recebeu e vai fazer, 204 pronto e sem corpo, 200 o resto.
- **API-03** Toda entrada passa por schema JSON com `additionalProperties: false`; fora dele → 400 `QIT000001`.
- **API-05** A tabela de rotas da RFC diz os status de erro e quando cada um sai, e se a rota é idempotente e por quê.
- **API-06** REST é convenção, não lei: escolher uma convenção de nomes e dizer na RFC qual foi. Ação que não vira substantivo (estorno, fechamento de conta) usa o substantivo mais próximo, com o porquê.

**Decididas**

- **API-07** Inglês em rotas, campos e valores, como o base (o `translation` dos erros em português); plural sempre (`/customers`, `/customers/{key}`).
- **API-08** Rotas aninhadas (`/customers/{key}/accounts`, `/accounts/{key}/transactions`): a checagem de dono é uma regra só, "a conta da URL é a conta do token".
- **API-10** Resposta de sucesso: criação → 201 com a key e poucos campos; consulta → 200 com o objeto pelo DTO; transferência → key da operação e o saldo novo.
- **API-11** Status de erro: 400 formato; 404 não existe ou não é seu; 409 duplicado ou estado que não permite; 422 regra de negócio. Além desses: 403 token interno, 429 tentativas demais e 503 dependência fora do ar ou lenta.
- **API-12** Catálogo de erros: cada falha com situação, status e código próprio, a partir de `QIT001008`; fecha na etapa 3, com o contrato.
- **API-13** Rotas internas (virada do dia, bloquear e desbloquear conta) ficam sob `/internal`, com token próprio (PRD-07).
- **API-14** Rota própria para consultar a gamificação: XP, nível e XP que falta; pontos livres, em tarifa e em chance; tarifa e chance atuais; ranque, % do CDI que rende, recorde do cofrinho e fim da carência (se houver).
- **API-15** Excluir categoria é `DELETE`, que só muda o estado e grava o evento. Depois: a consulta pela key devolve 200 com `status: deleted`, a lista mostra só as ativas e guardar nela → 409.

- **API-18** Valor que não é inteiro ≥ 1 centavo (float, texto, zero, negativo) → 400 `QIT000001` pelo schema, em todas as rotas de dinheiro.

*API-04 (`INTERNAL-TOKEN`), API-09 (dono pelo token da conta), API-16 (como o token da conta funciona) e API-17 (quem consulta o cliente) estão em [[#11. Segurança]].*

---

## 11. Segurança

Tudo o que protege a API, venha de que tópico vier. Os códigos mantêm o prefixo do tópico de origem.

**Quem pode chamar a API**

- **API-04** *(fixa)* Toda rota pede o cabeçalho `INTERNAL-TOKEN`, menos `/` e `/health_check`; faltou ou errou → 403 `QIT000002`, e o resource nem roda.
- **PRD-07** Dois tokens internos: o `INTERNAL-TOKEN`, das rotas de cliente, e outro só para as rotas `/internal`. O token de cada conta vale à parte (API-16).
- **PRD-01** *(fixa)* Segredos e configuração em variável de ambiente, nunca no código; o `.env` não vai para o Git, só o `.env.example`.
- **PRD-13** As rotas `/internal` pedem o `INTERNAL-TOKEN` e mais um cabeçalho próprio de administração (ex.: `ADMIN-TOKEN`); errar o segundo → 403.

**De quem é o recurso**

- **R8** *(fixa)* Autorização, não só autenticação: recurso de outro dono responde 404, não 403 (IDOR; nº 1 do OWASP API Top 10).
- **API-09** O dono de cada recurso é identificado por um token individual de cada conta: recurso de outra conta → 404.
- **API-16** O token da conta nasce na abertura, sai uma vez só (na resposta 201) e é guardado só como hash SHA-256; vai num cabeçalho próprio, junto com o `INTERNAL-TOKEN`. Cadastrar cliente, abrir conta e depositar não pedem token de conta. Sem troca de token.
- **API-17** Consultar o cliente (`GET /customers/{key}`) pede o token da conta não encerrada dele; outra conta ou nenhuma → 404. O CPF sai inteiro, porque é o dono vendo o próprio dado.

**O que nunca sai**

- **R5** *(fixa)* O `id` interno nunca sai: nem em resposta, erro, log ou exemplo da RFC; só a key (UUID).
- **PRD-12** CPF e CNPJ de outra pessoa só saem mascarados (ex.: `***.456.789-**`); inteiros, só no banco. Logs nunca guardam CPF ou CNPJ inteiro nem token.

**Abuso e fraude**

- **PRD-10** Barreira contra chute de token: 10 erros de token em 15 minutos (por conta + IP no token da conta; por IP nos internos) → 429, sem rodar a regra. Limites em variável de ambiente.
- **PRD-11** Sobrecarga e DDoS ficam fora do código, só na RFC (balanceador, auto scaling, API Gateway, WAF, CDN).
- **CLI-08** Bloqueio automático: a 11ª transferência enviada no mesmo dia contábil é recusada (422) e a conta é bloqueada na mesma requisição, com motivo `SUSPICIOUS_ACTIVITY` e origem automática.

**Também protegem** (decisões de outros tópicos com efeito de segurança): API-03 (schema fechado na entrada) · API-08 (checagem de dono igual em toda rota) · API-10 (resposta sem campo interno) · API-13 (rotas internas separadas) · MOV-04 (no máximo 100 itens por página) · MOV-12 (duplo clique não debita duas vezes) · MOV-15 e MOV-16 (quem deposita; o depósito não devolve saldo) · CLI-05 (só o banco bloqueia) · DAD-11 (movimentação não se altera) · ARQ-09 (`/docs` desligada) · PRD-03 e PRD-08 (timeouts) · PRD-06 (log de toda requisição) · TIM-04 (repositório privado até a entrega).

Também de segurança, em ARQ: ARQ-12 (Banco Central só no download, nunca na execução). Nada de segurança está em aberto.

---

## 12. Produção (Aula 4) — PRD

O que muda quando a API roda "no mundo real" (Aula 4). A parte de segurança da aula está em [[#11. Segurança]].

**Fixas**

- **PRD-02** Health check só diz "estou de pé": rápido e sem depender de ninguém, nem do banco (`GET /health_check` → 204, como o base).
- **PRD-03** Todo connector tem timeout; sem ele, o prazo é "para sempre". O base usa 5 s.
- **PRD-04** A API não guarda estado na memória do processo, para rodar em várias cópias atrás de um balanceador.

**Decididas**

- **PRD-05** Da Aula 4, ficam só na RFC: métricas, alarmes, tracing, readiness, balanceador, réplicas, auto scaling, retry com backoff, circuit breaker, TLS e API Gateway. O resto está no código, em decisões próprias.
- **PRD-06** Uma tabela de logs com um registro por requisição, deu certo ou não, além da saída padrão do base, gravada fora da transação da regra; ela também alimenta a barreira da PRD-10. Logger nos pontos críticos.
- **PRD-08** Timeout no banco: `lock_timeout` e `statement_timeout` na sessão (ex.: 5 s); passou, a transação é desfeita e a API responde 503 com código próprio.
- **PRD-09** Só liveness, como o base; readiness fica na RFC.
- **PRD-14** Colunas da tabela de logs: `request_id`, `created_at`, `method`, `path`, `status`, `error_code`, `client_ip`, `account_key` e `auth_failure` (qual token falhou), com índice para a barreira contar.

*PRD-01 (segredos), PRD-07 (tokens internos), PRD-13 (tokens das rotas internas), PRD-10 (barreira contra chute de token), PRD-11 (sobrecarga e DDoS) e PRD-12 (dados sensíveis) estão em [[#11. Segurança]].*

---

## 13. Testes — TST

A lista de casos está em [[09 - Plano de trabalho#Testes previstos]].

**Fixas**

- **TST-01** Padrão QI Tech: black box via HTTP e TDD (o teste fica vermelho antes do código). Cada `if` do controller tem pelo menos dois testes: o que passa e o que é barrado.
- **TST-02** Se a RFC diz que barra, existe um teste que fica vermelho quando deixa de barrar.
- **TST-03** Mínimo: as 5 regras que viram teste da Aula 3 (CPF único, conta só com cliente, sem saldo, tarifa e extrato paginado).
- **TST-07** A banca roda os testes do próprio repositório; não há contrato fixo de rotas, e nomes e formatos são decisão do time.

**Decididas**

- **TST-05** Unitários + black box: as contas puras (tarifa, XP, nível, rendimento, IR/IOF, sorteio) têm teste unitário, numa pasta separada e escrito primeiro; toda regra também tem teste black box.
- **TST-06** Sorteio com gerador injetável: o unitário usa um gerador falso; o black box confere o que vale nos dois resultados.
- **TST-08** Provas extras: duas transferências ao mesmo tempo quando o saldo só cobre uma; a mesma chave de idempotência duas vezes; A paga B e B paga A ao mesmo tempo; reconciliação (a soma do extrato bate com o saldo); nenhum 5xx na suíte. Se o tempo apertar, só as duas primeiras.

---

## 14. RFC e entrega — RFC

O que se entrega, como e quando.

**Fixas**

- **RFC-01** PDF com lógica de RFC, no modelo oficial de 2 a 4 páginas: Contextualização (o problema; a solução macro, com 2 a 4 alternativas descartadas) e Implementação (rotas; banco só com diagrama; fluxos feliz e de falha). "Principal desafio" aparece uma vez, na seção onde mora. Sem seções novas.
- **RFC-02** Repositório público no GitHub no dia da entrega (pode ser privado antes): "o que estiver no repositório nessa data é o que a banca vê".
- **RFC-03** Teste de fogo: apagar a pasta, clonar de novo e subir do zero; se precisar de mais de um comando, falta algo no compose.
- **RFC-04** Prazo: 12/10, às 12h.

**Decididas**

- **RFC-05** A RFC é escrita em Markdown, com diagrama em Mermaid, e exportada para PDF, como a da biblioteca; testar a exportação cedo.
- **RFC-07** Repositório público até 11/10 à noite, depois do teste em Linux limpo; PDF e link entregues até 12/10, às 10h. O Bruno cuida do repositório.

---

## Códigos que deixaram de existir

Repetiam outra decisão e foram juntados na revisão de 07/10. O conteúdo não se perdeu: está no código indicado.

- **DAD-02** → R4 (era a mesma regra).
- **DAD-03** → R6 (era a mesma regra).
- **COF-09** → MOV-09 (sem tarifa), GAM-17 (sem XP) e GAM-22 (sem sorteio).
- **GAM-03** → GAM-16 (o cofrinho dá mais XP que a transferência).
- **GAM-08** → GAM-21 (redistribuir = zerar e aplicar de novo).
- **GAM-20** → GAM-14 (carência) e GAM-19 (a queda é vista na virada).
- **TST-04** → TST-05 (as contas puras primeiro, com teste unitário).

Códigos de antes de 05/10 (D1, B5, A4, P3…) e o texto original das ideias do Bruno: [[04 - Decisões explicadas#Histórico dos códigos]].
