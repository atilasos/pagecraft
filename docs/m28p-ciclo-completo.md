# Ciclo completo das 28 palavras em TIC: recombinar, ler palavras novas e frases

Proposta de 16/11/2026, a pedido do professor de TIC, para os alunos do 2.º ano que estão no método. Completa a coleção v3 descrita em [m28p-contrato-percursos.md](m28p-contrato-percursos.md). Essa coleção tem seis minijogos por palavra que trabalham só a própria palavra: comparar, associar, ordenar, lacuna e reconstruir. A Sebenta (*Método das 28 Palavras*) descreve o ciclo completo: reconhecer, escrever, segmentar, recombinar sílabas conhecidas em palavras novas, ler frases curtas e verificar a generalização. Associar imagem a palavra, sozinho, é o «uso degradado» do método. O que falta à coleção é precisamente a generalização.

## Decisões do professor (16/11/2026)

- Entram as quatro operações abaixo.
- **Fonte:** o material escolar da pasta «m28p» do Drive do professor, com direito de uso confirmado. Aproveita-se só o conteúdo linguístico. A letra, as imagens e as atividades não se reutilizam, porque estão desatualizadas: cursiva, clip-art e cópia mecânica. O inventário das páginas 1–29 identificou ainda figuras impróprias nas páginas 4 e 7, que não se usam.
- **Repertório por famílias silábicas:** até à palavra-chave N contam as consoantes das palavras 1..N, combinadas com as vogais (com e sem acento). É o que o manual faz na p.29: «ovo», «novo», «nove», «neve», «avó», «avô». Os dígrafos e os ditongos só entram quando uma palavra-chave os traz.
- **Só palavras reais.** Não entram pseudopalavras nem nomes próprios sem personagem apresentada. As exclusões ficam registadas com a razão em `policy.excludedFromSource`.
- **Frases:** o PageCraft propõe frases curtas só com o repertório e o professor revê-as. O formato aceita depois frases ditadas pela turma (texto livre, MEM).
- **Repertório por aluno:** o professor escolhe a palavra-chave de cada criança.
- **Piloto:** menina, menino e uva.

## Repertório e dados

Os dados vivem em `drafts/m28p-v3/cycle.json`, cujo estado é «proposta para revisão docente». Cada palavra nova entra na primeira palavra-chave em que é formável e cita a página de origem, ou fica marcada `"source": "proposta"`. `picturable` indica se a palavra tem uma imagem inequívoca: só essas entram em «Ler e escolher». Palavras como «nome», «nova» e «novo» ficam em «Ouvir e montar», «Descobrir palavras» e frases.

O gerador recusa os dados quando:
- uma palavra nova ou um token de frase usa uma consoante que ainda não foi aprendida até N, ou um ditongo ou dígrafo que ainda não foi introduzido;
- a concatenação das sílabas não reproduz a grafia;
- falta a imagem ou o áudio de algum item.

As imagens são SVG originais e o áudio é pt-PT com a voz da coleção. O TTS nunca modela fonemas nem sílabas isoladas.

Nas três primeiras palavras há poucas palavras novas, e o próprio método funciona assim. Por isso, as rondas misturam as palavras-chave já trabalhadas com as palavras novas. Um jogo só é gerado se houver itens distintos para as suas quatro rondas.

## Ordem das palavras-chave

As fontes disponíveis não concordam na ordem (verificado a 16/11/2026):

| Fonte | Ordem | Notas |
| --- | --- | --- |
| Catálogo oficial de *O Novo Mundo das Palavras* (Porto Editora, edição de 2024), consultado a 23/10/2026 ([investigação](research/metodo-28-palavras-2026.md)) | menina, menino, uva, dedo, sapato, bota, leque, casa, janela, telhado, escada, chave, galinha, gema, rato, cenoura, girafa, palhaço, zebra, bandeira, funil, árvore, quadro, passarinho, peixe, cigarra, fogueira, flor | É a edição mais recente e a ordem de `words.json`. O catálogo apresenta a lista em quatro colunas lidas na vertical. A 16/11 o site devolveu 403 a pedidos automáticos e não foi possível voltar a confirmar. |
| Fichas da escola («1º Ano - Fichas-Método 28 palavras», 432 `.doc`) | menina, menino, bota, sapato, uva, leque, casa, janela, escada, telhado, chave, gema, galinha, girafa, rato, cenoura, palhaço, zebra, peixe, bandeira, árvore, quadro, passarinho, cigarra, fogueira, flor | São 26 palavras, sem dedo nem funil. A ordem foi deduzida da numeração das fichas «Sílabas». |
| «Manual Metodo-28-Palavras-Outras-Fichas» (2011) | menina, menino, uva, sapato, bota, mamã, leque, … | Inclui «mamã» e não inclui «dedo». |

