# Frações acessíveis e escolha de nível durante a retoma

## Problema e requisito

Base funcional `480521e`, branch `fix/regressoes-browser-fracoes-niveis`.
Dois testes procuravam títulos de frações em linha, apesar da representação vertical acessível aprovada.
A escolha de nível do grupo também podia ficar guardada sem chegar à atividade durante a retoma.
O grupo deve poder mudar livremente de apoio, incluindo enquanto recupera o trabalho.

## Critérios de aceitação

- Reconhecer o título acessível `Pinta 1/4 .` e a imagem `1/4`, preservando a fração vertical.
- Aplicar `challenge` às sete unidades de `dedo`, mesmo quando escolhido nos frames finais da retoma.
- Conservar a escolha após guardar e fazer reload, sem mudanças artificiais no histórico.
- Permitir depois `support` e `intermediate`, incluindo o alias legado `middle`.

## Evidência antes e depois

A reprodução original deu duas falhas de frações e um sucesso em `dedo-middle-7`.
O snapshot confirmou `heading "Pinta 1/4 ."` com `img "1/4"`; os testes esperavam `Pinta 1/4.`.
As expectativas corrigidas verificam o título e a imagem acessível nos níveis correspondentes.

O novo teste suspende o `requestAnimationFrame` do anfitrião durante a retoma.
Depois das preferências iniciais, escolhe `challenge` no seletor visível e liberta os frames.
Antes da correção, as sete tabs mantinham `data-level=middle`, mesmo após cinco segundos de espera.
Uma sondagem confirmou que guardar e fazer reload recuperava sete tabs `challenge`.

A causa está em `server/static/student/app.js`.
`sendGroupPreferences()` descartava a escolha explícita enquanto `state.restoringWork` permanecia ativo nos dois frames finais.
O handler da escolha passa a enviar com `duringRestore:true`.
O teste passa com sete tabs `challenge`, confirma a persistência e uma única mudança no histórico, e verifica os outros níveis.
O mapeamento do adaptador funciona; não foi necessário regenerar artefactos ou alterar HTML publicados.

## Validação

Browser real do Agent Browser Hub, sessão própria `temporary`, Playwright 1.63.0 por CDP em `PAGECRAFT_TEST_CDP`.
Os testes usam servidor e dados descartáveis, sem publicação nem acesso a alunos reais.

- Novo teste de corrida: falhou antes da correção, esperando `challenge` e recebendo `middle`.
- `uv run --offline --with playwright==1.63.0 pytest -q tests/browser/test_group_levels.py`: 8 aprovados.
- `uv run --offline --with playwright==1.63.0 pytest -q tests/browser`: 63 aprovados em 103,54 segundos.
- `uv run --offline pytest -q --ignore=tests/browser`: 315 aprovados na repetição completa.
- `node --test tests/js/activity_support.test.cjs`: 21 aprovados.

A primeira execução de servidor teve 314 sucessos e uma falha em
`test_permanent_code_feedback_is_contextual_private_and_idempotent`, por diferença `source=ai` e `source=cache`.
Passou isoladamente e na repetição completa. Os ficheiros envolvidos são idênticos à base; fica para a frente de feedback.

## Fundamento pedagógico

As sínteses da Sebenta consultadas pela coordenação via API local orientam esta decisão de produto.
[[Diferenciação Pedagógica]] sustenta metas comuns, apoios variados e escolha livre, sem grupos fixos ou rótulos pessoais.
[[Avaliação Formativa]] liga evidência a ajustes de apoio, tempo ou explicações e ao trabalho sobre o erro.
A correção faz chegar à atividade o apoio escolhido pela criança; não demonstra eficácia pedagógica.
[[Avaliação Cooperada]] distingue voz do aluno, evidência e interpretação docente.
A retoma conserva uma única mudança declarada, sem fabricar novas escolhas.
As três páginas têm estado `review` e confiança `medium`, conforme `2026-10-22-avaliacao-pagecraft.md`; não constituem certificação.

## Riscos e oportunidades adiadas

O envio mantém o contrato `postMessage` e o funcionamento offline existentes.
A cobertura inclui seis atividades com variantes de controlos; não representa todo o catálogo.
O teste controla o agendamento dos frames, sem medir a frequência da corrida em dispositivos reais.
A revisão das cores semáforo e terminologia antigas de `dedo` fica adiada para alteração própria.
As mudanças locais de nível continuam a poder reiniciar exercícios em atividades antigas, conforme o comportamento existente.

## Integração da suite pelo agente principal

A execução conjunta revelou dois problemas de recolha já presentes: módulos
`test_group_continuation` com o mesmo nome em diretórios diferentes e imports
incondicionais de Playwright apesar de a dependência ser opcional. O teste de
browser foi renomeado para `test_group_continuation_ui.py`, e os dois módulos
com imports ao nível do módulo usam `pytest.importorskip`. A recolha conjunta
com Playwright encontra 403 testes; sem a dependência, os módulos opcionais
são omitidos e os testes de servidor continuam disponíveis.

A corrida de feedback referida acima foi reproduzida e corrigida separadamente
no refinamento da branch `fix/feedback-formativo-fiavel` (PR #52), com testes
sincronizados por Events. A validação final conjunta consta da avaliação geral.
