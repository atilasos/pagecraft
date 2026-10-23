# Avaliação 03: apoios, escolha e acesso à participação

Base inspecionada: `4c6ba90`, em 22/10/2026. Investigação só de leitura do repositório; único ficheiro produzido em `/tmp`. Consultei `AGENTS.md`, `CONTEXT.md`, `PRODUCT.md`, `DESIGN.md`, ADRs 0002 e 0007, a avaliação de 22/10 e fontes de implementação. Confirmei no GitHub que #51–55 estão integrados. As propostas abaixo não repetem essas correções. Não abri browser nem usei dados de alunos.

## Fundamentação e limites

Executei `health`, `search` e `read --content` pela API local da Sebenta. Síntese da wiki:

- **Diferenciação Pedagógica**, `20_Wiki/Diferenciação Pedagógica.md`, estado `review`, confiança `medium`: variar vias e apoios para metas comuns, organizar cooperação e permitir regulação do percurso pelo aluno; evitar grupos fixos de nível.
- **Educação Inclusiva**, `20_Wiki/Educação Inclusiva.md`, estado `review`, confiança `medium`: reorganizar o contexto para permitir participação, oferecer apoio no trabalho comum e construir relações de ajuda recíproca.

As propostas seguintes são minhas, derivadas destas sínteses. Não afirmam eficácia demonstrada nem conformidade legal. A verificação foi estática, com uma reprodução JavaScript descrita abaixo; leitura por crianças, voz real e usabilidade tátil continuam por ensaiar.

Já existem nomes neutros, escolha livre do nível do grupo, pistas progressivas por obstáculo, leitura facultativa, alternativa local à IA e distinção entre pista apresentada e utilidade declarada. A faixa etária integra o contexto de apoio em `server/activity_support.py:59`. O modal usa `dialog`, nomes acessíveis e botões de 56px em `server/static/student/support-modal.js:17`. Estes mecanismos merecem ser preservados.

## 1. Voltar à pista escolhida, mesmo depois de experimentar

**Problema e evidência.** O aluno perde a pista visível quando altera a resposta: `invalidate()` limpa `current` em `server/pipeline/prompts/activity-support.js:51`; `update()` chama-o quando a tentativa muda, em `:136`. O pedido seguinte seleciona apenas pistas ainda não usadas, em `:158–161`. A retoma conserva o histórico, mas não oferece consulta no painel, em `:263–274`.

Reproduzi com o ambiente VM de `tests/js/activity_support.test.cjs:6`, sem editar ficheiros: pedir a pista `alinhar`, rever a resposta e pedir novamente entrega `sobrepor`. Restaurar ambas e pedir outra encaminha ao professor. As pistas continuam registadas; falta acesso a elas junto da tarefa durante o trabalho.

**Comportamento proposto.** Acrescentar “Pistas que já experimentei”, com consulta e leitura de cada pista, separadas de “Outra pista”. Mostrar etapa e versão originais; depois de mudar de tarefa, apresentá-las como anteriores, sem as aplicar automaticamente. Como extensão criativa, permitir escolher “Quero voltar a esta estratégia” para preparar a reflexão individual.

**Benefício pedagógico.** A criança pode experimentar, comparar e recuperar estratégias ao seu ritmo, sem gastar outra pista nem depender de memorizar a primeira. A escolha para reflexão expressa a sua voz.

**Risco.** Uma pista antiga pode parecer pertinente à tarefa atual. Exigir identificação do contexto; consulta não deve criar declaração de utilidade nem prova de aprendizagem.

**Esforço e fronteira.** Médio. `server/pipeline/prompts/activity-support.js`, respetivo CSS, cópias canónicas em `skills/{codex,claude}/assets/` e `tests/js/activity_support.test.cjs`. Primeiro incremento só com consulta, sem novo acontecimento. Atividades publicadas permanecem intactas; distribuição por nova revisão aprovada, conforme ADR-0002.

