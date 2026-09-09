#!/usr/bin/env python3
"""Registar um rascunho ou publicar uma atividade após aprovação do professor."""
import argparse
import http.cookiejar
import json
import os
import urllib.error
import urllib.request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    register = commands.add_parser('register')
    register.add_argument('slug')
    register.add_argument('--metadata', required=True)
    publish = commands.add_parser('publish')
    publish.add_argument('code')
    publish.add_argument('--approved', action='store_true', help='A atividade foi explicitamente aprovada pelo professor.')
    args = parser.parse_args()
    if args.command == 'publish' and not args.approved:
        parser.error('Publicar exige aprovação explícita do professor e --approved.')
    # This helper only bootstraps through the documented local trust channel.
    base = 'http://127.0.0.1:8777'
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    try:
        with opener.open(base + '/api/teacher-bootstrap', timeout=10):
            pass
        if args.command == 'register':
            with open(args.metadata, encoding='utf-8') as f:
                data = json.load(f)
            data['slug'] = args.slug
            path = '/api/learning/activities'
        else:
            data = {}
            path = '/api/learning/activities/' + urllib.parse.quote(args.code, safe='') + '/publish'
        request = urllib.request.Request(base + path, data=json.dumps(data).encode(),
                                         headers={'Content-Type': 'application/json'}, method='POST')
        with opener.open(request, timeout=30) as response:
            activity = json.load(response)
        print(json.dumps({'code': activity['code'], 'published': activity['published'],
                          'preview': base + '/' + activity['code'],
                          'url': 'https://pagecraft.infantinho.xyz/' + activity['code'] if activity['published'] else None}, ensure_ascii=False, indent=2))
    except urllib.error.HTTPError as error:
        parser.exit(1, f'PageCraft recusou a operação (HTTP {error.code}). Verifica os dados e a autorização.\n')
    except urllib.error.URLError:
        parser.exit(1, 'PageCraft indisponível em 127.0.0.1:8777. Verifica o serviço antes de repetir.\n')


if __name__ == '__main__':
    main()
