# Verificação do ticket #39

Implementação da primeira unidade de Frações em banda desenhada. Referência: [ticket #39](https://github.com/atilasos/pagecraft/issues/39), especificação #38 e decisões do professor em setembro de 2026. Base de revisão: `08b187d`; implementação revista até `85e3d5b`.

## Resultado funcional

O novo rascunho tem duas páginas de trabalho e um ecrã de revisão. Broto oferece comparação visual desde o início, Árvore jovem pede a comparação de partilhas e Árvore robusta pede uma partilha inventada e uma explicação. Todos os caminhos de avanço verificam as respostas obrigatórias; errar não bloqueia. Alterar um corte invalida a resposta dependente e conserva as respostas independentes.

A realização recupera páginas, cortes e respostas através da fila e persistência existentes, incluindo mudanças de nível ainda por sincronizar. Os checkpoints `activity_state` não são Evidências nem aparecem nos relatórios. As tentativas e mudanças de nível continuam separadas.

O Quadro obtém o conteúdo da sessão atual por uma rota exclusiva do seu papel. A rota permite demonstrar um rascunho registado sem o tornar público, recusa sessões diferentes ou fechadas e deixa de responder depois de revogar o emparelhamento. A demonstração permite navegar sem responder e não emite acontecimentos.

A atividade publicada `fracoes-2-minecraft` não tem alterações. As restantes unidades e o Minecraft pertencem aos tickets #40 e #41. As alterações do servidor estão nesta branch, testadas numa instância isolada; o Studio de produção não foi atualizado neste passo.

## Testes executados

Suite completa, com browser aberto pelo Agent Browser Hub: **252 testes passaram**.

```sh
PAGECRAFT_TEST_CDP=http://127.0.0.1:9330 uv run --with playwright pytest -q
```

O endereço CDP deve ser o da sessão atual do Hub. Os testes não lançam browsers independentes. Sem `PAGECRAFT_TEST_CDP`, os testes de browser ficam assinalados como ignorados; o resto da suite continua disponível.

- Resposta parcial, erro com pista, correção, regresso, invalidação e bloqueio dos separadores nos três níveis.
- Teclado e ausência de transbordamento horizontal a 390, 768 e 1280 px; a medição considera a largura útil, incluindo a barra de deslocamento.
- Tentativa e mudança de nível recebidas pelo histórico do professor numa sessão de teste real.
- Demonstração no cliente real do Quadro com rascunho registado e privado, sem copiar esse rascunho para uma atividade pública.
- Registo privado, rejeição anónima, restrição à sessão atual, fecho, revogação e exclusão dos ensaios dos relatórios.
- Restauro de respostas e de perguntas invalidadas ao reabrir a mesma realização.
- Recarga com os pedidos de gravação a devolver 503: conserva o nível escolhido e a resposta, sem a preferência antiga do servidor apagar trabalho.
- HTTPS 200 e igualdade dos bytes entre a pré-visualização remota e o HTML entregue. Percursos de resposta errada e demonstração verificados também no endereço público.

Os testes novos foram executados em vermelho antes das respetivas alterações. Uma execução da suite durante a inspeção remota interferiu com o mesmo separador do browser; a suite foi repetida sem essa operação concorrente e passou integralmente. A inspeção remota passou depois num separador próprio. Na verificação visual final, a asserção de largura foi reforçada e o teste responsivo voltou a passar.

## Standards

A revisão paralela encontrou uma divergência documentada e uma duplicação de critérios de acerto. Corrigidas: mudanças de nível passaram ao registo canónico, com artefactos gerados atualizados, e feedback e evidência usam os mesmos critérios.

Resultado final: **0 violações documentadas pendentes**. Há uma sugestão opcional de reunir a procura de conteúdo por identificador num método de Learning. Mantida a resolução curta na fronteira HTTP neste recorte, sem criar outra interface para um único chamador.

## Spec

A revisão paralela detetou três falhas, todas corrigidas com regressão: acesso do Quadro ao rascunho privado real, restauro da realização e preferência desatualizada quando existiam mudanças ainda por sincronizar.

Resultado final: **0 achados pendentes** na revisão `08b187d...85e3d5b`.

## Pré-visualização e capturas

- [Experimentar a primeira unidade](https://graham-collaboration-exemption-contacting.trycloudflare.com/pao/).
- [Demonstração com navegação livre](https://graham-collaboration-exemption-contacting.trycloudflare.com/pao/?presentation=1).
- [Captura de computador](/home/proteu/agent-browser-hub/screenshots/fracoes-unidade1-desktop.png).
- [Captura de telemóvel](/home/proteu/agent-browser-hub/screenshots/fracoes-unidade1-mobile.png).

O endereço público é uma cópia estática do rascunho e não está ligado a realizações nem a dados de alunos. Continua disponível enquanto a origem e o Quick Tunnel de revisão estiverem ativos. A integração com professor e quadro foi verificada na instância isolada de testes.

Para atualizar apenas esta cópia:

```sh
cp drafts/fracoes-banda-desenhada-2ano.html /home/proteu/.cache/pagecraft/fracoes-preview/pao/index.html
```

Para retirar apenas esta pré-visualização, remover esse `index.html` e a pasta vazia `pao`. Os exemplos A/B/C permanecem na raiz da origem. As unidades transitórias e a forma de parar o túnel completo estão nas decisões de usabilidade.
