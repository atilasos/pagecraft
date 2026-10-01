#!/usr/bin/env python3
"""Acrescenta apenas pagecraft.infantinho.xyz ao túnel PageCraft confirmado."""
from pathlib import Path
import argparse
import copy
import json
import os
import urllib.request
import urllib.error

HOSTNAME = 'pagecraft.infantinho.xyz'
TUNNEL = '4fe7736a-2de5-4f0a-ac00-646495532eb3'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--apply', action='store_true')
args = parser.parse_args()
config = dict(os.environ)
file = Path.home()/'.config/cloudflare-publish/credentials.env'
if file.exists():
    for line in file.read_text().splitlines():
        if '=' in line and not line.lstrip().startswith('#'):
            key,value=line.split('=',1)
            config.setdefault(key.strip(),value.strip().strip('"').strip("'"))
for key in ['CLOUDFLARE_API_TOKEN','CLOUDFLARE_ACCOUNT_ID','CLOUDFLARE_ZONE_ID']:
    if not config.get(key):
        raise SystemExit('Falta '+key+' na credencial local protegida.')

def request(path, method='GET', data=None):
    req=urllib.request.Request('https://api.cloudflare.com/client/v4'+path,
        data=json.dumps(data).encode() if data is not None else None,
        headers={'Authorization':'Bearer '+config['CLOUDFLARE_API_TOKEN'],'Content-Type':'application/json'}, method=method)
    try:
        with urllib.request.urlopen(req,timeout=25) as response:
            result=json.load(response)
    except (urllib.error.HTTPError, urllib.error.URLError) as error:
        raise SystemExit(f'Operação {method} sem confirmação de sucesso. Relê o estado remoto antes de repetir. HTTP {getattr(error,"code","indisponível")}') from None
    if not result.get('success'):
        raise SystemExit('A API recusou a operação; inspeciona as permissões antes de repetir.')
    return result['result']

zone='/zones/'+config['CLOUDFLARE_ZONE_ID']
if request(zone)['name']!='infantinho.xyz':
    raise SystemExit('Zona diferente da autorizada.')
path='/accounts/'+config['CLOUDFLARE_ACCOUNT_ID']+'/cfd_tunnel/'+TUNNEL+'/configurations'
current=request(path)
before=current['config']
if not any(r.get('hostname')=='estudio.infantinho.xyz' for r in before['ingress']):
    raise SystemExit('O túnel não tem a rota PageCraft esperada; reavaliar destino.')
existing=request(zone+'/dns_records?name='+HOSTNAME)
expected=TUNNEL+'.cfargotunnel.com'
if any(r['type']!='CNAME' or r['content']!=expected or not r['proxied'] for r in existing):
    raise SystemExit('Hostname ocupado; nenhuma alteração realizada.')
route={'hostname':HOSTNAME,'service':'http://127.0.0.1:8777','originRequest':{}}
routes=[r for r in before['ingress'] if r.get('hostname')==HOSTNAME]
if routes and any(r!=route for r in routes):
    raise SystemExit('Rota existente diferente; nenhuma alteração realizada.')
after=copy.deepcopy(before)
if not routes:
    if after['ingress'][-1].get('hostname'):
        raise SystemExit('Falta a regra final do túnel.')
    after['ingress'].insert(-1,route)
print(json.dumps({'hostname':HOSTNAME,'origin':route['service'],'route_change':not bool(routes),'dns_change':not bool(existing),'teacher_access':'cookie HttpOnly, emparelhamento local','apply':args.apply},ensure_ascii=False))
if not args.apply:
    raise SystemExit(0)
backup=Path.home()/'.local/state/pagecraft-deploy'
backup.mkdir(parents=True,exist_ok=True,mode=0o700)
record={'tunnel':TUNNEL,'hostname':HOSTNAME,'before':before,'added_route':not bool(routes),'added_dns':not bool(existing)}
backup_file=backup/'hostname-before.json'
# Preserve the original reversal receipt across idempotent reruns.
if not backup_file.exists():
    backup_file.write_text(json.dumps(record,indent=2))
    backup_file.chmod(0o600)
if not routes:
    fresh=request(path)
    if fresh['version']!=current['version'] or fresh['config']!=before:
        raise SystemExit('O túnel mudou entretanto; nenhuma alteração realizada.')
    request(path,'PUT',{'config':after})
    if request(path)['config']!=after:
        raise SystemExit('Não foi possível verificar a rota; parar e inspecionar.')
if not existing:
    # Recheck DNS immediately before creating it.
    if request(zone+'/dns_records?name='+HOSTNAME):
        raise SystemExit('O DNS mudou entretanto; a rota foi guardada, mas o DNS exige inspeção.')
    created=request(zone+'/dns_records','POST',{'type':'CNAME','name':HOSTNAME,'content':expected,'proxied':True,'ttl':1})
    receipt=json.loads(backup_file.read_text())
    receipt['created_dns_id']=created['id']
    backup_file.write_text(json.dumps(receipt,indent=2))
print('Rota e DNS verificados. Estado anterior em '+str(backup_file))
