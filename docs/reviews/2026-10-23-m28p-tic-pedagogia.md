# Revisão linguística e pedagógica M28P para TIC

Revisão independente de 23/10/2026, fases Proofreader e Evaluator pedagógico. Foram lidas as identidades e instruções desses papéis, os princípios, o contrato v3, o desenho comum, o gerador, o template e os dados incorporados nos 168 HTML. Esta é uma revisão estática. O coordenador executa separadamente o ensaio no browser real; este relatório não afirma ter visto os ecrãs renderizados, ouvido gravações ou observado crianças.

## Resultado desta passagem

A entrada deixou de exigir critérios em prosa ou conversa com adulto. As seis instruções principais são concretas e corretas em português europeu. Os dados cobrem 28 palavras, seis jogos por palavra e quatro rondas por jogo. Não encontrei distratores de palavras futuras nos dados dos jogos. Menina usa fragmentos próprios; flor usa letras móveis; passarinho e cigarra preservam os dígrafos na segmentação oral.

A primeira passagem encontrou falhas que afetam apoio e interpretação do desempenho. Foram comunicadas ao coordenador enquanto o Builder ainda alterava a implementação. É necessário conferir a correção nos HTML regenerados antes de aceitar esta versão. O estado estruturado está em [proofread.json](../../drafts/m28p-v3/proofread.json).

## Problemas encontrados

1. A demonstração usa sempre pato, pata, pa, to e la. Não usa a palavra e as peças da tarefa. No caso de flor, diz "Toca nas sílabas por ordem", "Escolhe a sílaba que falta" e "Ouve. Junta as sílabas", apesar de a tarefa usar quatro letras. O primeiro contacto de menina introduz vocabulário e código exteriores ao seu repertório. A demonstração deve mostrar a operação com unidades pertinentes e dizer "peças" ou, em flor, "letras". Mostrar a própria resposta em recall é apoio, que precisa de ficar registado.
2. Após erro, a implementação lida mostra "Podes experimentar outra vez", ícone de repetição e borda tracejada do modelo. Não assinala o lugar, relação ou peça a rever. O apoio comum está dentro de "Mais ajuda", com ativação automática desabilitada. A criança que não lê pode continuar sem entender como reparar. É necessária uma pista visual junto da ação, preservando a resposta e o direito de avançar.
3. Ouvir e abrir a demonstração não aparecem no estado nem nos detalhes da tentativa na versão lida. O guia diz que ouvir é apoio declarado e que as ajudas ficam nos registos. Uma tentativa de recall pode ter usado modelo ou demonstração sem esse contexto chegar ao professor. Guardar esses apoios sem criar tentativas novas, e conservar a informação ao recuperar trabalho.
4. `TicModel.validAnswer` aceita um único par numa ronda com dois ou três pares. A criança pode confirmar e continuar deixando desenhos sem resposta. Exigir uma ligação por desenho, incluindo ligações incorretas, conserva a regra de avanço por resposta sem o tornar dependente do acerto.
5. Os quatro tabuleiros iniciais de menina-pairs lidos nos HTML eram idênticos: um desenho à esquerda e uma palavra à direita. O gerador começou entretanto a acrescentar `flipColumns`. Falta confirmar a utilização desse campo pelo runtime e a regeneração dos artefactos. Alternar posições torna a repetição menos mecânica. Um par serve sobretudo para aprender a ação; não é evidência suficiente de leitura.

## Seis jogos e diferenças face ao desenho

`match` é agora "Palavra igual", uma comparação escrita com modelo. O desenho comum descrevia associação entre palavra e referente. `pairs` faz essa associação; `hunt` pede localizar várias formas iguais. A alteração de título não é problema, mas os dois jogos de igualdade visual devem ser descritos como tal e não contados como provas distintas de leitura. O coordenador deve confirmar esta escolha ou recuperar a operação inicialmente prevista.

`syllables` apresenta modelo e banco de peças; `gap` varia a lacuna; `recall` retira o modelo por defeito na tarefa. Os dados implementam essas diferenças. O título "Montar de memória" não permite concluir que a criança trabalhou sem ajuda: Com pistas mostra modelo, ouvir está disponível e a introdução mostra a palavra. O relatório precisa de conservar os apoios efetivamente usados.

Há seis IDs e operações utilizáveis, mas quatro rondas não são automaticamente três a seis minutos. O único par de menina pode durar bastante menos. A duração é uma estimativa de planeamento, sujeita à experiência com alunos; não se deve atrasar artificialmente o jogo para a cumprir.

## Casos verificados nos dados reais

- Menina: `me`, `ni`, `na`; opções dos jogos de igualdade contêm a palavra e fragmentos próprios. As instruções não exigem conversa nem digitação. Pares mantém apenas um item nesta primeira palavra.
- Flor: uma sílaba lexical, `flor`; unidades de construção `f`, `l`, `o`, `r`, com `unit: letter`. As quatro lacunas percorrem as quatro letras. O problema encontrado está na demonstração genérica, não na segmentação dos dados.
- Passarinho: `pa`, `ssa`, `ri`, `nho`; cigarra: `ci`, `ga`, `rra`. As peças mantêm ss, nh e rr juntos. Não há áudio de fonemas ou de sílabas isoladas declarado no manifesto.
- Instruções principais: "Toca na palavra igual ao modelo", "Toca no desenho. Depois, toca na palavra", "Procura as palavras iguais ao modelo", "Toca nas peças para formar a palavra", "Escolhe a peça que falta" e "Forma a palavra. Podes ouvir outra vez". São frases curtas e compreensíveis em PT-PT; a prova de que a criança percebe a ação depende da demonstração e do ensaio real.

## Evidência e limites

Foi extraído e analisado o JSON de `script#m28p-content` de todos os HTML em `drafts/m28p-v3/*/*.html`: 168 atividades, 28 por ID e 672 rondas. Verificaram-se instruções, opções, respostas, peças, lacunas e repertório. Foram lidos os SVG de menina, gema e cigarra como código, sem concluir clareza visual a partir dessa leitura. O manifesto identifica voz sintética `pt-PT-RaquelNeural` e transcrições coerentes com as instruções; não foi feita verificação auditiva da pronúncia nesta fase.

A fotografia inicial dos HTML usados para os achados inclui menina-pairs SHA-256 `35f40395a9684ec0327b07d9895bc7cd61714508ea590fce1543872993830325` e flor-syllables `14e772633428001ceb0c115002dcc6c67314de2630b5fc60e7835edf9fc32de1`. O runtime e o gerador estavam a ser editados durante a revisão. Uma correção no template só resolve a atividade entregue depois de regenerar e verificar o HTML correspondente.

Ficam para o coordenador: browser real, áudio audível, contraste renderizado, clareza das imagens, rato/toque/teclado, estados de erro e ajuda, recuperação no host e ligações privadas no site. A futura experiência com alunos é necessária para avaliar autonomia de utilização. Não se afirma autonomia comprovada nem aquisição de leitura com esta revisão.
