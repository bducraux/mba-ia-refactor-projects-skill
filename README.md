# Skill `refactor-arch` — Auditoria e Refatoração Arquitetural Automatizada

Skill do **Claude Code** que analisa um backend, audita contra um catálogo de anti-patterns, gera um relatório por severidade e, **após confirmação humana**, refatora o projeto para MVC e valida que a aplicação continua funcionando. A skill foi executada nos 3 projetos legados deste repositório (2× Python/Flask, 1× Node.js/Express).

| Entregável | Onde |
| --- | --- |
| Skill (cópia idêntica nos 3 projetos) | `*/.claude/skills/refactor-arch/` → `SKILL.md` + `references/01..05` |
| Código refatorado (saída da Fase 3) | `code-smells-project/`, `ecommerce-api-legacy/`, `task-manager-api/` |
| Relatórios de auditoria (saída da Fase 2) | [`reports/audit-project-1.md`](reports/audit-project-1.md), [`audit-project-2.md`](reports/audit-project-2.md), [`audit-project-3.md`](reports/audit-project-3.md) |
| Estado original dos projetos | tag `baseline-original` |

---

## A) Análise Manual

Feita **antes** de escrever a skill, lendo cada arquivo com número de linha (estado `baseline-original`). Serviu de gabarito para conferir a Fase 2.

### Projeto 1 — `code-smells-project` (Python/Flask 3.1.1, SQLite, e-commerce) — 4 arquivos, 780 linhas

| Severidade | Problema | Local | Por que é relevante |
| --- | --- | --- | --- |
| CRITICAL | SQL injection por concatenação de strings | `models.py:28, 47-50, 57-61, 92, 109-111, 126-129, 174, 280, 289-297` (entre outras) | Entrada do usuário entra direto na query: bypass do login (`' OR 1=1 --`), leitura e escrita em qualquer tabela. |
| CRITICAL | `SECRET_KEY` e `DEBUG` hardcoded e expostos | `app.py:7-8, 88`; `controllers.py:285-289` | Segredo no código, e `GET /health` devolve a `secret_key` para qualquer pessoa. O debug ativo expõe o debugger do Werkzeug. |
| CRITICAL | Endpoints administrativos sem autenticação (SQL arbitrário e reset do banco) | `app.py:47-57, 59-78` | `/admin/query` é SQL injection por design; `/admin/reset-db` apaga tudo. |
| CRITICAL | Senhas em texto puro, comparadas e devolvidas pela API | `database.py:75-83`; `models.py:83, 99, 109-111` | `GET /usuarios` lista as senhas de todos os usuários. |
| HIGH | Regra de negócio e efeitos colaterais nos controllers/models, sem camada de serviço | `controllers.py:28-54, 208-210, 247-250`; `models.py:256-262` | Validação, notificação e regra de desconto ficam espalhadas, e nada é testável isoladamente. |
| HIGH | Conexão global mutável compartilhada entre threads | `database.py:4-11` | Singleton com `check_same_thread=False`: acoplamento e risco de concorrência. |
| MEDIUM | Queries N+1 na listagem de pedidos | `models.py:187-199, 219-231` | 1 + N + N×M queries por chamada. |
| MEDIUM | Validação e mapeamento row→dict duplicados | `controllers.py:28-50` vs `72-90`; `models.py:12-21, 31-40, 304-313` | As cópias divergem com a manutenção. |
| MEDIUM | Tratamento de erro espalhado, devolvendo `str(e)` | `controllers.py:10-12, 21-22, 60-62…` | Vaza detalhes internos; não há handler central. |
| LOW | `print` usado como log | `controllers.py:8, 57, 179, 208-210` | Sem níveis de log; e-mails de usuários vão para o stdout. |
| LOW | Magic numbers e listas mágicas | `models.py:257-262`; `controllers.py:52, 242` | Faixas de desconto e listas de status sem nome nem fonte única. |
| LOW | Import não usado e shadowing de builtin | `models.py:2`; `controllers.py:56` (`id`) | Ruído e risco de bug sutil. |

### Projeto 2 — `ecommerce-api-legacy` (Node.js/Express 4, sqlite3 em memória, LMS + checkout) — 3 arquivos, 180 linhas

