# Ensaiar o apoio contextual numa atividade de Canva

O Canva é um caso de validação do apoio comum da skill. A configuração está em `pilots/canva-autonomia/support-plan.json`; o adaptador do guião não contém o motor de pistas.

Esta variante está preparada para revisão do professor. A atividade publicada `canva-animais-4ano` conserva o conteúdo anterior. Não houve publicação ou alteração de dados da turma nesta implementação.

## Percursos confirmados

A entrada em `/student/` com código de aula ou de grupo usa Studio. O anfitrião envia `feedback_request` para o registo da sessão; `FeedbackService` responde por SSE. O anfitrião encaminha a resposta para a atividade.

A entrada com código permanente em `/{code}` usa realizações. Antes desta alteração, o anfitrião descartava `feedback_request`: não fazia parte da lista de mensagens aceites. Agora o encaminha para `/api/learning/me/feedback`, que guarda pedido e resultado e devolve a pista ao mesmo anfitrião. Os testes percorrem entrada, credencial, pedido, persistência e resposta nos dois circuitos. Não comprovam a disponibilidade de um fornecedor de IA em produção.

No Studio, as respostas conjuntas continuam a pertencer ao grupo e as reflexões a cada participante. Para o piloto a pares, usar este percurso. No permanente, escolher «trabalho a pares ou em grupo» adapta o apoio, mas não cria identidades dos participantes nem reflexões individuais para todos. Escrever o mesmo nome não recupera uma pessoa ou um grupo entre realizações.

## Rever e abrir o piloto

1. Rever as duas pistas de cada etapa e de cada obstáculo em `pilots/canva-autonomia/support-plan.json`. São conteúdo preparado para revisão, sem aprovação docente presumida.
2. Reconstruir os ficheiros com `uv run python scripts/build_canva_support_pilot.py`. A variante fica em `drafts/canva-animais-autonomia-piloto.html`, acompanhada de registo, DocSpec e guia.
3. Abrir o ensaio isolado com `uv run python -m scripts.preview_canva_support_pilot`. O terminal mostra o código Studio e o endereço permanente de revisão. Usa alunos fictícios, uma resposta de IA simulada e armazenamento temporário. O terminal identifica o ensaio. Não chama um modelo externo.
4. Usar perfis de browser separados para professor e aluno, para não misturar credenciais. Entrar no código Studio, selecionar um par e usar «Precisamos de uma pista». Experimentar «Ainda estamos presos», «Ouvir», «Esclarecer com IA» e «Pedir ajuda ao professor».
5. No painel, abrir «Resumo do apoio nesta aula». Ao terminar a aula, o resumo fica disponível na página de preparação. Para sessões anteriores, escolher a turma em «Ver registo» e abrir o resumo da sessão.

O registo JSON permite preparar o rascunho no servidor habitual pela API de atividades já existente. A publicação fica disponível para aprovação explícita na interface docente. Não publicar o ensaio nem substituir a atividade antiga antes da revisão.

## Apoio durante a atividade

A ajuda fica junto da ação da etapa atual. O grupo declara o obstáculo: perceber a instrução, encontrar comando, organizar ideias, rever trabalho ou guardar produto. Recebe uma pista do guião por vez. «Outra pista» oferece outra abordagem. «Ainda estamos presos» também regista que a pista anterior não ajudou. Depois das duas pistas, o apoio orienta a mostrar ao professor o que já foi tentado.

«Esclarecer com IA» é um pedido explícito, com objetivo, etapa, produto, critérios relevantes, respostas recentes, composição individual ou conjunta, versão e pistas anteriores. A IA recebe informação do que o grupo disse não ajudar. Uma resposta que repete literalmente uma pista anterior não é apresentada de novo. Reformulações semanticamente repetidas ainda exigem observação no piloto.

A chave da cache inclui todo o contexto semântico. O identificador do pedido liga a resposta à tentativa correspondente. Uma resposta atrasada não é apresentada após mudar etapa, produto, apoio, composição, obstáculo ou resposta. No Studio, pedidos correlacionados também não aparecem no aviso global do anfitrião.

Não há pistas por tecla ou por tempo sem cliques. «Estamos a trabalhar no Canva» e «Estamos a ler ou conversar» são declarações. «Regressar ao guião» marca o retorno. A ausência de acontecimentos não comprova dificuldade. `assessment_result` conta como trabalho na triagem.

«Ouvir» usa a leitura disponível no dispositivo, sem áudio automático. A disponibilidade e a pronúncia dependem do browser e das vozes instaladas. A atividade permite continuar a ler se não houver voz. A falha de IA indica que não foi possível obter uma pista e sugere guião ou professor, sem afirmar leitura docente.

## Rever o resumo em dois minutos

O resumo é calculado diretamente dos registos, sem uma nova chamada ao modelo. Mostra etapas com pedidos de vários grupos ou realizações, pistas declaradas pouco úteis, pedidos sem resolução registada, até três exemplos de alterações e propostas para revisão do professor. Cada conclusão abre os registos de origem, com autor do grupo, etapa, data e identificador.

No permanente, escolher uma atividade, turma e datas antes de gerar o resumo. Os ensaios privados ficam fora dos relatórios normais. As conclusões dizem «grupos ou realizações» porque duas realizações com o mesmo nome não identificam o mesmo grupo.

Uma nova resposta ou pista não encerra um pedido ao professor. O grupo tem de indicar que já consegue continuar. Isto é resolução declarada, sem comprovar intervenção docente. A ausência de pedidos pendentes não demonstra ausência de bloqueios.

Uma alteração de texto no PageCraft é observável. «Aumentámos o título no Canva» é uma declaração sobre um produto externo. A associação temporal a uma pista não prova que a pista causou a alteração. A apresentação da pista não prova leitura; a indicação de utilidade não prova aprendizagem.

