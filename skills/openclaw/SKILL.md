---
name: pagecraft
description: Gerar páginas de aula interactivas (HTML) com visualizações exploráveis para crianças 4-10 anos, usando pipeline multi-agente (Architect→Builder→Evaluator). Inspirado no ViviDoc (DocSpec/SRTC) com extensões pedagógicas (SRTC-AM), alinhamento MEM, Aprendizagens Essenciais, Perfil do Aluno, diferenciação obrigatória e extensões Maker (Minecraft, Lego, impressão 3D, robótica). Usar quando o utilizador pedir uma aula interactiva, explorable explanation, página com sliders/drag/quiz, actividade digital explorável, ou actividade maker com componente digital. NÃO usar para páginas estáticas simples (usar quick-lesson-page).
---

# PageCraft 🛠️

Gera páginas de aula interactivas com visualizações exploráveis, fundamentação curricular e extensões maker.

**Modo por defeito:** iterativo até aprovação ou até atingir o limite de iterações. O objetivo é chegar a uma versão final boa e funcional, não apenas produzir uma primeira versão.

## ⚠️ REGRA FUNDAMENTAL: Especialização por Prompt + Modelo

**Cada fase usa uma identidade/prompt especialista E um modelo calibrado para o seu papel.**

- O orchestrador (Myau) NÃO faz o trabalho dos agentes — orquestra, delega, verifica.
- Todos os agentes (Architect, Designer, Builder, Proofreader, Evaluator/Judge) devem ser lançados via **ACP/acpx**.
- **Modelo por papel:**
  - Architect → `agentId:"claude"`, `model: sonnet` (qualidade pedagógica e curricular)
  - Designer → `agentId:"cursor"`, `model: composer-2` (visuais, sistema de design, UX)
  - Builder → `agentId:"cursor"`, `model: composer-2` para tickets simples/definidos; `agentId:"codex"` para primeira build complexa ou refactor estrutural
  - Proofreader → `agentId:"claude"`, `model: sonnet` (linguística pt-PT AO90 + adequação pedagógica)
  - Evaluator/Judge → `agentId:"codex"`, `model: codex` (gate técnico + decisão PASS/FAIL)
- O Builder é SEMPRE um coding agent externo via ACP/acpx com PTY quando o agente o exigir.
- O Evaluator FAZ verificação visual obrigatória (browser snapshot).
- Para o PageCraft, **não usar `runtime:"subagent"`**; usar `sessions_spawn(runtime:"acp", agentId:...)`.
- Se um agente ACP falha, corrigir e relançar — NÃO fazer o trabalho por ele como fallback.

Identidades dos especialistas: `identities/architect.md`, `identities/designer.md`, `identities/builder.md`, `identities/evaluator.md`

## Pipeline

```
Tópico + faixa etária + duração + [recursos maker]
    → 0. Orchestrator (planeamento, routing ACP, estado da run)
    → 1. Architect [Sonnet] (agente ACP especialista → DocSpec-AM JSON)
    → 2. Designer [Cursor Composer 2] (agente ACP especialista → design-spec.json)
    → 3. [revisão humana opcional]
    → 4. Builder [Cursor Composer 2 / Codex] (coding agent ACP via PTY → HTML interactivo)
    → 5. Proofreader pt-PT AO90 [Sonnet] (agente ACP especialista → ortografia, gramática, semântica, adequação pedagógica)
    → 6. Evaluator/Judge [Codex] (agente ACP especialista + browser → verificação visual + decisão, considerando também o relatório do Proofreader)
    → 7. [Loop de reparação]
         - se problema de implementação/UX/JS/render/layout -> Builder corrige
         - se problema de sistema visual (paleta/tipografia/componentes/consistência) -> Designer atualiza design-spec e Builder reaplica
         - se problema linguístico/semântico/pedagógico fino -> Proofreader emite ticket e Builder corrige o HTML/texto sem regredir a intenção pedagógica
         - se problema de conceção pedagógica/estrutura/spec -> Architect revê o DocSpec
    → 8. Rebuild + re-evaluate até passar ou atingir limite de iterações
    → Output: outputs/lessons/<slug>.html + .md + -docspec.json + -design-spec.json + -proofread-vN.json
```

