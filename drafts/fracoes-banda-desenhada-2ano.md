# Uma metade para cada um

Rascunho da unidade inicial, preparado para o ticket #39. É uma revisão parcial de Frações com Minecraft, do 2.º ano, com identificador próprio. As restantes unidades e a construção Minecraft serão acrescentadas nos tickets #40 e #41; o ensaio não substitui a atividade publicada.

## Percurso

1. A criança corta o pão e responde se ficaram duas metades. Só depois de responder pode avançar, mesmo que se engane. Alterar o corte exige responder outra vez.
2. Em Broto e Árvore jovem, escolhe entre duas partilhas. Broto mostra apoio para alinhar as partes desde o início. Em Árvore robusta, inventa um corte desigual e escolhe uma explicação. O avanço exige a resposta, não o acerto.
3. O ecrã de revisão permite regressar ao trabalho. No contexto de uma Realização da atividade, reabrir ou recarregar recupera a página, os cortes e as respostas guardados, incluindo uma pergunta que voltou a ficar por responder. Aberta diretamente ou numa Sessão de aula, a página mantém as manipulações em memória enquanto está aberta. As tentativas enviadas ao Studio seguem a persistência existente.

Os três níveis permanecem disponíveis à criança. O nível inicial é Árvore jovem; o contrato `learning_preferences` aplica o nível recebido do contexto de realização. O cliente de sessões ao vivo atual não fornece Perfis de diferenciação; aí mantém-se o nível por defeito e a escolha local. As mudanças de nível são registadas tanto em realizações como nas sessões ao vivo.

## Rever

Abrir o HTML diretamente permite experimentar sem rede. Acrescentar `?presentation=1` ativa a demonstração, com navegação livre e sem emitir acontecimentos. O quadro usa este modo automaticamente. Este parâmetro altera apenas a apresentação, não concede permissões de acesso.

Para registar o rascunho no Studio, usar o JSON de registo que acompanha o HTML como corpo de `POST /api/learning/activities`, num cliente autenticado de professor. A API devolve o código para abrir a pré-visualização; o rascunho continua privado e os ensaios não entram nos relatórios de alunos. O registo é idempotente pelo identificador da atividade. Esta etapa não fornece um DocSpec completo para publicação, pois o percurso completo ainda está em preparação.

## Evidências e ajuda

Cada resposta emite uma tentativa da unidade `u1`, com acerto e descrição curta. Alterar o corte ou navegar não emite tentativas. Correções preservam as tentativas anteriores. A demonstração não emite acontecimentos, incluindo pedidos de ajuda e batimentos de ligação. A página direta sugere chamar o professor; integrada no Studio, «Preciso de ajuda» usa a ponte existente.

Os controlos usam toque ou teclado. As vinhetas passam a uma coluna em ecrãs estreitos. Esta divisão foi aprovada para esta atividade; nas restantes, rever o percurso caso a caso.

## Retoma da realização

O anfitrião de realizações aceita `activity_state` na mesma fila de gravação dos acontecimentos existentes e devolve esses registos em `learning_restore`. São pontos de restauro, não tentativas nem Evidências, e ficam excluídos dos relatórios do professor. O payload inclui identificador da atividade, versão e estado limitado ao trabalho da criança. O rascunho valida os valores recebidos antes de os usar. A demonstração não guarda estado nem responde a pedidos de restauro.
