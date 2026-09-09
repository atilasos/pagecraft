# Codex e OpenClaw

A instalação liga esta pasta a `~/.agents/skills/pagecraft-codex`, localização pessoal descoberta por Codex e OpenClaw nesta máquina. Os recursos permanecem versionados no repositório.

No Codex, invoca `$pagecraft-codex` e executa o percurso da skill. Não fixa nomes de modelos: usa os agentes disponíveis e os prompts de fase.

No OpenClaw, carrega esta skill e a skill `coding-agent` quando estiver elegível. Delega o pedido a Codex com a pasta de trabalho `/home/proteu/pagecraft` e o pedido explícito de usar `$pagecraft-codex`; transmite tema, ano, duração, línguas e a obrigação de parar no rascunho para revisão. Segue os comandos e o transporte declarados pela instalação atual do `coding-agent`, sem inventar ACP ou `agentId`.

Se a delegação não estiver disponível, o OpenClaw pode seguir as fases sequencialmente com as mesmas identidades e artefactos, usando as suas ferramentas disponíveis. Só promete QA real se o Hub funcionar nesse runtime. Não cria uma segunda versão da pedagogia nem publica por ter terminado a geração.

Verifica a descoberta com `openclaw skills info pagecraft-codex` e `openclaw skills check`. Para o Codex, a documentação oficial de descoberta está em https://developers.openai.com/codex/skills/ . Se a sessão já aberta mantiver o catálogo anterior, abre uma nova sessão.
