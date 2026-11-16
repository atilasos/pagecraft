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

## Quatro minijogos novos por palavra-chave

Cada jogo segue as regras da v3:
- quatro rondas;
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
| `discover` | Descobrir palavras | Quadro silábico do repertório: junta 2 ou 3 sílabas e, se formar uma palavra da lista, revela imagem e áudio e guarda-a na «caixa de palavras» | Combinações diferentes dão palavras diferentes | Palavras descobertas e tentativas; nunca uma nota |

Os apoios ajustam a visibilidade de modelo, imagem e segmentação, como na v3:
- **Com ajuda:** o modelo segmentado fica disponível.
- **Sozinho:** a ação é feita sem modelo.
- **Consigo ajudar um amigo:**
  - sem modelo nem imagem auxiliar;
  - no fim, há um convite opcional e só oral para explicar a um colega como leu;
  - o convite não se regista como avaliação.

## Volume e fases

São no máximo 28 × 4 jogos, limitados às palavras-chave em que a lista editorial tenha itens. Os recursos novos são áudio por palavra nova e por frase (`edge-tts`, via `scripts/prepare_m28p_tic_assets.py`) e um SVG original por palavra nova e por frase. As imagens são o maior custo de produção e de revisão.

1. **Contrato e motor:** `cycle.json`, a validação no gerador e os quatro jogos no template comum. Testes de dados e de interação, com dados de ensaio que não chegam aos alunos.
2. **Piloto:** três palavras-chave escolhidas pelo professor, com a lista editorial real. Recursos, registo como rascunho e revisão docente.
3. **Coleção:** as restantes palavras-chave, por lotes, com revisão docente por atividade, conforme o fluxo de aprovação.

Os registos digitais descrevem ações e ajudas. Não certificam leitura, fluência nem domínio do método. A verificação de generalização em sala (ler palavras novas, escrever sem copiar) continua a ser feita pelo professor.
