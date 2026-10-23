# Revisão linguística e pedagógica M28P para TIC

Revisão independente de 23/10/2026, fases Proofreader e Evaluator pedagógico. Foram lidas as identidades e instruções dos papéis, os princípios, o contrato v3, o desenho comum, o gerador, o template e os dados incorporados nos 168 HTML. Esta é uma revisão estática, com verificações do modelo JavaScript extraído do artefacto real. O coordenador executa separadamente o ensaio no browser real. Este relatório não afirma ter visto os ecrãs renderizados, ouvido gravações ou observado crianças.

## Resultado após correções

A revisão linguística e pedagógica estática passa após as correções de `e17bee1` e a regeneração da coleção. Não ficaram pendências materiais nesta passagem. A aceitação final para revisão docente depende também da verificação de browser e do site pelo coordenador. A autonomia de utilização por crianças continua por validar em sala.

A entrada não exige critérios em prosa ou conversa com adulto. As seis instruções principais são concretas e corretas em português europeu. Os dados cobrem 28 palavras, seis jogos por palavra e quatro rondas por jogo. Não encontrei distratores de palavras futuras nos dados dos jogos. Menina usa fragmentos próprios; flor usa letras móveis; passarinho e cigarra preservam os dígrafos na segmentação oral.

## Correções verificadas nos HTML regenerados

1. A demonstração passou a usar a palavra, imagem e peças da tarefa. Desapareceram pato, pata e as peças genéricas. As instruções da demonstração dizem "peças", incluindo flor, sem chamar sílabas às suas quatro letras. Mostrar a própria resposta em recall é ajuda e fica registado como demonstração vista.
2. O erro passou a assinalar uma relação concreta. Na ordenação destaca a primeira peça fora de lugar; na lacuna destaca o lugar vazio; nos pares assinala a ligação a rever; na procura assinala escolhas inadequadas e a linha em que continuar a procurar; na igualdade mostra comparação de caracteres. A resposta permanece e o avanço continua possível depois de responder, mesmo incorretamente. A clareza visual desses sinais deve ser confirmada no browser.
3. O estado conserva por ronda `demo_shown`, `model_shown`, `audio_word_requested` e `audio_instruction_requested`. A tentativa inclui esses apoios e `model_visible`. A recuperação preserva os campos. Isto permite distinguir o contexto da resposta; pedir áudio não comprova que a criança o ouviu ou que a reprodução terminou.
4. Uma ronda de pares só fica respondida depois de ligar todos os desenhos. Confirmei no modelo real que uma ligação parcial é recusada e que um conjunto completo de ligações incorretas permite confirmar. O avanço depende de responder, sem exigir acerto.
5. Os quatro tabuleiros iniciais de menina-pairs alternam agora os lados através de `flipColumns`, aplicado pelo runtime. Mantêm um único par e servem sobretudo para familiarização com a ação. Não são evidência suficiente de leitura.

A primeira passagem, conservada no histórico do commit `1861952`, tinha assinalado estes problemas. O estado estruturado atualizado está em [proofread.json](../../drafts/m28p-v3/proofread.json).

## Operações e apoios efetivamente implementados

Os seis jogos finais são Palavra igual, Ligar pares, Procurar palavras, Montar com modelo, A peça que falta e Montar de memória. Palavra igual pede uma seleção por comparação escrita com modelo. Procurar palavras pede várias seleções por igualdade visual. Ligar pares associa desenhos a palavras. Os restantes trabalham ordenação, lacuna e reconstrução com modelo oculto por defeito na tarefa.

Os princípios, o contrato e o desenho comum foram reconciliados com esta escolha. Não descrevem Palavra igual como prova de associação semântica ou leitura. Os dois jogos de igualdade praticam operações próximas, com cargas de seleção diferentes.

Com pistas, Passo a passo e Mais desafios alteram a visibilidade de imagem, modelo, segmentação e destaques. Conservam todos os itens e as respostas. O número de opções ou pares varia entre palavras e rondas, sem mudar ao selecionar outro apoio. A documentação deixou de prometer redução de alternativas por apoio.

O título Montar de memória não permite concluir que a criança trabalhou sem ajuda. Com pistas mostra modelo, ouvir está disponível e a demonstração apresenta a palavra. Os registos conservam esses contactos. Não se atribui leitura oral, escrita independente ou fluência à reconstrução gráfica.

## Casos verificados nos dados reais

- Menina: `me`, `ni`, `na`; opções dos jogos de igualdade contêm a palavra e fragmentos próprios. As instruções não exigem conversa nem digitação. Pares mantém apenas um item nesta primeira palavra e alterna os lados.
- Flor: uma sílaba lexical, `flor`; unidades de construção `f`, `l`, `o`, `r`, com `unit: letter`. As quatro lacunas percorrem as quatro letras. A demonstração utiliza essas unidades e chama-lhes peças.
- Passarinho: `pa`, `ssa`, `ri`, `nho`; cigarra: `ci`, `ga`, `rra`. As peças mantêm ss, nh e rr juntos. Não há áudio de fonemas ou de sílabas isoladas declarado no manifesto.
- Instruções principais: "Toca na palavra igual ao modelo", "Toca no desenho. Depois, toca na palavra", "Procura as palavras iguais ao modelo", "Toca nas peças para formar a palavra", "Escolhe a peça que falta" e "Forma a palavra. Podes ouvir outra vez". São frases curtas e compreensíveis em PT-PT. A demonstração e o ensaio real têm de confirmar que a criança percebe a ação sem leitura adulta.

## Evidência e limites

Foi extraído e analisado o JSON de `script#m28p-content` de todos os HTML em `drafts/m28p-v3/*/*.html`: 168 atividades, 28 por ID e 672 rondas. Verificaram-se instruções, opções, respostas, peças, lacunas e repertório. A segunda passagem confirmou nos 168 HTML a demonstração contextual, a terminologia corrigida, os campos de apoio, a confirmação completa dos pares, a alternância de lados e a função de pistas locais. Imagens SVG e os sete áudios de cada atividade estão incorporados nos dados.

Executei em Node o modelo JavaScript extraído do HTML de menina-pairs. Asserções confirmaram bloqueio de pares incompletos, aceitação de pares completos incorretos, rejeição do acerto dessas ligações e conservação dos apoios na recuperação. Isso verifica a lógica pura, sem substituir o ensaio de interação.

Fotografia da revisão pedagógica, anterior à barreira de recuperação do host: menina-pairs SHA-256 `b5a85e9389cce729f92d6ce28b19abd3ff04dc8775a2ed7e82b9f60ee043c9bd`; flor-syllables `9d4338076fe83d5a090f5ddbadc546476032f62701c0368ac797d5102105ea69`; template `e848f2ef1e6311d22563277b872b2221f49eacd42f0da3a421d10ad78b818652`.

Foram lidos os SVG de menina, gema e cigarra como código, sem concluir clareza visual a partir dessa leitura. O manifesto identifica voz sintética `pt-PT-RaquelNeural` e transcrições coerentes com as instruções. Não foi feita verificação auditiva da pronúncia nesta fase.

Ficam para o coordenador: browser real, áudio audível, contraste renderizado, clareza das imagens, rato/toque/teclado, estados de erro e ajuda, recuperação no host e ligações privadas no site. Quatro rondas não são automaticamente três a seis minutos: o único par de menina pode durar menos. A duração é uma estimativa de planeamento; não se deve atrasar o jogo para a cumprir.

A futura experiência com alunos é necessária para avaliar a autonomia de utilização. Esta revisão não demonstra aquisição de leitura.
