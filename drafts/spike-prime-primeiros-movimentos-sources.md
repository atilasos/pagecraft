# Fontes — SPIKE Prime: primeiros movimentos

Consulta: 2026-10-02. Pedido: alunos do 3.º e 4.º anos, base motriz em construção, início da programação na próxima aula seguindo a unidade LEGO Education «Prontos para a competição».

## Síntese da Sebenta
API local verificada; pesquisa por TIC, avaliação e robótica. Páginas lidas integralmente (cópias temporárias de consulta em `/tmp/pagecraft-spike-primeiros-movimentos-research/`; os originais permanecem na Sebenta):
- **PageCraft** — `20_Wiki/PageCraft.md`: descoberta por interação, diferenciação desde o desenho, evidências formativas; documentação operacional atual do repositório prevalece sobre exemplos antigos.
- **TIC no Ensino Básico** — `20_Wiki/TIC no Ensino Básico.md`: TIC transversal no 1.º ciclo, projetos e progressão decidida pelo professor; clube de robótica no contexto do professor. A proposta de março de 2026 não foi assumida como norma.
- **Avaliação Cooperada** — `20_Wiki/Avaliação Cooperada.md`: critérios partilhados, alunos participam no plano e no balanço, comunicação e entreajuda.
- **Pensamento Computacional** — `20_Wiki/Pensamento Computacional.md`: decompor, planear sequências, testar e corrigir; programação ao serviço da resolução de problemas.
Estas páginas estão em review/draft; as sínteses não equivalem a fontes oficiais. As fontes brutas bibliográficas aí referidas não foram todas relidas neste trabalho.

## Fontes originais consultadas
- PDF fornecido pelo professor: **Acampamento de Treinamento 1: Dirigindo Por Aí**, LEGO Education, extraído integralmente com pdftotext; cópia do texto em `/tmp/spike-driving.txt`. Programas ilustrados usam C+D, velocidade 30%/50% e exemplo de 17,5 cm por rotação. Estes valores dependem da montagem; graus do motor não equivalem ao ângulo da base.
- [Aula oficial LEGO](https://education.lego.com/pt-br/lessons/prime-competition-ready/training-camp-1-driving-around/): progressão de movimentos e percursos; consulta web para confirmar a versão atual.
- [Aplicação SPIKE Prime](https://spike.legoeducation.com/prime/project): aberta no browser T3; confirmadas categorias de Movimento, Eventos, Controlo e Sensores e existência dos blocos de motores, velocidade, distância, rotação e guinada. A aplicação abriu em inglês e os rótulos do PDF estão em pt-BR; a atividade usa explicações pt-PT e avisa sobre diferenças de idioma/versão. Não foi ligada uma base real.
- [ERTE — documentos orientadores TIC](https://erte.dge.mec.pt/tic-1o-ceb-documentos-orientadores): verificado o link atual para as OC de 2018.
- [OC TIC 1.º ciclo, 2018, original PDF](https://www.erte.dge.mec.pt/sites/default/files/oc_1_tic_-_vf_03out2018.pdf), pp. 7–9: comunicação e colaboração; criação de algoritmos simples; programação de objetos tangíveis e orientação espacial. São OC de ciclo, não AE separadas do 3.º/4.º ano. Foram lidos os descritores e ações pertinentes no original.

## Proposta de adaptação desta atividade
Missões breves e retomáveis. Primeiro planear, experimentar e comparar; começar com distância e baixa velocidade, trocar papéis no grupo e alterar apenas um parâmetro por teste. Percurso em L antes do quadrado; repetição e giroscópio como continuação orientada pelo professor. Não introduzir cálculo de circunferência nem prometer ângulos exatos por rotações de motor. Os registos do robot são declarações dos alunos, distintas das interações observadas na página e da observação do professor.

## Pressupostos e lacunas para revisão
Professor confirmou aulas de 45 minutos e esclareceu que seguem a unidade «Prontos para a competição», sem necessariamente preparar uma competição real. Nenhum regulamento ou pontuação foi presumido. Portas e tamanho real das rodas carecem de confirmação em aula. Conexão, transferência e funcionamento no robot físico não podem ser verificados sem o equipamento. O browser foi usado para consulta da app, não para observar programação dos alunos.

## Capturas reais acrescentadas a pedido do professor
Em 2026-10-02, aplicação SPIKE 3.6.1, idioma Português (Brasil), projeto de blocos de palavras. Capturas no browser T3; original e recortes em `drafts/spike-prime-primeiros-movimentos-assets/`, com dimensões, caixas de recorte e hashes em `captures.json`. Programa de exemplo criado na aplicação com os seus blocos originais; sem ligação a um hub. Apenas recorte: sem redesenhar, traduzir ou alterar os pixels dos blocos. As legendas da atividade permanecem em PT-PT. C+D, 30%, 17,5 cm por rotação e 20 cm são exemplos; as portas e a medida real das rodas são confirmadas em aula. A viragem de exemplo usa direção 100 e 0,25 rotações, sem equivalência garantida a 90 graus; ajustar por ensaio com o professor. Os PNG são incorporados na página para não dependerem de rede. Originais © LEGO Group; fonte: [LEGO Education SPIKE](https://spike.legoeducation.com/prime/project).

## Revisão da língua e qualidade das capturas — 2026-10-05
Selecionado Português (Brasil) na interface SPIKE, em Configurações > Idioma; seleção confirmada pela marca de visto após recarregar a aplicação. Evidência em `spike-prime-primeiros-movimentos-assets/spike-language-pt-br.png` e `spike-prime-primeiros-movimentos-qa/language-quality.json`. Aplicação 3.6.1. T3 preview_status e preview_open devolveram Authentication required; usado Agent Browser Hub, perfil research, com a sessão própria. Capturas novas PNG sem perdas, 3200×2200 pixels para viewport1600×1100 a2×, através do CDP do browser gerido pelo Hub. Os recortes preservam os pixels do novo original e a forma completa dos blocos. Não foram ampliados os PNG antigos. `captures.json` regista originais, caixas de recorte, rótulos e hashes; `captures-v1.json` e o histórico Git preservam a referência da versão anterior. Blocos e rótulos originais pt-BR; explicações didáticas permanecem pt-PT. Valores e portas continuam exemplos. Não foi ligado um hub.