| Severidade | Problema | Local | Por que é relevante |
| --- | --- | --- | --- |
| CRITICAL | Credenciais e chave de pagamento hardcoded | `src/utils.js:1-7` | Senha do banco e chave `pk_live` no código-fonte versionado. |
| CRITICAL | God Class: banco, schema, seed, rotas e regras numa classe | `src/AppManager.js:4-141` | Nenhuma separação de camadas. |
| CRITICAL | Número do cartão no log e "hash" de senha reversível | `src/AppManager.js:45, 68`; `src/utils.js:17-23` | Dado PCI no log; `badCrypto` é base64 truncado; senha padrão `"123456"`. |
| HIGH | Regra de negócio dentro do handler, com callback hell | `src/AppManager.js:28-78` | Pagamento, criação de usuário, matrícula e auditoria aninhados em 5 níveis. |
| HIGH | Estado global mutável | `src/utils.js:9-15` | `globalCache` e `totalRevenue` são de módulo e cresce sem limite. |
| MEDIUM | N+1 no relatório financeiro | `src/AppManager.js:89-127` | 2 queries por matrícula, mais contadores manuais de callbacks. |
| MEDIUM | Validação ausente e erros inconsistentes (texto vs JSON) | `src/AppManager.js:35, 38, 41, 48, 135` | Um `card` numérico derruba o processo. |
| MEDIUM | DELETE sem cascata e com o erro ignorado | `src/AppManager.js:131-137` | Matrículas e pagamentos ficam órfãos, e a resposta é sempre de sucesso. |
| LOW | Nomes crípticos | `src/AppManager.js:29-33` (`u`, `e`, `p`, `cid`, `cc`) | Leitura difícil. |
| LOW | Magic values | `src/AppManager.js:46` (`"4"` = aprovado), `68`; `src/utils.js:6` | Regra de negócio escondida em literais. |

### Projeto 3 — `task-manager-api` (Python/Flask 3.0 + Flask-SQLAlchemy, SQLite, Task Manager) — 15 arquivos, ~1.150 linhas

| Severidade | Problema | Local | Por que é relevante |
| --- | --- | --- | --- |
| CRITICAL | Segredos hardcoded (`SECRET_KEY`, senha de SMTP) | `app.py:13`; `services/notification_service.py:7-10` | Segredos no repositório. |
| CRITICAL | Senha com MD5 sem salt e hash exposto nas respostas | `models/user.py:21, 27-32` | `to_dict()` devolve `password` em GET/POST/PUT `/users` e no login. |
| HIGH | Fat routes: lógica e queries nas rotas, camada de serviço não usada | `routes/task_routes.py:11-63, 156-223`; `routes/report_routes.py:12-101` | Organização só aparente: as pastas existem, mas as camadas não. |
| HIGH | Autenticação falsa | `routes/user_routes.py:207-211` | Token `fake-jwt-token-<id>` previsível. |
| MEDIUM | Queries N+1 | `routes/task_routes.py:41-57`; `routes/report_routes.py:53-68, 157-165`; `routes/user_routes.py:22` | Uma query por task, usuário ou categoria. |
| MEDIUM | Regra de "atraso" duplicada 6×, ignorando `Task.is_overdue` e os helpers | `routes/task_routes.py:30-39, 71-80, 283-287`; `routes/report_routes.py:33-43, 132-135` | Código morto ao lado das cópias. |
| MEDIUM | `except:` genérico engolindo erros | `routes/task_routes.py:62, 137, 204, 236`; `routes/user_routes.py:130, 149` | Esconde a causa; não há handler central. |
| MEDIUM | APIs deprecated | `datetime.utcnow()` (`models/task.py:15-16, 52`…), `Query.get()` (`routes/task_routes.py:42, 51, 67`…) | `utcnow` está deprecated desde o Python 3.12; `Query.get` é legado no SQLAlchemy 2.x. |
| LOW | Imports não usados e `print` usado como log | `app.py:7`; `routes/task_routes.py:7, 149`; `utils/helpers.py:2-7` | Ruído. |
| LOW | Magic numbers e listas repetidas | `routes/task_routes.py:110, 113, 177, 182`; `routes/report_routes.py:24-28, 129` | As constantes de `utils/helpers.py:110-116` existem e não são usadas. |

