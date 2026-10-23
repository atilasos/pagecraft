# Atividades permanentes, realizações por nome e professor remoto

O professor confirmou atividades reutilizáveis em aula e em casa, entrada pelo nome escrito pela criança e acompanhamento privado por realização. Acrescentamos endereços permanentes de seis caracteres, separados dos códigos temporários de Sessão de aula: o nome ajuda o professor a reconhecer o aluno, mas não autentica acesso a históricos. Cada realização tem uma credencial própria e dados privados; correções de identificação pertencem ao professor.

**Atualização:** a autenticação remota por emparelhamento descrita no parágrafo seguinte foi substituída pelo [ADR-0006](0006-professor-com-cloudflare-access.md), a pedido do professor. As decisões sobre atividades e realizações mantêm-se.

Esta decisão alarga o [ADR-0004](0004-acesso-com-negacao-por-omissao.md): o bootstrap local continua a ser a origem de confiança, mas pode autorizar outro dispositivo do professor por um código de uso único com dez minutos de validade. A sessão remota usa cookie HttpOnly/Secure e continua sujeita às políticas de Acesso. Não exigimos contas de email aos alunos nem uma política Cloudflare Access global que impedisse a entrada pelo nome; a aplicação protege a área do professor.

Os ensaios de rascunhos não entram nos relatórios. A autoavaliação declarada não substitui evidências nem origina notas automáticas. O código conserva a mesma atividade publicada; revisões de conteúdo usam um novo rascunho e slug para preservar o contexto dos trabalhos anteriores. Os registos novos usam a persistência JSON existente, com um processo servidor e exclusão mútua nas escritas.

## Isolamento das gerações e da aprovação

Em 22/10/2026, concretizamos a regra de novo slug por revisão no Studio. Cada geração recebe um slug com o identificador do job e um diretório próprio para todos os artefactos. Assim, dois jobs do mesmo tema não partilham HTML, plano, design, Markdown ou pareceres. Os prompts e os acontecimentos mantêm os diretórios próprios de cada job.

O conjunto final inclui hashes SHA-256 de todos os ficheiros de geração, incluindo pareceres de iterações anteriores. O identificador da revisão vincula esses hashes ao job, slug e mapa de artefactos. O preview e a aprovação exigem esse identificador. A publicação verifica novamente os hashes e usa os bytes verificados, incluindo os elementos deterministas que antes eram acrescentados só ao publicar. Uma alteração, remoção ou adição invalida a revisão. Uma decisão explícita do professor pode dispensar o parecer do Evaluator, mas não esta verificação de integridade.

A aprovação fica persistida antes de publicar. Após restart, uma publicação interrompida exige a mesma revisão aprovada. O diretório completo da atividade é instalado atomicamente e o catálogo continua derivado dos `meta.json`, conforme o ADR-0003. Repetir a mesma publicação conserva conteúdo e metadados e recupera o catálogo quando necessário. Um slug ocupado não aceita outra geração. As gerações publicadas pelo Studio também recusam substituições pelo percurso manual. O percurso manual anterior conserva as suas regras para atividades sem identidade de geração.

Jobs antigos sem isolamento comprovado conservam os ficheiros para diagnóstico, mas ficam bloqueados para publicação e pedem uma nova geração. Jobs antigos já concluídos e atividades entregues mantêm os seus registos e endereços. Não inferimos a autoria de ficheiros partilhados nem migramos esses ficheiros para uma aprovação nova. A opção explícita `auto_publish` conserva o funcionamento anterior, registando a revisão autorizada antes de publicar.
