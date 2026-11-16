# Percurso PageCraft: fases, artefactos e gates

`SKILL_DIR` é a pasta desta skill no repositório: `skills/claude` ou `skills/codex`. Corre os comandos na raiz do repositório PageCraft. `CHECK` abrevia `uv run python "$SKILL_DIR/scripts/pagecraft_check.py"`.

## Conteúdo

- Artefactos
- Lista de verificação
- Gates e reparação
- Pronto para revisão
- Registo, aprovação e publicação

## Artefactos

Tudo fica em `drafts/`, fora das pastas públicas. `<slug>` segue o padrão `<tema>-<ano>ano`, em minúsculas e com hífenes.

| Artefacto | Autor | Schema ou verificação |
|---|---|---|
| `<slug>-run-manifest.json` | orquestrador, via `CHECK log` | entradas `runs[]` com fase, estado e modelo |
| `<slug>-sources.md` | Architect | títulos, caminhos e data de consulta da Sebenta |
| `<slug>-docspec.json` | Architect | `docspec.schema.json` |
| `<slug>.md` | `build_markdown.py` | guia do professor |
| `<slug>-design-spec.json` | Designer | `design-spec.schema.json` |
| `<slug>-builder-prompt.md` | `build_prompt.py` | gerado, não editar |
| `<slug>.html` | Builder | `validate_activity_html` |
| `<slug>-proofread-vN.json` | Proofreader | `proofread.schema.json` |
| `<slug>-evaluation-vN.json` | Evaluator | `evaluation.schema.json` |
| `<slug>-repair-ticket-vN.json` | Evaluator, só se reprovar | `evaluation.schema.json` |
| `<slug>-activity.json` | orquestrador | metadados de registo ([learning.md](learning.md)) |

Obtém sempre o nome versionado com `CHECK next <slug> proofread|evaluation|repair-ticket`, para nunca sobrescreveres o histórico. No schema de avaliação, `route` só aceita `builder`, `designer`, `architect` ou `both`. Quando `pass:true`, omite `route`.

## Lista de verificação

Copia esta lista para a tua resposta de progresso e marca cada passo:

```text
- [ ] 0 Pedido normalizado e manifest iniciado
- [ ] 1 Fontes da Sebenta e DocSpec (Architect)    → CHECK check <slug> --phase architect
- [ ] 2 Guia do professor (build_markdown.py)
- [ ] 3 Design-spec (Designer)                     → CHECK check <slug> --phase designer
- [ ] 4 HTML e incorporações (Builder)             → CHECK check <slug> --phase builder
- [ ] 5 Revisão linguística (Proofreader)          → CHECK check <slug> --phase proofreader
- [ ] 6 Avaliação no browser (Evaluator)           → CHECK check <slug> --phase evaluator
- [ ] 7 Reparações até PASS (no máximo 3 iterações)
- [ ] 8 Rascunho registado e entregue              → CHECK check <slug> --phase delivery
```

0. **Normalizar o pedido.** Fixa tema, ano, duração, línguas (só `pt` por defeito), maker (`none` por defeito), restrições, ligação ao trabalho da turma quando o professor a indicar, e o slug. Inicia o manifest com `CHECK log <slug> --phase orchestrator --status planning`. Pergunta ao professor apenas o que mudaria materialmente a atividade.
1. **Architect.** Consulta a Sebenta (ver abaixo) e escreve `sources.md` e `docspec.json`. As unidades seguem SRTC-A, as três vias partilham a mesma meta e a atividade tem um plano `support` próprio. O Architect consulta a Sebenta sozinho, para que a pesquisa não ocupe o contexto do orquestrador.
2. **Guia.** Gera-o com `uv run python "$SKILL_DIR/scripts/build_markdown.py" drafts/<slug>-docspec.json > drafts/<slug>.md`.
3. **Designer.** Escreve `design-spec.json` a partir do DocSpec e dos mínimos por idade. Em M28P, preserva a paleta e as `syllableColors` da palavra.
4. **Builder.** Gera o prompt com `uv run python "$SKILL_DIR/scripts/build_prompt.py" drafts/<slug>-docspec.json --output drafts/<slug>.html > drafts/<slug>-builder-prompt.md`. Esse prompt já inclui a experiência, a adaptação à idade e o apoio contextual, por isso não os voltes a passar. Depois de escrever o HTML, e após cada reparação, corre:
   `uv run python scripts/embed_activity_support.py --activity drafts/<slug>.html --docspec drafts/<slug>-docspec.json`
   `uv run python scripts/embed_gothic_font.py --activity drafts/<slug>.html`
5. **Proofreader.** Lê a vista enxuta `CHECK lean drafts/<slug>.html`, nunca o HTML integral. Revê português e, quando pedido, inglês, incluindo estados, feedback, `aria-label` e autoavaliação.
6. **Evaluator.** Testa no browser a página servida localmente e segue [a lista do Evaluator](../agents/pagecraft-evaluator.md). Para ler o código, usa a vista enxuta.
7. **Reparar.** Cada reprovação gera um ticket e regressa à fase responsável. Volta a correr os gates a partir dessa fase.
8. **Entregar.** Regista o rascunho e entrega ao professor a pré-visualização, os objetivos, os critérios, a evidência e as limitações.