**Teste concreto.** Ver duas pistas, editar resposta, recarregar e reler a primeira. Verificar texto/versão, ausência de chamada IA e de `hint_feedback`; mudar de tarefa e confirmar a indicação “pista anterior”. Ensaiar teclado e leitor de ecrã.

## 2. Tornar a escolha de ajuda acessível antes de saber ler fluentemente

**Problema e evidência.** O componente pede a identificação textual do obstáculo antes da pista, em `server/pipeline/prompts/activity-support.js:219–226`; “Ouvir” só aparece depois e lê exclusivamente `current.text`, em `:205–209`. No Studio, o corpo tem 20px, mas rótulos usam `1rem` e texto secundário `0.9rem`, em `server/static/studio.css:787–812`. Com raiz habitual de 16px, são 16px e 14,4px. Os seletores de nível ficam em 48px, em `:993`. `DESIGN.md:169–176` prevê 22px para 6–7 anos e microtexto infantil nunca inferior a 16px.

**Comportamento proposto.** Oferecer leitura voluntária da pergunta e das opções de ajuda antes da primeira pista. No anfitrião infantil, usar corpo de 22px, rótulos herdados, texto secundário mínimo de 16px e seletores de 56px. Não associar necessidade de leitura a um nível curricular.

**Benefício pedagógico.** Reduzir a dependência de um adulto para escolher apoio, mantendo o mesmo objetivo de aprendizagem.

**Risco.** Mais controlos e fala longa; ler apenas o bloco escolhido, permitir parar e manter o som desligado inicialmente.

**Esforço e fronteira.** Médio. `server/static/studio.css`, componente comum de apoio e suas cópias canónicas; sem alterar perfis ou catálogo.

**Teste concreto.** Fixture de 6–7 anos, 320px de largura, zoom 200%, teclado e voz indisponível. Confirmar acesso às opções antes da pista, alvos de 56px e ausência de áudio automático.

## 3. Concretizar perfis por disciplina e convites consentidos

**Problema e evidência.** `CONTEXT.md:13–18` descreve ambos. Contudo, os alunos são criados apenas com identificador/nome em `server/classroom/service.py:151–154`; o contrato de entrada individual só recebe `student_id`, em `server/api/classroom.py:54–55`. As ações docentes expostas em `server/static/teacher/class.html:208–211` são mensagem e chamada de atenção. Não encontrei armazenamento de perfil nem percurso de convite. O teste chamado “individual_profiles”, em `tests/test_work_groups.py:95–103`, verifica apenas que a lista de alunos não mudou.

**Comportamento proposto.** Implementar primeiro o valor inicial por disciplina, com Passo a passo por omissão e escolha individual sempre disponível. Depois, convite discreto com aceitar/ignorar; nunca selecionar automaticamente. Em grupo, conservar a escolha conjunta, sem calcular um nível a partir dos perfis individuais.

**Benefício pedagógico.** Preparar apoios sem fixar identidades nem retirar decisão à criança.

**Risco.** Âmbito grande e perfis cristalizados. Separar ato docente de resposta do aluno no vocabulário; resolver a tensão entre “convite como evidência” em `CONTEXT.md:18` e a restrição de autores de evidência em `server/classroom/event_types.py:50–53`.

**Esforço e fronteira.** Grande, em duas entregas. Serviço/API de sala, vocabulário, clientes professor/aluno e testes de autoridade/retoma; acrescentar contrato de ponte sem renomear mensagens existentes.

**Teste concreto.** Perfis diferentes em Português e Matemática; mudar livremente sem reescrever o perfil; ignorar convite sem alteração; aceitar uma vez; retomar sem duplicar resposta; impedir acesso por outro aluno.

**Melhor proposta recomendada: 1.** Resolve uma barreira reproduzida, aproveita registos existentes e devolve à criança controlo sobre a utilização das pistas.
