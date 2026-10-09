> **Git local — Bruno, 08/10/2026:** durante a produção, branches, commits, merges e tags ficam locais. Não executar push, pull ou fetch nem exigir acesso ao GitHub. O envio completo será feito pelo Bruno somente no final, quando tudo estiver pronto. As verificações de commits e dependências são locais.

# AGENTS.md — protótipo bancário do Bootcamp QI Tech 2026

Vale para qualquer agente que mexa neste repositório: Codex, Claude Code ou outro. O Claude Code lê este arquivo pelo `CLAUDE.md`, que só o importa.

## 1. O projeto

1. Protótipo bancário do Bootcamp QI Tech 2026, do time João, Ana e Bruno, com entrega em 12/10/2026, às 12h.
2. API REST em Python 3.11, FastAPI, SQLAlchemy 2 e PostgreSQL 16, em Docker, feita a partir do `bootcamp-base-api`.
3. Obrigatórios: cliente, conta, depósito e transferência com tarifa (saldo nunca negativo) e extrato paginado. Extra: a gamificação 2.1 (XP, nível, pontos, cofrinho com ranque e rendimento pelo CDI, virada do dia).
4. A banca clona, roda `docker compose up` e `pytest` num Linux limpo (ARQ-04 — um comando, sem `.env`): nada pode depender desta máquina.
5. O plano fica em `docs/plano/`: `PLANO-00-indice.md` e um arquivo por fase, `PLANO-fase-NN.md` (NN com dois dígitos).

## 2. Como trabalhar

- Execute só o passo pedido (`Passo N.M` de `docs/plano/PLANO-fase-NN.md`), exatamente como está escrito. Pedido com vários passos: um por vez, na ordem, cada um com o seu commit; parou num, não comece o seguinte.
- Leia o passo inteiro antes de começar e siga o **Passo a passo** na ordem, sem pular item.
- O campo **Arquivos** é a lista completa do que o passo toca. Proibido criar, editar ou apagar qualquer outro arquivo.
- Proibido acrescentar o que o passo não traz: dependência, tabela, coluna, campo, rota, erro, código de erro, variável de ambiente ou teste. Proibido renomear, refatorar, reformatar ou "melhorar" o que o passo não pede.
- Conteúdo que o plano dá inteiro (SQL, JSON, configuração, código) entra igual, caractere por caractere. Nome que o plano dá entra igual, com as mesmas maiúsculas e minúsculas.
- Nomes no código em inglês; comentários e o campo `translation` dos erros em português, como no base (API-07 — rotas e campos em inglês).
- O campo **Decisões** é referência: o que vale já está escrito no passo. O espelho das decisões é `docs/decisoes.md` (TIM-07), só para consulta.
- Nunca edite `AGENTS.md`, `CLAUDE.md`, `docs/plano/` ou `docs/decisoes.md`. Nunca crie nem edite o `.env`.
- Crie e edite arquivos só com a ferramenta de edição do agente, em UTF-8 sem BOM. Nunca por redirecionamento do terminal (`>`, `>>`, `Set-Content`, `Out-File`): no Windows, ele pode gravar outra codificação.
- Nunca rode comando que não termina sozinho (`docker compose up` sem `-d`, `docker compose logs -f`). Nunca instale nada fora do `.venv`.
- Faltou uma decisão de negócio que o roteiro não define: PARE (seção 8). Escolhas operacionais seguem a política de autonomia abaixo.

### Autonomia de execução — autorização do Bruno

