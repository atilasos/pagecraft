# Avaliação do PageCraft — 22 de outubro de 2026

## Objetivo e âmbito

Avaliar o funcionamento do PageCraft, desenvolver melhorias em branches independentes, selecionar as que justificam integração e acompanhar os respetivos PRs até ao `main`. Ponto de partida: `480521e` (PR #50 integrado).

A avaliação cobre entrada no Studio, trabalho individual e em grupo, diferenciação, registo de evidência, autoavaliação, feedback e retoma. Os ensaios usam dados descartáveis e um browser gerido pelo Agent Browser Hub; não constituem observação de utilização por crianças. Não há publicação de atividades nem alteração de registos reais.

## Base verificada

- `uv run pytest -q --ignore=tests/browser`: 315 testes aprovados.
- `node --test tests/js/activity_support.test.cjs`: 21 testes aprovados.
- `bash skills/sync-from-canonical.sh --check`: sem divergência.
- API da Sebenta disponível; páginas pedagógicas abaixo lidas integralmente.
- GitHub sem issues ou PRs abertos no início da avaliação.

## Grelha pedagógica

Síntese das páginas da Sebenta consultadas pela API local, em 22 de outubro de 2026:

- **[[Avaliação Formativa]]**, `20_Wiki/Avaliação Formativa.md`: recolher informação só tem função formativa quando permite ajustar tarefas, apoios, tempos ou explicações. Os critérios devem ser conhecidos pelo aluno; os erros permitem estudar estratégias e orientar novas ações.
- **[[Diferenciação Pedagógica]]**, `20_Wiki/Diferenciação Pedagógica.md`: vias e apoios podem variar, mantendo metas comuns. Cooperação e autonomia são centrais; não transformar níveis em rótulos pessoais ou agrupamentos fixos.
- **[[Avaliação Cooperada]]**, `20_Wiki/Avaliação Cooperada.md`: a participação na avaliação pressupõe participação na planificação. Instrumentos e critérios precisam de poder ser revistos pelo grupo; os registos apoiam a discussão e a entreajuda.

As três páginas têm estado `review` e confiança `medium`. Esta avaliação usa as suas sínteses, sem transformar citações com OCR duvidoso em normas nem afirmar conformidade legal ou eficácia pedagógica demonstrada.

**Aplicação proposta ao produto:** preservar respostas e autoria; permitir rever a reflexão; apresentar evidência, voz do aluno e observação do professor separadamente; fornecer pistas pertinentes ao trabalho atual; manter escolha livre de apoio e possibilidade de pedir ajuda. A aplicação destes critérios é uma decisão de produto desta avaliação, não uma afirmação literal das fontes.

## Frentes delegadas e critérios de seleção

1. **Trabalho do aluno:** encontrar e corrigir uma perda ou confirmação indevida de gravação, ou um problema de retoma. Aceitar apenas com reprodução e teste de regressão; conservar autoria e acesso privado.
2. **Feedback:** encontrar e corrigir uma falha de contexto, cache, concorrência ou indisponibilidade. Aceitar apenas sem transformar falhas técnicas em juízos sobre a criança.
3. **Relatórios:** corrigir uma apresentação ou agregação que confunda trabalho observado, reflexão ou interpretação. Aceitar apenas com evidência verificável e sem inferência automática de aprendizagem.

Cada agente trabalha num worktree e branch isolados, com commits incrementais. A revisão final verifica separadamente normas do repositório e cumprimento dos requisitos. Uma ideia sem problema demonstrado ou com alcance desproporcionado fica registada para evolução posterior.

## Oportunidades para aprofundar

- **Anos múltiplos no catálogo:** `index.html:itemYears` e `server/api/catalog.py:_parse_year` têm regras diferentes. A atividade `tinkercad-pontes-3e4` declara `3.º e 4.º anos (8–10 anos)`, mas os filtros não modelam explicitamente o conjunto dos dois anos. Convém definir um contrato comum de anos antes de alterar as várias interfaces.
- **Participação nos critérios:** os instrumentos atuais permitem reflexão e observação docente; a construção e revisão de critérios com a turma merece desenho próprio. Não basta acrescentar mais campos para chamar cooperada à avaliação.

## Resultado da seleção

Selecionadas cinco melhorias, todas com problema demonstrado, alteração delimitada e regressão verificável:

- [PR #51](https://github.com/atilasos/pagecraft/pull/51): retirar checkpoints dos relatórios exportados. Preserva a distinção entre estado técnico e trabalho observado, sem apagar o histórico de retoma.
- [PR #52](https://github.com/atilasos/pagecraft/pull/52): conservar acentos, maiúsculas e espaços no contexto da cache de feedback. O refinamento serializa leitura e conclusão do mesmo pedido, preservando o desfecho integral e evitando chamadas duplicadas.
- [PR #53](https://github.com/atilasos/pagecraft/pull/53): recuperar a mesma realização após falha de rede/HTTP 503, mantendo respostas pendentes e rascunho da reflexão. A página só oferece nova entrada depois de confirmar ausência de credencial.
- [PR #54](https://github.com/atilasos/pagecraft/pull/54): usar os nomes neutros dos apoios nos guias novos do Studio e CLI. Conserva os identificadores internos e os artefactos históricos.
- [PR #55](https://github.com/atilasos/pagecraft/pull/55): entregar a escolha explícita de apoio mesmo nos frames finais da retoma. Inclui expectativas atualizadas para frações verticais acessíveis e correções da recolha dos testes.

O teste de browser da base encontrou três falhas: duas expectativas antigas sobre nomes acessíveis das frações e uma corrida real na escolha de nível. A correção do nível foi reproduzida com o último frame da retoma suspenso; não depende de repetir testes até passarem. A corrida do feedback foi reproduzida com Events, tanto para uma pista válida como para indisponibilidade.

As oportunidades de anos múltiplos e participação nos critérios ficam para desenho posterior. Não foram adicionadas nesta ronda por exigirem decisões próprias de contrato e de participação da turma.

## Standards

Duas rondas de revisão independente, com os diffs fixados contra `480521e`, e depois contra os pontos anteriores aos refinamentos: **0 achados acionáveis**. As revisões verificaram AGENTS, linguagem de domínio, princípios de produto/design e ADRs de acesso, ponte, realizações e continuação. As cópias CLI são distribuição canónica prevista pelo projeto, não duplicação acidental.

## Spec

Duas rondas independentes: **0 achados acionáveis**. Os requisitos de recuperação, cache, evidência, rótulos neutros, livre escolha e idempotência foram considerados implementados, sem desvio de âmbito identificado. As revisões foram sobretudo estáticas; os testes abaixo são a verificação dinâmica do agente principal.

## Validação final conjunta

- `uv run pytest -q --ignore=tests/browser`: **337 aprovados**.
- `PAGECRAFT_TEST_CDP=<CDP do Hub> uv run --offline --with playwright==1.63.0 pytest tests/browser -q`: **66 aprovados**, em 108,62 s, com dados e servidores descartáveis.
- `uv run pytest -q`, sem Playwright: **337 aprovados, 30 omitidos**; a ausência da dependência opcional já não impede os testes de servidor.
- Recolha conjunta com Playwright: **403 testes**; resolvida a colisão entre nomes dos módulos de retoma.
- `node --test tests/js/activity_support.test.cjs`: **21 aprovados**.
- Sincronização canónica, `git diff --check` e sintaxe dos dois clientes JavaScript alterados: aprovados.
- GitGuardian aprovado nos commits dos PRs. A execução de pytest e JavaScript foi local; o repositório não tem um workflow próprio que as execute no GitHub.

A pesquisa e o filtro do catálogo foram verificados num servidor estático local. A pesquisa «Tinkercad» com o filtro do 3.º ano devolveu zero resultados, apesar do destino declarar 3.º e 4.º anos. Captura: `/home/proteu/agent-browser-hub/screenshots/pagecraft-catalogo-tinkercad-3ano.png`.

## Limites da avaliação

Os ensaios técnicos e a revisão da Sebenta não substituem observação em sala nem demonstram a qualidade de cada texto gerado por IA. Mantêm-se os limites de um processo escritor, expiração da credencial em 24 horas e dependência de `sessionStorage` para trabalho ainda não enviado. A cache mais precisa pode aumentar chamadas ao fornecedor. Não houve publicação de atividades, reinício de produção ou alteração de dados reais.