## Fase 0: Orchestrator (Myau / sessão isolada)

**Quem:** O orchestrator da run pode (e por defeito deve) correr numa **sessão isolada** para reduzir contágio de contexto. Pode ser um sub-agent dedicado (ex.: `pagecraft-orchestrator`) que gere o pipeline e usa `sessions_spawn(runtime:"acp")` para lançar os papéis.

O orchestrator **não cria** o conteúdo pedagógico nem o HTML final; coordena o pipeline, escolhe o agente certo via ACP/acpx, recolhe evidência, aplica routing e decide quando parar.

**Responsabilidades mínimas:**
1. Normalizar input (`topic`, `year`, `duration`, `maker`, constraints do utilizador).
2. Definir `slug` e caminhos de output.
3. Criar e manter `outputs/lessons/<slug>-run-manifest.json` com estado da run.
4. Garantir que Architect, Designer, Builder, Proofreader e Evaluator/Judge usam ACP/acpx.
5. Aplicar o loop de reparação sem regressões desnecessárias.
6. Parar ao atingir `max_iterations = 3` ou quando houver aprovação clara.
7. Entregar ficheiros finais + resumo curto do que mudou.

**Artefactos do Orchestrator:**
- `outputs/lessons/<slug>-run-manifest.json` — estado atual da run
- `outputs/lessons/<slug>-iteration-log.md` — changelog curto por iteração

**Manifest mínimo sugerido:**
```json
{
  "slug": "<slug>",
  "topic": "<tema>",
  "year": "<ano>",
  "duration": 45,
  "maker": "minecraft|lego|none",
  "max_iterations": 3,
  "current_iteration": 0,
  "agents": {
    "architect": "claude/sonnet",
    "designer": "cursor/composer-2",
    "builder": "cursor/composer-2",
    "proofreader": "claude/sonnet",
    "evaluator": "codex"
  },
  "status": "planning|architect|designer|builder|proofreader|evaluator|repair|done|blocked",
  "artifacts": {}
}
```

**Iteration log mínimo sugerido:**
- Iteração N
- issues
- ações
- evidência
- decisão (`pass|builder|architect|both|blocked`)

## Fase 1: Architect (agente ACP)

**Quem:** Agente ACP via `sessions_spawn(runtime:"acp")` com identidade de Architect.

**Procedimento:**
1. Gerar o prompt do Architect:
```bash
python3 {baseDir}/scripts/pagecraft.py --topic "TÓPICO" --year "ANO" --duration MINS --architect-only
```
2. Ler o prompt gerado em `outputs/lessons/_last_architect_prompt.md`
3. Ler a identidade do Architect: `{baseDir}/identities/architect.md`
4. Lançar agente ACP:
```
sessions_spawn:
  runtime: "acp"
  agentId: "claude"
  task: "[conteúdo de identities/architect.md]\n\n---\n\n[conteúdo do prompt do architect]"
  model: sonnet
  mode: run
  runTimeoutSeconds: 300
```
5. Guardar o JSON resultante em `outputs/lessons/<slug>-docspec.json`
6. Se o Architect for chamado novamente por decisão do Evaluator/Judge, recebe sempre:
   - `docspec-vN.json` anterior;
   - `repair-ticket-vN.json` do Evaluator;
   - instrução explícita para corrigir apenas os problemas assinalados sem regredir o resto.
7. Cada revisão do Architect gera uma nova versão do spec (`docspec-v2.json`, `docspec-v3.json`, ...).

## Fase 1.5: Designer (agente ACP)

**Quem:** Agente ACP via `sessions_spawn(runtime:"acp")` com identidade de Designer.

**Objetivo:** gerar um **design-spec.json** com sistema visual (paleta, tipografia, layout, componentes) para guiar o Builder.

