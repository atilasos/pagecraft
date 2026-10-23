# Auditoria 07: geração, validação e publicação

Base `4c6ba90`, 22/10/2026. Investigação só de leitura; sem browser, publicação, commits ou alterações ao repositório. Preservados `catalog.json` e as duas atividades locais. Lidos AGENTS, CONTEXT, ADRs 0002/0003/0005, avaliação anterior e implementação. As propostas não repetem #51–55: checkpoints, cache, recuperação da realização, nomes dos apoios e escolha durante retoma.

## Fundamentação e controlos existentes

API da Sebenta saudável; pesquisa `avaliação formativa diferenciação feedback` e leitura integral por `read --content` de:

- **Avaliação Formativa**, `20_Wiki/Avaliação Formativa.md`, estado `review`, confiança `medium`, revista em 09/07/2026. Síntese da wiki: informação permite regular tarefas e apoios; o aluno precisa de conhecer critérios e compreender os seus erros.
- **Diferenciação Pedagógica**, `20_Wiki/Diferenciação Pedagógica.md`, mesmo estado, confiança e data. Síntese da wiki: variar vias e apoios mantendo metas comuns e autonomia, sem fixar rótulos pessoais.

As soluções abaixo são propostas minhas, não prescrições literais da wiki nem demonstração de eficácia em sala.

Já existem esquemas JSON, apoio obrigatório nas gerações novas (`server/pipeline/phases.py:53`), validador offline, revisão linguística e ciclo de reparação (`server/pipeline/runner.py:283`). Há testes de interação para atividades concretas (`tests/browser/test_fraction_draft.py:3`). A publicação centraliza a derivação do catálogo, conforme ADR-0003. `bash skills/sync-from-canonical.sh --check` passou. As cópias CLI são distribuição prevista, não duplicação a eliminar.

## 1. Isolar cada geração e vincular a aprovação ao artefacto revisto

**Problema e evidência.** O slug depende apenas de ano e tema, embora o job tenha identificador próprio (`server/pipeline/runner.py:83`). Os artefactos usam apenas o slug (`:183`). A publicação relê esses caminhos (`:364`). Dois jobs de Frações, até sequenciais, partilham HTML, DocSpec e avaliações. B pode substituir os ficheiros enquanto A aguarda revisão; aprovar A pode publicar B, incluindo uma versão que falhou. Confirmei a colisão chamando o método real. A consequência completa decorre do fluxo, sem ensaio de publicação.

**Comportamento proposto.** Guardar os artefactos por identificador de job; preview aponta para esse conjunto. Ao apresentar para revisão, registar hashes do conjunto final. Aprovação rejeita conteúdo alterado. Revisões publicadas recebem novo slug, conforme `docs/adr/0005-realizacoes-e-professor-remoto.md:9`.

**Benefício pedagógico.** O professor entrega exatamente as instruções, apoios e critérios que reviu.

**Risco e esforço.** Migração dos caminhos de jobs pendentes; médio, 2–3 dias. Não reescrever atividades entregues nem nomes congelados da ponte.

**Teste concreto.** A passa, B do mesmo tema falha; aprovar A conserva os bytes de A. Repetir após restart e rejeitar alteração posterior ao parecer.

**Fronteira.** `server/pipeline/runner.py`, preview em `server/static/teacher/app.js:64`, `tests/test_runner.py`; bloqueio de substituição em `server/publish.py` e respetivos testes.

## 2. Caderno de contraprovas executáveis por atividade

**Problema e evidência.** O Evaluator do Studio declara não ter browser (`server/pipeline/phases.py:192`); o validador verifica padrões e comprimento, sem analisar sintaxe JS (`server/pipeline/validators.py:46`). Um HTML sintético com `function confirmar( {` passou sem erros nem avisos; `node --check` rejeitou-o. Com pareceres positivos, `decide_repair` devolveu `None`. A publicação comum copia o HTML sem exigir estes controlos (`server/publish.py:154`). Isto demonstra uma lacuna de deteção, não uma atividade publicada defeituosa.