---

## B) Construção da Skill

### Estrutura

```
.claude/skills/refactor-arch/
├── SKILL.md                          # o "prompt": 3 fases, regras, formatos de saída
└── references/
    ├── 01-project-analysis.md        # heurísticas: stack, versão, banco, domínio, arquitetura, inventário de endpoints
    ├── 02-anti-patterns-catalog.md   # 18 anti-patterns (sinais de detecção + severidade) + tabela de APIs deprecated
    ├── 03-report-template.md         # formato exato do relatório da Fase 2
    ├── 04-mvc-guidelines.md          # camadas, o que é proibido em cada uma, estrutura-alvo Flask/Express e projetos já organizados
    └── 05-refactoring-playbook.md    # 16 transformações com código antes/depois (Python e JS)
```

### Decisões de design

1. **O SKILL.md orquestra e as referências trazem o conhecimento.** Cada fase começa mandando ler a referência da própria fase. O conteúdo do SKILL.md é prescritivo: campos obrigatórios, formato exato dos blocos `PHASE 1`, `ARCHITECTURE AUDIT REPORT` e `PHASE 3`, e regras de ouro.
2. **Somente leitura até o "y".** As Fases 1 e 2 não podem criar nem editar nada, **nem o relatório**. O relatório só é gravado depois da resposta, seja ela "y" ou "n". Com "n", a skill salva o relatório e encerra sem tocar no projeto.
3. **"Endpoints funcionando" é medido, e não presumido.** A Fase 3 começa gravando um baseline: sobe a app original, chama cada endpoint do inventário da Fase 1 e registra status e chaves das respostas. Depois de refatorar, repete as mesmas chamadas e compara.
4. **Preservação de contrato com exceção explícita.** Mesmos paths, métodos, status, formato de resposta e comando de start. Corrigir segurança às vezes **obriga** a mudar uma resposta (tirar `senha` do JSON, exigir token num endpoint que executa SQL arbitrário). Isso só é permitido para remover vulnerabilidade, e cada mudança tem de aparecer em **"Intentional contract changes"**.
5. **Linhas reais.** A skill é proibida de estimar números de linha: precisa tirá-los da leitura com número de linha ou do `grep -n`. Cada finding cita a entrada do catálogo e a transformação do playbook (`PB-xx`).
6. **`disable-model-invocation: true`.** A skill modifica código, então só roda quando chamada explicitamente com `/refactor-arch`.

### Anti-patterns do catálogo e por quê

| Severidade | Anti-patterns | Motivo da inclusão |
| --- | --- | --- |
| CRITICAL | AP-01 credenciais e config hardcoded · AP-02 SQL injection · AP-03 God file/class · AP-04 endpoints perigosos sem proteção · AP-05 senha insegura e exposição de dados sensíveis | São falhas de segurança ou de separação total de camadas, os exemplos da própria definição de CRITICAL do desafio, e apareceram na análise manual. |
| HIGH | AP-06 fat controllers · AP-07 estado global mutável · AP-08 acoplamento sem DI · AP-09 autenticação falsa ou ausente | São as violações de MVC/SOLID da definição de HIGH. |
| MEDIUM | AP-10 N+1 · AP-11 validação ausente · AP-12 erro espalhado · AP-13 duplicação e abstração não usada · AP-14 escrita não atômica e integridade · AP-15 callback hell | Performance, padronização e integridade. Aparecem nos 3 projetos com formas diferentes. |
| LOW | AP-16 print/console como log · AP-17 magic numbers · AP-18 nomes ruins, imports e código morto | Legibilidade. |
| Deprecated | Tabela com 13 APIs (Python 3.12, SQLAlchemy 2.x, Flask, Node, Express) e o equivalente moderno de cada uma | Exigência do desafio. Pegou `utcnow`, `Query.get`, MD5 e o sqlite3 em callbacks. |

Cada entrada traz **sinais de detecção concretos** (padrões de `grep -n` e o que confirmar no contexto), exemplo em Python e/ou JS e a transformação recomendada.

