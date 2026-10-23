# Contrato dos minijogos M28P v3

Este contrato substitui o desenho v2 de 12–16 ecrãs acompanhados. Os ficheiros v2 e os arquivos mantêm-se como histórico. A proposta atual está nos [princípios](m28p-principios-implementacao.md) e na [pesquisa para TIC](research/m28p-tic-autonomia-2026.md).

## Entradas e artefactos

- `drafts/m28p-v3/words.json`: lista revista das 28 palavras. É a fonte lexical editável.
- `drafts/m28p-v3/collection-design.json`: arquitetura pedagógica e visual comum, com seis jogos independentes.
- `scripts/build_m28p_tic.py`: gerador e validação dos dados, sem publicar nem editar o catálogo.
- `scripts/templates/m28p-tic.html`: interação comum, sem dependências de rede.
- Recursos locais de origem: `images/{slug}.svg`, `audio/{slug}.mp3` e áudio de instrução por ID de jogo, como `audio/match.mp3`, na árvore de recursos v3 usada pelo gerador.

Cada atividade gerada incorpora imagem, fonte e áudios necessários. Caminhos dos recursos de origem não se tornam pedidos de rede em tempo de utilização. O gerador produz 28 × 6 = 168 minijogos HTML, acompanhados pelos artefactos exigidos pelo registo PageCraft, incluindo DocSpec, design, metadados e manifesto. A duração orientadora é cinco minutos nos metadados, com intervalo de planeamento de três a seis minutos. Uma palavra não é um percurso obrigatório de trinta minutos.

A interface de linha de comandos deve permitir gerar a coleção e validar sem escrita. O manual de comandos e destinos finais consta do próprio script e do [registo de renovação](m28p-renovacao.md); não alterar o catálogo como efeito lateral da geração.

## Palavra

`words.json` é um array com esta forma mínima:

```json
[
  {
    "slug": "menina",
    "label": "menina",
    "order": 1,
    "syllables": ["me", "ni", "na"],
    "phonologyNotes": "Palavra em PT-PT; divisão oral em três sílabas."
  }
]
```

`slug` é identificador estável sem acentos; `label` preserva a grafia correta. `order` é único e cobre 1–28. A posição 14 é gema. A concatenação de `syllables` recompõe `label`, com revisão humana da segmentação oral e dos dígrafos. `phonologyNotes` destina-se ao professor e não aparece como instrução infantil. A revisão lexical não importa do v2 as tarefas, pré-requisitos de conversa ou obrigatoriedade do adulto.

Por defeito, a unidade móvel é a sílaba. Se a palavra tem uma sílaba, como flor, os jogos `syllables`, `gap` e `recall` usam os grafemas/letras da palavra. A interface diz "letras" ou "partes" e os registos identificam essa unidade. Não dividir grupos consonânticos em falsas sílabas nem apresentar cada letra como fonema.

## Jogos e SRTC-A

Os IDs são fixos. Cada jogo tem quatro rondas; a resposta e o apoio ficam ligados à ronda. A primeira apresentação inclui demonstração da ação, recuperável depois por um controlo visível. No jogo `recall`, uma demonstração com modelo conta como ajuda, não como evocação independente.

| ID | Estado e representação | Ação e transição | Restrição descoberta | Evidência observável |
| --- | --- | --- | --- | --- |
| `match` | Imagem, palavra e controlo de áudio; escolhas de cartão | Escolher o cartão correspondente, rever ou continuar | Palavra inteira corresponde ao referente apresentado | Cartão escolhido e ajudas vistas |
| `pairs` | Cartões emparelháveis, referência conforme apoio | Escolher dois cartões; repetir pares sem perder os já feitos | Dois cartões correspondem ao mesmo item | Pares tentados e concluídos, com apoio |
| `hunt` | Palavra-modelo e cartões em posições variadas | Tocar na palavra igual; seleção permanece visível | A sequência completa coincide com o modelo | Forma selecionada, comparação visual |
| `syllables` | Modelo, lugares vazios e unidades móveis | Tocar unidades pela ordem; desfazer e confirmar | As partes têm uma ordem na palavra | Sequência confirmada com modelo |
| `gap` | Palavra com uma unidade em falta e alternativas | Escolher a unidade; variar lacuna entre rondas | Uma unidade completa aquele lugar | Unidade escolhida para a lacuna |
| `recall` | Imagem/áudio, lugares vazios e peças sem modelo inicial | Reconstruir, confirmar; recuperar modelo por pedido | A ordem recompõe a palavra trabalhada | Sequência sem modelo inicial e ajuda efetivamente usada |

