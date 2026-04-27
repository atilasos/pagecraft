#!/usr/bin/env python3
"""Audit canonical M28P main pages against docs/m28p.md principles."""
from __future__ import annotations
import argparse, json, re, unicodedata
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CANONICAL_DISPLAY=['menina','menino','uva','dedo','sapato','bota','leque','casa','janela','telhado','escada','chave','galinha','ovo','rato','cenoura','girafa','palhaço','zebra','bandeira','funil','árvore','quadro','passarinho','peixe','cigarra','fogueira','flor']

def slugify(word:str)->str:
    s=unicodedata.normalize('NFD', word).encode('ascii','ignore').decode('ascii')
    s=re.sub(r'[^a-zA-Z0-9]+','-',s.lower()).strip('-')
    return s
CANONICAL=[{'order':i+1,'word':w,'slug':slugify(w)} for i,w in enumerate(CANONICAL_DISPLAY)]
PT_BAD={
 'Você':'pt-BR', 'ônibus':'pt-BR', 'tela':'pt-BR', 'mouse':'pt-BR',
 'Objectivos':'pre-AO', 'objectivos':'pre-AO', 'interactivo':'pre-AO', 'interactiva':'pre-AO', 'interactivas':'pre-AO', 'interactivo':'pre-AO',
 'selecciona':'pre-AO', 'Selecciona':'pre-AO', 'seleccionar':'pre-AO', 'Seleccionar':'pre-AO',
 'colectivo':'pre-AO', 'colectiva':'pre-AO', 'colectivamente':'pre-AO', 'Actividade':'pre-AO', 'actividade':'pre-AO', 'activação':'pre-AO', 'Activação':'pre-AO',
 'vêem':'pre-AO', 'acção':'pre-AO', 'Acção':'pre-AO', 'objectos':'pre-AO', 'objecto':'pre-AO', 'projecto':'pre-AO', 'Projecto':'pre-AO'
}
CHECKS={
 'meaningful_context_image':['imagem','história','historia','contexto','micro-história','micro-historia','situação','situacao'],
 'global_recognition':['reconhecer global','reconhecimento global','palavra completa','forma global','leitura global'],
 'reading_writing':['escrever','escrita','copiar','cópia','leitura e escrita','ler e escrever'],
 'syllabic_segmentation':['sílaba','silaba','segment','palmas'],
 'recombination':['recombina','novas palavras','palavras novas','pseudopalavra','pseudo-palavra','forma palavras'],
 'sound_letter':['som-letra','som/letra','letra-som','grafema','fonema','grafofon','consciência fonológica','fonológica','sons/letras','sons e letras'],
 'new_word_generalization':['generalização','generalizacao','palavras novas','nova palavra','palavra nova','não memorizad','nao memorizad'],
 'phrases_texts':['frase','texto curto','pequeno texto'],
 'quick_verification':['verificação','verificacao','avaliação','avaliacao','mini-avaliação','bilhete','assessment'],
 'anti_pure_visual':['não é só memorizar','nao e so memorizar','não memorizar','nao memorizar','memorização visual','memorizacao visual','código alfabético','codigo alfabetico','funcionamento alfabético','puramente visual','uso puramente visual'],
}
ARTIFACTS=['index.html','teacher.md','docspec.json','design-spec.json','meta.json']
REPORT_DIR=ROOT/'.omx'/'reports'

def read(p:Path)->str:
    try: return p.read_text(encoding='utf-8')
    except FileNotFoundError: return ''

def evidence(text:str, needles:list[str])->dict:
    low=text.lower()
    for n in needles:
        i=low.find(n.lower())
        if i>=0:
            return {'pass':True,'needle':n,'snippet':text[max(0,i-80):i+160].replace('\n',' ')}
    return {'pass':False,'needle':None,'snippet':''}

def page_text(d:Path)->str:
    return '\n'.join(read(d/f) for f in ARTIFACTS if (d/f).exists())

