---
name: pagecraft-codex
description: Criar e preparar atividades PageCraft para revisão do professor, com pesquisa na Sebenta, diferenciação, PT/EN quando pedido, autoavaliação e registos de trabalho. Usar no Codex ou através do OpenClaw para aulas interativas do 1.º ciclo e publicação aprovada em pagecraft.infantinho.xyz.
---

# PageCraft

Produz uma atividade que o professor possa usar e avaliar com a turma. A fonte desta skill vive em `skills/codex/` no repositório PageCraft; a instalação é um link para essa pasta. Resolve o repositório pelo destino real desta skill ou por `PAGECRAFT_REPO`. Nesta instalação: `/home/proteu/pagecraft`.

## Pedido e fontes

O professor indica tema, ano e duração. Usa português europeu por defeito. Só inclui inglês se o professor o pedir; nesse caso, cria uma versão PT/EN completa com seletor para cada aluno, incluindo instruções, feedback, acessibilidade e autoavaliação. O relatório do professor mantém os critérios em português e preserva as respostas originais do aluno.

Consulta `AGENTS.md`, `PRODUCT.md` e `CONTEXT.md` do repositório. O pedido atual do professor prevalece sobre orientações antigas. Os níveis são **Broto — Apoio**, **Árvore jovem — Intermédio** e **Árvore robusta — Desafio**, sem paleta semáforo.

Antes de conceber a atividade, usa a skill `sebenta-wiki`, instalada em `/home/proteu/.codex/skills/sebenta-wiki/SKILL.md`. Confirma a API, pesquisa e lê integralmente poucas páginas sobre:

- a pedagogia PageCraft/MEM e a avaliação formativa ou cooperada;
- o contexto atual de trabalho do professor, incluindo `TIC no Ensino Básico`;
- o tema, as aprendizagens e os apoios pertinentes.

Distingue síntese da wiki, fonte original e proposta tua. Guarda títulos, caminhos e data de consulta em `drafts/<slug>-sources.md`. Confirma documentos curriculares quando fundamentares alinhamentos; uma proposta curricular não é automaticamente um referencial homologado. Se a API falhar, usa o fallback indicado na skill; se não houver fontes suficientes, explicita a lacuna no rascunho para revisão, sem inventar pesquisa realizada.

## Papéis e artefactos

Usa subagentes Codex para as fases abaixo quando disponíveis. A execução via OpenClaw está descrita em [runtime](references/runtime.md). Mantém papéis e artefactos separados quando o runtime exigir execução sequencial. O orquestrador integra e verifica.

1. **Architect:** lê `agents/pagecraft-architect.md`, `identities/architect.md` e as fontes pesquisadas. Cria `drafts/<slug>-docspec.json`, válido contra `server/pipeline/schemas/docspec.schema.json`. Define objetivos observáveis, unidades SRTC-A, duração, critérios compreensíveis e três apoios. Cria também `drafts/<slug>.md`, guia do professor.
2. **Designer:** lê `agents/pagecraft-designer.md` e `identities/designer.md`. Produz `drafts/<slug>-design-spec.json` a partir do DocSpec e dos padrões do repositório.
3. **Builder:** lê `agents/pagecraft-builder.md`, `identities/builder.md` e os dois artefactos. Produz `drafts/<slug>.html`. O HTML é autocontido, CSS/JS inline, sem dependências de rede. Uma tarefa numa aplicação externa pode precisar de internet; distingue isso da página PageCraft e não simules observação do trabalho externo.
4. **Proofreader:** lê `agents/pagecraft-proofreader.md` e `identities/proofreader.md`. Revê português e, quando pedido, inglês, incluindo estados, instruções e mensagens. Guarda problemas e correções em `drafts/<slug>-proofread.json`.
5. **Evaluator:** lê `agents/pagecraft-evaluator.md` e `identities/evaluator.md`. Usa `agent-browser-hub`, perfil `research` ou `temporary`, para testar interação principal, três apoios, troca de língua, teclado, tablet/telemóvel, autoavaliação e gravação no relatório. Fecha a sessão. Guarda evidência em `drafts/<slug>-evaluation.json`.

Regista o estado e caminhos reais em `drafts/<slug>-run-manifest.json`. Uma reprovação regressa à fase responsável. Não declara testes que não executaste. Se uma falha persistir sem nova evidência, entrega o diagnóstico e o rascunho, não uma atividade supostamente pronta.

## Atividade e reflexão

Controlos com pelo menos 48 × 48 px, foco visível, contraste legível, labels e alternativa a arrastar por teclado/clique. A interação ajuda a descobrir o conceito e dá feedback útil; não entrega apenas instruções e um questionário desligado da tarefa.

Apresenta os critérios antes do trabalho. A autoavaliação retoma esses critérios, com linguagem ajustada ao ano e apoios de proficiência: escolher com ajuda visual/oral; descrever uma estratégia; explicar e justificar com exemplos. A criança pode mudar de apoio ou deixar respostas por dar. O nível de apoio não produz uma classificação da criança.

A ponte usa `postMessage`; consulta [integração com realizações](references/learning.md) e o contrato canónico em `server/pipeline/prompts/references/bridge-contract.md`. O HTML não chama a API nem contém credenciais. O host guarda evidências e a autoavaliação. O nome escrito pelo aluno identifica os registos para o professor, mas não dá acesso a históricos. Mantém evidência observada, voz do aluno e observação do professor separadas.

## Rever e publicar

Rascunhos ficam em `drafts/`, fora das pastas públicas. Regista o rascunho com `scripts/activity.py register <slug> --metadata <ficheiro>`; o servidor reserva um código estável de seis caracteres. Entrega ao professor a ligação de pré-visualização, os objetivos, os critérios e a evidência de testes. Confirma que a API pública recusa o rascunho.

A revisão do professor é necessária **para cada atividade**. A autorização de instalar esta skill, arrancar o serviço ou criar o túnel não aprova a atividade. Depois da aprovação, usa `scripts/activity.py publish <CODIGO> --approved`; o servidor reutiliza `server.publish.publish_activity`, injeta a ponte, regenera o catálogo e disponibiliza o endereço permanente. Não escreve diretamente no catálogo. Para rever conteúdo já publicado, usa um novo slug de versão e novo rascunho; preserva a versão que os alunos já realizaram.

O hostname estável serve todas as atividades; não cria um túnel por atividade. Para instalar, alterar ou reparar a publicação, usa `cloudflare-publish` em `/home/proteu/.codex/skills/cloudflare-publish/SKILL.md`. Verifica a origem e as rotas, preserva os serviços partilhados e executa apenas alterações autorizadas. O servidor e o conector precisam de continuar ativos.

Cumpre os commits incrementais do repositório. Push, mensagens ou envio de relatórios a terceiros precisam de pedido próprio. Os relatórios desta versão ficam na área privada do professor e podem ser descarregados.

## Entrega

Entrega a pré-visualização ou o URL publicado conforme o estado real, os ficheiros produzidos, os testes executados e quaisquer limitações. Para consultar resultados: `/teacher/activities.html`. A entrada remota do professor é `https://estudio.infantinho.xyz/teacher/activities.html`, protegida por Cloudflare Access com código enviado ao e-mail autorizado. Não uses o antigo emparelhamento. Os alunos usam `https://pagecraft.infantinho.xyz/<CODIGO>`; nunca lhes entregues o hostname privado. O helper de automação continua a usar apenas o bootstrap local; nunca revela credenciais no chat.
