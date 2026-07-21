# Design Brief

## Feature Summary

Pagina PageCraft de produto para uma aula de 30 min sobre fracoes equivalentes no 2.º ano. A acao principal da crianca e tocar em fracoes e observar se a parcela Minecraft pinta a mesma quantidade de blocos.

## Register

Product. A interface serve a tarefa pedagogica, nao uma campanha visual.

## Scene

Pares de criancas de 7-8 anos usam tablets numa sala com luz natural, enquanto a professora circula e pede que expliquem a descoberta com palavras suas.

## Colour Strategy

Full palette contida. Base clara tintada PageCraft, verde-terreno como identidade Minecraft, castanho-madeira como acento maker, azul funcional para foco, verde funcional so para sucesso e ambar para tentativa.

## Layout Strategy

Topo curto, superficie principal em duas colunas no desktop e uma coluna no tablet pequeno. A grelha fica sempre visivel perto dos controlos. Cards so aparecem para zonas funcionais: exploracao, feedback e missao maker.

## Key States

Default: nivel intermedio e 1/2 selecionado. Exploring: fracao ativa muda a grelha e o contador. Success: mensagem positiva quando 1/2 e 2/4 sao comparadas. Try-again: sugestao ambar sem linguagem punitiva. Reset: volta a intermedio e 1/2. Reduced-motion: sem transicoes visuais. Small viewport: controlos empilham antes da grelha.

## Interaction Model

Tabs de diferenciacao com `role=tablist`, botoes de fracao com estado pressionado e grelha 4x4 atualizada em JS vanilla. No desafio, um pequeno quiz pede a fracao equivalente a 1/2.

## Feedback Model

Feedback imediato em `aria-live=polite`, com contador de blocos e frase concreta. A regra nao aparece no primeiro texto; surge apos a crianca tocar nas fracoes relevantes.

## Open Risks and Anti-goals

Risco: o tema Minecraft pode distrair da equivalencia. Mitigacao: grelha simples, sem assets externos, sem animacoes decorativas. Anti-goals: landing page, paleta semaforo para niveis, gradientes, glassmorphism, modais, dependencias remotas.