def audit():
    cat=json.loads(read(ROOT/'catalog.json'))
    items={i.get('slug'):i for i in cat.get('items',[])}
    by_order={i.get('order'):i for i in cat.get('items',[]) if 'm28p' in i.get('tags',[]) and i.get('order') and not i.get('variantOf')}
    pages=[]; priority=[]
    for c in CANONICAL:
        slug=c['slug']; d=ROOT/'activities'/slug; item=items.get(slug, {})
        text=page_text(d); low=text.lower(); html=read(d/'index.html')
        page={'slug':slug,'word':c['word'],'order':c['order'],'checks':{},'issues':[],'evidence':{}}
        if not d.exists(): page['issues'].append('missing_activity_dir')
        if not item: page['issues'].append('missing_catalog_item')
        if by_order.get(c['order'],{}).get('slug')!=slug: page['issues'].append('canonical_order_mismatch')
        if item.get('variantOf'): page['issues'].append('is_variant_unexpected')
        for f in ARTIFACTS:
            if not (d/f).exists(): page['issues'].append(f'missing_{f}')
        for check,needles in CHECKS.items():
            ev=evidence(text, needles); page['checks'][check]=ev['pass']; page['evidence'][check]=ev
            if not ev['pass']: page['issues'].append('missing_'+check)
        # duration
        durations=[]
        if item.get('duration') is not None: durations.append(('catalog', item.get('duration')))
        for fn in ['meta.json','docspec.json']:
            try: durations.append((fn, json.loads(read(d/fn)).get('duration')))
            except Exception: pass
        if slug=='leque': expected=45
        else: expected=item.get('duration',45)
        bad=[f'{k}:{v}' for k,v in durations if v!=expected]
        if bad: page['issues'].append('duration_inconsistent_'+','.join(bad))
        if slug=='leque' and expected!=45: page['issues'].append('leque_expected_45')
        if slug=='leque':
            stale=[]
            for fn in ['teacher.md','index.html','docspec.json']:
                stale_text=read(d/fn)
                if re.search(r'40\s*(minutos|min\b)', stale_text, re.I):
                    stale.append(fn)
            if stale:
                page['issues'].append('leque_stale_40min_text_'+','.join(stale))
        # docspec unit sum if available
        try:
            doc=json.loads(read(d/'docspec.json')); units=doc.get('units',[]); s=sum(u.get('duration',0) for u in units)
            page['unit_duration_sum']=s
            if doc.get('duration') and s and s!=doc.get('duration'): page['issues'].append(f'unit_duration_sum_{s}_not_{doc.get("duration")}')
        except Exception as e: page['issues'].append('docspec_parse_error')
        # offline scan relevant artifacts including design-spec
        off=[]
        for f in ['index.html','design-spec.json','docspec.json','teacher.md']:
            t=read(d/f)
            if re.search(r'https?://|<script\s+src|<link\s+[^>]*href=|@import|googleapis|fontUrl', t, re.I): off.append(f)
        if off: page['issues'].append('external_dependency_'+','.join(off))
        # lang
        if html and '<html lang="pt-PT"' not in html and "<html lang='pt-PT'" not in html:
            page['issues'].append('html_lang_not_pt_PT')
        # pt/AO scan
        bad_tokens=[]
        for tok,kind in PT_BAD.items():
            if tok in text: bad_tokens.append(tok)
        if bad_tokens: page['issues'].append('pt_ao_tokens_'+','.join(sorted(set(bad_tokens))[:12]))
        # report proof/eval presence/pass
        for f in ['proofread-v1.json','evaluation-v1.json']:
            p=d/f
            if not p.exists(): page['issues'].append('missing_'+f)
            else:
                try:
                    if json.loads(read(p)).get('pass') is not True: page['issues'].append('nonpassing_'+f)
                except Exception: page['issues'].append('invalid_'+f)
        pages.append(page)
        priority.extend((slug,i) for i in page['issues'])
    return {'canonical':CANONICAL,'count':len(pages),'priority_issue_count':len(priority),'pages':pages}

def write_report(rep):
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (REPORT_DIR/'m28p-audit.json').write_text(json.dumps(rep,ensure_ascii=False,indent=2),encoding='utf-8')
    lines=['# M28P audit','',f"Pages: {rep['count']}",f"Priority issues: {rep['priority_issue_count']}",'']
    for p in rep['pages']:
        status='PASS' if not p['issues'] else 'FAIL'
        lines.append(f"## {p['order']}. {p['word']} (`{p['slug']}`) — {status}")
        if p['issues']:
            for i in p['issues']: lines.append(f"- {i}")
        lines.append('')
    (REPORT_DIR/'m28p-audit.md').write_text('\n'.join(lines),encoding='utf-8')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--format',choices=['json','md','both'],default='both')
    ap.add_argument('--no-fail',action='store_true')
    args=ap.parse_args(); rep=audit(); write_report(rep)
    if args.format in ['json','both']: print(json.dumps({'pages':rep['count'],'priority_issue_count':rep['priority_issue_count']},ensure_ascii=False,indent=2))
    if rep['priority_issue_count'] and not args.no_fail: raise SystemExit(1)
if __name__=='__main__': main()
