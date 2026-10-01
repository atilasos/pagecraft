# Verificação da entrada do professor por e-mail

Aplicação Cloudflare Access criada: `PageCraft — Professor`, `83026e04-18af-475d-8fcf-6ce56bc7180a`, hostname integral `estudio.infantinho.xyz`. Uma política Allow, apenas `atila.sos@gmail.com`, sem outras identidades, bypass ou service auth. Fornecedor One-time PIN existente, sessão de 24 horas. A aplicação, fornecedor selecionado e política foram relidos pela API. O fornecedor partilhado e as aplicações OPM/Sebenta não foram alterados. Não houve alterações a DNS ou rotas do túnel.

O serviço carrega uma audiência própria e emissor `https://inantinho.cloudflareaccess.com`; o token de administração Cloudflare não é fornecido à aplicação. `pagecraft.service` reiniciado com a configuração e ativo. Bootstrap e pré-visualização privados locais continuam acessíveis.

## Evidência

- **240 testes passaram em 5,70 s.** Casos de assinatura RSA real com chave de teste: identidade autorizada, assinatura errada, e-mail diferente, outra audiência, outro emissor, expiração, emissão no futuro, ausência de sujeito, headers falsos, cookie antigo, hostname público, origem LAN e falha na obtenção de chaves. Inclui redirecionamento para login e logout Access.
- Browser real via `agent-browser-hub`: o endereço privado abriu o formulário `Sign in · Cloudflare Access`, com e-mail e `Send login code`. [Screenshot](/home/proteu/agent-browser-hub/screenshots/pagecraft-email-login.png) inspecionado. Não foi enviado código nem usada a caixa de correio do professor; receção e autenticação humana permanecem por testar.
- Browser local: painel atualizado, sem o botão de emparelhamento; rascunho continua privado.
- HTTP sem cookies em `pagecraft.infantinho.xyz`: `/api/health` e `/student/` 200; `/login` e `/teacher/activities.html` 303 para o professor; `/api/learning/reports` 401; `/ZBEVB2` 404.
- HTTP sem cookies em `estudio.infantinho.xyz`: todos os caminhos testados, incluindo relatórios, pré-visualização e health, 302 para Access. Isto comprova proteção na entrada, não uma autenticação humana completa.
- Políticas e assinatura testadas para identidade diferente, sem enviar e-mails a uma terceira pessoa. A recusa com outra identidade real não foi ensaiada.

Referências oficiais: [One-time PIN](https://developers.cloudflare.com/cloudflare-one/integrations/identity-providers/one-time-pin/), [validação JWT](https://developers.cloudflare.com/cloudflare-one/access-controls/applications/http-apps/authorization-cookie/validating-json/) e [PyJWT](https://pyjwt.readthedocs.io/en/stable/api.html).

Esta verificação substitui os resultados anteriores sobre o login por emparelhamento e o acesso público a `estudio.infantinho.xyz` registados em `pagecraft-permanente.md`.
