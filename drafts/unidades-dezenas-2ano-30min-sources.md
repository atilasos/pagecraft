# Fontes — A oficina dos números

Consulta: **12/10/2026**. Pedido: Matemática, 2.º ano, unidades e dezenas, 30 minutos, português europeu. Pesquisa e leitura pela API local da Sebenta, confirmada saudável em `http://127.0.0.1:8765`; sem browser para investigar a wiki.

## Síntese da wiki

Foram pesquisados termos concretos relacionados com unidades/dezenas, matemática, avaliação formativa, TIC e MEM. Páginas consultadas integralmente via `sebenta_api.py read --content`:

| Página | Caminho no vault | Uso na proposta |
| --- | --- | --- |
| Avaliação Formativa | `20_Wiki/Avaliação Formativa.md` | Explicitar critérios; registar estratégias/erros; permitir rever; ajustar apoios enquanto se aprende. |
| Modelo Pedagógico do MEM | `20_Wiki/Modelo Pedagógico do MEM.md` | Cooperação e comunicação de estratégias à turma; autonomia apoiada; evitar classificação e papéis fixos. |
| TIC no Ensino Básico | `20_Wiki/TIC no Ensino Básico.md` | Integrar tecnologia num problema de Matemática; escolher progressão adequada ao ano, em articulação com o titular. |
| Ensino da Matemática | `20_Wiki/Ensino da Matemática.md` | Manipular, compor/decompor e confrontar representações; comunicar o raciocínio. |
| PageCraft | `20_Wiki/PageCraft.md` | SRTC-A, descoberta pela interação, avaliação observável, diferenciação desde o desenho, HTML autocontido. |

Estas páginas estão em estado `review`, com confiança `medium`; são sínteses editoriais da wiki, não observações desta turma. A página TIC tem atualização de 08/09/2026 e documenta a continuidade do trabalho do professor no 1.º ciclo em 2026/2027. A proposta usa essa articulação curricular, sem presumir qual é a turma ou o horário desta sessão.

A wiki assinala uma proposta de revisão das Orientações Curriculares de TIC de março de 2026 que, na última verificação documentada, não estava homologada. Esta atividade não apresenta essa proposta como obrigação curricular nem reivindica cobrir descritores anuais de TIC.

## Fonte original pedagógica

**Graça Cebola, «Do número ao sentido do número»**, Escola Superior de Educação de Portalegre.

- Caminho: `10_Sources/Knowledge/matemática/sentidonum.md`.
- Consultada pela API `source`, incluindo texto extraído do documento de 17 páginas; a nota assinala `ocr: false`.
- Usada a fonte extraída, não o resumo automático por rever.
- Fundamenta o uso de material de base dez, múltiplas representações, decomposição/recomposição e conversa sobre estratégias. O texto apresenta relações como várias formas de representar uma mesma quantidade.
- As referências curriculares históricas citadas nesse texto não são usadas como referencial curricular atual.

## Referencial curricular confirmado

**DGE, Aprendizagens Essenciais de Matemática, 2.º ano, versão de 2021**, PDF oficial consultado em 12/10/2026:

[Aprendizagens Essenciais — Matemática, 2.º ano](https://www.dge.mec.pt/sites/default/files/Curriculo/Aprendizagens_Essenciais/1_ciclo/aemat_2a_2021.pdf)

- Página 22: leitura/representação de naturais até 1000 e comparação da grandeza.
- Página 23: valor posicional com material de base dez; composição e decomposição por diferentes representações.
- O alinhamento declarado nesta atividade é um recorte desses objetivos, limitado a unidades/dezenas e números até 99; não equivale à cobertura do objetivo anual até 1000.
- A homologação das AE de 2021 é identificada pela [notícia oficial da DGE](https://www.dge.mec.pt/node/3935). Uma versão de março de 2026 surgiu nos resultados como revisão; não foi usada como norma.
- O acesso ao PDF sem `www` falhou no leitor web; o mesmo PDF com `www.dge.mec.pt` foi efetivamente lido. Nenhuma afirmação curricular depende do acesso falhado.

Os descritores no DocSpec são paráfrases do referencial. As áreas de competência do Perfil dos Alunos aparecem como mapeamento pedagógico da tarefa, sem inventar descritores oficiais: linguagem matemática, raciocínio, relacionamento interpessoal e autonomia.

## Proposta desta atividade

São decisões de conceção próprias, a rever pelo professor:

- Trocar dez cubos por uma barra segmentada e voltar atrás, conservando 14 unidades de quantidade.
- Construir 24, 30 e 57; o 30 obriga a considerar ausência de unidades soltas.
- Comparar 24/42 e identificar o valor do 4 em 42.
- Conservar pedidos base entre os três apoios; acrescentar uma representação equivalente de 24 como desafio facultativo.
- Avançar depois de responder, mesmo com erros, recebendo pistas visuais e podendo corrigir.
- Retomar os mesmos três critérios em reflexão individual facultativa; reservar cinco minutos para comunicação/reflexão.

## Regras operacionais consultadas

`AGENTS.md`, `PRODUCT.md`, `CONTEXT.md`, `skills/codex/agents/pagecraft-architect.md`, `skills/codex/identities/architect.md`, `skills/codex/references/activity-experience.md` e `skills/codex/references/age-adaptation.md`, no checkout `/home/proteu/pagecraft`.

A referência atual do repositório resolve a tensão histórica da wiki sobre semáforos: os apoios chamam-se **Com pistas**, **Passo a passo** e **Mais desafios**, sem verde/amarelo/vermelho. Aplicam-se os mínimos de 6–7 anos mesmo quando uma criança do 2.º ano já tem 8 anos.

## Lacunas para revisão

Não há dados desta turma sobre leitura, familiaridade com material de base dez ou disponibilidade de pares; o professor ajusta estes aspetos. O desenho pedagógico e a validação de schema não demonstram usabilidade: os testes reais do HTML pertencem à fase Evaluator. Não foi feita observação de trabalho fora da página.