**Procedimento:**
1. Ler a identidade do Designer: `{baseDir}/identities/designer.md`
2. Ler `outputs/lessons/<slug>-docspec.json`
3. Lançar agente ACP:
```
sessions_spawn:
  runtime: "acp"
  agentId: "cursor"
  task: "[conteúdo de identities/designer.md]\n\n---\n\n[conteúdo do docspec]"
  model: composer-2
  mode: run
  runTimeoutSeconds: 300
```
4. Guardar o JSON resultante em `outputs/lessons/<slug>-design-spec.json`

**JSON mínimo sugerido:**
```json
{
  "palette": {"bg":"#...","surface":"#...","primary":"#...","accent":"#...","text":"#..."},
  "typography": {"fontFamily":"...","scale":"base|kids|xl","weights":[400,600]},
  "layout": {"radius":12,"spacing":"comfortable|compact","maxWidth":960},
  "components": {"buttons":"rounded|pill","cards":"elevated|flat","badges":"soft"},
  "motion": {"transitions":"subtle|none"},
  "accessibility": {"contrast":"AA"},
  "notes": "decisões de estilo curtas"
}
```

## Regras de routing do Orchestrator

- **Architect**: usar quando o problema é pedagógico, curricular, estrutural ou de modelação do DocSpec.
- **Designer**: usar quando o problema é de sistema visual, consistência gráfica, micro-UI ou legibilidade.
- **Builder**: usar quando o problema é de HTML/CSS/JS, UX, estados, layout, acessibilidade técnica ou bugs.
- **Evaluator/Judge**: usar sempre após build ou rebuild com evidência real (snapshot + consola + pelo menos 1 interação).
- **Não saltar diretamente para conclusão** sem uma passagem explícita pelo Evaluator/Judge, salvo bloqueio técnico claro do próprio ambiente.
- Se houver bloqueio de ACP/acpx, registar em `run-manifest.json` e avisar o utilizador; não mascarar o problema como aprovação.
- Se a visibilidade entre sessões ACP estiver restrita neste ambiente, os agentes devem escrever sempre os artefactos finais directamente em ficheiros no workspace (`outputs/lessons/...`) em vez de depender de leitura posterior da conversa da sessão.

## Fase 2: Revisão humana (opcional)

Apresentar DocSpec-AM ao utilizador se pedido. Ajustes livres.

## Fase 3: Builder (coding agent via ACP/acpx + PTY — OBRIGATÓRIO)

**Quem:** Coding agent externo via ACP/acpx (Codex CLI, Claude Code, ou Cursor), usando PTY quando o agente o exigir.
**NUNCA** executar esta fase como sub-agente normal ou fazer o HTML directamente.

**Procedimento:**
1. Criar directório de trabalho:
```bash
WORK=$(mktemp -d) && cd $WORK && git init -q
```

2. Copiar ficheiros necessários:
```bash
cp outputs/lessons/<slug>-docspec.json $WORK/docspec.json
cp outputs/lessons/<slug>-design-spec.json $WORK/design-spec.json 2>/dev/null || true
cp {baseDir}/assets/template-base.html $WORK/template.html
cp {baseDir}/identities/builder.md $WORK/IDENTITY.md
```

3. Gerar prompt do Builder:
```bash
python3 {baseDir}/scripts/build_prompt.py $WORK/docspec.json > $WORK/PROMPT.md
```

4. **Injectar identidade + design spec no prompt**:
```bash
cat $WORK/IDENTITY.md $WORK/PROMPT.md > $WORK/TASK.md
if [ -f $WORK/design-spec.json ]; then
  printf "\n\n## Design spec\n" >> $WORK/TASK.md
  cat $WORK/design-spec.json >> $WORK/TASK.md
fi
```

5. Lançar coding agent com PTY:
```bash
# Opção A: Codex (builder normal, recomendado por defeito)
exec pty:true workdir:$WORK timeout:600 command:"codex exec --full-auto 'Read TASK.md and generate the complete interactive HTML page. Save as page.html.'"

# Opção B: Cursor (builder-heavy / refactor estrutural)
exec pty:true workdir:$WORK timeout:600 command:"agent 'Read TASK.md and generate the complete interactive HTML page. Save as page.html.'"

# Opção C: Claude Code (usar apenas quando a quota voltar)
exec pty:true workdir:$WORK timeout:600 command:"claude 'Read TASK.md and generate the complete interactive HTML page. Save as page.html.'"
```

