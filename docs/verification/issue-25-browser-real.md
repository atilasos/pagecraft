# Issue #25 — verificação em browser real

Data: 2026-07-29

Repositório: `atilasos/pagecraft`

Perfil do Agent Browser Hub: `research`

Sessão Hub: `pagecraft-issue25-20260729`

Servidor: `http://127.0.0.1:8777`

## Preparação reproduzível

O seed usa seis nomes fictícios. Cinco já têm estado observável e Fábio
fica livre para o tablet.

```bash
verification_dir=$(mktemp -d /tmp/pagecraft-issue25.XXXXXX)
uv run python scripts/seed_live_verification.py --data-dir "$verification_dir"
PAGECRAFT_DATA_DIR="$verification_dir" \
  uv run uvicorn server.app:app --host 127.0.0.1 --port 8777
```

Manifesto criado em `$verification_dir/verification.json`:

- sessão `verify25`, código `PC2525`;
- Sem sinal: Fábio, Alice;
- Precisa de ti: Beatriz, Carlos, por esta ordem;
- A tropeçar: Diana;
- A fluir: Eva;
- só Beatriz tem ajuda explícita.

Os eventos de presença expiram em 90 segundos. Quando uma exploração longa
precisar de manter as faixas originais, publicar `heartbeat` com os tokens
determinísticos do seed (exceto Fábio):

```bash
for student_id in beatriz1 carlos01 diana001 eva00001; do
  event_id="browser-refresh-$student_id-$(date +%s%N)"
  curl -fsS -X POST \
    http://127.0.0.1:8777/api/sessions/verify25/events \
    -H 'content-type: application/json' \
    --data \
    "{\"student_token\":\"token-$student_id\",\"events\":[{\"event_id\":\"$event_id\",\"type\":\"heartbeat\",\"payload\":{}}]}"
done
```

URLs abertas pelo Hub:

- painel: `http://127.0.0.1:8777/teacher/class.html`;
- tablet: `http://127.0.0.1:8777/student/`;
- projeção: `http://127.0.0.1:8777/teacher/present.html?session=verify25`.

## Resultados

### Faixas, ordem e ajuda

Passou. O painel apresentou as quatro faixas. Em «Precisa de ti», Beatriz
ficou antes de Carlos porque esperava há mais tempo. Só Beatriz mostrou
`🙋 Pediu ajuda`; o sinal não alterou a ordem.

O browser revelou uma regressão de apresentação: os cartões, por serem
`button`, herdavam `display:inline-flex`, e a régua não quebrava no viewport
de 765 px. O commit `16ea71c` tornou o cartão um bloco e alargou o breakpoint
da régua. A captura `issue25-02` é o antes e `issue25-03` o depois.

### Foco durante atualização e tique

Passou. Com Tab, o foco ficou no cartão de Fábio. Após esperar um tique de
30 segundos, as esperas e a composição das faixas mudaram, mas o contorno de
foco permaneceu no mesmo cartão. Capturas `issue25-04` e `issue25-05`.

### Interrupção e retoma do painel

Passou sem reload manual. Com o painel aberto:

1. o processo `uvicorn` foi interrompido com `Ctrl+C` (uma segunda vez para
   forçar o fecho das ligações SSE);
2. o mesmo comando foi arrancado com o mesmo `PAGECRAFT_DATA_DIR`;
3. o `EventSource` abriu novamente `/api/sessions/verify25/stream`;
4. o snapshot atual repôs a turma sem criar cartões ou números duplicados.

Os contadores observados mantiveram Eva com 2 descobertas e Diana com 4
tentativas, os valores anteriores à interrupção.

### Interrupção, fila e retoma do tablet

Passou:

1. Fábio entrou com `PC2525`;
2. foi enviada a mensagem dirigida «Mensagem antiga de controlo»;
3. o servidor foi interrompido;
4. o botão «Preciso de ajuda» foi ativado por teclado durante a falha;
5. após o arranque, a fila publicou exatamente um `help_needed`, com `seq=30`;
6. 16 segundos depois a contagem no JSONL continuava em 1 e a mensagem antiga
   não reapareceu.

Capturas: `issue25-07` (mensagem antes), `issue25-08` (trabalho enfileirado)
e `issue25-09` (retoma sem replay).

### Release com fila pendente

Passou. Para tornar a corrida determinística:

1. servidor parado;
2. novo toque em «Preciso de ajuda», ficando na outbox;
3. libertação autoritativa de Fábio no mesmo diretório:

```bash
uv run python -c 'import asyncio; from pathlib import Path; from server.config import Config; from server.storage import Storage; from server.events import EventHub; from server.classroom.service import ClassroomService; c=Config(data_dir=Path("'"$verification_dir"'")); s=Storage(c.data_dir); asyncio.run(ClassroomService(c,s,EventHub(s)).release_identity("verify25","fabio001"))'
```

No arranque seguinte, o stream e `/me` responderam 401. O tablet descartou
a outbox e regressou ao ecrã sem identidade (`issue25-10`). Seis segundos
depois, o registo permanecia em `help_needed=1` e
`identity_released=1`: não houve POST repetido nem ciclo de reenvio.

### Freeze, reconexão e unfreeze

Passou. O controlo foi exercido contra a fonte de verdade:

```bash
teacher_token=$(jq -r .token "$verification_dir/teacher-token.json")
curl -fsS -X POST \
  http://127.0.0.1:8777/api/sessions/verify25/control \
  -H 'content-type: application/json' \
  -H "x-teacher-token: $teacher_token" \
  --data '{"action":"freeze"}'
```

- projeção: passou para «Libertar os ecrãs» (`issue25-11`);
- painel: passou para «Libertar os ecrãs» (`issue25-13`);
- tablet: expôs o alerta modal «Olha para o quadro!» (`issue25-12`).

O servidor foi novamente interrompido ainda congelado. No arranque, o log
registou dois streams `role=teacher` (painel e projeção) e um
`role=student`; o snapshot manteve os três congelados. Depois:

```bash
curl -fsS -X POST \
  http://127.0.0.1:8777/api/sessions/verify25/control \
  -H 'content-type: application/json' \
  -H "x-teacher-token: $teacher_token" \
  --data '{"action":"unfreeze"}'
```

O tablet perdeu o alerta e o painel voltou a «Olhem para o quadro».
O registo final contém um `freeze_screens` e um `unfreeze_screens`.

Durante o reload do tablet foi encontrada outra regressão: `tryResume()`
entrava diretamente em `startActivity()`, que não escondia o passo do código.
O commit `75e3e5b` tornou explícitos os três passos; após reload, o estado
estruturado já não continha o input do código enquanto a atividade estava
ativa.

### Fecho

Passou. «Terminar sessão» no painel emitiu um único `session_closed` e
recarregou a bancada. O tablet limpou a identidade e, numa nova navegação,
mostrou apenas o passo do código. A projeção mostrou «Sessão terminada»
(`issue25-19`). Verificação final:

```json
{
  "status": "closed",
  "help_fabio": 1,
  "releases_fabio": 1,
  "freezes": 1,
  "unfreezes": 1,
  "closes": 1
}
```

## Screenshots principais

- `/home/proteu/agent-browser-hub/screenshots/issue25-02-painel-ordem-ajuda.png`
- `/home/proteu/agent-browser-hub/screenshots/issue25-03-painel-responsivo.png`
- `/home/proteu/agent-browser-hub/screenshots/issue25-04-foco-antes-update.png`
- `/home/proteu/agent-browser-hub/screenshots/issue25-05-foco-apos-tique.png`
- `/home/proteu/agent-browser-hub/screenshots/issue25-06-tablet-inicial.png`
- `/home/proteu/agent-browser-hub/screenshots/issue25-07-tablet-mensagem-antes-falha.png`
- `/home/proteu/agent-browser-hub/screenshots/issue25-08-tablet-fila-durante-falha.png`
- `/home/proteu/agent-browser-hub/screenshots/issue25-09-tablet-retoma-sem-replay.png`
- `/home/proteu/agent-browser-hub/screenshots/issue25-10-tablet-release-descarta-fila.png`
- `/home/proteu/agent-browser-hub/screenshots/issue25-11-freeze-tablet.png`
- `/home/proteu/agent-browser-hub/screenshots/issue25-12-freeze-tablet.png`
- `/home/proteu/agent-browser-hub/screenshots/issue25-13-freeze-tablet-retoma-corrigida.png`
- `/home/proteu/agent-browser-hub/screenshots/issue25-19-fecho-projecao.png`

Os nomes de `issue25-11` e `issue25-13` são históricos: a primeira captura
é a projeção congelada e a segunda é o painel congelado.

## Verificações de código

```bash
node --check server/static/student/app.js
uv run pytest tests/test_classroom.py tests/test_live_session_api.py \
  tests/test_seed_live_verification.py -q
uv run pytest
```