- Resolva autonomamente preparação documental, falhas do executor ou sandbox, comandos indisponíveis, caminhos e problemas de ambiente. Tente novamente ou use uma alternativa equivalente e segura; uma primeira falha operacional não exige parar nem perguntar. Preserve Windows, UTF-8 sem BOM, uso do editor do agente, instalação somente no `.venv` e Git exclusivamente local.
- Correções necessárias para fazer os comandos, testes e lint prescritos funcionarem também são autorizadas, inclusive em arquivos fora do campo **Arquivos**, quando o diagnóstico define a correção sem mudar o contrato de negócio. Limite a mudança à causa comprovada, confira os testes afetados e registre a correção em commit local próprio, separado do commit do passo. Não invente funcionalidades, dependências ou decisões de negócio; não apague, pule ou afrouxe testes para obter aprovação.
- As correções operacionais autorizadas são exceções às proibições de escopo e às condições **Pare se** de ambiente, comandos, testes e lint dos roteiros. Confira e registre separadamente seus arquivos; a conferência do commit de implementação continua exigindo exatamente os arquivos do passo. Correções de `AGENTS.md` expressamente solicitadas podem ser registradas durante a fase em commit próprio.
- Pare somente se, após diagnóstico e alternativas seguras, persistir um bloqueio real: decisão de negócio ausente ou contraditória, risco de perder dados ou trabalho, alteração de contrato não autorizada, conflito de merge ou falha não resolvida após três tentativas de correção. Traga o relatório da seção 8; não peça confirmação para providências operacionais já autorizadas.

### Execução econômica

- Além das leituras obrigatórias do ambiente, leia o passo atual inteiro e apenas os trechos do índice e das dependências necessários para executá-lo. Não releia todas as fases nem a auditoria a cada passo.
- Consulte arquivos existentes pelos imports, funções e testes afetados. Reutilize o contexto já lido no mesmo chat; as referências a nomes anteriores não exigem reler os roteiros inteiros.
- Execute todas as verificações prescritas, inclusive repetições de concorrência. Depois de aprovadas, só repita se houve alteração, falha ou exigência expressa do passo.
- Não refaça a auditoria nem replaneje trechos completos. Para contas numéricas, consulte ARR em `docs/decisoes.md` somente quando necessário; os códigos originais continuam válidos.
- Limite saídas ao resultado necessário para verificar o passo e siga o formato de conclusão ou parada deste arquivo.

## 3. Comandos

Windows, no Git Bash ou no PowerShell: os comandos são iguais nos dois e rodam da raiz do repositório.

- Um comando por vez, na ordem. Nunca junte comandos com `&&` ou `;` (o PowerShell 5.1 não aceita `&&`).
- Python só pelo executável do `.venv`: `./.venv/Scripts/python.exe -m <módulo>`. Nunca `activate`, nem `python`, `pip` ou `pytest` soltos: cada comando pode rodar num terminal novo, onde o `activate` anterior não vale.

| Quero | Comando |
|---|---|
| Subir tudo ou pôr a API em dia com o código | `docker compose up -d --build --wait` |
| Recriar o banco do zero | `docker compose down -v` e, depois, `docker compose up -d --build --wait` |
| Rodar a suíte inteira | `./.venv/Scripts/python.exe -m pytest` |
| Rodar um arquivo de teste | `./.venv/Scripts/python.exe -m pytest -v <caminho do arquivo>` |
| Rodar só os unitários | `./.venv/Scripts/python.exe -m pytest tests/unit` |
| Lint | `./.venv/Scripts/python.exe -m flake8 src tests` |
| Criar o `.venv` (só quando o plano mandar) | `python -m venv .venv` |
| Instalar as dependências no `.venv` | `./.venv/Scripts/python.exe -m pip install -r requirements-dev.txt` |
| Ver o estado dos serviços | `docker compose ps` |
| Ver o fim do log da API | `docker compose logs --tail 100 api` |
| Ver o fim do log do banco | `docker compose logs --tail 100 db` |

Quando usar:

- Antes de rodar teste de integração: `docker compose up -d --build --wait`. Ele põe o código atual na imagem da API e só termina quando ela responde ao health check.
- O passo mudou `database/database.sql`: recrie o banco do zero antes dos testes (ARQ-03 — o SQL só roda com o banco vazio).
- O passo mudou `requirements.txt` ou `requirements-dev.txt`: instale as dependências no `.venv` de novo. A imagem, o `--build` refaz.
- `docker compose up -d --build --wait` falhou: rode os dois comandos de log e PARE, com as duas saídas no relatório.
- Apareceu `port is already allocated` ou `failed to connect to the docker API`: PARE.
- Os testes procuram a API em `http://127.0.0.1:3000`, padrão do repositório (o Windows não aceita `0.0.0.0` como destino).
- Requisição à mão: só `curl.exe` (no PowerShell, `curl` sem `.exe` é outro programa), numa linha, sem corpo JSON. Rota com corpo se confere pelo pytest.

