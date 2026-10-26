# Verificação dos roteiros e da aprovação em lote

Em 26/10/2026, o percurso do professor e do aluno foi exercitado num servidor descartável, num browser aberto pelo Agent Browser Hub, perfil `research`. Os testes ligaram-se ao CDP dessa sessão através do percurso existente em `tests/browser/conftest.py`.

## Percursos verificados

- Uma pesquisa por um jogo permite selecionar os seis jogos da respetiva palavra. Uma confirmação publica a seleção completa.
- O professor atribui os seis jogos a Ana e Bruno, e uma atividade de matemática a Carla, no mesmo roteiro.
- A entrada habitual `/student/` reconhece o código de sete caracteres. Cada aluno vê apenas as atividades que lhe foram atribuídas no roteiro.
- O nome e a turma são preenchidos a partir da turma guardada. A realização fica associada ao roteiro e ao identificador do aluno.
- Depois da autoavaliação, o aluno volta à sua lista de atividades.
- O professor altera um conjunto, encerra o roteiro e abre os registos filtrados pela aula.
- Escolher outro nome no mesmo browser não apresenta o trabalho do aluno anterior. A troca explícita guarda primeiro os registos pendentes.
- Encerrar o roteiro impede novas entradas, mas uma realização já iniciada recupera após recarregar a página e pode terminar.
- A API rejeita atribuições de rascunhos, alunos fora da turma e listas vazias. Alterações concorrentes do roteiro devolvem conflito. Um aluno em vários conjuntos recebe a união das atividades, sem duplicação.

## Comandos e resultados

```bash
.venv/bin/pytest --ignore=tests/browser -q
```

584 testes passaram; um falhou em `tests/test_m28p_tic.py::test_all_generated_games_are_complete_private_artifacts_with_offline_assets`. Esse teste exige a ausência de todos os jogos em `activities/`, mas vários desses diretórios já estavam presentes e por versionar no início desta sessão. A verificação não apagou nem alterou esses conteúdos.

```bash
.venv/bin/pytest tests/test_learning.py tests/test_access.py tests/test_teacher_client_access.py tests/test_student_client_access.py -q
```

32 testes passaram.

```bash
PAGECRAFT_TEST_CDP=http://127.0.0.1:9330 uv run --offline --with playwright==1.63.0 pytest tests/browser/test_lesson_plans.py tests/browser/test_learning_authorship_ui.py tests/browser/test_learning_recovery.py tests/browser/test_learning_initialization.py -q
```

34 testes passaram. Depois de acrescentar a recuperação de realizações em roteiros encerrados e o respetivo teste, a execução de `tests/browser/test_lesson_plans.py` passou nos seus três testes. O endereço CDP pertence à sessão do Hub e deve ser substituído pelo da sessão atual ao repetir.

```bash
node --test tests/js/*.test.cjs
```

35 testes passaram. A análise sintática dos seis ficheiros JavaScript alterados e `git diff --check` também passaram.

## Servidor local

O serviço `pagecraft.service` foi reiniciado depois de verificar que não existiam alterações nos registos JSON/JSONL nos cinco minutos anteriores. O serviço ficou ativo, e os pedidos autenticados a `/api/learning/lessons`, `/teacher/lesson.html` e `/teacher/activities.html` devolveram HTTP 200. O novo ecrã foi aberto no Hub e confirmou a lista de alunos e atividades disponíveis. Não foram criados roteiros nem publicadas atividades nos dados reais durante esta verificação.

Captura local: `/home/proteu/agent-browser-hub/screenshots/pagecraft-roteiros-professor.png`.
