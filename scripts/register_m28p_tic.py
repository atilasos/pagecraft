#!/usr/bin/env python3
"""Regista v3 para revisão e retira rascunhos v2 pela API canónica.

Sem --apply, apenas valida e mostra o plano. Nunca publica atividades.
"""
import argparse
import http.cookiejar
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from server.api.learning import ActivityInput


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    paths=sorted((ROOT/'drafts/m28p-v3').glob('*/*-activity.json'))
    data=[ActivityInput.model_validate_json(p.read_text()).model_dump() for p in paths]
    if len(data)!=168:
        parser.error('São necessárias as 168 miniatividades geradas antes do registo.')
    for item in data:
        for suffix in ['.html','-docspec.json','-design-spec.json','.md']:
            if not (ROOT/'drafts'/(item['slug']+suffix)).is_file():
                parser.error('Artefacto em falta: '+item['slug']+suffix)
    opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    base='http://127.0.0.1:8777'
    def api(path,body=None):
        request=urllib.request.Request(base+path,data=json.dumps(body).encode() if body is not None else None,
            headers={'Content-Type':'application/json'} if body is not None else {})
        with opener.open(request,timeout=30) as response:
            return json.load(response) if response.status!=204 else None
    api('/api/teacher-bootstrap')
    items=api('/api/learning/activities?include_archived=true')
    previous=[item for item in items if item['slug'].startswith('m28p-v2-') and not item['published'] and not item.get('archived_at')]
    if not args.apply:
        print(json.dumps(dict(register=len(data),retire=[i['slug'] for i in previous],applied=False),ensure_ascii=False,indent=2))
        return
    # Só retirar o conjunto anterior depois de confirmar todos os novos.
    registered=[api('/api/learning/activities',item) for item in data]
    if any(item.get('archived_at') for item in registered):
        raise RuntimeError('O conjunto v3 já contém uma versão retirada; rever manualmente.')
    for item in previous:
        api('/api/learning/activities/'+item['code']+'/archive',{})
    current=api('/api/learning/activities')
    if len([item for item in current if item['slug'].startswith('m28p-v3-')])!=168:
        raise RuntimeError('A leitura após o registo não confirma 168 atividades.')
    if any(item['slug'].startswith('m28p-v2-') for item in current):
        raise RuntimeError('Persistem percursos v2 na lista ativa.')
    # Um pedido sem cookie docente não pode obter nenhum destes conteúdos.
    for item in registered:
        if item['published']:
            continue
        try:
            urllib.request.urlopen(base+'/api/learning/activities/'+item['code']+'/content',timeout=10)
        except urllib.error.HTTPError as error:
            if error.code==404:
                continue
            raise
        raise RuntimeError('Rascunho acessível sem credencial docente: '+item['code'])
    manifest=dict(activities=[dict(slug=i['slug'],code=i['code'],published=i['published'],preview='https://estudio.infantinho.xyz/'+i['code']) for i in registered],
        retired=[dict(slug=i['slug'],code=i['code']) for i in previous],publicContentCheck=f"{sum(not i['published'] for i in registered)} drafts returned 404 without teacher cookie")
    (ROOT/'drafts/m28p-v3/registration.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(registered=len(registered),retired=len(previous),published=sum(i['published'] for i in registered),publicDrafts='denied'),ensure_ascii=False))


if __name__=='__main__':
    main()