Novo em relação ao base: `--build` e `--wait` no `up` (o `database/Dockerfile` copia o `database.sql` para dentro da imagem do banco, e sem `--build` o `up` reaproveita a imagem antiga), `--tail` nos logs, o `flake8` (fixado no `requirements-dev.txt`), o `pytest.ini` e a pasta `tests/unit/`.

## 4. Arquitetura

As camadas da ARQ-02, na ordem em que a requisição passa por elas:

| Camada | Onde | Trabalho | No base |
|---|---|---|---|
| Middlewares | `src/middlewares/`; registro em `src/app.py`, onde o último registrado é o primeiro a rodar | o que vale para toda requisição: identificador, log, token, sessão de banco | `register_internal_token_middleware`: sem o `INTERNAL-TOKEN` certo, responde 403 `QIT000002` |
| Schemas | `src/schemas/*.json` | o formato aceito na entrada, conferido antes de a rota rodar | `post_sample_entity.json`, ligado à rota por `@SchemaHandler.validate("post_sample_entity.json")` |
| Resources | `src/resources/`; cada rota é um `add_api_route` em `src/app.py` | recebe a requisição, chama o controller e devolve a resposta com o status de sucesso | `on_post` devolve `JSONResponse` com `status_code=http_status.HTTP_201_CREATED` |
| Controllers | `src/controllers/` | as regras de negócio, na ordem do plano; levanta os erros; faz o commit | `create`: CPF válido → CPF único → e-mail único → idade, antes de gravar; `self.session.commit()` antes do `return` |
| Repositories | `src/repositories/` | consulta e gravação; a key nasce aqui | `create` gera a key com `uuid4()`; `list_page` pede `limit + 1` |
| Models | `src/models/`, um arquivo por tabela, listado em `src/models/__init__.py` | a tabela descrita em Python | `SampleEntity` espelha a tabela `sample_entity` |
| DTOs | `src/dtos/` | o dicionário que vira a resposta | `SampleEntityDTO.obj_to_dict`, sem `id` |

Fora da linha da requisição:

| Peça | Onde | No base |
|---|---|---|
| Erros | `src/errors/custom_errors.py` (do projeto); `base_error.py` e `handlers.py` (genéricos) | `DuplicatedDocumentNumber`: `QIT001004`, 409 |
| Connectors | `src/connectors/` | `RestConnector.send`: endereço vindo do ambiente, timeout, log da ida e da volta |
| Ferramentas | `src/utils/` | `is_valid_cpf`, `get_logger` |
| Sessão de banco | `src/database.py` | `get_context()`, chamado pelo `BaseController` |
| Configuração | `src/constants.py` (lê o ambiente) e `docker-compose.yml` (padrão em `${VAR:-padrao}`) | `INTERNAL_TOKEN` |

Regras de camada (ARQ-02 — camadas):

- Resource: nenhum `raise`, nenhum SQL, nenhum atributo novo em `self` (o mesmo resource atende todas as requisições); chama um controller só.
- Controller: confere as regras na ordem do plano, antes de qualquer escrita; `self.session.commit()` é a última linha antes do `return`; não sabe de HTTP; nunca escreve consulta. Só ele chama `get_context()`, pelo `BaseController`.
- Repository: nenhuma regra de negócio; `with_for_update()` só onde o plano manda.
- DTO: só os campos que o plano lista.
- Connector: a única peça que chama serviço de fora, sempre com timeout (PRD-03 — timeout); quem o chama é o controller.
- Arquivo novo numa pasta com `__init__.py` entra também nesse `__init__.py`, na linha que o plano der. Em `src/models/__init__.py`, um model entra depois daquele de que depende; na ordem invertida, dá `ImportError`.