6. Copiar output:
```bash
cp $WORK/page.html outputs/lessons/<slug>.html
```

### Selecção automática de coding agent
- Regra base: usar **Cursor (Composer 2)** como Builder por defeito.
- Usar **Codex** quando houver primeira build complexa, refactor estrutural, alterações multi-ficheiro ou correções grandes após falhas críticas.
- Usar **Claude Code** apenas quando estiver novamente disponível e houver motivo claro para revisão premium.
- **Se nenhum disponível → PARAR e avisar o utilizador. NÃO fazer fallback manual.**

## Fase 4: Proofreader pt-PT AO90 (agente ACP — OBRIGATÓRIO antes do Evaluator)

**Quem:** Agente ACP via `sessions_spawn(runtime:"acp")`, `agentId:"claude"`, `model: sonnet`, com foco em **português europeu (pt-PT), AO90, gramática, semântica e adequação pedagógica**.

**Objetivo:** rever a página já construída e emitir um relatório estruturado antes da avaliação final.

**O que verifica:**
1. ortografia e gramática em **pt-PT AO90**;
2. consistência lexical e sintáctica (evitar brasileirismos, anglicismos desnecessários, registos mistos);
3. coerência semântica (frases ambíguas, instruções contraditórias, exemplos pouco claros);
4. adequação pedagógica ao ano/faixa etária;
5. clareza das instruções, feedback e microcopy da interface;
6. alinhamento entre texto apresentado, objetivo e mini-avaliação.

**Output obrigatório:** `outputs/lessons/<slug>-proofread-vN.json`

**JSON mínimo:**
```json
{
  "pass": true,
  "severity": "low|medium|high|critical",
  "issues": [
    {
      "type": "orthography|grammar|semantic|pedagogical|ptpt-usage",
      "severity": "low|medium|high|critical",
      "location": "selector, unit, snippet ou secção",
      "original": "texto original",
      "suggestion": "texto revisto",
      "reason": "justificação curta"
    }
  ],
  "summary": "síntese curta",
  "acceptance_checks": ["..."]
}
```

**Routing:**
- Se houver problemas textuais/UI copy → **Builder corrige** o HTML/texto.
- Se houver problema pedagógico estrutural → **Architect revê** o DocSpec.
- O Evaluator/Judge recebe sempre este relatório e deve tê-lo em conta no veredicto final.

## Fase 5: Evaluator (agente ACP + browser — OBRIGATÓRIO)

**Quem:** Agente ACP via `sessions_spawn(runtime:"acp")` com identidade de Evaluator.
A verificação visual via browser snapshot é **mandatória**.

**Procedimento:**
1. Servir a página localmente:
```bash
exec background:true command:"python3 -m http.server 8765 --directory $WORKSPACE"
```

2. Abrir no browser do OpenClaw:
```
browser action:open profile:openclaw url:http://127.0.0.1:8765/outputs/lessons/<slug>.html
```

3. Tirar snapshot (accessibility tree):
```
browser action:snapshot profile:openclaw refs:aria
```

4. Verificar consola JavaScript:
```
browser action:console profile:openclaw level:error
```

5. Testar pelo menos 1 interacção:
```
browser action:act kind:click ref:<botão ou tab>
```

6. Ler a identidade do Evaluator: `{baseDir}/identities/evaluator.md`

7. Lançar agente ACP com toda a informação recolhida:
```
sessions_spawn:
  runtime: "acp"
  agentId: "codex"
  task: "[identidade evaluator]\n\n## DocSpec-AM:\n[JSON do spec]\n\n## Design-spec:\n[JSON do design-spec]\n\n## Snapshot HTML:\n[accessibility tree]\n\n## Consola:\n[erros]\n\n## Interacção testada:\n[resultado]\n\n## Proofread report:\n[JSON do proofread]\n\nAvalia segundo os critérios da tua identidade e devolve JSON estruturado com: {pass:boolean, route:'builder'|'designer'|'architect'|'both', severity:'low'|'medium'|'high'|'critical', issues:[...], required_fixes:[...], evidence:[...], acceptance_checks:[...], blocked_by:[...]}"
  model: codex
  mode: run
  runTimeoutSeconds: 120
```

