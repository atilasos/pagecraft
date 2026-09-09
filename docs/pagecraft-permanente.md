# Usar o PageCraft permanente

## Criar uma atividade

No Codex ou OpenClaw, pede `$pagecraft-codex` com tema, ano e duração. Para inglês, pede explicitamente uma atividade bilingue: cada aluno terá um seletor PT/EN. A skill consulta a Sebenta e prepara HTML, critérios, autoavaliação e guia do professor.

No computador do PageCraft, abre [Atividades e progressos](http://127.0.0.1:8777/teacher/activities.html). Usa **Pré-visualizar** para experimentar a atividade e os apoios. Estes ensaios ficam excluídos dos relatórios dos alunos. **Aprovar e publicar** disponibiliza o endereço reservado, depois da tua revisão. A instalação do serviço não aprova atividades.

O aluno abre `https://pagecraft.infantinho.xyz/<CODIGO>`, escreve o nome e começa. Pode indicar a turma e se trabalha em aula ou em casa. Uma nova realização não mostra trabalhos anteriores de pessoas com o mesmo nome. No mesmo dispositivo, **Trocar de aluno** limpa a identificação e os dados locais dessa realização.

## Consultar e acompanhar

Na área do professor, filtra por nome, turma, atividade e datas. Cada registo separa evidências no PageCraft, autoavaliação e observação/próximo passo do professor. Podes corrigir o nome/turma quando uma criança escreveu uma variante, guardar a observação e descarregar o relatório em Markdown.

O trabalho em aplicações externas, como o Canva, precisa de observação do professor ou de uma declaração do aluno. O PageCraft não observa automaticamente o que acontece noutra aplicação.

Para usar outro computador ou telemóvel, no computador do servidor escolhe **Autorizar outro dispositivo**. Abre [Entrada do professor](https://pagecraft.infantinho.xyz/login) no outro dispositivo e escreve o código. Expira em dez minutos, só pode ser usado uma vez e deve ficar contigo. A autorização remota não permite gerar novos códigos; estes nascem no computador local. Usa **Sair** num dispositivo partilhado.

## Operação nesta máquina

- Serviço: `systemctl --user status pagecraft.service`.
- Atualizar após alterações testadas: `systemctl --user restart pagecraft.service`.
- Logs: `journalctl --user -u pagecraft.service`.
- Origem: `http://127.0.0.1:8777`, com proxy headers do Uvicorn desativados para preservar a resolução de Acesso.
- Conector existente: `pagecraft-studio-tunnel.service`, com as rotas `estudio.infantinho.xyz` e `pagecraft.infantinho.xyz`. O túnel de OPM/Sebenta não foi alterado.
- O serviço do utilizador está habilitado e `Linger=yes`, pelo que arranca com o computador sem depender de login gráfico. A máquina e a ligação à internet precisam de continuar disponíveis.
- Dados privados: `server/data/learning/`. Inclui este diretório nos teus backups, fora de Git e do catálogo público. Não publiques os ficheiros de dados nem o token do professor.
- Sem internet, a página já aberta permite continuar as interações locais. A fila de acontecimentos é reenviada ao recuperar a ligação. A confirmação de gravação só aparece depois da resposta do servidor; evita fechar a aba enquanto indicar trabalho por guardar. Acesso inicial, sincronização e Canva requerem rede.

Para reinstalar os links pessoais da skill: `python3 skills/codex/install.py`. Para reinstalar o serviço: `python3 scripts/install-service.py`. A descoberta de skills segue a [documentação oficial Codex](https://developers.openai.com/codex/skills/); a instalação também foi verificada com `openclaw skills info pagecraft-codex --json`.

## Reverter só esta publicação

O estado anterior do túnel e o identificador do DNS criado ficam em `~/.local/state/pagecraft-deploy/hostname-before.json`, com permissões privadas. Remove apenas o DNS `pagecraft.infantinho.xyz` criado e a rota desse hostname, preservando a rota `estudio.infantinho.xyz` e todas as outras configurações atuais. Não reponhas cegamente o backup completo se entretanto houver alterações concorrentes. Usa a skill `cloudflare-publish` e verifica o resultado pela API.

Para parar o novo serviço: `systemctl --user disable --now pagecraft.service`. Não pares os conectores partilhados. Não desatives `linger` sem verificar os outros serviços do utilizador.

API usada: [configuração do túnel](https://developers.cloudflare.com/api/resources/zero_trust/subresources/tunnels/subresources/cloudflared/subresources/configurations/methods/update/) e [registos DNS](https://developers.cloudflare.com/api/resources/dns/subresources/records/methods/create/).