Onde mora cada coisa nova (o nome de cada arquivo vem do plano; "novo" = não existe no base):

| Coisa | Onde |
|---|---|
| Tabelas | `database/database.sql`, completo desde a fase 02 (DAD-15 — banco nasce inteiro) |
| Contas puras: tarifa, XP, nível, rendimento, impostos, sorteio | `src/calculations/` (novo). Importa só a biblioteca padrão do Python, `constants` e arquivos da própria pasta. Quem chama é o controller |
| Testes unitários | `tests/unit/` (novo, com `__init__.py` vazio); o `pytest.ini` (novo, na raiz) tem `pythonpath = src`, para o import achar `src/` |
| Testes de integração | `tests/integration/<recurso>/` |
| Funções de teste que montam dados por HTTP | `tests/utils/` |
| Rotas internas (API-13 — rotas `/internal`) | resource em `src/resources/`, caminho começando em `/internal`, registro em `src/app.py` |
| Connector do Banco Central (ARQ-07 — CDI) | `src/connectors/` |
| Arquivos que o Mockserver lê ao subir (ARQ-07, ARQ-12) | `mockserver/` (novo) |
| Script que baixa o CDI (ARQ-12 — Banco Central só no download) | `scripts/` (novo); nunca roda na suíte nem no compose |
| O arquivo que o Claude Code lê | `CLAUDE.md` (novo, na raiz), com uma linha só: `@AGENTS.md` |

## 5. Regras de todo passo

**Dinheiro e dados**

- **DAD-08, R6 — dinheiro em centavos inteiros.** `BIGINT` no banco, `int` no Python, inteiro no JSON (`5050` = R$ 50,50). Nunca `float`: nem em código, schema, teste ou exemplo. Nunca divida dinheiro com `/`, que devolve `float`. Fração de centavo (o resíduo do rendimento, COF-15) é `Decimal`.
- **API-18 — valor na entrada.** Campo de dinheiro no schema: `"type": "integer"` e `"minimum": 1`.
- **R5, DAD-12 — o `id` interno nunca sai.** Nem em resposta, erro, log ou exemplo. Para fora, só a key: UUID v4 gerado no repository. DTO nunca devolve `id` nem coluna terminada em `_id`.
- **R4, DAD-11 — append-only.** Nenhum código apaga ou altera operação, lançamento, depósito ou evento. Mudar estado é atualizar a coluna de estado e inserir o evento, na mesma transação. Proibido `DELETE` e soft delete.
- **MOV-05, MOV-11 — saldo sob trava.** Ler o saldo e gravar com base nele acontecem na mesma transação, com a linha travada por `with_for_update()`. Duas contas: as duas travadas, na ordem do `id`, menor primeiro.

**Erros e contrato**

- **R3, API-01, API-11 — toda falha tem código próprio e o status certo.** Corpo `{title, description, translation, code}`, com o `translation` em português. 400 formato · 403 token · 404 não existe ou não é seu · 409 duplicado ou estado que não permite · 422 regra de negócio · 429 tentativas demais · 503 dependência fora do ar ou lenta. Nunca 200 com erro; nunca 500 por regra de negócio.
- **API-12 — catálogo de erros.** Código, status, `title`, `description` e `translation` vêm do catálogo do `PLANO-fase-03.md`. Nunca invente um código; nunca repita um (a API não sobe).
- **R3, MOV-19 — `IntegrityError` nunca vira 500.** A violação de `UNIQUE` é tratada no controller e responde o que o plano define.
- **API-03 — schema fechado.** Corpo e query string passam por um schema de `src/schemas/` com `"additionalProperties": false`; fora dele, 400 `QIT000001`.
- **API-02 — status de sucesso sai do resource.** 201 criou, 202 recebeu e vai fazer, 204 pronto e sem corpo, 200 o resto.

**Segurança**