### Como garanti que a skill é agnóstica

- **Decisão por evidência, nunca pelo nome da pasta.** A stack vem dos manifests, dos imports e da versão no `requirements.txt` ou no lockfile.
- **Catálogo e playbook com exemplos em Python e em JS**, e estrutura-alvo para Flask e para Express. Para projetos já organizados a regra é **evoluir**: manter as pastas que já servem e adicionar só as camadas que faltam.
- **Nenhum identificador dos projetos-alvo nas referências.** A primeira versão estava acoplada: os exemplos usavam `/produtos`, `AppManager`, `/admin/query`, `cc.startsWith("4")`, as faixas de desconto 10000/0.1, as tabelas `courses`/`enrollments`, `Task` e o envelope `erro`/`dados`/`sucesso`. Uma varredura com `grep` pelos nomes dos 3 projetos achou tudo isso, e troquei por exemplos neutros (items, invoices, groups/members, Post, `X-Admin-Token`). Ficaram só sinais de detecção multilíngues (`senha|password`) e mapeamentos genéricos de domínio.
- **A mesma skill, byte a byte, nos 3 projetos** (`diff -r` sem saída).

### Desafios encontrados e como resolvi

| Desafio | Solução |
| --- | --- |
| A segurança conflita com "endpoints originais respondem" (senha no JSON, `/admin/query` executando SQL). | Regra de **mudança intencional de contrato**, restrita a correções de segurança e listada na saída da Fase 3. As rotas perigosas são **protegidas por token** (`X-Admin-Token` ou Bearer admin), nunca removidas. |
| Garantir que a Fase 2 não modifica arquivos. | Regra no SKILL.md somada a uma execução com ferramentas de escrita **bloqueadas pela própria CLI**. Testei a resposta "n" num fork da sessão: só o relatório foi criado e o `git status` do projeto ficou limpo. |
| O relatório precisa ir para `reports/audit-project-N.md`, mas `/refactor-arch` não recebe argumento. | A skill grava em `<raiz do git>/reports/audit-<pasta>.md`, e eu renomeei para `audit-project-N.md`. |
| Risco de a Fase 3 "consertar" a autenticação falsa do projeto 3 exigindo token em todas as rotas, o que quebraria os 22 endpoints. | As regras de contrato do SKILL.md seguraram: só `DELETE /users` e a troca de role passaram a exigir admin, e as demais rotas seguem abertas como no original (documentado). |
| Validar sem confiar só no relato da skill. | Script de smoke **independente** (fora do repositório): 72 chamadas de sucesso e de erro gravadas no estado original e comparadas com o estado refatorado (status e formato do JSON). |
| Falso alarme: na minha primeira validação manual do projeto 1 apareceram erros 500. | A causa era um servidor **órfão da minha própria tentativa anterior**, preso na porta 5000 com o banco apagado por baixo dele. Reproduzi em processo isolado (tudo certo), encerrei o PID, refiz o teste e passou. O smoke agora aborta se a porta já estiver ocupada. |
| Python 3.14 local, mas as dependências estão fixadas para versões mais antigas. | Virtualenvs com Python 3.12 via `uv`. |

---

## C) Resultados

### Execução

A skill foi executada em **sessões headless do Claude Code**, uma por projeto:

```bash
cd <projeto>
claude -p "/refactor-arch" --permission-mode dontAsk --disallowedTools Edit Write ...   # Fases 1–2 (somente leitura)
claude -p "y" --resume <session-id> --permission-mode acceptEdits ...                  # resposta à pergunta da Fase 2 → Fase 3
```

| Projeto | Fases 1–2 | Fase 3 |
| --- | --- | --- |
| 1 — code-smells-project | 12 turnos | 63 turnos |
| 2 — ecommerce-api-legacy | 13 turnos | 51 turnos |
| 3 — task-manager-api | 25 turnos | 63 turnos |

### Findings por severidade

