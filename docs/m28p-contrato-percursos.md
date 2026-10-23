# Contrato dos percursos M28P v2

Cada agente escreve apenas `drafts/m28p-v2/<slug>/content.json` e `guia-docente.md`. O motor `python3 scripts/build_m28p_journeys.py --word <slug>` valida o conteúdo e gera HTML, DocSpec, design e manifesto na mesma pasta. `--all` gera toda a coleção; `--validate-only` verifica sem escrever.

O JSON usa esta estrutura. Os nomes dos campos e valores de `phase` e `type` são fixos. Não incluir HTML.

```json
{
  "slug": "menina",
  "word": "menina",
  "order": 1,
  "syllables": ["me", "ni", "na"],
  "phonologyNotes": "A divisão é oral. O adulto modela os sons sem acrescentar vogais.",
  "prerequisites": ["Conversar sobre uma experiência com uma menina."],
  "assistedReading": "O adulto lê instruções e textos ainda não decifráveis. Não lê pelo aluno os itens de transferência e revisão.",
  "objectives": ["Reconhecer e analisar menina.", "Ler novas combinações e escrever para alguém."],
  "criteria": ["Relaciono a palavra com uma experiência.", "Leio uma combinação sem imagem.", "Escrevo e revejo uma mensagem para alguém."],
  "sessions": [
    {"title": "Conhecer e descobrir", "minutes": 8},
    {"title": "Analisar e combinar", "minutes": 8},
    {"title": "Ler e compreender", "minutes": 8},
    {"title": "Escrever e partilhar", "minutes": 8}
  ],
  "pages": [
    {
      "id": "encontro",
      "session": 1,
      "phase": "context",
      "type": "oral",
      "title": "Uma pessoa da nossa vida",
      "prompt": "Conta uma situação que viveste.",
      "text": "Conversa com um adulto sobre uma menina que conheces.",
      "adultPrompt": "Escute a experiência. Registe uma frase da criança; este botão apenas declara que houve conversa.",
      "hints": [
        {"individual": "Pensa numa pessoa da tua escola.", "group": "Pensem numa pessoa da vossa escola."},
        {"individual": "Conta o que fizeram juntos.", "group": "Contem o que fizeram juntos."}
      ],
      "challenge": "Conta mais um pormenor."
    }
  ]
}
```

O exemplo mostra uma página; cada percurso exige **12 a 16 páginas**, agrupadas em **3 ou 4 sessões** com **6 a 12 minutos** cada. `session` é um inteiro a partir de 1, em ordem. `id` é único, em minúsculas sem acentos, com hífen permitido. `objectives` tem 2 a 4 itens; `criteria`, 2 a 4. `order` é a posição 1–28. Não automatizar a divisão silábica. Em divisão oral usam-se, por exemplo, `ca-rro`, `ma-ssa`, `ci-ga-rra`, `pa-ssa-ri-nho`; não confundir com translineação.

Cada página tem `id`, `session`, `phase`, `type`, `title`, `prompt` e **duas ou três** `hints`, cada uma com `individual` e `group` escritos de propósito. As pistas indicam abordagens progressivas sem dar a resposta. Campos opcionais: `text` apresenta contexto ou texto de leitura; `challenge` acrescenta explicação ou aplicação, conservando a mesma resposta de base. `adultPrompt` explica a mediação e é obrigatório nas páginas orais. `criterion` pode explicitar o critério próprio da página; na sua ausência usa-se o pedido.

Tipos de resposta:

- `choice`: `options` tem 2 a 5 strings diferentes; `answer` é exatamente uma dessas strings. A escolha recebe feedback imediato. A posição da resposta certa deve variar entre páginas.
- `order`: `pieces` contém 2 a 8 strings apresentadas fora da ordem certa; `answer` é um array com exatamente as mesmas peças na ordem pretendida, incluindo duplicados. A criança toca nas peças e confirma. As peças podem ser sílabas ou palavras. A avaliação compara a sequência sem inventar regras fonológicas.
- `write`: texto aberto; `placeholder` pode sugerir o género de produção, sem fornecer o texto final. Nunca recebe veredicto automático. O adulto acompanha escrita emergente, escrita a par ou ditado ao adulto, preservando o que a criança quis comunicar.
- `oral`: declaração «Já conversei com um adulto». Não observa pronúncia, leitura ou compreensão. Exige `adultPrompt`, e a tarefa pode ser realizada oralmente, em papel ou com objetos. Não usar voz sintética para ensinar fonemas.

Fases obrigatórias em cada percurso: `context`, `recognition`, `syllables`, `code`, `transfer`, `comprehension`, `writing`, `communication`, `review`. Cada uma pode ocupar mais de uma página. As primeiras fases partem de sentido e da experiência da criança, e antecedem análise e transferência. A revisão aparece no fim, depois da comunicação. `code` exige mediação explícita que modele a relação som/grafema. `transfer` e `review` **não têm imagens nem modelos da resposta**: `text`, `prompt` e `title` não devem revelar o item correto, e o motor oculta pistas até à primeira resposta. O adulto observa leitura/explicação e decide retoma; escolhas fechadas só mostram reconhecimento entre alternativas. A sessão de revisão inclui leitura sem imagem e uma declaração oral com adulto ou escrita, pois clicar numa opção não comprova leitura autónoma.

Os textos de leitura usam o repertório cumulativo já trabalhado, identificado em `prerequisites`; palavras ainda não decifráveis ficam expressamente para leitura do adulto. Não declarar que percorrer páginas comprova domínio da leitura. Incluir compreensão de frase e de pequeno texto, recombinação com sílabas/padrões anteriores quando disponíveis, produção com destinatário real, revisão e comunicação. A autoavaliação facultativa é acrescentada pelo motor e retoma os critérios iniciais.

O guia docente identifica repertório e partes lidas pelo adulto, modelação de código, respostas verificáveis, indicadores de observação oral e de escrita, materiais, destinatário, revisão em dias seguintes e critérios para voltar a apoiar. Regista as adaptações MEM como decisões propostas, sem atribuí-las ao método original.

O motor conserva respostas ao mudar entre Com pistas, Passo a passo e Mais desafios, guarda no dispositivo e restaura sem emitir novas tentativas. O restauro reenvia apenas o checkpoint para atualizar a disponibilidade da reflexão no host. Avançar depende de responder, incluindo respostas incorretas; acerto não bloqueia. A escrita no ecrã admite até 180 caracteres e apresenta contador; a produção pode continuar em papel. Não publicar nem escrever no catálogo através deste motor.

Para compatibilidade com o registo canónico, o motor cria ligações simbólicas relativas em `drafts/m28p-v2-<slug>.html`, `drafts/m28p-v2-<slug>-docspec.json`, `drafts/m28p-v2-<slug>-design-spec.json`, `drafts/m28p-v2-<slug>-activity.json`, `drafts/m28p-v2-<slug>-run-manifest.json` e `drafts/m28p-v2-<slug>.md`. O guia e todos os artefactos continuam na pasta da palavra. O motor nunca substitui um ficheiro existente por uma ligação simbólica.
