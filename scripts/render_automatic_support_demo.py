"""Cria um ensaio reproduzível do modal, com IA simulada e sem guardar dados."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from server.activity_support import embed_activity_support
from server.typography import embed_activity_typography


def render(output: Path):
    output.mkdir(parents=True,exist_ok=True)
    spec=json.loads((ROOT/'tests/fixtures/support-examples.json').read_text())[0]
    spec['topic']='Compor uma unidade com quartos'
    spec['objectives']=['Relacionar uma parte com a unidade', 'Explicar como contou as partes']
    spec['support'].update(version='ensaio-quartos-v1',languages=['pt'])
    unit=spec['units'][0];unit['summary']='Compor a unidade'
    unit['support']['objective']='Descobrir quantas peças de um quarto cobrem uma unidade.'
    unit['support']['criteria']=['Conta as partes iguais necessárias para cobrir a unidade.']
    obstacle=unit['support']['obstacles'][0];obstacle['label']={'pt':'Relacionar a parte com a unidade'}
    obstacle['hints'][0]['text']={'pt':{
        'individual':'Desenha uma tira que represente a unidade. Assinala um quarto da tira; quanto falta cobrir?',
        'group':'Desenhem uma tira que represente a unidade. Assinalem um quarto da tira; quanto falta cobrir?'}}
    obstacle['hints'][1]['text']={'pt':{
        'individual':'No desenho, junta partes iguais à primeira até cobrires a unidade. Quantas usaste?',
        'group':'No desenho, juntem partes iguais à primeira até cobrirem a unidade. Quantas usaram?'}}
    html='''<!doctype html><html lang="pt-PT"><head><meta charset="utf-8"><style>
body{padding:20px;background:#fffefa;color:#233c32;font:22px/1.45 'Didact Gothic',sans-serif}
button{font:inherit;padding:12px;min-height:56px;margin:5px}input{font:inherit;width:100px}
</style></head><body><section id="u1"><h1>Ensaio de tentativas confirmadas</h1>
<p>Quantos quartos completam uma unidade?</p><label for="answer">A tua resposta</label>
<input id="answer" type="number"><button id="check">Confirmar tentativa</button><p id="result" role="status"></p>
<aside data-pagecraft-support="u1"></aside></section><script>
const answer=document.getElementById('answer');
function sync(){if(window.PageCraftSupport)PageCraftSupport.update({unit_id:'u1',task_id:'quartos',question:'Quantos quartos completam uma unidade?',answer:answer.value});}
document.addEventListener('pagecraft-support-ready',sync);answer.addEventListener('input',sync);
document.getElementById('check').onclick=()=>{
  if(!answer.value)return;
  sync();const correct=Number(answer.value)===4;
  document.getElementById('result').textContent=correct?'Completa a unidade.':'Experimenta representar as partes.';
  const event={pagecraft:1,type:'attempt',unitId:'u1',payload:{correct,detail:{value:answer.value,question:'Quantos quartos completam uma unidade?',task_id:'quartos'}}};
  document.dispatchEvent(new CustomEvent('pagecraft:activity-event',{detail:event}));
  parent.postMessage(event,'*');
};
</script></body></html>'''
    (output/'activity.html').write_text(embed_activity_typography(embed_activity_support(html,spec)))
    modal=(ROOT/'server/static/student/support-modal.js').read_text()
    host='''<!doctype html><html lang="pt-PT"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>PageCraft · Ensaio do apoio automático</title><style>body{margin:0;background:#f5f3ea;color:#233c32;font:22px/1.45 'Didact Gothic',sans-serif}header{padding:16px}iframe{width:100%;height:700px;border:0}summary{cursor:pointer}pre{white-space:pre-wrap;overflow-wrap:anywhere}</style></head><body>
<header><strong>Ensaio local. IA simulada. Sem gravação ou publicação.</strong><p>Introduz e confirma 1, 2 e 3 para ensaiar o apoio após três respostas incorretas. O acerto é 4.</p>
<label>Percurso simulado <select id="route"><option value="permanent">Atividade permanente</option><option value="studio">Studio a pares</option></select></label>
<label><input type="checkbox" id="offline">Simular falha do fornecedor</label><details><summary>Ver registos do ensaio</summary><pre id="records"></pre></details></header>
<iframe id="lesson" title="Atividade de ensaio" sandbox="allow-scripts" src="activity.html"></iframe>
<script>MODAL</script><script>
const frame=document.getElementById('lesson'),route=document.getElementById('route'),events=[];
const options=new URLSearchParams(location.search);route.value=options.get('route')==='studio'?'studio':'permanent';
document.getElementById('offline').checked=options.has('offline');
function preferences(){frame.contentWindow.postMessage({pagecraft:1,type:'learning_preferences',payload:{route:route.value,participant_count:route.value==='studio'?2:1}},'*');}
frame.addEventListener('load',preferences);route.onchange=()=>{frame.src='activity.html';};
window.addEventListener('message',event=>{
 if(event.source!==frame.contentWindow || event.data?.pagecraft!==1 || event.data.type==='support_modal')return;
 events.push(event.data);document.getElementById('records').textContent=JSON.stringify(events,null,2);
 if(event.data.type==='feedback_request'){
  const p=event.data.payload,offline=document.getElementById('offline').checked;
  setTimeout(()=>frame.contentWindow.postMessage({pagecraft:1,type:'ai_feedback',payload:{request_id:p.request_id,unit_id:'u1',source:offline?'unavailable':'simulated',text:offline?'Não foi possível obter uma pista.':p.participant_count>1?'Representem uma unidade com peças de um quarto. Contem as peças necessárias para a cobrir.':'Representa uma unidade com peças de um quarto. Conta as peças necessárias para a cobrir.'}},'*'),500);
 }
});
</script></body></html>'''.replace('MODAL',modal)
    (output/'index.html').write_text(embed_activity_typography(host))
    return output/'index.html'


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,type=Path)
    print(render(parser.parse_args().output))
