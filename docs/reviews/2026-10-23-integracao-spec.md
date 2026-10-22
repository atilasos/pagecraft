# Integração final, revisão Spec da ronda 3

SHA fixo `e105d76c26f417a3dc5cbd9fc11ce90d0a25c796`, incluindo comparação incremental com `a609f64`, reparação `c4c8e6a` e conclusão das pontes em `e85359c`. **0 achados.**

A reparação devolve o foco no próprio iframe após receber a escolha explícita Continue/Professor. O identificador precisa de coincidir com a pista e o modal atuais; mensagens obsoletas são ignoradas. Outra pista ou indicação de bloqueio abre novo modal sem focar o exterior. O auxiliar também recusa painéis desligados, ocultos ou inertes. Uma confirmação assíncrona do pedido docente pode reconstruir o painel, mas o render conserva o foco na nova instância da ação, quando esta ainda pertence ao contexto atual. A consulta do histórico conserva o tratamento anterior, antes de qualquer mudança de unidade.

O diff não relaxa sandbox, CSP ou autorização. Não altera a declaração de utilidade, não resolve pedidos de ajuda automaticamente e não acrescenta evidências para a simples mudança de foco. A fonte canónica, os espelhos Codex/Claude e a incorporação JS/CSS/modal no rascunho coincidem exatamente.

Os ficheiros de fila, bilhete, páginas anfitriãs, realização individual, publicação, serviço/API da sala e drawer continuam iguais aos revistos em `a609f64`. Mantêm versões de cache, IDs e contratos já aprovados. A personagem continua restrita aos resultados laterais testados; agora existe uma regressão persistente que inspeciona geometria, posições, representação acessível e invariância do topo.

Li os três novos casos JS, os dois percursos de anfitriões reais e a regressão SVG. A avaliação final regista PASS, sem achados, com 23 testes de browser; o SHA-256 do HTML nesta integração coincide com o artefacto dessa avaliação. A recomendação de cobertura persistente da ronda anterior ficou satisfeita. Os resultados vermelhos anteriores permanecem identificados como históricos.

Não executei browser nem repeti a suite que o principal está a executar. Esta revisão consistiu na inspeção do código e contratos, comparação dos conteúdos Git fixos e verificação do hash do artefacto. Só criei este relatório em `/tmp`, sem alterar o checkout.
