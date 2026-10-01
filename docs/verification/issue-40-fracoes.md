# Verificação das cinco unidades de Frações

Em 29/09/2026, o ticket #40 estende o rascunho `fracoes-banda-desenhada-2ano` às cinco unidades. A atividade publicada `fracoes-2-minecraft` não foi alterada. Minecraft e reflexão final continuam no #41.

## Comportamento verificado

- Partes e símbolos: confirmação explícita, avanço com erro, alteração das partes invalida a confirmação.
- Associações: cada escolha fica registada, mesmo errada; pedidos em falta bloqueiam o avanço; correção preserva os restantes pedidos.
- Grelha: confirmação distinta da manipulação; desenho livre opcional, sem tentativa nem classificação automática, com rato/toque e alternativa de teclado.
- Unidade inteira: confirmação da composição e resposta sobre estar inteira são obrigatórias e independentes. Alterar partes invalida ambas.
- Comparações: todos os pares precisam de resposta, com A, B ou Iguais; unidades iguais e representações corretas. Mudar de percurso conserva o mesmo par mesmo quando muda de posição.
- Navegação e restauro não inventam tentativas. Recarregar uma realização recupera as respostas, a página e o desenho. O histórico do professor numa sessão ao vivo recebe as unidades `u1` a `u5`, incluindo erros.
- Ensaios continuam privados e excluídos dos relatórios; demonstração não envia respostas de alunos.

## Testes

As novas interações foram implementadas por ciclos vermelho → verde através do browser do Agent Browser Hub, sessão `fracoes-unidades-40`, perfil `research`. Os testes ligam-se por CDP ao browser do Hub. As integrações usam instâncias Studio e dados descartáveis.

Comando completo:

```sh
PAGECRAFT_TEST_CDP=http://127.0.0.1:9330 uv run --with playwright pytest -q
```

Resultado final: **273 testes passaram em 56,76 s**, incluindo 28 testes de browser. Cada teste usa um contexto próprio dentro do browser do Hub, para impedir que cookies de professor contaminem o ensaio seguinte de aluno.

Foram percorridos os três níveis nas larguras 390, 768, 900 e 1280 px, com respostas em falta e erradas, regresso, foco por teclado e alvos de toque de pelo menos 56 px. O caso de 900 px reproduziu a compressão das cinco partes antes do ajuste do breakpoint para 960 px. A geometria SVG de 2/5 foi verificada contra cinco partes de 60 unidades, duas pintadas, numa unidade de 300.

A retoma foi verificada pela API de realizações e o histórico de aula pela API do professor, sem consultar diretamente a persistência. A criação de rascunhos e o acesso do Quadro continuam cobertos pelos testes existentes.

## Revisão de código

Base fixa: `ef267917900453fe3e97fbc23ae0cdb9845a4996`. Duas revisões independentes pela skill `code-review`.

### Standards

Resolvidos os três achados: alvos de toque de 56 px, pistas de correção em âmbar e fundos tintados. A revisão adicional da largura de 900 px foi reproduzida e corrigida. Sem violações documentadas pendentes. Ficou uma sugestão não bloqueante: reunir as definições das páginas num registo ordenado antes de acrescentar Minecraft, para reduzir índices repetidos.

### Spec

Resolvida a perda de resposta quando o mesmo par de frações muda de posição entre níveis. O teste `test_same_comparison_survives_a_different_position_in_next_level` passou depois de falhar no comportamento anterior. Sem requisitos em falta identificados no recorte #40.

## Pré-visualização

A cópia pública isolada em `/home/proteu/.cache/pagecraft/fracoes-preview/pao/index.html` foi atualizada pelo túnel temporário já autorizado. O conteúdo HTTPS foi comparado byte a byte com o rascunho. O túnel serve apenas a pasta de exemplos; a produção não foi atualizada.

- https://graham-collaboration-exemption-contacting.trycloudflare.com/pao/
- Demonstração: acrescentar `?presentation=1`.
- Capturas do Hub: `/home/proteu/agent-browser-hub/screenshots/fracoes-cinco-unidades-desktop.png` e `/home/proteu/agent-browser-hub/screenshots/fracoes-cinco-unidades-mobile.png`.

Os testes demonstram o comportamento técnico. A adequação do ritmo e das pistas à turma deve ser observada pelo professor no ensaio.
