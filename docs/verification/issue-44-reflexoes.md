# Verificação das reflexões individuais

Em 30/09/2026, a etapa [#44](https://github.com/atilasos/pagecraft/issues/44) foi implementada no ramo `t3code/melhorar-usabilidade-atividades`. No computador do grupo, cada criança escolhe o seu nome, responde ou omite a reflexão e pode voltar para a rever. A reflexão fica na sua voz individual, separada da produção conjunta.

## Comportamentos verificados

- O nome da criança permanece no título do formulário. Trocar de participante abre as suas respostas, sem copiar as do colega.
- São usados os critérios registados da atividade ou os critérios explícitos do documento de uma atividade publicada. Objetivos e instruções de avaliação do professor não são transformados em critérios. Sem critérios declarados, ficam disponíveis as perguntas livres sobre ajuda e próximo passo.
- Perguntas e reflexão inteira são facultativas. A omissão explícita fica identificada como “Preferiu não responder”; não é um resultado errado nem uma classificação.
- O servidor valida a autorização do grupo e a pertença do participante. A atividade não escolhe a autoria. A reflexão interna de um HTML antigo não é copiada como reflexão individual dos membros. O rascunho de Frações abre a reflexão do anfitrião através da ponte existente.
- Cada revisão fica no registo canónico da sessão, com autor individual, critérios apresentados e contexto do grupo original. Não existe armazenamento paralelo de reflexões no servidor.
- Repetir o mesmo envio não duplica o registo nem repõe uma revisão antiga. Um envio diferente com a mesma identificação e uma revisão desatualizada são recusados. Fechar a sessão impede novas reflexões.
- O dispositivo mantém rascunhos separados por sessão, grupo e criança neste separador. Um envio com resposta perdida pode ser repetido depois de recarregar. Uma resposta atrasada de uma identidade anterior não altera o formulário nem o rascunho do novo grupo.
- Históricos do professor preservam todas as revisões; relatórios apresentam a última reflexão de cada criança e grupo original. Não contam autoavaliações como tentativas certas ou competência individual. A entrada individual e os nomes congelados da ponte permanecem compatíveis.

## Testes automáticos

```sh
uv run --with playwright pytest -q
node --check server/static/student/reflection.js
node --check server/static/student/app.js
node --check server/static/teacher/class.js
```

Resultado final: **264 aprovados, 57 omitidos, em 11,40 s**. Os 57 testes de browser exigem `PAGECRAFT_TEST_CDP`, não configurado nesta sessão. Incluem três novas regressões para turnos/reflexões/professor, resposta perdida e resposta tardia após libertação. Estes testes foram acrescentados e revistos, mas não se apresentam como executados. A sintaxe dos clientes e `git diff --check` passaram.

Os testes HTTP passaram primeiro por falhas observáveis: ausência do percurso de reflexão, ausência das reflexões no relatório e perda dos critérios de uma atividade publicada. Exercitam autoria, duas reflexões diferentes, omissão, revisão, repetição, conflito de revisão, isolamento entre grupos, critério inválido, reflexão antiga e encerramento. As fronteiras são as interfaces públicas de aluno e professor já aprovadas.

## Browser real

Foi usado o browser colaborativo nativo do T3 Code com uma instância descartável do Studio, dados fictícios e HTTPS temporário. O ensaio inicial incluiu teclado com Space/Enter e inspeção a 390 px: sem transbordamento horizontal, opções com altura de 82 px. As ferramentas de apontador e screenshot tiveram falhas e alguns cliques atingiram outro controlo após deslocação. Nos ensaios posteriores usaram-se os controlos e formulários reais pelo DOM do browser. Não se afirma uma auditoria completa de toque; pertence à etapa #45.

Na sessão de ensaio, Ana guardou “Consegui com ajuda” e “Comparei os blocos com o Bruno.”. Bruno abriu um formulário vazio e guardou “Quero praticar mais” e outra estratégia. Carla omitiu a reflexão. Ana reviu depois a resposta para “Consegui com autonomia”. A API real do professor confirmou duas revisões de Ana, uma de Bruno e uma omissão de Carla; nenhuma voz foi atribuída aos colegas.

No ensaio de resposta perdida, a API guardou normalmente com HTTP 200 e o browser perdeu apenas a resposta. Depois de recarregar, Ana viu o envio por guardar e repetiu-o. O histórico do professor continuou com um único registo antes da revisão posterior.

No ensaio de resposta tardia, Iris enviou a reflexão e a leitura da resposta HTTP real ficou retida. O professor libertou o grupo; o dispositivo voltou à entrada e Lara entrou noutro par. Depois de libertar a resposta antiga, o formulário “A reflexão de Lara” continuou aberto, com “O meu novo rascunho.” intacto.

O HTML e JavaScript reais do professor foram ensaiados com uma captura das respostas HTTP autorizadas e do snapshot real do ensaio. O histórico de Ana mostrou ambas as revisões com o seu nome, separado dos acontecimentos conjuntos; o de Carla mostrou a omissão. O relatório mostrou as três vozes e os números individuais sem tentativas certas atribuídas a partir da reflexão. A fotografia é só de leitura: não testa autenticação remota de professor nem SSE contínuo e não acompanha novos envios da demonstração do aluno.

## Revisão

Base fixa: `e974916e2416fe20b9089694819d6eb4dbe02ba0`. Duas revisões independentes segundo a skill code-review.

### Standards

Sem violações documentais. Foi corrigida uma falha de ciclo de vida: a geração da identidade é novamente verificada depois de ler a resposta JSON. A regressão e o ensaio real preservaram o novo formulário. Permanece uma sugestão facultativa de reunir os textos de autoavaliação dos clientes e do relatório.

### Spec

Foi corrigida a omissão dos critérios explícitos das atividades publicadas. O teste HTTP passou de lista vazia para os critérios reais de Leitura al/el/il/ol/ul. A revisão final não encontrou requisitos pendentes ou alargamento de âmbito em #44.

Resultado: **zero problemas bloqueantes nas duas frentes**.

## Demonstração temporária

- [Aluno](https://democratic-program-nurses-smile.trycloudflare.com/student/), código **LV7AMZ**, seis nomes fictícios livres no momento da entrega.
- [Professor, fotografia só de leitura](https://democratic-program-nurses-smile.trycloudflare.com/outputs/groups-teacher/index.html?v=44-review), com as reflexões do ensaio anterior de Ana, Bruno e Carla.

Os dois endereços e o JavaScript atualizado foram verificados por HTTPS. O endereço privado real do professor recusou o visitante remoto não autorizado. A origem continua isolada em `/tmp/pagecraft-groups-43-lw7de0b_`, na porta de loopback 18781, através do túnel temporário já autorizado. Não foram alterados DNS, Access ou produção. A demonstração depende da origem e do conector ativos. Os artefactos de ensaio e os processos podem ser retirados sem alterar o ramo ou a implantação de produção.

Alterações de participantes, tratamento da composição de respostas pendentes e verificação integrada pertencem à etapa [#45](https://github.com/atilasos/pagecraft/issues/45).