As peças e posições variam entre rondas. Repetições de sílaba usam identidade por ocorrência para permitir remover e recolocar sem apagar outra igual. Não avaliar ordenação apenas pelo conjunto de peças. O botão de desfazer devolve a peça ao banco e preserva as restantes.

Os distratores escritos usam o repertório atual e anterior que o professor confirmou. No início, menina pode contrastar com os seus fragmentos `me`, `ni` e `na`, apresentados como partes. Não preencher opções com pseudopalavras ou palavras futuras. Pares da primeira palavra podem usar um só par em quatro rondas de posições distintas; depois, acrescentar até três pares do repertório conhecido. Imagens distratoras podem ser apresentadas sem exigir a leitura de nomes novos.

## Apoios e avanço

Os valores da ponte são `support`, `intermediate` e `challenge`, correspondendo a Com pistas, Passo a passo e Mais desafios. Quando o DocSpec exigir `standard`, mapear para `intermediate` na ponte. Os três apoios ajustam modelo, alternativas e destaque; não mudam a resposta correta nem a grafia-alvo no meio da ronda.

Apoio local tem três passos recuperáveis: observar referência; destacar a relação ou lugar a rever; demonstrar a próxima ação. Não exigir leitura de instruções sobre utilidade da ajuda para regressar à tarefa. Conservar unidades, seleção, pares, ronda e respostas ao mudar de apoio. Não emitir tentativa por mudar apoio, ouvir, ver demonstração ou restaurar.

Avançar depende de responder ao pedido da ronda, mesmo com erro. Ordenação requer confirmar uma sequência completa, que pode estar incorreta. Erro não apaga trabalho nem retira acesso a "Seguinte". Há feedback visual imediato e opção de corrigir. Uma ajuda não deve responder automaticamente pela criança nem acrescentar uma tentativa correta ao relatório.

## Interface, áudio e recuperação

Uma ação principal por momento, instrução de duas a seis palavras sempre que possível, controlos estáveis, corpo ≥22 px e alvos ≥56 px. Sem entrada com objetivos em prosa, critérios para ler ou conversa obrigatória. Áudio PT-PT incorporado da palavra e da instrução, iniciado por gesto e repetível. `speechSynthesis` pode ser acessório, mas a disponibilidade de uma voz do sistema não satisfaz este contrato.

A demonstração mostra uma ação observável junto dos controlos reais. Oferecer alternativa por clique e teclado a qualquer arrasto; foco e rótulos acessíveis; redução de movimento; fonte offline. A criança pode sair ou pedir ajuda sem ter de concluir a coleção. A autoavaliação é visual/oral e facultativa.

Guardar jogo, palavra, ronda, resposta, apoio e ajudas. Persistência local não pode misturar tentativas entre participantes ou realizações do host. Recuperar trabalho restaura estado sem novos eventos de tentativa. A conclusão atualiza o host pelo contrato canónico de `postMessage`; o HTML não chama APIs nem leva credenciais. Não se afirma sincronização com o professor sem confirmação do servidor.

## Critérios de aceitação

Validar os 28 registos, ordem, grafia, concatenação, seis jogos e recursos. O teste deve inspecionar os HTML produzidos e confirmar que os áudios e imagens incorporados existem. Testar interação real: resposta errada permite avançar, pista ajuda sem apagar, demonstração reaparece, mudar apoio conserva, desfazer funciona, teclado/toque operam e recuperação não duplica tentativas. Menina, passarinho/cigarra e flor cobrem casos pedagógicos distintos; não substituem a validação de dados de toda a coleção.

A revisão docente recebe ligações privadas de todas as 168 atividades e os guias. Registo como rascunho e integração em main não são aprovação para publicação aos alunos. Associação visual, memória e reconstrução não são classificadas automaticamente como leitura, fluência ou domínio do método.