| Projeto | CRITICAL | HIGH | MEDIUM | LOW | Total | Deprecated detectadas | Análise manual coberta |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [1 — code-smells-project](reports/audit-project-1.md) | 5 | 4 | 5 | 3 | **17** | nenhuma (declarado no relatório) | 12/12 |
| [2 — ecommerce-api-legacy](reports/audit-project-2.md) | 4 | 3 | 6 | 3 | **16** | sqlite3 em callbacks → promises/async | 10/10 |
| [3 — task-manager-api](reports/audit-project-3.md) | 2 | 4 | 7 | 4 | **17** | `datetime.utcnow()`, `Query.get()`, `hashlib.md5` | 10/10 |

### Estrutura antes → depois

<details open><summary><b>Projeto 1 — code-smells-project</b> (monólito com divisão superficial → MVC em <code>src/</code>)</summary>

```
ANTES                         DEPOIS
app.py                        app.py                      # entry point fino (python app.py)
controllers.py                .env.example
database.py                   src/
models.py                     ├── app.py                  # create_app(): composition root
requirements.txt              ├── config/settings.py
                              ├── database/{connection,schema}.py   # conexão por request (flask.g), schema+seed
                              ├── models/{produto,usuario,pedido,admin}_model.py
                              ├── services/{produto,usuario,pedido,relatorio,notificacao,health,admin}_service.py
                              ├── controllers/{produto,usuario,pedido,sistema}_controller.py
                              ├── routes/{produto,usuario,pedido,sistema}_routes.py
                              ├── validators/{produto,usuario,pedido,admin}_validator.py
                              ├── middlewares/{error_handler,auth}.py
                              └── utils/{constants,errors,logger,security}.py
```
</details>

<details open><summary><b>Projeto 2 — ecommerce-api-legacy</b> (God Class → MVC)</summary>

```
ANTES                         DEPOIS
src/app.js                    package.json                # "start": "node src/server.js"
src/AppManager.js             .env.example
src/utils.js                  src/
api.http                      ├── server.js               # composition root + listen
package.json                  ├── app.js                  # buildApp(): rotas + error middleware
                              ├── config/index.js
                              ├── database/{index,schema}.js        # wrapper promisificado + transaction()
                              ├── models/{user,course,enrollment,payment,auditLog}Model.js
                              ├── services/{checkout,report,user}Service.js, paymentGateway.js
                              ├── controllers/{checkout,report,user}Controller.js
                              ├── validators/{checkout,user}Validator.js
                              ├── routes/index.js
                              ├── middlewares/{errorHandler,requireAdmin,asyncHandler}.js
                              └── utils/{constants,errors,logger,password}.js
```
</details>

<details open><summary><b>Projeto 3 — task-manager-api</b> (parcialmente em camadas → camadas completas, evoluindo a estrutura existente)</summary>

```
ANTES                         DEPOIS
app.py                        app.py                      # entry point (python app.py)
database.py                   app_factory.py              # composition root (novo)
seed.py                       database.py                 # db + transaction() + PersistenceMixin
models/{task,user,category}   seed.py                     # usa create_app(); senhas com hash
routes/{task,user,report}     config/settings.py          # (novo)
services/notification         models/{task,user,category}.py        # todo o acesso a dados (select 2.x, GROUP BY, joinedload)
utils/helpers.py              services/{task,user,auth,report,category,notification}_service.py
requirements.txt              controllers/{task,user,report,category,system}_controller.py   # (novo)
                              routes/{task,user,report,category,system}_routes.py            # só mapeamento
                              validators/{task,user,category}_validator.py                   # (novo)
                              middlewares/{error_handler,auth}.py                            # (novo)
                              utils/{constants,errors,helpers}.py
```
</details>

### Checklist de validação