- **API-04 — `INTERNAL-TOKEN` em toda rota**, menos `/` e `/health_check`. Nunca acrescente rota em `BYPASS_ENDPOINTS`.
- **PRD-07, PRD-13 — rotas `/internal`.** Pedem o `INTERNAL-TOKEN` e mais o cabeçalho de administração; errar o segundo dá 403.
- **R8, API-08, API-09 — recurso de outro dono responde 404, nunca 403.** A conta da URL tem de ser a conta do token.
- **API-16 — token da conta.** Nasce na abertura, sai uma vez (na resposta 201) e fica guardado só como hash SHA-256. Nunca em log, nunca em outra resposta.
- **PRD-12 — dado sensível.** CPF e CNPJ de outra pessoa só saem mascarados. Log nunca guarda CPF, CNPJ, token nem corpo de requisição.
- **PRD-01 — configuração no ambiente.** Lida em `src/constants.py`, com padrão no `docker-compose.yml` e valor de mentirinha no `.env.example`. Nunca segredo no código; nunca `.env` no Git.
- **PRD-04 — nada de estado na memória do processo.** Contador e registro de regra moram no banco.

## 6. Testes

**O ciclo de todo passo** (TST-01 — black box e TDD):

1. Escreva os testes do campo **Testes**, exatamente como descritos.
2. Rode o arquivo do teste e veja falhar pelo motivo certo:
   - integração: asserção de status ou de corpo, porque a rota ou a regra ainda não existe;
   - unitário: `ModuleNotFoundError`, `ImportError` ou `AttributeError` com o nome do arquivo ou da função que o passo cria, ou asserção.

   Motivo errado se corrige antes de seguir: `SyntaxError`, `NameError` ou `IndentationError` no teste → corrija o teste; "Não consegui falar com a API" → rode `docker compose up -d --build --wait`. Teste novo que passa antes do código: PARE.
3. Escreva o código do passo.
4. Rode `docker compose up -d --build --wait` e a suíte inteira: tudo verde.
5. Rode o lint: nenhuma linha de saída.

Passo cujo campo **Testes** diz "nenhum teste novo": pule 1 e 2.

Passo cujo campo **Testes** diz "prova": o teste confere o que já existe. Escreva, rode e veja passar; se falhar, PARE, porque o conserto fica fora do passo.

**Regras**

- **TST-01 — black box.** Teste de integração fala com a API só por HTTP, pelas funções de `tests/utils/`, e programa o Mockserver por `tests/utils/mock_generator.py`; nunca importa de `src/`; monta os dados pelas rotas. O único contato com o banco é `DbUtils.rollback()`, na primeira linha dos testes que contam linhas.
- **PRD-10 e DIA-01 — testes que mexem no que é de todos.** Teste que erra token de propósito, ou que depende do relógio do banco, também começa com `DbUtils.rollback()`: a barreira conta erros de token por IP, e o relógio é um só para a suíte inteira.
- **TST-01 — dois testes por `if`.** Cada `if` do controller tem pelo menos um teste em que passa e um em que é barrado.
- **TST-02 — o que barra tem teste.** Se o plano diz que barra, existe um teste que fica vermelho quando deixa de barrar.
- **TST-05 — contas puras com unitário.** Toda função de `src/calculations/` tem teste em `tests/unit/`, escrito antes dela. O unitário de cálculo importa só de `calculations`, da biblioteca padrão e do `pytest`. Exceção TST-09: testes isolados em `tests/unit/infrastructure/` podem importar os módulos de infraestrutura sob teste e controlar relógio/conector/repository; não substituem os black box HTTP nem a prova de concorrência no PostgreSQL.
- **TST-06 — sorteio com gerador injetável.** A função do sorteio recebe o gerador de números como parâmetro; o unitário passa um gerador falso; o black box confere o que vale nos dois resultados.
- O nome de cada arquivo de teste é único em todo o `tests/`: o pytest importa os arquivos de pastas sem `__init__.py` só pelo nome.
- Dado de teste é inventado: CPF de `RandomGenerator.generate_cpf()`, e-mail com `uuid4()`. Nunca dado de gente de verdade.
- Proibido apagar, pular (`pytest.mark.skip`, `skipif`, `xfail`), comentar ou afrouxar teste, trocar valor esperado ou editar teste que já existia para ele passar. Só o plano manda mudar teste antigo, pelo campo **Arquivos**.

