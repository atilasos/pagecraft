# Integração com realizações

O host em `/<CODIGO>` pede nome, turma opcional e contexto de realização (aula/casa). Abre a atividade num iframe sandbox. O conteúdo não recebe cookies nem acesso direto ao servidor. Os registos são privados e vivem em `server/data/learning/`.

## Metadados de registo

Guarda `drafts/<slug>-activity.json` para o comando `register`:

```json
{
  "title": "Título em português",
  "title_en": "English title when requested",
  "year": 4,
  "duration": 45,
  "group": "",
  "languages": ["pt", "en"],
  "requires_completion": true,
  "criteria": [{"id": "objetivo-1", "pt": "Consigo explicar a minha escolha.", "en": "I can explain my choice."}]
}
```

Por defeito, `languages` contém apenas `pt`. Os identificadores dos critérios são estáveis e as traduções exprimem o mesmo critério. O ano e os apoios adaptam a forma de resposta, não inventam notas de desempenho.

## Ponte

Emite os acontecimentos canónicos `activity_loaded`, `unit_started`, `attempt`, `discovery`, `assessment_result`, `help_needed` e `share_requested`. O envelope é `{pagecraft:1,type,unitId,payload}`. Os resultados descrevem o que foi observado na página, não o domínio presumido de uma competência.

Ao carregar o iframe, o host envia `learning_restore` com `payload.events`, os registos da realização atual. Recupera os campos e a etapa pelos teus acontecimentos, validando os valores conhecidos, sem emitir novos registos durante a recuperação. Guarda alterações de texto na ponte ao sair do campo e ao mudar de etapa.

O host pode enviar `{pagecraft:1,type:"learning_preferences",payload:{language:"pt"|"en",level:"support"|"intermediate"|"challenge"}}`. Aceita apenas mensagens de `window.parent`. Aplica as preferências sem voltar a emiti-las: evita ciclos entre host e atividade.

Quando a criança muda de língua/apoio na atividade, emite `language_changed` com `{language}` ou `level_changed` com `{level}`. O botão final emite `{pagecraft:1,type:"open_reflection"}`. O host apresenta os critérios e guarda a autoavaliação. Se o HTML abrir autonomamente, oferece reflexão local sem afirmar envio ao professor.

O iframe tem origem opaca. Acede a `sessionStorage` apenas em modo autónomo e com tratamento de indisponibilidade. Não depende de `fetch`, armazenamento de cookies ou APIs do pai.

O host guarda eventos com identificadores únicos, reenvia a fila após falha de rede e só confirma gravação depois da resposta do servidor. Cada realização tem a sua credencial HttpOnly; escrever novamente o mesmo nome inicia outra realização, não recupera a anterior. A troca de aluno limpa o estado local dessa realização.

## Respostas obrigatórias e conclusão

Para novas atividades com exploração obrigatória, registar `requires_completion: true`. Ao carregar, restaurar, responder e mudar de apoio, enviar `{pagecraft:1,type:"activity_state",payload:{activity:"<slug>",version:1,readyForReflection:false,state:{}}}` com o estado real e `readyForReflection` calculado a partir de todas as respostas obrigatórias. A reflexão só fica disponível quando esse valor for `true`, mesmo com respostas erradas. Emitir o estado inicial incompleto antes de a criança poder concluir; restaurar a realização recebida sem duplicar tentativas. Conservar o payload abaixo de 4096 bytes e validar a versão e os valores no restauro. Usar uma representação compacta para desenhos.

Esta mensagem pertence ao protocolo do host de realizações; não inventar um novo acontecimento de Sessão de aula. Na sessão, o host resolve participantes e autoria conjunta e oferece reflexão individual à vez. A atividade não deve emitir a autoavaliação de uma criança em nome dos restantes membros.

## API

O helper local usa bootstrap do professor em `http://127.0.0.1:8777`, mantendo cookies em memória. `register` é idempotente por slug; `publish --approved` exige aprovação da atividade e só torna público depois da publicação canónica. O hostname público é sempre verificado separadamente pela skill Cloudflare.

Os ensaios de rascunhos são marcados `preview` e excluídos dos relatórios. Testes com publicações devem usar dados e diretórios temporários, nunca publicar o piloto real para simular uma aprovação.