As propostas identificam o problema e as fontes. Não alteram automaticamente instruções ou pistas. Rever primeiro um exemplo da instrução, testar a interpretação com um grupo e preparar uma nova versão do rascunho.

## Avaliar o primeiro piloto

Usar uma atividade numa aula e, se necessário, a sua continuação. Registar estes sinais sem classificar os alunos:

- Reconhecimento: perguntar a alguns grupos onde apareceu a pista e qual a ação que sugeriu. Um clique ou a apresentação da pista, por si só, não responde a isto.
- Uso: observar um pequeno exemplo de aplicação ou ouvir a explicação do grupo. Comparar com a indicação de utilidade e com a ação seguinte registada, quando existir.
- Continuidade com sentido: pedir que expliquem o que fizeram e porquê, sem exigir velocidade. Recolher a voz de cada participante quando a questão é compreensão individual.
- Bloqueios persistentes: consultar pedidos não resolvidos e pistas declaradas pouco úteis. Perguntar se a instrução ou a interface do guião contribuiu para o bloqueio.
- Utilidade docente: reservar dois minutos depois da aula. Anotar se o resumo permitiu escolher uma alteração concreta ao guião ou um apoio para a aula seguinte.

Menos pedidos de ajuda não é uma medida isolada de sucesso. Pode significar autonomia, desistência ou dificuldade em pedir. Confirmar com observação e explicações dos alunos. Não usar tempo, cliques ou quantidade de respostas como classificação.

## Dados necessários e duração proposta

Guardar apenas o contexto da etapa, versão, tentativa curta, categoria declarada, texto e origem da pista, indicação de utilidade, pedido de leitura e ação seguinte observável. Conservar os registos de origem para permitir contestar as conclusões. Os acontecimentos do grupo não se tornam resultados individuais.

Para este piloto, a proposta a aprovar antes da recolha é rever os dados em 30 dias e eliminar os registos identificáveis do piloto até 90 dias depois da última aula. Conservar depois apenas instruções revistas e exemplos anonimizados escolhidos pelo professor. Rever também cópias de segurança e ficheiros exportados. A expiração de um código ou cookie não elimina os registos.

Não existe eliminação automática configurada nesta alteração. O professor tem de definir o responsável e o procedimento de eliminação no armazenamento e nas cópias antes da aula. O servidor de ensaio usa armazenamento temporário e remove-o ao encerrar normalmente.

## Decisões e limites do primeiro piloto

Escolheu-se conteúdo de apoio no guião com esclarecimento opcional pela IA, em vez de pedir ao modelo uma resposta a cada saída de campo. Dá uma primeira ação imediata, permite rever as dificuldades previsíveis e mantém o trabalho quando o modelo falha. O servidor é dono da persistência e do acesso; a atividade é dona do contexto atual e só regista uma pista apresentada depois de a aceitar.

Ainda não há entrega ou análise de capturas/PDF, comparação visual de versões, memória entre aulas ou identificação longitudinal. A memória futura precisa de identidade estável gerida pelo professor, observações pequenas datadas, ligação a objetivos e exemplos, consulta, correção e remoção, prazo de revisão e eliminação e apoios que o aluno possa recusar. Não inferir identidades por nome nem guardar rótulos permanentes.

Depois de avaliar o apoio atual, experimentar separadamente: ensaio de um percurso com cenários simulados; uma pergunta que distinga causas de um erro; comparação de dois ficheiros voluntariamente entregues; verificação de um pequeno procedimento de software. Cada experiência precisa de critérios e fontes próprios. Simular alunos não substitui observar a turma.

## Verificações reproduzíveis

```sh
uv run python scripts/build_canva_support_pilot.py --check
node --test tests/js/activity_support.test.cjs
uv run pytest -q --ignore=tests/browser
```

O primeiro comando deteta desatualização da variante. Os testes JavaScript verificam progressão, contexto, correlação, invalidação de respostas atrasadas, leitura apenas solicitada e associação entre pista e revisão de resposta. Os testes Python cobrem os dois circuitos, cache, persistência, falhas, triagem, síntese, fontes e acesso docente.


## Resultado da verificação local em 22 de outubro de 2026

Passaram 299 testes Python e cinco testes JavaScript. No browser real, através do Agent Browser Hub, foi verificada a entrada de um par com código Studio, a primeira pista, outra abordagem após «Ainda estamos presos», a chegada de uma resposta do fornecedor simulado, o pedido de leitura e o pedido ao professor. O resumo guardou três pistas apresentadas, uma indicada como útil, uma indicada como pouco útil e um pedido pendente. Só a declaração explícita de que o grupo já conseguia continuar passou esse total a zero.

Foi também verificada a declaração de trabalho no Canva e o regresso ao guião, a abertura das fontes do resumo e a entrada no rascunho pelo código permanente com devolução de feedback. O ensaio permanente foi uma pré-visualização docente; o acesso de alunos a uma atividade permanente publicada é coberto pelos testes de API. Não foi publicada nenhuma atividade.

A inspeção visual encontrou a pista inicialmente abaixo dos controlos. O cartão foi reorganizado para apresentar a ação primeiro e focá-la na zona visível. O pedido de voz foi exercitado no browser; a qualidade e audibilidade da voz instalada precisam de confirmação no dispositivo da turma. O fornecedor real de IA e a utilização por alunos em aula continuam por validar.

A versão v2 do rascunho usa o mesmo componente e plano DocSpec que qualquer nova atividade gerada. A skill define as pistas a partir do pedido, em vez de copiar o conteúdo Canva. As verificações descritas acima referem-se ao primeiro ensaio local; a generalização tem testes próprios em Matemática, escrita e Scratch.