8. Se `pass: false`: aplicar roteamento explícito de retorno.
   - `route: builder` quando as falhas forem de implementação (HTML/CSS/JS, acessibilidade técnica, erros de consola, interações quebradas, layout responsivo, performance).
   - `route: designer` quando as falhas forem visuais/estéticas (paleta errada, tipografia ilegível, inconsistência gráfica, contraste fraco).
   - `route: architect` quando as falhas forem de conceção (objetivos mal mapeados, sequência didática fraca, diferenciação insuficiente, desalinhamento MEM/AE, avaliação formativa mal definida, constraints mal modelados no DocSpec).
   - `route: both` quando houver falhas críticas nos dois ou mais níveis.
9. Loop obrigatório de melhoria (coordenado pelo Orchestrator):
   - limite padrão e máximo aceitável: `max_iterations = 3` (Evaluator → Builder/Architect → Builder → Evaluator ...)
   - objetivo do loop: atingir uma versão **funcional** e suficientemente boa para entrega.
   - cada avaliação reprovada gera um artefacto obrigatório: `repair-ticket-vN.json`.
   - `repair-ticket-vN.json` deve conter: `route`, `severity`, `issues`, `required_fixes`, `acceptance_checks`, `blocked_by`, `evidence`.
   - se `route: architect`, o Architect recebe o `repair-ticket-vN.json`, produz `docspec-vN.json` atualizado e o Builder reconstrói a página a partir dessa versão.
   - se `route: builder`, o Builder recebe o `repair-ticket-vN.json` e corrige sem alterar a intenção pedagógica salvo indicação explícita.
   - se `route: both`, a ordem é: Architect revê spec -> Builder reconstrói -> Evaluator reavalia.
   - cada iteração deve gerar um changelog curto: `issues -> ações -> evidência`, guardado em `outputs/lessons/<slug>-iteration-log.md`.
10. Critério de saída:
   - `pass: true` e sem `critical` -> avançar para Fase 5.
   - se atingir `max_iterations = 3` e a página estiver funcional, mas ainda com melhorias não-críticas, aceitar como versão final aceitável e listar limitações/melhorias futuras.
   - se atingir `max_iterations = 3` e a página ainda **não** estiver funcional -> parar e pedir decisão humana com resumo objetivo do bloqueio.

## Definição operacional de "funcional"

O Evaluator/Judge deve considerar a página **funcional** apenas quando todos estes mínimos forem verdadeiros:

1. abre sem erro fatal no browser;
2. não há erros críticos na consola JavaScript;
3. pelo menos 1 interação principal funciona como esperado;
4. o conteúdo principal é legível em layout tablet/desktop sem colapso grave;
5. existe coerência mínima entre objetivo, atividade e feedback/avaliação;
6. a página não depende de internet nem de recursos externos frágeis para o fluxo principal;
7. há pelo menos um percurso completo utilizável por um aluno do nível intermédio.

A página pode ser considerada **aceitável mas não perfeita** se cumprir os critérios acima e restarem apenas melhorias não-críticas (polish visual, microcopy, refinamentos de ritmo, pequenas otimizações).

Deve ser considerada **não funcional** se falhar qualquer um destes pontos:
- interação principal quebrada;
- erro JS crítico;
- layout inutilizável;
- atividade sem sequência compreensível;
- desalinhamento pedagógico que impeça o uso em aula.

## Fase 5: Output final

1. Gerar versão Markdown (professor):
```bash
python3 {baseDir}/scripts/build_markdown.py <slug>-docspec.json > outputs/lessons/<slug>.md
```

2. Ficheiros finais:
- `outputs/lessons/<slug>.html` — página interactiva (gerada pelo Builder)
- `outputs/lessons/<slug>.md` — versão professor (gerada pelo script)
- `outputs/lessons/<slug>-docspec.json` — especificação (gerada pelo Architect)
- `outputs/lessons/<slug>-design-spec.json` — sistema visual (gerado pelo Designer)

