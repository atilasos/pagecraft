# Explorar as frações

Rascunho das cinco unidades de exploração, preparado nos tickets #39 e #40. É uma revisão de Frações com Minecraft, do 2.º ano, com identificador próprio. A construção Minecraft e a reflexão final pertencem ao ticket #41; o ensaio não substitui a atividade publicada. Reservar cerca de 30 minutos para esta exploração, ajustando o ritmo à turma.

## Percurso

1. A criança corta o pão e responde se ficaram duas metades. Só depois de responder pode avançar, mesmo que se engane. Alterar o corte exige responder outra vez.
2. Em Com pistas e Passo a passo, escolhe entre duas partilhas. Com pistas mostra apoio para alinhar as partes desde o início. Em Mais desafios, inventa um corte desigual e escolhe uma explicação. O avanço exige a resposta, não o acerto.
3. Pinta e confirma uma fração. A grelha inicial não conta como resposta.
4. Escolhe o símbolo para cada imagem ou expressão. Todas as associações ficam registadas, incluindo as erradas.
5. Confirma uma representação na grelha. O desenho livre é opcional e não recebe classificação automática.
6. Compõe uma unidade, confirma a composição e responde se está inteira. Mudar as partes invalida a confirmação e a resposta.
7. Compara cada par, escolhendo A, B ou Iguais. As barras representam unidades do mesmo tamanho.
8. O ecrã de revisão permite regressar ao trabalho. No contexto de uma Realização da atividade, reabrir ou recarregar recupera a página, as representações, as respostas e o desenho guardados, incluindo uma pergunta que voltou a ficar por responder. Aberta diretamente ou numa Sessão de aula, a página mantém as manipulações em memória enquanto está aberta. As tentativas enviadas ao Studio seguem a persistência existente.

Os três níveis permanecem disponíveis à criança. O nível inicial é Passo a passo; o contrato `learning_preferences` aplica o nível recebido do contexto de realização. O cliente de sessões ao vivo atual não fornece Perfis de diferenciação; aí mantém-se o nível por defeito e a escolha local. As mudanças de nível são registadas tanto em realizações como nas sessões ao vivo.

## Rever

Abrir o HTML diretamente permite experimentar sem rede. Acrescentar `?presentation=1` ativa a demonstração, com navegação livre e sem emitir acontecimentos. O quadro usa este modo automaticamente. Este parâmetro altera apenas a apresentação, não concede permissões de acesso.

Para registar o rascunho no Studio, usar o JSON de registo que acompanha o HTML como corpo de `POST /api/learning/activities`, num cliente autenticado de professor. A API devolve o código para abrir a pré-visualização; o rascunho continua privado e os ensaios não entram nos relatórios de alunos. O registo é idempotente pelo identificador da atividade. Esta etapa não fornece um DocSpec completo para publicação, pois o percurso completo ainda está em preparação.

## Evidências e ajuda

Cada resposta ou confirmação emite uma tentativa da unidade correspondente, de `u1` a `u5`, com acerto e descrição curta. Alterar uma representação, desenhar, restaurar ou navegar não emite tentativas. A confirmação da composição e a resposta sobre estar inteira são dois pedidos distintos, com evidências separadas. Correções preservam as tentativas anteriores. A demonstração não emite acontecimentos, incluindo pedidos de ajuda e batimentos de ligação. A página direta sugere chamar o professor; integrada no Studio, «Preciso de ajuda» usa a ponte existente.

Os controlos usam toque ou teclado. As vinhetas passam a uma coluna em ecrãs estreitos. Esta divisão foi aprovada para esta atividade; nas restantes, rever o percurso caso a caso.

## Retoma da realização

O anfitrião de realizações aceita `activity_state` na mesma fila de gravação dos acontecimentos existentes e devolve esses registos em `learning_restore`. São pontos de restauro, não tentativas nem Evidências, e ficam excluídos dos relatórios do professor. O payload inclui identificador da atividade, versão e estado limitado ao trabalho da criança. O rascunho valida os valores recebidos antes de os usar. A demonstração não guarda estado nem responde a pedidos de restauro.

## Desafios de cada percurso

| Pedido | Com pistas | Passo a passo | Mais desafios |
| --- | --- | --- | --- |
| Pintar | 1/2, modelo visível | 1/4 | 2/5 |
| Associar | imagem 1/2 e palavras «um quarto» com modelo | imagem 1/2 e palavras «três quartos» | imagens 2/5 e 3/4, palavras «um quarto» |
| Grelha | 1/2 | 3/4 | 3/4 |
| Unidade inteira | 2 partes | 4 partes | 5 partes |
| Comparar | 1/2 com 1/4; 1/2 com 1/2 | 1/4 com 1/2; 2/4 com 1/2 | 2/5 com 1/2; 3/4 com 2/4; 2/4 com 1/2 |

As listas são finitas e os cartões mostram quantos faltam. Uma mudança de percurso conserva as respostas a pedidos iguais e invalida os pedidos que mudaram. Na grelha e no desenho livre, a criança representa e conversa com o colega; não precisa de escrever uma explicação longa. O desenho usa dedo/rato ou setas e Espaço; «Limpar desenho» permite recomeçar. O registo está limitado a 1000 pontos por desenho.
