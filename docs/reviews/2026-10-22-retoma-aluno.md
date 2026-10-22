# Retoma segura da realização permanente

## Problema e requisito

Na base `480521e`, `server/static/learning/activity.js` ignora qualquer erro ao consultar `/api/learning/me`. Um HTTP 503 ou uma interrupção de rede deixa disponível o formulário para começar outra realização. Submetê-lo substitui a credencial da realização anterior, retirando à criança o acesso ao trabalho e ao rascunho da reflexão. O formulário também aparece antes de terminar a consulta.

A página deve distinguir ausência de credencial de falha de recuperação. Esta alteração abrange apenas o anfitrião da realização permanente. A página de aula em `server/static/student/`, os relatórios e o feedback IA não mudam.

## Critérios de aceitação

- A entrada permanece oculta enquanto a realização está a ser consultada.
- Um HTTP 401 permite nova entrada. Uma realização válida de outra atividade mantém o comportamento anterior de permitir entrada nesta atividade.
- Falhas de rede ou do servidor mostram um aviso calmo e a ação "Tentar recuperar novamente", sem oferecer nova entrada.
- Voltar a tentar recupera a mesma realização, incluindo respostas por enviar e rascunho da autoavaliação.
- Terminar depois da recuperação grava esses valores no servidor.

## Evidência antes e depois

O teste `tests/browser/test_learning_recovery.py` usa um servidor descartável e o rascunho Canva das fixtures. Não publica atividades nem consulta dados reais.

Antes da correção, o caso HTTP falhou em 7,53 segundos: depois de interromper a retoma, `#status` estava vazio em vez de apresentar o aviso de recuperação. O código mantinha o formulário de entrada visível.

Depois da correção, os três casos passaram. Os ensaios HTTP 503 e falha de rede recuperam uma resposta guardada, outra por enviar, a escolha "Consegui com ajuda", a estratégia e o próximo passo. Verificam a mesma identidade e os valores efetivamente gravados pela API após terminar. O terceiro caso retém a resposta a `/me` e comprova que o formulário só aparece depois de receber HTTP 401.

Verificação executada numa sessão temporária do Agent Browser Hub:

```bash
PAGECRAFT_TEST_CDP=<endpoint-CDP-do-Hub> uv run --with playwright==1.63.0 pytest -q tests/browser/test_fraction_studio.py tests/browser/test_learning_recovery.py
uv run pytest -q tests/test_learning.py tests/test_student_client_access.py tests/test_student_cookie_access.py tests/test_group_continuation.py
node --check server/static/learning/activity.js
git diff --check
```

Resultado: 9 testes de browser e 27 testes de APIs e acesso passaram. As verificações de sintaxe e diff também passaram.

## Fundamento pedagógico

As sínteses da Sebenta fornecidas na tarefa, [[Avaliação Formativa]], [[Diferenciação Pedagógica]] e [[Avaliação Cooperada]], estão em revisão e têm confiança média. São fundamento para esta revisão, sem constituírem certificação pedagógica.

Conservar respostas e erros permite ao professor ajustar apoios, tempo e explicações. Conservar a reflexão mantém a voz da criança e o próximo passo que propõe, separados da interpretação docente. A recuperação mantém as escolhas de apoio existentes, sem criar rótulos, punições ou classificações automáticas.

## Limites e oportunidades adiadas

- A credencial continua a expirar ao fim de 24 horas. Este trabalho não cria acesso a históricos pelo nome nem recuperação entre dispositivos.
- A fila e o rascunho continuam em `sessionStorage`. Fechar o separador, limpar dados ou perder a credencial continua fora desta garantia.
- Se o armazenamento local estiver indisponível ou contiver JSON inválido, a página apresenta falha de recuperação. Reparar ou exportar esse rascunho exige um percurso próprio que não o apague silenciosamente.
- Rever separadamente `tryResume()` da página de aula: uma resposta não bem-sucedida a `/api/sessions/{id}/me` apaga a identidade local, mesmo que seja uma falha transitória.
- O servidor continua necessário para recuperar a realização. O HTML da atividade conserva o funcionamento offline existente.