## 7. Git

Todos os roteiros podem entrar juntos antes da implementação, no commit local `docs(plano): roteiros auditados`. Verifique sua presença no histórico completo; não exija commit documental ou cópia antes de cada fase.

**Preparação documental antes da primeira implementação:** se o commit `docs(plano): roteiros auditados` ainda não existir e o `git status --short` mostrar somente roteiros auditados não rastreados em `docs/plano/`, registre esses arquivos no commit documental previsto, na `main`, antes de conferir o começo do passo. Use `git add --` com cada caminho explícito e confira o conteúdo staged e a mensagem do commit. Essa preparação é autorizada e não exige confirmação; a saída não vazia nessa situação não é condição de parada. Se houver qualquer outra alteração, aplique as condições de parada normalmente. Não modifique os roteiros.

Correções de `AGENTS.md` expressamente solicitadas pelo Bruno podem ser feitas e registradas em commit local próprio antes dessa preparação; não fazem parte dos arquivos de um passo de implementação. Fora dessa autorização expressa, permanece a proibição de editar este arquivo.

**TIM-04, TIM-08 — git automático.** Uma branch por fase, `fase/NN-<nome>` (o valor do campo **Branch**); um commit por passo; merge na `main` só no `Passo N.fim`; sem pull request.

A mensagem de commit e a de merge são as do plano, exatas, numa linha (Conventional Commits em português). Nenhuma linha a mais: nem `Co-Authored-By`, nem assinatura de ferramenta.

**Começo de todo passo**

1. `git status --short` → saída vazia.
2. No `Passo N.1`, abra a fase:
   ```
   git switch main
   git switch -c fase/NN-<nome>
   ```
   Nos outros passos: `git branch --show-current` → exatamente o valor do campo **Branch**.
3. Cada passo do campo **Depende de** tem a sua mensagem de commit em `git log --oneline`.

**Fim de todo passo** (suíte verde e lint sem saída)

```
git add -- <cada arquivo criado ou editado no passo>
git rm -- <cada arquivo que o passo manda apagar>
git diff --cached --name-only
git diff --name-only
git ls-files --others --exclude-standard
git commit -m "<mensagem exata do campo Commit>"
git log -1 --format=%B
```

- O `git rm` só entra no passo que manda apagar arquivo, e é o único jeito de apagar.
- O `git diff --cached --name-only` lista exatamente os arquivos do passo; os dois comandos seguintes saem vazios.
- O `git log -1 --format=%B` mostra só a mensagem do plano.
- O aviso `LF will be replaced by CRLF` não é erro.

**Fim da fase — `Passo N.fim`**

```
docker compose down -v
docker compose up -d --build --wait
./.venv/Scripts/python.exe -m pytest
./.venv/Scripts/python.exe -m flake8 src tests
git status --short
git switch main
git merge --no-ff --no-edit -m "<mensagem exata do plano>" fase/NN-<nome>
git tag fase-NN
```

- O merge só acontece com a suíte verde, o lint sem saída e o `git status --short` vazio.
- O `git status --short` antes do merge não mostra alterações.

**Proibido:** `git push --force`, `-f` e `--force-with-lease`; `git commit --amend`; `git rebase`; `git reset`; `git add .`, `git add -A` e `git add --all`; `git commit -a`; `git stash`; `git restore`; `git checkout -- <arquivo>`; `git clean`; `git merge --squash`; apagar branch ou tag; mudar o `git config`; abrir pull request; commit com teste vermelho ou lint com saída; commitar o `.env`.

## 8. Quando parar

As condições abaixo se aplicam depois das exceções de preparação documental e da política de autonomia da seção 2. Falha operacional recuperável e correção necessária expressamente autorizada não são motivos para interromper a execução na primeira tentativa.

PARE quando:

