"use strict";
window.PageCraftSupportSummary = {
  render(root, summary) {
    const node = (tag, text) => { const element=document.createElement(tag); if(text!==undefined)element.textContent=text; return element; };
    root.replaceChildren(node('h2','Depois da aula · Apoio e próximos passos'));
    const c=summary.counts;
    root.append(node('p',`${c.presented} pistas apresentadas · ${c.helped} indicadas como úteis · ${c.not_helped} indicadas como pouco úteis · ${c.revisions} revisões de respostas · ${c.unresolved} pedidos sem resolução registada`));
    function sources(parent, ids) {
      const details=node('details');
      details.append(node('summary',`Consultar ${ids.length} registo(s)`));
      for(const id of ids) {
        const record=summary.records[id];
        if(!record)continue;
        details.append(node('p',`${record.actor_label} · ${record.unit_id||'sem etapa'} · ${record.at||''} · registo ${id}`));
        const pre=node('pre',JSON.stringify({type:record.type,payload:record.payload},null,2));
        pre.style.whiteSpace='pre-wrap';pre.style.overflowWrap='anywhere';details.append(pre);
      }
      parent.append(details);
    }
    function section(title, rows, empty) {
      root.append(node('h3',title));
      if(!rows.length){root.append(node('p',empty));return;}
      const list=node('ul');
      for(const row of rows){
        const item=node('li');item.append(node('p',row.text));
        if(row.before)item.append(node('p','Antes: '+row.before));
        if(row.after)item.append(node('p','Depois ou alteração declarada: '+row.after));
        if(row.problem)item.append(node('p','Problema a investigar: '+row.problem));
        sources(item,row.evidence);list.append(item);
      }
      root.append(list);
    }
    section('Etapas com pedidos de vários grupos ou realizações',summary.recurring,'Sem recorrência demonstrada nos registos desta seleção.');
    section('Pistas que disseram não ajudar',summary.unhelpful,'Sem indicação de pistas pouco úteis nesta seleção.');
    section('Pedidos sem resolução registada',summary.unresolved,'Sem pedidos pendentes nos registos. Isto não comprova que todos os bloqueios foram resolvidos.');
    section('Exemplos de alterações',summary.changes,'Sem exemplos de alterações registados.');
    section('Propostas para revisão do professor',summary.proposals,'Faltam dados para propor uma alteração concreta ao guião.');
    const limits=node('details');limits.open=true;limits.append(node('summary','Dados em falta e limites da leitura'));
    for(const line of summary.limits)limits.append(node('p',line));root.append(limits);
  }
};