**Comportamento proposto, criativo.** Cada novo rascunho leva cenários observáveis: pedido vazio bloqueia; resposta errada completa permite avançar e oferece pista; corrigir funciona nos três apoios. Executar contra o HTML final, em ambiente descartável. Introduzir mutantes deliberados, como JS inválido ou bloqueio pelo acerto, para provar que o ensaio os deteta. Exigir relatório associado ao hash na publicação; distinguir falha técnica de parecer pedagógico dispensável pelo professor.

**Benefício pedagógico.** Protege a oportunidade de errar, receber apoio e continuar, já definida em `server/pipeline/prompts/references/activity-experience.md:17`.

**Risco e esforço.** Cenários gerados podem repetir o erro do Builder. Usar regras comuns independentes e amostras revistas pelo professor; alto, 4–6 dias para piloto limitado a um padrão.

**Teste concreto.** A atividade válida passa; cada mutante falha pelo motivo esperado, com o mesmo cenário e sem dados reais.

**Fronteira.** Esquemas e prompts canónicos em `server/pipeline/`, runner, publicação e `tests/browser/`; propagar apenas derivados por `skills/sync-from-canonical.sh`.

## 3. Recuperar o trecho curricular do tema e mostrar a sua proveniência

**Problema e evidência.** `server/knowledge/ae.py:93` corta os primeiros 12 000 caracteres, sem receber tema. No documento local de Matemática, 3.º ano, `frações` aparece primeiro na posição 28 716: fica fora do excerto. Apesar disso, o prompt pede descritores reais desse excerto (`server/pipeline/phases.py:120`). O esquema aceita AE vazias e fontes inventadas (`server/pipeline/schemas/docspec.schema.json:79`). A wiki também é cortada por prefixo (`server/knowledge/wiki.py:177`).

**Comportamento proposto.** Selecionar secções por tema e conservar caminho, trecho, hash, estado da wiki e limites da consulta. Mostrar referências não verificadas na revisão; não tratar o índice genérico DGE como descritor confirmado. Começar pelas AE, sem bloquear rascunhos exploratórios.

**Benefício pedagógico.** Metas e apoios assentam no conteúdo consultado, com lacunas visíveis ao professor.

**Risco e esforço.** OCR e títulos irregulares; médio, 2–3 dias.

**Teste concreto.** Fixture com descritor após 12 000 caracteres: Frações recupera-o; fonte inexistente fica não verificada; indisponibilidade mantém aviso.

**Fronteira.** `server/knowledge/ae.py`, `wiki.py`, `server/pipeline/phases.py`, runner e `tests/test_knowledge.py`.

## Prova mínima reexecutável

Na raiz do repositório, estes asserts confirmam lacunas atuais, sem publicar:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B - <<'PYCODE'
import json, subprocess
from pathlib import Path
from types import SimpleNamespace
from jsonschema import Draft202012Validator
from server.pipeline.runner import PipelineRunner
from server.pipeline.validators import validate_activity_html
from server.knowledge.ae import AEClient
r = object.__new__(PipelineRunner)
r.config = SimpleNamespace(outputs_dir=Path('outputs/lessons'))
a = dict(id='A', slug='3ano-fracoes')
b = dict(id='B', slug='3ano-fracoes')
assert r._artifact_path(a,'.html') == r._artifact_path(b,'.html')
js = 'function confirmar( {'
h = '<!doctype html><html lang="pt-PT"><meta name="viewport"><body>'
h += '<section id="u1" data-pagecraft-support="u1">' + 'texto '*700
h += '</section><script>' + js + '</script></body></html>'
assert validate_activity_html(h,1,expected_support=True).passed
assert subprocess.run(['node','--check'],input=js,text=True,capture_output=True).returncode
s = json.loads(Path('server/pipeline/schemas/docspec.schema.json').read_text())
assert Draft202012Validator(s['$defs']['CurriculumRef']).is_valid(dict(ae=[],competencies=[]))
d = AEClient(Path('/home/proteu/obsidian-vault')).find('Matemática',3)
assert d.body.find('frações') > 12000
print('Lacunas reproduzidas')
PYCODE
```

**Melhor proposta recomendada: 1.** Corrige uma colisão demonstrada que pode invalidar toda a revisão, tem fronteira reduzida e permite regressão determinista sem depender de IA ou browser.