3. Atualizar `run-manifest.json` para `status: "done"` (ou `blocked`).
4. Limpar servidor HTTP temporário.

## Fase 6: Publish (catálogo + commit/push) — TAREFA DO ORCHESTRATOR

**Objetivo:** publicar automaticamente a atividade aprovada no repo `workspace/pagecraft`.

**Nota:** Esta fase é **explicitamente responsabilidade do orchestrator** (não do Builder nem do Evaluator). O orchestrator só publica quando houver veredicto `pass:true` do Evaluator e sem itens `critical`.

**Pré-condições obrigatórias:**
- veredicto final do Evaluator/Judge com `pass: true`
- sem itens `critical`
- existência dos três artefactos finais (`.html`, `.md`, `-docspec.json`)

**Passos do Orchestrator:**
1. Publicar a atividade no repo `pagecraft` usando o script dedicado:
```bash
python3 {baseDir}/scripts/publish_to_catalog.py \
  --slug <slug> \
  --html outputs/lessons/<slug>.html \
  --md outputs/lessons/<slug>.md \
  --docspec outputs/lessons/<slug>-docspec.json \
  --repo /Users/igor/.openclaw/workspace/pagecraft \
  --maker <maker-ou-none> \
  --tags "tag1,tag2,tag3"
```
2. O script deve:
- copiar artefactos para `pagecraft/activities/<slug>/`
- gerar/atualizar `meta.json`
- atualizar `pagecraft/catalog.json`
- preservar `createdAt` quando o `slug` já existir

3. Commit + push automático no repo `pagecraft`:
```bash
cd /Users/igor/.openclaw/workspace/pagecraft
git add -A
git diff --cached --quiet || git commit -m "pagecraft: publish <slug>"
git push
```
4. Registar no `run-manifest.json`:
- `publish.status`: `published|pending|failed`
- `publish.url`: URL pública final quando disponível
- `publish.error`: mensagem curta em caso de falha

**Regras de segurança operacional:**
- Se `pass` não for true, **não publicar**.
- Se falhar push remoto, manter ficheiros preparados localmente e marcar `publish.status: pending`.
- Nunca publicar artefactos intermédios de iterações reprovadas.

## DocSpec-AM

Schema completo: `references/docspec-schema.md`

Cada knowledge unit contém:
- **SRTC-A**: State, Render, Transition, Constraint (descobre), Assessment (observável)
- **Maker** (opcional): type, challenge, connection, communication, alternatives
- **Curriculum**: AE + competências PA
- **MEM**: módulos, instrumentos, organização social
- **Differentiation**: 🟢 apoio / 🟡 intermédio / 🔴 desafio

## References

- `references/ae-index.md` — índice AE 1.º ciclo + Perfil do Aluno
- `references/docspec-schema.md` — schema JSON + exemplo completo
- `references/interaction-patterns.md` — 8 patterns (slider, drag, matching, etc.)
- `references/maker-patterns.md` — 5 recursos maker com templates
- `references/srtc-examples.md` — exemplos por idade
- `identities/architect.md` — identidade do Architect
- `identities/designer.md` — identidade do Designer
- `identities/builder.md` — identidade do Builder
- `identities/evaluator.md` — identidade do Evaluator

## Regras

- Público: 4-10 anos, pt-PT (AO90)
- HTML self-contained (CSS+JS inline), responsive, tablet-friendly, offline
- Diferenciação obrigatória em 3 níveis
- Constraint descoberto, não declarado
- Assessment formativo e observável
- Maker sempre em grupo, sempre com comunicação (circuito MEM)
- Validar factos; sinalizar incerteza
- **Especialização por prompt + modelo é regra.** Cada papel usa identidade própria e modelo calibrado (Sonnet para Architect/Proofreader, Cursor Composer 2 para Designer/Builder simples, Codex para Evaluator e builds complexas).

## Inspiração

ViviDoc (Tang et al., 2026) — arXiv:2603.01912
Extensões: SRTC-AM, referências curriculares, MEM, maker, multi-agente real (coding agent para HTML).
