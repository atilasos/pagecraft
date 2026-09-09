# Verificação do PageCraft permanente

Estado: implementação instalada; piloto `canva-agua-4ano`, código `ZBEVB2`, preparado para revisão do professor e ainda não publicado. O manifesto está em [canva-agua-4ano-run-manifest.json](../../drafts/canva-agua-4ano-run-manifest.json).

## Testes e artefactos

- Suite completa: **231 testes passaram em 5,17 segundos**. Os novos testes cobrem privacidade do rascunho, nomes iguais com credenciais distintas, recuperação, eventos repetidos/concorrentes, conclusão idempotente, reflexão, relatório e observação privada do professor, emparelhamento de uso único, expiração, rejeição de origem diferente e entrada de 30 alunos pelo mesmo IP.
- DocSpec, design-spec, proofread e evaluation do piloto validados contra os schemas do repositório.
- Skill validada por `quick_validate.py`; `skills/sync-from-canonical.sh --check` sem divergências; JavaScript verificado com `node --check`.
- `openclaw skills info pagecraft-codex --json`: `eligible`, `modelVisible` e `userInvocable` verdadeiros; caminho para a skill deste repositório. Isto confirma a descoberta da skill. Não foi ensaiada uma execução delegada OpenClaw → worker Codex.

## Percurso real no browser

Executado com `agent-browser-hub`, em sessões de pesquisa e temporária, fechadas no final:

1. Área local do professor: cartão do rascunho e pré-visualização acessíveis. O botão de aprovação do piloto não foi acionado.
2. Entrada com nome de teste; mudança para inglês traduziu alojamento e HTML; interação na comparação entre texto curto e longo.
3. Seleção de Broto e autoavaliação em inglês: um critério preenchido, restantes omitidos, estratégia e próximo passo guardados. O JSON privado confirmou `language=en`, `level=support` e as respostas enviadas. As realizações de pré-visualização não entram nos relatórios dos alunos.
4. Nova realização: escrita de «A torneira continua a pingar depois do recreio.», mudança para Testar e recarga. A etapa foi recuperada; ao regressar a Explorar, o estado do browser mostrou a frase no textarea.
5. Seleção de Árvore robusta por teclado: reflexão passou a pedir justificação da estratégia e como verificar o progresso. Árvore jovem foi usada no percurso inicial.

Capturas locais: [atividade final](/home/proteu/agent-browser-hub/screenshots/pagecraft-pilot-final.png) e [autoavaliação](/home/proteu/agent-browser-hub/screenshots/pagecraft-pilot-reflection.png). A captura anterior [compactação intermédia](/home/proteu/agent-browser-hub/screenshots/pagecraft-pilot-compact.png) foi examinada pelo Evaluator; a captura final da atividade foi examinada pelo integrador. A captura inicial [antes dos ajustes](/home/proteu/agent-browser-hub/screenshots/pagecraft-pilot-desktop.png) fica apenas como registo de desenvolvimento.

## Serviço, publicação e acesso

`pagecraft.service` e `pagecraft-studio-tunnel.service`: ativos e habilitados. `loginctl show-user proteu -p Linger`: `Linger=yes`. Configuração preparada para arranque sem sessão gráfica; não foi feito um reboot durante esta verificação.

Verificação HTTP sem cookies, tanto em `127.0.0.1:8777` como em `pagecraft.infantinho.xyz` e no hostname existente `estudio.infantinho.xyz`:

| Pedido | Estado esperado e observado |
|---|---|
| `/api/health` | 200 |
| `/api/learning/reports` | 401 |
| `/ZBEVB2` | 404 — rascunho privado |
| `/api/learning/activities/ZBEVB2/content` | 404 — HTML privado |

Pedidos HTTPS usaram um User-Agent de browser; o User-Agent padrão de urllib encontrou a proteção Cloudflare 1010. Não foram desativadas proteções. O browser real abriu o site.

O percurso remoto do professor também foi verificado por HTTP: gerar código na origem local, trocar no hostname HTTPS, receber cookie Secure, consultar painel/relatórios/rascunho autenticados e terminar sessão. Códigos e cookies não foram incluídos nos artefactos.

## Limites

A revisão pedagógica e textual permite entregar o rascunho ao professor. Não houve utilização com alunos nem criação real de apresentação no Canva; duração e acesso Canva precisam de confirmação nos equipamentos da escola. Não foi ensaiado telefone estreito, zoom elevado, leitor de ecrã ou disponibilidade de vozes PT/EN. Não foi recolhida uma captura explícita da consola durante o percurso. Estas provas não certificam acessibilidade completa.

A reflexão integrada usa critérios, estratégia e próximo passo; o HTML autónomo usa também perguntas separadas de conquista e ajuda. A diferença está documentada no guia do professor. A evidência guardada pelo PageCraft não prova ações realizadas numa aplicação externa.

Operação e utilização: [guia do PageCraft permanente](../pagecraft-permanente.md).
