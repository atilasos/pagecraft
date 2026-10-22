# Gerações isoladas e aprovação vinculada à revisão

Implementação da proposta 1 de `/tmp/pagecraft-audit-07.md`, sobre a base `4c6ba90476a498a03b08fd88dea96c432ba767cd`.

Worktree: `/home/proteu/.t3/worktrees/pagecraft/t3-b6e498e9`.
Branch: `fix/geracoes-isoladas-revisao`.

O checkout atribuído estava limpo e isolado, na branch inicial `fix/isolated-activity-generations`. A implementação usa uma branch própria criada na mesma base. Foram lidos AGENTS, CONTEXT, PRODUCT, DESIGN e os ADRs 0002, 0003 e 0005. A alteração é operacional: preserva o conteúdo revisto e as realizações existentes. Não altera metas, apoios nem critérios pedagógicos, pelo que não acrescenta uma consulta pedagógica à Sebenta.

## Problema reproduzido

O teste `test_same_topic_failed_job_cannot_replace_approved_job` executa o pipeline real com respostas deterministas de `FakeProvider`. A gera HTML com o marcador `Geração A revista` e passa. B tem o mesmo ano e tema, gera `Geração B falhada` e falha na avaliação. Depois, o teste aprova A e lê o ficheiro efetivamente publicado.

Na base, os dois jobs escreviam os mesmos caminhos. A publicação de A lia os ficheiros substituídos por B. A primeira execução falhou na asserção do conteúdo publicado:

```text
uv run --project /home/proteu/pagecraft pytest tests/test_runner.py::test_same_topic_failed_job_cannot_replace_approved_job -q
FAILED test_same_topic_failed_job_cannot_replace_approved_job
assert 'Geração A revista' in html and 'Geração B falhada' not in html
1 failed in 0.29s
```

O commit `0cceac6` contém essa contraprova antes da correção. A falha foi observada em diretórios temporários, sem publicar no catálogo do checkout ou em produção.

## Comportamento implementado

- `runner.py` usa `outputs_dir/<job-id>/<slug>...` e acrescenta o identificador do job ao slug. HTML, DocSpec, design, Markdown, validação determinista e pareceres ficam separados. Prompts e acontecimentos já pertenciam ao job e continuam separados.
- O conjunto final recebe hashes SHA-256 de todos os ficheiros do diretório, incluindo pareceres anteriores. `review.id` inclui também job, slug e mapa de artefactos. Não há uma aprovação reutilizável para outro conjunto.
- O HTML inclui os elementos deterministas de suporte, tipografia e a ponte existente antes de ser revisto. O preview servido e o HTML publicado conservam os mesmos bytes. Não se alterou o protocolo da ponte.
- O preview passa por `GET /api/jobs/{id}/preview?review_id=...`. Verifica os hashes, exige professor, usa `no-store` e corre com CSP sandbox. A visibilidade do mount `/outputs` permanece igual e tem uma asserção própria.
- A interface usa `preview_url` do job e envia o identificador da revisão no corpo de `POST /api/jobs/{id}/approve`. Um conflito devolve 409 e aparece no cartão. Pedidos sem identificador válido não aprovam.
- A aprovação verifica os hashes, persiste a intenção e a publicação volta a verificá-los. Os bytes usados na cópia vêm dessa verificação, sem uma nova leitura de caminhos mutáveis. `override` só dispensa a avaliação, nunca a integridade.
- `publish_activity` regista job e revisão no `meta.json`, instala o diretório completo por rename e regenera o catálogo. Uma repetição com a mesma identidade e conteúdo recupera o catálogo sem alterar a atividade. Outra geração, outra revisão ou outros bytes no mesmo slug são recusados antes de qualquer escrita na atividade.
- Jobs antigos sem `artifact_version=1` ficam explicitamente bloqueados ao arrancar, com mensagem para gerar novamente. Os ficheiros partilhados não são migrados ou apagados. Jobs antigos concluídos e atividades já entregues ficam conservados.
- O restart reutiliza os artefactos próprios de Architect e Designer e retoma publicações com aprovação persistida. Publicações sem aprovação ou com conteúdo alterado falham. A opção explícita `auto_publish` conserva a publicação automática com a revisão persistida.

