# Fila individual do Studio

Implementa apenas a proposta 2 de `/tmp/pagecraft-audit-05.md`, sobre persistência, autoria e recusa da fila. Base `4c6ba90476a498a03b08fd88dea96c432ba767cd`. Worktree isolado `/home/proteu/.t3/worktrees/pagecraft/t3-586e9540`, branch `fix/studio-offline-queue`, inicialmente limpo.

Li `AGENTS.md`, `CONTEXT.md`, `PRODUCT.md`, `DESIGN.md` e ADRs 0002, 0004, 0005 e 0007. Esta correção protege transporte de acontecimentos existentes. Não acrescenta comportamento pedagógico nem altera atividades.

## Problema reproduzido

O transporte só atribuía uma chave de `sessionStorage` aos grupos. Uma resposta individual sem ligação ficava exclusivamente na memória. O recetor também ignorava a recusa de `enqueue` quando atingia 200 acontecimentos. Depois de esvaziar os 200 aceites, o botão podia confirmar "Guardado" apesar de haver alterações recusadas.

O teste de browser foi escrito e executado antes da implementação, no commit `8d79fb1`, com dados descartáveis e o rascunho Canva real. Falhou na asserção `Individual work needs a persistent outbox`: encontrou zero filas depois da resposta e do envio abortado. A mesma observação deixa de ocorrer depois da correção.

## Solução

A fila individual usa `pc-student-outbox:<sessão>:<aluno>:<versão>`. A versão é o `claimed_at` da atribuição autenticada, devolvido por `claim` e `/me`. Não é uma credencial e não dá acesso a históricos. O cliente obtém a identidade atual do servidor antes de escolher a fila. Uma nova atribuição do mesmo aluno usa outra chave. As filas anteriores permanecem no separador, sem serem reproduzidas na identidade nova.

O carregamento elimina duplicados por `event_id` antes de admitir novos acontecimentos. A recuperação combina histórico autorizado e fila local, sem repetir identificadores já presentes no histórico. O envio conserva os mesmos identificadores e a deduplicação existente do servidor. As chaves e regras de composição/acesso dos grupos mantêm-se.

Os lotes individuais declaram `expected_identity`, com aluno e versão. A API compara o aluno com o cookie autenticado e verifica a versão dentro do bloqueio de escrita. Divergência devolve `409 identity_changed`, fecha o transporte e conserva a fila antiga. Isto evita depender de um pedido `/me` separado do envio, que deixaria uma janela para troca do cookie. A API continua a aceitar clientes anteriores sem esse campo; a proteção adicional aplica-se aos lotes do cliente atualizado.

A fila mantém o limite de 200. Ao atingir o limite, apresenta um aviso. Uma alteração recusada ativa um marcador persistente e impede novas admissões até à revisão explícita. Esvaziar a fila aceite não limpa o marcador e `savePending` continua a devolver falso. O botão "Voltar ao último trabalho aceite" fica disponível quando existe espaço e a persistência funciona. A ação conserva a fila aceite, limpa apenas o marcador e recarrega a atividade para rever o estado conservado antes de repetir as alterações recusadas. Falhas de armazenamento também pedem para manter a página aberta.

Respostas de envios de uma geração anterior não removem acontecimentos nem invalidam a identidade atual. Não alterei `reflection.js`, `learning/activity.js`, atividades, prompts ou dados de produção. Em `app.js`, as alterações limitam-se ao estado da identidade e ao transporte/fila; em `index.html`, ao aviso, ação de recuperação e versão do script.

## Verificação

A sessão própria do Agent Browser Hub foi `pagecraft-individual-outbox`, perfil `temporary`, CDP `http://127.0.0.1:9330`. Os testes ligaram Playwright a essa sessão, sem lançar outro browser. O servidor e os dados são criados numa diretoria temporária pelo fixture `studio_origin`.

Comando do teste que falhou antes da correção:

```bash
PAGECRAFT_TEST_CDP=http://127.0.0.1:9330 uv run --project /home/proteu/pagecraft --with playwright pytest tests/browser/test_individual_outbox.py -x -q
```

Validação depois da implementação:

```bash
PAGECRAFT_TEST_CDP=http://127.0.0.1:9330 uv run --project /home/proteu/pagecraft --with playwright pytest tests/browser/test_individual_outbox.py tests/browser/test_group_continuation_ui.py -x -q
```

Resultado: **8 passed in 23.35s**. Os cenários verificam:

- Pedidos de acontecimentos abortados com `internetdisconnected`, resposta individual e reload enquanto o envio continua indisponível. Reconexão conserva uma única evidência com o aluno correto, mesmo com o mesmo identificador na fila duas vezes e já presente no servidor.
- Mais de 200 acontecimentos pela ponte real do iframe, individualmente e em grupo. Conserva os 200 aceites, recupera a resposta anterior após reload e mantém o aviso de recusa depois da sincronização. Só confirma "Guardado" depois da revisão explícita.
- Libertação revoga o cookie anterior. Uma nova entrada, com outra criança ou com o mesmo nome e nova versão, não recupera nem envia a fila anterior. Os acontecimentos antigos continuam intactos no armazenamento local.
- Troca de cookie com a página ainda aberta recebe conflito e não atribui o trabalho de Ana a Bruno.
- Os dois testes existentes de continuação dos grupos conservam a recuperação entre aulas e dispositivos, e mantêm legível a composição anterior sem a reproduzir na composição atual.

Testes de API, acesso e clientes:

```bash
uv run --project /home/proteu/pagecraft pytest tests/test_access.py tests/test_classroom_api_authority.py tests/test_live_session_api.py tests/test_identity_release.py tests/test_group_continuation.py tests/test_work_groups.py tests/test_teacher_client_access.py tests/test_student_client_access.py -q
```

Resultado: **55 passed in 2.70s**. Inclui versão estável em `/me`, versão nova após libertação, cookie revogado, recusa de aluno ou versão divergentes e ausência de escrita em ambos os históricos. Também executei `tests/test_live_session_api.py tests/test_classroom.py`: **22 passed in 0.94s**.

`node --check server/static/student/app.js` e `git diff --check` passam. O módulo novo ignora-se na recolha quando Playwright não está instalado, como dependência opcional de browser. O comando acima usa `--with playwright` para não alterar dependências do projeto.

Capturas dos avisos, geradas pelos testes e inspecionadas visualmente:

- `/tmp/pagecraft-fila-individual.png`
- `/tmp/pagecraft-fila-grupo.png`

Os dois testes de excesso de fila voltaram a passar ao gerar as capturas: **2 passed, 4 deselected in 6.55s**.

## Limites e integração

`sessionStorage` conserva o trabalho entre reloads no mesmo separador; fechar o separador ou apagar o armazenamento pode eliminá-lo. As filas de versões antigas são conservadas, mas esta proposta não acrescenta uma interface para o professor as importar. O teste corta a rede do transporte de acontecimentos, mantendo disponíveis shell, identidade e histórico para testar a recuperação. Não acrescenta uma shell offline nem permite iniciar a aula sem conseguir validar a identidade.

Os commits são incrementais: `8d79fb1` reproduz a falha, `e301eae` expõe a versão individual, `f4b1006` persiste a fila e mostra recusas, `e24ed22` valida a autoria no envio. O principal fará revisão independente e abrirá o PR. Não foi aberto PR, feito merge ou publicada qualquer atividade nesta tarefa.
