# Aula ao vivo servida por túnel Cloudflare num subdomínio estável

A aula ao vivo (PageCraft Studio: sessões, códigos de entrada, eventos, controlo de sala) é servida a partir do portátil do professor através de um túnel Cloudflare num subdomínio estável de `infantinho.xyz` (ex.: `estudio.infantinho.xyz`). Os PCs fixos da sala de TIC guardam um favorito permanente para esse URL; o arranque da aula reduz-se a «abrir o favorito, escrever o código de 6 letras». Decisão tomada em 2026-07-21 com aprovação explícita do professor, incluindo o redesenho da autenticação de professor que hoje recusa pedidos atrás de proxy/túnel (`server/security.py`).

## Considered Options

- **GitHub Pages / Cloudflare Pages / hosting estático** — rejeitado para a aula ao vivo: só servem ficheiros estáticos e o fluxo de sessão precisa do servidor FastAPI (SSE, tokens, eventos). Continuam válidos para o catálogo público.
- **Supabase (ou backend gerido equivalente)** — rejeitado: exigiria reescrever o backend inteiro sem ganho pedagógico.
- **Rede local direta (bind na LAN, favorito para o IP do portátil)** — rejeitado como via principal porque o IP do portátil muda (DHCP) e o favorito parte-se; mantém-se como **plano B documentado** para quando a internet da escola falhar.

## Consequences

- **Tensão assumida com o princípio «Offline é identidade» (PRODUCT.md):** as atividades continuam self-contained e offline, mas a *camada de sessão* passa a depender da internet da escola. O princípio aplica-se às páginas, não ao Studio; o plano B em LAN é a rede de segurança.
- A autenticação do professor (hoje token só em loopback direto) tem de ser redesenhada para funcionar atrás do túnel sem abrir o Studio a terceiros.
- O `/student/` fica exposto à internet pública: códigos de sessão passam a ser a única barreira de entrada e o roster expõe primeiros nomes a quem tiver o código — mitigações (expiração de sessões, rate limiting no join) passam a ser requisito, não luxo.