| Item | P1 | P2 | P3 |
| --- | --- | --- | --- |
| **Fase 1** — Linguagem detectada corretamente | ✅ Python | ✅ JavaScript (Node, CommonJS) | ✅ Python |
| Framework detectado corretamente | ✅ Flask 3.1.1 | ✅ Express 4.22.1 (via lockfile) | ✅ Flask 3.0.0 |
| Domínio descrito corretamente | ✅ E-commerce | ✅ LMS com checkout | ✅ Task management |
| Nº de arquivos condiz com a realidade | ✅ 4 / 780 LOC / 19 rotas | ✅ 3 / 180 LOC / 3 rotas | ✅ 15 / 1158 LOC / 22 rotas |
| **Fase 2** — Relatório segue o template | ✅ | ✅ | ✅ |
| Cada finding com arquivo e linhas exatos | ✅ (amostra conferida) | ✅ (amostra conferida) | ✅ (amostra conferida) |
| Findings ordenados CRITICAL → LOW | ✅ | ✅ | ✅ |
| Mínimo de 5 findings | ✅ 17 | ✅ 16 | ✅ 17 |
| Detecção de APIs deprecated (se aplicável) | ✅ n/a (declarado) | ✅ 1 | ✅ 3 |
| Pausa e pede confirmação antes da Fase 3 | ✅ (testado com "n") | ✅ | ✅ |
| **Fase 3** — Estrutura de diretórios MVC | ✅ | ✅ | ✅ |
| Config extraída (sem hardcoded) | ✅ `src/config/settings.py` + `.env.example` | ✅ `src/config/index.js` + `.env.example` | ✅ `config/settings.py` + `.env.example` |
| Models abstraem os dados | ✅ | ✅ | ✅ |
| Views/Routes separadas | ✅ | ✅ | ✅ |
| Controllers concentram o fluxo | ✅ | ✅ | ✅ |
| Error handling centralizado | ✅ | ✅ | ✅ |
| Entry point claro | ✅ `python app.py` | ✅ `npm start` | ✅ `python app.py` |
| Aplicação inicia sem erros | ✅ | ✅ | ✅ |
| Endpoints originais respondem | ✅ 28/33 idênticos + 5 mudanças intencionais | ✅ 5/7 idênticos + 2 intencionais | ✅ 27/32 idênticos + 5 intencionais |

### Validação independente: endpoints antes × depois

Smoke próprio, fora do repositório, rodado com banco zerado no estado original e no refatorado. Ele compara status HTTP e o formato do JSON (chaves). Todas as diferenças são **exatamente** as que a skill declarou em "Intentional contract changes", e as rotas protegidas foram testadas também **com** o token:

| Projeto | Diferenças (todas por segurança) | Teste com token/credencial |
| --- | --- | --- |
| 1 | `GET /health` sem `secret_key`/`db_path`/`debug`; `GET /usuarios`, `/usuarios/1` sem `senha`; `POST /admin/query` e `/admin/reset-db` → 403 sem `X-Admin-Token` | Com token: `SELECT` → 200; `DELETE` via `/admin/query` → 400 (somente leitura); token errado → 403; SQL injection no login → 401 |
| 2 | `GET /api/admin/financial-report` e `DELETE /api/users/:id` → 403 sem `X-Admin-Token` | Com token: relatório 200 com o mesmo JSON; DELETE 200 apagando também matrículas e pagamentos; token errado → 403 |
| 3 | `password` (hash) removido de `GET /users/1`, `POST /users`, `PUT /users/2`, `POST /login`; `DELETE /users/3` → 401 sem token | Token de admin (do `/login`) → 200; token de usuário comum → 403; token antigo `fake-jwt-token-1` → 401 |

### Logs das aplicações refatoradas rodando

Projeto 1 (`python app.py`):
```
INFO src.database.schema: Banco populado com dados de exemplo
INFO __main__: Servidor iniciado em http://localhost:5000
 * Serving Flask app 'src.app'
 * Debug mode: off
 * Running on all addresses (0.0.0.0)
[smoke] boot=OK | 33 chamadas | 33 com status < 500
```

Projeto 2 (`npm start`). O cartão aparece só com os 4 últimos dígitos:
```
[info] ADMIN_TOKEN não configurado: endpoints administrativos desabilitados (403).
[info] LMS API rodando na porta 3000...
[info] Pagamento de 497 no cartão final 4444: PAID
[info] Pagamento de 997 no cartão final 4444: DENIED
[smoke] boot=OK | 7 chamadas | 7 com status < 500
```

Projeto 3 (`python seed.py && python app.py`):
```
 * Serving Flask app 'app_factory'
 * Debug mode: off
 * Running on http://127.0.0.1:5000
[smoke] boot=OK | 32 chamadas | 32 com status < 500
(0 DeprecationWarning / LegacyAPIWarning no log)
```

