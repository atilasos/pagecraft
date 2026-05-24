# Product

## Register

product

## Users

PageCraft serve dois grupos no mesmo ecossistema. O utilizador final é a criança do 1.º ciclo, sobretudo 6–10 anos, com tolerância para pré-escolar 4–5, a usar atividades digitais em tablet, computador de sala ou quadro interativo. O adulto utilizador é o professor ou criador de atividades, que precisa de páginas fiáveis, acessíveis, em pt-PT, prontas para aula e fáceis de publicar no catálogo.

As crianças estão em contexto de aprendizagem acompanhado. Precisam de instruções curtas, toque confortável, feedback encorajador e tarefas que deixam descobrir o conceito pela interação. Os professores precisam de confiança pedagógica: diferenciação, alinhamento curricular, materiais offline e evidência de que a atividade foi revista.

## Product Purpose

PageCraft cria, publica e cataloga atividades HTML interativas, self-contained, para o 1.º ciclo. Cada atividade é uma aula explorável: um único ficheiro HTML com CSS e JS inline, sem dependências externas, desenhado para funcionar offline, em tablet e em quadro interativo.

O produto existe para transformar temas curriculares em experiências pequenas, táteis e verificadas, usando um pipeline multi-agente com papéis separados: Architect, Designer, Builder, Proofreader e Evaluator. Sucesso significa que uma criança consegue explorar, errar sem punição, tentar de novo, descobrir o invariante pedagógico e deixar evidência observável para o professor.

## Brand Personality

Calmo, tátil e rigoroso.

A voz é próxima e portuguesa, trata a criança por tu e evita teatralidade vazia. O produto deve sentir-se como material de sala bem preparado: quente sem ser infantilizado, claro sem ser seco, lúdico sem sacrificar legibilidade ou acessibilidade. Para o professor, a personalidade é de confiança operacional: cada página deve parecer pronta para abrir numa aula real.

## Anti-references

- SaaS educativo genérico com cartões repetidos, métricas grandes e gradientes decorativos.
- Interface punitiva de quiz: vermelho de erro, sons automáticos, mensagens como “Errado”.
- Paleta semáforo para níveis de dificuldade. Verde, amarelo e vermelho não podem codificar Apoio, Intermédio e Desafio.
- Páginas dependentes de internet, CDNs, Google Fonts, frameworks ou assets remotos.
- UI de catálogo “dashboard azul Inter” como identidade principal. Pode existir no catálogo atual, mas não deve governar as atividades infantis.
- Glassmorphism decorativo, gradient text, side-stripe borders e modais como primeira solução.
- Texto pequeno, itálico em corpo, ALL CAPS em instruções, linhas longas e alvos de toque inferiores aos mínimos por idade.

## Design Principles

1. **A sala vem antes da montra.** Cada decisão visual deve funcionar em tablet, quadro interativo, luz variável e atenção partilhada.
2. **Descobrir, não declarar.** A interação conduz ao conceito; a interface não entrega a regra antes da criança a experimentar.
3. **Feedback é convite.** O erro é âmbar, concreto e reparável; nunca vermelho, humilhante ou sonoro por defeito.
4. **Coerência com variação.** O sistema usa uma gramática visual comum, mas cada atividade pode ter uma cor de identidade ligada ao tema.
5. **Offline é identidade.** Self-contained, sem fontes remotas e sem dependências externas não é só requisito técnico; é uma promessa de fiabilidade para a sala.

## Accessibility & Inclusion

O mínimo é WCAG AA em texto normal e AAA em microcopy crítico. Foco visível é obrigatório. Toda a informação importante deve existir em mais de um canal quando a idade o exige: texto + ícone, texto + áudio opt-in ou cor + texto. Som é sempre opt-in e nunca o único portador de significado.

Mínimos por idade: 4–5 anos com corpo 24px e alvo 64px; 6–7 anos com corpo 22px e alvo 56px; 8–10 anos com corpo 20px e alvo 48px. A cor nunca é a única semântica. Motion respeita `prefers-reduced-motion`, evita bounce e elastic, e serve apenas estado, feedback ou revelação pedagógica.
