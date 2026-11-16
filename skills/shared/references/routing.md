# Encaminhamento de fases para modelos

O orquestrador é a sessão que carregou a skill. Coordena, lança as fases, corre os gates e decide. Não faz o trabalho das fases nem carrega os ficheiros grandes delas, que ficam no contexto dos delegados.

## Escolher o mecanismo

1. **T3 Code**, quando existe a ferramenta `delegate_task`:
   - chama `orchestrator_capabilities` uma vez por thread e escolhe na lista que essa chamada devolve;
   - fase com modelo do mesmo fornecedor da sessão e sem opções acima das tuas → subagente nativo (Claude: `Agent` com `pagecraft-<fase>`; Codex: `spawn_agent`);
   - fase com modelo de outro fornecedor, ou com opções próprias → `delegate_task` com `target` (fornecedor, modelo, esforço), `role` adequado e isolamento `shared`, porque os artefactos vivem na mesma checkout;
   - segue o `next` que o `delegate_task` devolve: a conclusão reacorda a thread. Não faças polling nem `sleep`;
   - não cries worktrees nem threads novas para as fases.
2. **Claude Code sem T3:** usa os subagentes `pagecraft-*` com a ferramenta `Agent`. O `model:` do frontmatter aplica a classe de cada fase dentro da família Claude. Para a independência, corre o Builder no Codex com `/codex:rescue` quando o plugin existir.
3. **Codex sem T3:** usa os subagentes do Codex com o ficheiro de fase como instrução. Para a independência, corre o Proofreader e o Evaluator noutra família quando houver um CLI disponível (por exemplo, `claude -p`).

4. **Sem delegação:** executa as fases em sequência e escreve o artefacto de cada uma antes de começar a seguinte. Não mistures responsabilidades. A mesma sessão pode produzir, mas não pode aprovar o que produziu: sem revisão independente, o Evaluator não emite `pass:true`.

## Classe de modelo por fase

Escolhe pela classe, não por um nome fixo. Os exemplos são indicativos; o que `orchestrator_capabilities` devolver tem prioridade.

| Fase | Classe necessária | Exemplo no T3 | Esforço |
|---|---|---|---|
| Architect | raciocínio pedagógico profundo, pt-PT | Claude Opus | high |
| Designer | médio, JSON curto | Claude Sonnet | medium |
| Builder | código longo e saída extensa | GPT via Codex (Sol) | high |
| Proofreader | pt-PT fiável, de preferência família ≠ Builder (o gate avisa) | Claude Sonnet | medium |
| Evaluator | julgamento e browser, família ≠ Builder | Claude Opus ou Sonnet | high |
| Reparação | a classe da fase que falhou | igual à fase | igual |

As regras de família:

- **Independência:** o Evaluator é obrigatoriamente de família diferente da do Builder; o Proofreader, de preferência (o gate avisa). Se o Builder for Claude, o Evaluator é GPT ou Grok (Cursor). Regista o par autor/revisor no manifest.
- **Terceira família:** Grok via Cursor serve como crítico independente quando já há duas famílias envolvidas, ou para uma segunda opinião sobre o DocSpec em atividades de duas ou mais unidades.
- **Indisponibilidade:** se faltar um modelo que o professor pediu, diz-lho e espera autorização antes de o substituir. Se faltar só o exemplo por defeito, escolhe outro da mesma classe e de família diferente da do autor, e regista-o no manifest.
- **Sem segunda família:** em qualquer modo, se não houver revisão independente, o Evaluator não aprova. Entrega o rascunho com a limitação declarada e pede ao professor uma decisão: autorizar a revisão na mesma família ou disponibilizar outro fornecedor. A decisão regista-se com `CHECK log <slug> --phase teacher --status approved --note "revisão na mesma família: <decisão>"`. Depois da autorização, volta a correr o Evaluator e regista-o com `--status done --artifact drafts/<slug>-evaluation-vN.json`. O gate de entrega só aceita a exceção se a última decisão do professor for `approved` e for seguida desse novo relatório.

## Brief de cada delegado

O delegado não vê o histórico da conversa. O brief tem de ser autónomo e curto:

```text
Fase: <architect|designer|builder|proofreader|evaluator> — iteração <N>
Repositório: <raiz>; SKILL_DIR=<skills/claude|skills/codex>
Lê primeiro: $SKILL_DIR/agents/pagecraft-<fase>.md (o teu contrato) e segue-o.
Pedido normalizado: tema, ano, duração, línguas, maker, slug, restrições.
Entradas: <caminhos em drafts/>; em reparação: <ticket-vN>.
Saída: <caminho exato>. Valida com CHECK antes de terminar.
Devolve só: caminho escrito, resultado do CHECK (código de saída), 3–8 linhas de decisões ou riscos.
Não faças commit, push, publicação nem registo.
```

Não colas no brief o conteúdo de referências nem o HTML, só os caminhos. Para conteúdo grande, o delegado usa `CHECK lean`. O browser do Evaluator está descrito no ficheiro dessa fase. Se o delegado não tiver ferramentas de browser, o orquestrador recolhe a evidência com `preview_*` (T3) ou `agent-browser-hub` e entrega-lha para julgamento.

## Economia

- **Leitura:** o orquestrador lê os artefactos JSON e o resultado do `CHECK`, nunca o HTML integral.
- **Combinar fases:** em atividades de uma só unidade, Architect e Designer podem correr no mesmo delegado, em passos separados e com artefactos separados. Builder e Evaluator nunca correm no mesmo delegado.
- **Reparações:** cada reparação é um delegado novo com o ticket e a vista enxuta, e não a continuação de uma conversa longa.
- **Apoio do orquestrador:** só corrige diretamente substituições de texto triviais vindas do Proofreader (no máximo 5, sem lógica). Volta depois a correr a incorporação e o `CHECK`, e corre de novo o Proofreader antes do Evaluator, porque o gate de entrega recusa revisões mais antigas do que o HTML.
