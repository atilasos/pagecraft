/* Adaptador do guião Canva ao apoio comum; as pistas vivem no DocSpec. */
const revisionHints = new Map();
function syncSupport() {
  if(!window.PageCraftSupport)return;
  PageCraftSupport.update({unit_id:'u'+(state.step+1),level:state.level,
    product:state.values.product||'',question:DATA.units[state.step].title,
    answer:fieldsFor(state.step).map(f=>f[2]+': '+(state.values[f[0]]||'sem resposta')).join('\n'),
    attempt:fieldsFor(state.step).map(f=>[f[0],state.values[f[0]]||'',state.invalid.includes(f[0])])});
}
function requestTeacherHelp(){syncSupport();window.PageCraftSupport?.help();}
const renderLesson = render;
render = function() {
  renderLesson();
  const panel=document.createElement('aside');
  panel.dataset.pagecraftSupport='u'+(state.step+1);
  $('pagecraft-feedback').remove();
  ($('sheet').querySelector('.action')||$('support-panel')).after(panel);
  syncSupport();
};
fieldEvent = function(key) {
  const f=fieldMap[key];if(!f)return;
  dirty.delete(key);
  PageCraftBridge.assessment('u'+(f[1]+1),'Declaração do grupo',{
    activity:SLUG,activity_version:window.PageCraftSupport?.version(),field:key,
    value:state.values[key]||'',confirmed:!state.invalid.includes(key),note:f[2],
    external_change:key==='revisionResult',after_hint_id:revisionHints.get(key)||window.PageCraftSupport?.currentHintId()||null});
  revisionHints.delete(key);
  syncSupport();
};
const editLesson=inputValue;
inputValue=function(...args){
  const hintId=window.PageCraftSupport?.currentHintId();
  if(hintId&&!revisionHints.has(args[0]))revisionHints.set(args[0],hintId);
  editLesson(...args);syncSupport();
};
const goLesson=go;
go=function(...args){goLesson(...args);syncSupport();};
const levelLesson=setLevel;
setLevel=function(...args){levelLesson(...args);syncSupport();};
const restoreLesson=restoreEvents;
restoreEvents=function(...args){restoreLesson(...args);syncSupport();};
document.addEventListener('pagecraft-support-ready',syncSupport);
