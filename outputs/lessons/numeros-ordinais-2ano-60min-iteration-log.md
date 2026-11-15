# numeros-ordinais-2ano-60min — registo de iterações

- 2026-11-15 — Pedido: página para o 2.º ano sobre números ordinais, 60 minutos, sem maker.
- Fonte curricular: AE Matemática 2.º ano — «Reconhecer os numerais ordinais até ao 20.º, em contextos diversos» (~/obsidian-vault/documentos-oficiais/aprendizagens-essenciais/matematica-2-ano-1-ciclo.md, p. 22).
- Architect: DocSpec com 6 unidades (8+11+11+10+10+10). Nota: o schema do Studio limita duration a 50; mantido 60 por pedido explícito.
- Designer: design-spec OKLCH (primary azul, accent violeta para ordinais).
- Proofreader v1: 0 critical, 2 high, 3 medium, 6 low → ticket de texto para o Builder.
- Iteração 1 (texto): Builder corrigiu 2 high + 3 medium + 4 low do proofread v1 → 0b5a421.
- Evaluator v1: FAIL critical (route builder). E1: u6 Intermédio nunca fecha (keypad() chama live('') e apaga p.lugar/conf); E2: falta favicon (404 na consola); E3: sobreposição no quadro «Lugar» da u6. u1–u5, níveis, layout 3 viewports, teclado e rede OK.
- Iteração 2: Builder corrigiu E1/E2/E3 → 114ca5c.
- Evaluator v2: FAIL high (route builder). E1 e E2 confirmados; E3b: keypad da u6 (Intermédio) transborda a 768–1024 px, teclas 5 e 0 tapadas; E4 low: bloco final e «Pergunta guardada» ficam visíveis após editar a pergunta confirmada.
- Iteração 3: Builder corrigiu E3b/E4 → 8076dc4.
- Evaluator v3: FAIL high. E3b, E4, E1 e regressão OK. A1 (novo): a pista automática após 3 falhas abre e fecha de imediato (commit()→sync() muda a assinatura do contexto e invalida a modal).
- Decisão do orquestrador: max_iterations atingido, mas A1 é novo, localizado e com causa confirmada no código → reparação extra única (v4) com verificação dirigida.
- Reparação extra: Builder sincroniza o contexto do apoio antes da tentativa → 7c33b3b.
- Evaluator v4: PASS, severidade low, sem issues. Riscos não críticos: textos de pergunta em att() vs ctx().q (u3/u4); modal só testada standalone; voz, «Ditar» e Safari/Firefox não testados.