**Decisão:** a coleção mantém a ordem do catálogo oficial mais recente, confirmada pelo professor a 16/11/2026. O repertório de cada palavra-chave é calculado a partir dessa ordem. Uma turma que siga outra variante só precisa de outra ordem em `consonantsByKeyword` e `words.json`. As diferenças entre fontes são trocas locais (bota/sapato, escada/telhado, gema/galinha, peixe/bandeira). O piloto é válido nas três ordens porque usa só m, n e v.

**Frases das fichas da escola:** «O menino tem o balão», «A Ana faz o Sol», «O menino vai à escola» e outras são de leitura global e usam letras que ainda não foram trabalhadas. Não servem os jogos de recombinação de menina e menino. Ficam como referência para palavras-chave posteriores, quando o repertório as cobrir.

## Quatro minijogos novos por palavra-chave

Cada jogo segue as regras da v3:
- quatro rondas; Montar frases admite uma a quatro rondas fixas;
- demonstração recuperável;
- avanço por resposta, mesmo com erro;
- pista local antes da demonstração;
- conservação do trabalho ao mudar de apoio;
- áudio iniciado pela criança;
- alvos ≥56 px;
- registos sem classificar a criança.

Os três apoios chamam-se **Com ajuda**, **Sozinho** e **Consigo ajudar um amigo**. As chaves técnicas não mudam.

| ID | Nome | Estado e ação | Restrição a descobrir | Evidência |
| --- | --- | --- | --- | --- |
| `listen-build` | Ouvir e montar | Ouve uma palavra nova e monta-a com peças silábicas do repertório (alvo e distratores conhecidos), sem modelo | Sílabas conhecidas formam palavras que ainda não tinham sido vistas | Sequência confirmada e ajudas usadas, incluindo ver o modelo |
| `read-choose` | Ler e escolher | Lê uma palavra nova escrita e escolhe a imagem entre três; o áudio é ajuda registada | A leitura das sílabas dá o significado | Imagem escolhida e se ouviu antes de escolher |
| `sentence` | Montar frases | Vê a imagem (o áudio é opcional) e ordena cartões de palavras para formar a frase | As palavras têm ordem e a frase diz o que a imagem mostra | Ordem confirmada e ajudas usadas |
| `discover` | Descobrir palavras | Até quatro rondas com 2 ou 3 palavras escondidas cada; o tabuleiro tem só as sílabas dessas palavras e mais uma. Contador «1 de 2», lugar por palavra (imagem e som em Com ajuda, sílabas vazias em Sozinho) e «Não encontro mais», que revela as que faltam. Revisto a 16/11/2026: com 39–52 sílabas e sem contador, o professor não sabia quantas palavras havia nem quando o jogo acabava | Combinações diferentes dão palavras diferentes | Palavras descobertas e tentativas; nunca uma nota |

Os apoios ajustam a visibilidade de modelo, imagem e segmentação, como na v3:
- **Com ajuda:** o modelo segmentado fica disponível.
- **Sozinho:** a ação é feita sem modelo.
- **Consigo ajudar um amigo:**
  - sem modelo nem imagem auxiliar;
  - no fim, há um convite opcional e só oral para explicar a um colega como leu;
  - o convite não se regista como avaliação.

### Frase da turma

Na página da turma, o professor guarda frases ditadas pelas crianças, escolhe a palavra-chave e pode projetá-las no Quadro durante a sessão, até carregar em «Esconder frase no Quadro». O banco funciona também sem sessão. Aceita frases com 2 a 12 palavras e acrescenta ponto final quando falta pontuação. Os avisos de repertório ajudam o professor a decidir, sem bloquear texto livre nem nomes próprios.

Em Montar frases, as quatro frases mais recentes da turma até à palavra-chave da atividade entram primeiro. As frases fixas completam as rondas até quatro. Menina e menino passam a ter este jogo, mesmo com menos de quatro frases fixas. As frases da turma mostram o rótulo «Frase da turma», sem imagem; Com ajuda mostra os tokens e os restantes níveis ocultam o texto. O áudio destas frases usa apenas vozes locais pt-PT; sem voz local, o botão de ouvir fica oculto. As frases fixas conservam o MP3 incluído. O progresso é recuperado mesmo quando as frases chegam depois do estado guardado.