### Como a skill se comportou em stacks diferentes

- **Monólito Python (P1):** criou toda a estrutura em `src/` e manteve `app.py` como bootstrap fino, de modo que o comando de start não mudou. Migrou as senhas em texto puro de um banco existente para hash na inicialização.
- **Node/Express (P2):** trocou o callback hell por um wrapper promisificado com `async/await` e transação explícita, e transformou o N+1 do relatório em um único `LEFT JOIN` que mantém o JSON original. Preservou as respostas em texto puro (`"Bad Request"`, `"Curso não encontrado"`) que o original usava.
- **Flask parcialmente organizado (P3):** **não reescreveu**. Manteve `models/`, `routes/`, `services/` e `utils/` na raiz, adicionou `config/`, `controllers/`, `validators/`, `middlewares/` e `app_factory.py`, moveu o acesso a dados para os models (`select` 2.x, `GROUP BY`, `joinedload`) e substituiu as APIs deprecated.
- Nos 3 projetos, a skill identificou o domínio e a versão do framework pelos arquivos de manifest e lock, e não pelo nome da pasta.

---

## D) Como Executar

### Pré-requisitos

- **Claude Code** instalado e autenticado (`npm install -g @anthropic-ai/claude-code`, depois `claude`).
- Python 3.12 (projetos 1 e 3) e Node.js 18+ (projeto 2).
- Git (a skill grava o relatório na raiz do repositório).

### Rodar a skill num projeto

A skill já está em `.claude/skills/refactor-arch/` dentro de cada projeto. Para reexecutar a partir do código original:

```bash
git checkout baseline-original -- code-smells-project   # opcional: volta o projeto ao estado original (mantém a skill)
cd code-smells-project
claude "/refactor-arch"
# Fase 1 (análise) → Fase 2 (relatório) → pergunta "Proceed with refactoring (Phase 3)? [y/n]"
# responda "y" para refatorar ou "n" para só salvar o relatório
```

Repita em `ecommerce-api-legacy/` e `task-manager-api/`. O relatório é gravado em `reports/audit-<pasta>.md`; nesta entrega eles foram renomeados para `reports/audit-project-{1,2,3}.md`.

### Rodar e validar as aplicações refatoradas

```bash
# Projeto 1 — http://localhost:5000
cd code-smells-project && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python app.py
curl localhost:5000/health && curl localhost:5000/produtos
ADMIN_TOKEN=troque-me .venv/bin/python app.py      # habilita /admin/* (header X-Admin-Token: troque-me)

# Projeto 2 — http://localhost:3000
cd ecommerce-api-legacy && npm install && npm start
curl -X POST localhost:3000/api/checkout -H 'Content-Type: application/json' \
  -d '{"usr":"Ana","eml":"ana@x.com","pwd":"s3nha","c_id":2,"card":"4111222233334444"}'
ADMIN_TOKEN=troque-me npm start                     # habilita relatório financeiro e DELETE de usuário

# Projeto 3 — http://localhost:5000
cd task-manager-api && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python seed.py && .venv/bin/python app.py
curl localhost:5000/tasks && curl localhost:5000/reports/summary
# token de admin: POST /login com joao@email.com / 1234 → usar "Authorization: Bearer <token>" em DELETE /users/<id>
```

Cada projeto tem um `.env.example` com todas as variáveis. Sem `.env`, as aplicações sobem com defaults seguros de desenvolvimento: debug desligado e rotas administrativas desabilitadas.

**Como confirmar que a refatoração funcionou:** chame os endpoints de `api.http` (P2) ou do inventário da Fase 1 (no relatório de cada projeto) e compare com o comportamento original, recuperável com `git checkout baseline-original -- <projeto>`. As únicas diferenças esperadas são as listadas acima.

### Ordem sugerida

1. Projeto 1 (monólito Python: mostra o fluxo completo).
2. Projeto 2 (stack diferente: prova o agnosticismo).
3. Projeto 3 (projeto parcialmente organizado: prova a adaptação sem reescrever).
