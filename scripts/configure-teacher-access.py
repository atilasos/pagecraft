#!/usr/bin/env python3
"""Protege só estudio.infantinho.xyz com Access; preserva aplicações partilhadas."""
import argparse
import json
import os
from pathlib import Path
import urllib.error
import urllib.request

HOST = 'estudio.infantinho.xyz'
EMAIL = 'atila.sos@gmail.com'
TEAM = 'inantinho.cloudflareaccess.com'
# Fornecedor já selecionado na aplicação Oficina OPM desta conta.
OTP_ID = '91ee49db-d93e-4d40-b23a-da6a3a24cad5'

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    config = dict(os.environ)
    for line in (Path.home()/'.config/cloudflare-publish/credentials.env').read_text().splitlines():
        if '=' in line and not line.lstrip().startswith('#'):
            key, value = line.split('=', 1)
            config.setdefault(key.strip(), value.strip().strip('\"').strip("'"))
    def api(path, method='GET', body=None):
        req = urllib.request.Request('https://api.cloudflare.com/client/v4'+path,
            data=json.dumps(body).encode() if body is not None else None,
            headers={'Authorization': 'Bearer '+config['CLOUDFLARE_API_TOKEN'], 'Content-Type': 'application/json'}, method=method)
        try:
            with urllib.request.urlopen(req, timeout=25) as response:
                data = json.load(response)
        except urllib.error.HTTPError as error:
            # Codes/messages only; no headers or request credentials.
            detail = json.loads(error.read()).get('errors', [])
            raise SystemExit(f'HTTP {error.code}: {detail}. Relê o estado antes de repetir.') from None
        if not data.get('success'):
            raise SystemExit('Operação não confirmada; relê o estado remoto.')
        return data['result']
    account = '/accounts/'+config['CLOUDFLARE_ACCOUNT_ID']
    if api('/zones/'+config['CLOUDFLARE_ZONE_ID'])['name'] != 'infantinho.xyz':
        raise SystemExit('Zona inesperada.')
    apps = api(account+'/access/apps')
    opm = next(a for a in apps if a.get('domain') == 'opm.infantinho.xyz')
    if OTP_ID not in opm.get('allowed_idps', []):
        raise SystemExit('Fornecedor esperado não encontrado na configuração existente.')
    existing = [a for a in apps if a.get('domain') == HOST]
    if existing:
        app = api(account+'/access/apps/'+existing[0]['id'])
    else:
        print(json.dumps({'hostname':HOST,'allowed_email':EMAIL,'login':'One-time PIN','session':'24h','apply':args.apply}))
        if not args.apply:
            return
        # Recheck immediately before mutation. Never update a shared policy.
        if any(a.get('domain') == HOST for a in api(account+'/access/apps')):
            raise SystemExit('Aplicação criada entretanto; reavaliar.')
        app = api(account+'/access/apps', 'POST', {
            'name':'PageCraft — Professor', 'type':'self_hosted', 'domain':HOST,
            'session_duration':'24h', 'allowed_idps':[OTP_ID],
            'auto_redirect_to_identity':True, 'app_launcher_visible':False,
            'service_auth_401_redirect':False, 'options_preflight_bypass':False,
            'policies':[{'name':'Professor PageCraft', 'decision':'allow', 'precedence':1,
                         'include':[{'email':{'email':EMAIL}}], 'exclude':[], 'require':[]}],
        })
        receipt = Path.home()/'.local/state/pagecraft-deploy/teacher-access.json'
        receipt.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
        receipt.write_text(json.dumps({'created_app_id':app['id'],'hostname':HOST},indent=2)+'\n')
        receipt.chmod(0o600)
    app = api(account+'/access/apps/'+app['id'])
    policies = api(account+'/access/apps/'+app['id']+'/policies')
    if (app.get('allowed_idps') != [OTP_ID] or len(policies) != 1
        or policies[0].get('decision') != 'allow'
        or policies[0].get('include') != [{'email':{'email':EMAIL}}]
        or policies[0].get('exclude') or policies[0].get('require')):
        raise SystemExit('A aplicação precisa de inspeção: política diferente da autorizada.')
    print(json.dumps({'id':app['id'],'domain':app['domain'],'aud':app['aud'],
                      'team':TEAM,'email':EMAIL,'verified':True}))
    if args.apply:
        directory=Path.home()/'.config/pagecraft'
        directory.mkdir(parents=True,exist_ok=True,mode=0o700)
        env=directory/'access.env'
        env.write_text(f'PAGECRAFT_ACCESS_TEAM_DOMAIN={TEAM}\nPAGECRAFT_ACCESS_AUD={app["aud"]}\nPAGECRAFT_ACCESS_EMAIL={EMAIL}\nPAGECRAFT_TEACHER_ORIGIN=https://{HOST}\nPAGECRAFT_PUBLIC_ORIGIN=https://pagecraft.infantinho.xyz\n')
        env.chmod(0o600)

if __name__ == '__main__':
    main()