## Volume e fases

São no máximo 28 × 4 jogos, limitados às palavras-chave em que a lista editorial tenha itens. Os recursos novos são áudio por palavra nova e por frase (`edge-tts`, via `scripts/prepare_m28p_tic_assets.py`) e um SVG original por palavra nova e por frase. As imagens são o maior custo de produção e de revisão.

1. **Contrato e motor:** `cycle.json`, a validação no gerador e os quatro jogos no template comum. Testes de dados e de interação, com dados de ensaio que não chegam aos alunos.
2. **Piloto:** três palavras-chave escolhidas pelo professor, com a lista editorial real. Recursos, registo como rascunho e revisão docente.
3. **Coleção:** as restantes palavras-chave, por lotes, com revisão docente por atividade, conforme o fluxo de aprovação.

Os registos digitais descrevem ações e ajudas. Não certificam leitura, fluência nem domínio do método. A verificação de generalização em sala (ler palavras novas, escrever sem copiar) continua a ser feita pelo professor.

## Revisão do piloto pelo council (23/11/2026)

Quatro modelos de famílias diferentes reviram os 10 jogos do piloto antes de o gerador passar às restantes palavras-chave. As correções que mudam o contrato:

- **Demonstração:** usa sempre a palavra-chave (em Montar frases, «A menina», «O menino»…), com os mesmos controlos do jogo: ouvir, peças, tabuleiro e Confirmar. A palavra-chave nunca é uma ronda, por isso a demonstração não revela respostas. A demonstração aberta por «Começar» fica registada à parte (`introDemo`), não como ajuda da ronda 1.
- **Rondas:** primeiro as palavras novas da própria palavra-chave, depois as anteriores, das mais recentes para as mais antigas. Ouvir e montar e Ler e escolher têm 3 ou 4 rondas (menina só tem três palavras novas); Descobrir palavras tem 1 a 4; Montar frases 1 a 4. Os distratores de Ouvir e montar são sílabas da mesma família e do mesmo tamanho; os de Ler e escolher rodam entre as imagens disponíveis.
- **Repertório:** `cycle.json` descreve, por palavra-chave, os ataques (consoantes e dígrafos, com as vogais trabalhadas: ca/co/cu em casa, ce/ci em cenoura), os ditongos, as sílabas fechadas (escada, bandeira, funil, árvore) e os contextos de leitura (s entre vogais desde casa, r brando desde cenoura, r inicial desde rato). O validador confirma que as 28 palavras-chave se leem com esta tabela, que cada palavra nova entra na primeira palavra-chave em que é formável, que os tokens das frases são palavras registadas (`sentenceWords` para verbos como «vê») e que não há recursos partilhados por grafias diferentes.
- **Palavras reais:** a geração consulta o dicionário pt-PT da Universidade do Minho (Hunspell), descarregado para cache local numa revisão fixa (`scripts/m28p_lexicon.py`). Recusa palavras novas que não constem. Em Descobrir palavras, escolhe o grupo de palavras e a sílaba a mais de modo a minimizar as palavras reais que se formam fora da lista; nenhum tabuleiro deixa formar uma palavra do vocabulário que não esteja escondida, incluindo a palavra-chave. As que não se podem evitar ficam no relatório de geração e no guia do professor. Quando qualquer sílaba a mais formaria outra palavra do vocabulário, a ronda fica sem ela e o guia di-lo.
- **Frases:** cada frase declara a sua cena ilustrada (`scene`); falta de cena recusa a geração. Quando a ordem inversa diz o mesmo («A mana é a menina.»), regista-se em `alternatives` e conta como certa. Saíram «A mana e o mano.» (sem verbo) e «A uva é nova.» (a imagem não mostra «nova»); entrou «A avó vê o menino.».
- **Imagens:** a menina usa camisola e calças, sem vestido nem laços. «mana» e «mano» deixam de ter imagem própria, porque só se distinguem numa cena. O ovo está num oveiro e a neve mostra flocos a cair. Os SVG perdem o `<title>` ao ser incorporados, para a dica do rato não revelar a resposta.
- **Níveis em Ler e escolher:** Com ajuda mostra a palavra dividida em sílabas; Sozinho, a palavra inteira; Consigo ajudar um amigo, a palavra sem botão de ouvir. As opções chamam-se «Imagem 1», «Imagem 2» e «Imagem 3».
- **Descobrir palavras:** o contador diz «Encontraste 1 de 2.»; depois de concluída ou revelada, a ronda não reabre; o som só toca quando a criança o ligou.
