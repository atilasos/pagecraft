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

A preencher depois da revisão dos commits e dos testes de integração. Os números anteriores descrevem a base, não a validação das alterações futuras.
