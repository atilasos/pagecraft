# Atividades permanentes, realizações por nome e professor remoto

O professor confirmou atividades reutilizáveis em aula e em casa, entrada pelo nome escrito pela criança e acompanhamento privado por realização. Acrescentamos endereços permanentes de seis caracteres, separados dos códigos temporários de Sessão de aula: o nome ajuda o professor a reconhecer o aluno, mas não autentica acesso a históricos. Cada realização tem uma credencial própria e dados privados; correções de identificação pertencem ao professor.

Esta decisão alarga o [ADR-0004](0004-acesso-com-negacao-por-omissao.md): o bootstrap local continua a ser a origem de confiança, mas pode autorizar outro dispositivo do professor por um código de uso único com dez minutos de validade. A sessão remota usa cookie HttpOnly/Secure e continua sujeita às políticas de Acesso. Não exigimos contas de email aos alunos nem uma política Cloudflare Access global que impedisse a entrada pelo nome; a aplicação protege a área do professor.

Os ensaios de rascunhos não entram nos relatórios. A autoavaliação declarada não substitui evidências nem origina notas automáticas. O código conserva a mesma atividade publicada; revisões de conteúdo usam um novo rascunho e slug para preservar o contexto dos trabalhos anteriores. Os registos novos usam a persistência JSON existente, com um processo servidor e exclusão mútua nas escritas.
