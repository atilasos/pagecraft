# Evidência exportada sem checkpoints de retoma

## Problema e requisito

O painel das realizações exclui `activity_state`, mas o download Markdown
percorre os acontecimentos brutos. O descritor comum transformava checkpoints
em linhas sob «Evidências no PageCraft», incluindo respostas em rascunho.
O professor podia interpretar um estado intermédio como resposta submetida.

O relatório deve conservar as tentativas observadas e separar a autoavaliação
da interpretação docente. Guardar estado para retoma não demonstra que uma
criança respondeu a um pedido da atividade.

## Critérios de aceitação

- Nenhum conteúdo de `activity_state` aparece no relatório descarregado.
- Uma tentativa incorreta mantém o resultado observado e a justificação.
- A autoavaliação, o próximo passo do aluno e a observação docente conservam
  as suas secções e conteúdo.
- Os checkpoints continuam no histórico autorizado de retoma.
- Uma realização só com checkpoints não produz linhas de evidência.

## Evidência antes e depois

Base: `480521e3e8a9e27ed6234db52dd25ab14b10c4d6`.

Reprodução automática com realizações sintéticas, em diretórios temporários:

```sh
uv run pytest -q tests/test_learning.py -k download_keeps_checkpoints
```

Antes: os dois casos falharam. O download incluía `activity: restore-only-marker`,
`version: 1` e `state · answer: draft-answer-marker`, tanto com uma tentativa
intercalada como sem tentativas.

Depois: `describe_evidence` devolve uma lista vazia para `activity_state`,
aplicando a exclusão também ao export. No caso com tentativa, o Markdown
conserva «Resposta esperada: Não» e «Justificação: Comparei as partes.».
Conserva ainda «Consegui com ajuda», a estratégia, o próximo passo proposto
pelo aluno e a observação do professor. A leitura do histórico confirma que
todos os checkpoints continuam disponíveis para retoma.

Validação conjunta:

```sh
uv run pytest -q tests/test_learning.py tests/test_reports.py tests/test_work_groups.py tests/test_group_continuation.py
```

Resultado: **44 passed**. `git diff --check` passou antes do commit da correção.
Não foram consultados dados reais de alunos nem publicadas atividades reais.
Os testes usam apenas HTML e registos sintéticos no armazenamento temporário.

## Fundamento pedagógico

A síntese da consulta à Sebenta foi fornecida no mandato desta implementação.
[[Avaliação Formativa]] liga evidência à possibilidade de ajustar apoios, tempo
ou explicações e trata o erro como objeto de trabalho. Por isso, conservar a
tentativa incorreta é necessário, enquanto apresentar um checkpoint como
resposta pode orientar uma intervenção sem fundamento.

[[Avaliação Cooperada]] distingue a voz do aluno da interpretação docente.
Os testes verificam que ambas continuam legíveis nas suas secções.
[[Diferenciação Pedagógica]] sustenta apoios variados com metas comuns e sem
rótulos fixos. A correção não acrescenta classificações nem recomendações
automáticas de nível. As três páginas estão em `review`, com confiança
`medium`; este fundamento orienta a revisão e não certifica o produto.

## Riscos e oportunidades adiadas

O estado técnico deixa de ser visível no export destinado ao professor;
mantém-se no registo persistido. Não há migração de dados nem alterações ao
frontend do aluno ou aos serviços de feedback.

- Rever a distinção entre acontecimentos do assistente e evidência observada
  nos relatórios de realizações. Esta correção exclui apenas checkpoints.
- Distinguir a escolha explícita `skip` de uma resposta em branco na
  autoavaliação das realizações; ambas aparecem como «Sem resposta».
- Rever a apresentação do contexto de grupo e sessão nas reflexões agregadas
  quando uma criança muda de grupo durante o mesmo trabalho.