Regista cada fase concluída: `CHECK log <slug> --phase <fase> --status done|failed --model <família>/<modelo> --artifact <caminho>`. A família é a do modelo (`claude`, `gpt`, `grok`, `gemini`…), não o fornecedor que o serve. O gate de entrega compara a família do Builder com a do Evaluator. Uma exceção autorizada pelo professor regista-se com `CHECK log <slug> --phase teacher --status approved --note "<decisão>"`. Uma reparação do HTML regista-se como `--phase repair --artifact drafts/<slug>.html` ou como `--phase builder`, e o gate trata-a como trabalho do Builder.

### Sebenta

Usa a skill `sebenta-wiki`. Nesta máquina, o cliente é `python3 /home/proteu/.codex/skills/sebenta-wiki/scripts/sebenta_api.py`. A sequência é `health`, depois `search "<termos>" --kind wiki --limit 5`, depois `read "<Título>" --content` em poucas páginas. A nota canónica de pedagogia lê-se com `source "10_Sources/Knowledge/PageCraft/PageCraft-pedagogia-vault.md"`.

Os temas mínimos são:
- a pedagogia PageCraft/MEM e a avaliação formativa ou cooperada;
- *TIC no Ensino Básico*;
- o tema e as aprendizagens em causa;
- o *Método das 28 Palavras*, quando for leitura inicial.

Em `sources.md`, separa o que é Fonte, o que é Síntese da wiki e o que é proposta tua. Confirma documentos curriculares antes de afirmares alinhamentos. Se a API falhar, lê os ficheiros em `/home/proteu/obsidian-vault/20_Wiki/`. Se as fontes forem insuficientes, regista a lacuna. Não inventes pesquisa.

## Gates e reparação

- **Gate determinístico:** `CHECK check <slug> --phase <fase>` termina com código 0. Valida só os artefactos até essa fase, exige as saídas dela e aplica as regras de aprovação: seis scores ≥3, evidência e nenhum `blocked_by` quando `pass:true`, e unidades que cabem na duração. Numa reparação, corre o gate da fase reparada e depois o das seguintes. Só uma ligação externa a uma aplicação que o DocSpec declara como tarefa externa pode ficar como exceção, e a justificação vai para o manifest com `--note`. Os avisos são lidos e corrigidos ou justificados.
- **Gate do browser:** o Evaluator só aprova com evidência observada. Sem browser, `pass:false` e `blocked_by`, sem ticket: o orquestrador resolve o bloqueio e volta a correr o Evaluator. Uma análise estática não demonstra usabilidade.
- **Encaminhamento:**
  - JS, CSS, layout ou acessibilidade técnica → Builder;
  - paleta, tipografia ou sistema visual → Designer e depois Builder;
  - texto → Builder, com as sugestões do Proofreader;
  - meta, constraint, níveis, avaliação ou currículo → Architect e depois as fases a jusante;
  - várias falhas críticas → `both`, com a ordem indicada no ticket.
- **Reparações cirúrgicas:** o Builder corrige o ticket sobre o HTML atual. Não regenera a página.
- **Limite:** 3 iterações. Para passar desse limite é preciso nova evidência e a justificação no manifest. Se a mesma falha se repetir sem evidência nova, para e entrega o diagnóstico e o rascunho, não uma atividade dada como pronta.

## Pronto para revisão

Uma atividade está pronta para o professor quando:

- `CHECK check <slug> --phase delivery` sai com 0, ou com a exceção justificada. Este gate exige `pass:true` na última revisão linguística e na última avaliação, as duas mais recentes do que o HTML, e Builder e Evaluator de famílias diferentes;
- existem o guia `<slug>.md` e as fontes `<slug>-sources.md`;
- o último `evaluation-vN` tem `pass:true`, sem problemas críticos e com todos os scores ≥3;
- a página abre sem erros na consola e a interação principal funciona;
- há um percurso completo em cada nível, e a criança chega ao constraint pela interação;
- a página foi verificada nas larguras da referência de adaptação à idade, incluindo o iframe do host;
- a página funciona sem internet, à parte uma tarefa externa declarada.

## Registo, aprovação e publicação

1. `uv run python "$SKILL_DIR/scripts/activity.py" register <slug> --metadata drafts/<slug>-activity.json`. O servidor (`127.0.0.1:8777`) reserva um código estável de seis caracteres. Confirma que a API pública recusa o rascunho.
2. Entrega a ligação de pré-visualização e espera pela revisão do professor. **Cada atividade exige aprovação própria.** Instalar a skill, arrancar o serviço ou criar o túnel não aprova nenhuma atividade.
3. Só depois da aprovação explícita: `uv run python "$SKILL_DIR/scripts/activity.py" publish <CODIGO> --approved`. O servidor injeta a ponte, regenera o catálogo e serve o endereço permanente `https://pagecraft.infantinho.xyz/<CODIGO>`. Não escrevas diretamente em `activities/` nem em `catalog.json`.
4. Para mudar uma atividade publicada, cria um novo slug de versão. A versão que os alunos já realizaram fica preservada.

O hostname é estável e não se cria um túnel por atividade. Alterações ao túnel usam a skill `cloudflare-publish` e exigem autorização. O professor consulta os resultados em `https://estudio.infantinho.xyz/teacher/activities.html`, protegido por Cloudflare Access. Os alunos usam só o endereço público. Nunca reveles credenciais. Commits seguem as regras do repositório. Push, mensagens e envio de relatórios a terceiros só com pedido próprio.