O [ADR-0005](../adr/0005-realizacoes-e-professor-remoto.md) regista estas decisões e a compatibilidade do percurso manual para atividades anteriores sem identidade de geração.

## Prova depois da correção

O mesmo teste compara os bytes de A antes de B, depois de B e no ficheiro publicado. Passa também com um restart entre a falha de B e a aprovação de A. Os slugs e todos os caminhos dos dois jobs são distintos.

Os ensaios adicionais cobrem:

- Mutação de cada artefacto, de um parecer anterior e adição de ficheiro após revisão, tanto numa geração aprovada pela avaliação como numa geração falhada com `override`.
- Mudança entre persistir a aprovação e começar a publicação. A nova verificação bloqueia a cópia.
- Mudança do caminho original depois da verificação. A publicação consome o snapshot já verificado e conserva os bytes revistos.
- Crash antes de publicar, depois de instalar a atividade e antes de atualizar o catálogo. A retoma usa a mesma aprovação, sem IA, e mantém uma entrada no catálogo.
- Aprovações repetidas e concorrentes, preservando conteúdo, metadados e catálogo.
- Substituição de slugs antigos ou de outra geração, remoção de design e alteração de plano ou Markdown. Nenhum conflito altera a publicação anterior.
- Jobs antigos em fila, em execução, em revisão, em publicação, falhados e concluídos.
- Acesso ao preview sem papel de professor, identificador errado ou ausente e ficheiros removidos.

Comandos reexecutáveis na raiz deste worktree:

```bash
uv run --project /home/proteu/pagecraft pytest tests --ignore=tests/browser -q
node --check server/static/teacher/app.js
git diff --check
```

Resultado da suite sem browser: `381 passed in 12.22s`. `node --check` e `git diff --check` passaram.

A validação do browser usa uma sessão própria do Agent Browser Hub, perfil `temporary`, chamada `geracoes-isoladas`. Playwright liga-se apenas ao CDP dessa sessão. A fixture cria um servidor e catálogo descartáveis, substitui IA e conhecimento por fakes e termina o servidor no final.

```bash
PAGECRAFT_TEST_CDP=http://127.0.0.1:9330 uv run --with playwright --project /home/proteu/pagecraft pytest tests/browser/test_generation_review.py --basetemp=/tmp/pagecraft-delegate/generation-browser-test -q -s
```

O porto deve ser o da sessão própria aberta no Hub. O ensaio abre o preview por clique real, verifica A, publica A pelo botão, conserva B falhada e mostra o conflito de C alterada. Não ocorreram erros JavaScript. A sessão foi fechada no Hub.

Resultado do browser: `1 passed`. Screenshot conservada em `/tmp/pagecraft-delegate/geracoes-isoladas-browser.png`. A fixture também imprime o caminho da screenshot a cada execução.

## Limites e operação

O modelo de escrita continua a ser um processo servidor, como no ADR-0005. Os locks serializam aprovações e publicação nesse processo. A instalação atómica evita expor uma atividade parcialmente copiada. Um encerramento abrupto antes do rename pode deixar um diretório `.publish-*` fora de `activities`, que não entra no catálogo nem é usado na retoma. Não há garantia adicional contra falhas físicas do disco.

Os hashes protegem a correspondência entre revisão e artefactos. Não são uma assinatura contra alguém com acesso de escrita ao código e ao estado do servidor. Se um job novo perde os seus ficheiros, o professor cria outra geração. Jobs antigos não recebem uma aprovação por inferência dos caminhos históricos.

O mount público `/outputs`, as atividades entregues e o catálogo real não foram modificados. Não foram chamadas IA real, APIs de publicação remota, PRs ou merge.
