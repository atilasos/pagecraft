# Ciclo completo das 28 palavras em TIC: recombinar, ler palavras novas e frases

Proposta de 16/11/2026, a pedido do professor de TIC, para os alunos do 2.º ano que estão no método. Completa a coleção v3 descrita em [m28p-contrato-percursos.md](m28p-contrato-percursos.md). Essa coleção tem seis minijogos por palavra que trabalham só a própria palavra: comparar, associar, ordenar, lacuna e reconstruir. A Sebenta (*Método das 28 Palavras*) descreve o ciclo completo: reconhecer, escrever, segmentar, recombinar sílabas conhecidas em palavras novas, ler frases curtas e verificar a generalização. Associar imagem a palavra, sozinho, é o «uso degradado» do método. O que falta à coleção é precisamente a generalização.

## Decisões do professor (16/11/2026)

- Entram as quatro operações abaixo.
- **Fonte das palavras novas e das frases:** a lista editorial dos materiais do método que o professor usa com a turma. Não geramos listas nem inventamos pseudopalavras. O professor fornece o material e confirma o direito de uso em turma, que fica registado em `source.rights`.
- **Repertório por aluno:** os jogos de uma palavra-chave N usam só as sílabas e palavras de 1..N. O professor escolhe a palavra de cada criança.

## Repertório cumulativo

O repertório de N é a união das sílabas orais das palavras 1..N em `drafts/m28p-v3/words.json`. Os dígrafos ficam inteiros (`nha`, `lha`, `que`, `rra`, `ssa`). Alguns marcos de dimensão: menina tem 3 sílabas, sapato 11, galinha 28, gema 30 e flor 57. Nas primeiras palavras há poucas palavras novas possíveis, por isso só se geram jogos de ciclo para as palavras-chave em que a lista editorial tenha itens.

## Contrato de dados: `drafts/m28p-v3/cycle.json`

```json
{
  "source": {"title": "<material editorial>", "pages": "<páginas>", "rights": "<autorização de uso em turma>", "addedBy": "professor", "date": "2026-11-16"},
  "functionWords": ["a", "o", "e", "é", "um", "uma", "tem"],
  "keywords": {
    "casa": {
      "newWords": [{"label": "saco", "syllables": ["sa", "co"], "image": "saco", "audio": "saco"}],
      "sentences": [{"text": "A menina tem uma bota.", "tokens": ["A", "menina", "tem", "uma", "bota"], "image": "frase-casa-1", "audio": "frase-casa-1"}]
    }
  }
}
```

O exemplo `saco` é só ilustrativo da forma dos dados. O gerador valida o seguinte e recusa os dados quando falha:

- **Sílabas e grafia:**
  - cada `newWords[].syllables` pertence ao repertório de N;
  - a concatenação das sílabas reproduz `label`;
  - nenhuma palavra nova usa uma sílaba de uma palavra posterior a N.
- **Frases:** cada token é uma palavra-chave de 1..N, uma palavra nova já introduzida até N ou uma `functionWords` da fonte editorial.
- **Recursos:**
  - cada imagem e cada áudio referidos existem em `assets/m28p-tic/` (cycle);
  - as imagens são SVG originais e inequívocas;
  - o áudio é pt-PT com a mesma voz da coleção e regista-se no manifesto;
  - não se usa TTS para modelar fonemas nem sílabas isoladas.

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