1. Um teste, o lint ou o **Verificar** não passa depois de 3 tentativas. Tentativa = mudar só arquivos do campo **Arquivos** e rodar de novo o que falhou.
2. Um arquivo, função, comando ou nome que o plano cita não existe, ou um comando local do plano ou deste arquivo falha (inclusive `docker compose`).
3. O passo exige uma escolha que o plano não define: nome, valor, ordem, status, código de erro ou mensagem.
4. O passo exige mexer em arquivo fora do campo **Arquivos**.
5. O plano contradiz este arquivo.
6. Uma conferência do começo do passo (seção 7) falha.
7. Um teste novo passa antes do código (fora dos passos de prova).
8. O `git log -1 --format=%B` mostra mais que a mensagem do plano.
9. No fim da fase, o merge local dá conflito.
10. Acontece uma situação do campo **Pare se** do passo.

Ao parar: nada de commit, merge, desfazer ou apagar. Responda só com este relatório:

```
PASSO: <N.M — título>
O QUE FIZ: <números dos itens do Passo a passo concluídos>
ONDE PAREI: <item do Passo a passo e o comando>
ERRO (saída exata): <as últimas 60 linhas da saída que falhou, sem mudar nada>
ARQUIVOS ALTERADOS: <a saída de git status --short>
```

Se o erro envolve a API, junte ao ERRO a saída de `docker compose logs --tail 100 api`.

## 9. Checklist de fim de passo

- [ ] Li o passo inteiro e segui o **Passo a passo** na ordem.
- [ ] Só os arquivos do campo **Arquivos** foram criados, editados ou apagados.
- [ ] Os testes novos falharam antes do código, pelo motivo certo.
- [ ] `docker compose up -d --build --wait` terminou sem erro; o banco foi recriado do zero, se o passo mudou `database/database.sql`.
- [ ] Na suíte inteira, a última linha do pytest tem `passed` e não tem `failed`, `error`, `skipped`, `xfailed` nem `xpassed`.
- [ ] O lint não imprimiu nenhuma linha.
- [ ] Os comandos do **Verificar** deram a saída esperada; todos os itens do **Pronto quando** estão cumpridos.
- [ ] Nos arquivos do passo: nenhum `id` interno para fora, nenhum `float` em dinheiro, nenhum segredo, nenhum CPF, CNPJ ou token em log.
- [ ] Nenhum arquivo, dependência, campo, rota, erro ou teste além do passo.
- [ ] As conferências do fim do passo (seção 7) deram o esperado; o `.env` ficou fora.
- [ ] Commit local com a mensagem exata feito.

No `Passo N.fim`, o fechamento é o da seção 7, com o merge no lugar do commit.

Passo concluído: responda `PASSO N.M CONCLUÍDO` e a saída de `git log -1 --oneline`.


## Auditoria do plano — 08/10/2026

O plano fonte está em `Plano no chat/plano/`, na pasta mãe de `score`. As fases detalhadas disponíveis e auditadas são 2, 3, 4, 5, 6, 8, 7, 9 e 11, nessa ordem. As nove regras fechadas foram aplicadas aos trechos e testes dos roteiros na segunda auditoria de 08/10, registrada no relatório histórico da pasta fonte Plano no chat/plano, fora do score. Copiar todos os roteiros auditados para score/docs/plano no início e registrar o único commit documental previsto; não exigir cópia por fase nem relatório de auditoria no score. Não presumir que o plano foi implementado: `score` ainda contém o sample do base. Correção desta documentação foi autorizada expressamente pelo Bruno para esta auditoria.

Regra sobre commits e camadas: os passos detalhados de dinheiro tratam `IntegrityError` com rollback e repetição; bloqueio automático faz commit antes de lançar sua recusa, conforme CLI-08. Essas exceções expressas prevalecem sobre a frase geral “commit é a última linha antes do return”. Testes de prova da fase 11 podem começar verdes quando verificam comportamento existente; não exigir um erro de importação artificial. CPF, CNPJ e tokens também não podem aparecer nos parâmetros de exceções SQL (`hide_parameters=True`, fase 4.4).
