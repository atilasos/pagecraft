#!/usr/bin/env python3
"""Gera miniatividades M28P para trabalho autónomo em TIC, sem publicar."""
from __future__ import annotations

import argparse
import base64
import html
import hashlib
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from jsonschema import Draft202012Validator
from server.activity_support import embed_activity_support
from server.bridge_snippet import ensure_bridge_lite
from server.typography import embed_activity_typography

GAMES = {
    'match': ('Palavra igual', 'Toca na palavra igual ao modelo.', 'Encontro a palavra igual ao modelo.'),
    'pairs': ('Ligar pares', 'Toca no desenho. Depois, toca na palavra.', 'Ligo o desenho à palavra.'),
    'hunt': ('Procurar palavras', 'Procura as palavras iguais ao modelo.', 'Encontro a palavra entre outras peças.'),
    'syllables': ('Montar com modelo', 'Toca nas peças para formar a palavra.', 'Junto as peças com o modelo.'),
    'gap': ('A peça que falta', 'Escolhe a peça que falta.', 'Completo a palavra com uma peça.'),
    'recall': ('Montar de memória', 'Forma a palavra. Podes ouvir outra vez.', 'Formo a palavra sem o modelo.'),
}
BASE = ROOT / 'drafts/m28p-v3'
ASSETS = ROOT / 'assets/m28p-tic'


def read_words():
    words = json.loads((BASE / 'words.json').read_text())
    if len(words) != 28 or sorted(w['order'] for w in words) != list(range(1, 29)):
        raise ValueError('A coleção precisa das 28 palavras ordenadas, sem repetições.')
    for word in words:
        if ''.join(word['syllables']) != word['label']:
            raise ValueError(f"Divisão inconsistente: {word['label']}")
    return words


def data_audio(name):
    return 'data:audio/mpeg;base64,' + base64.b64encode((ASSETS / 'audio' / f'{name}.mp3').read_bytes()).decode()


def illustrated(word):
    return dict(slug=word['slug'], label=word['label'], syllables=word['syllables'],
                image=(ASSETS / 'images' / f"{word['slug']}.svg").read_text())


def shuffled(values, rng):
    result = list(values)
    rng.shuffle(result)
    return result


def rounds_for(word, game, words):
    """Itens e posições estáveis; distratores só do repertório cumulativo."""
    earlier = [w for w in words if w['order'] < word['order']]
    # Flor tem uma sílaba. As peças desta palavra são letras, não sons.
    units = word['syllables'] if len(word['syllables']) > 1 else list(word['label'])
    rounds = []
    for index in range(4):
        rng = random.Random(f"{word['slug']}/{game}/{index}")
        prior = shuffled(earlier, rng)[:2]
        options = []
        answer = []
        item = dict(id=f'r{index + 1}', kind=game, prompt=GAMES[game][1], model=game != 'recall')
        if game == 'pairs':
            selected = shuffled([word] + prior[:min(index, 2)], rng)
            options = [dict(id=w['slug'], label=w['label'], image=illustrated(w)['image']) for w in selected]
            answer = [o['id'] for o in options]
            item['flipColumns'] = index % 2 == 1
        elif game in {'match', 'hunt'}:
            # Na primeira palavra, os distratores são fragmentos da própria
            # palavra, não vocabulário futuro nem pseudopalavras inventadas.
            labels = [w['label'] for w in prior] or list(dict.fromkeys(word['syllables']))[:2]
            labels = [word['label']] * (2 + index % 2 if game == 'hunt' else 1) + labels
            if game == 'hunt':
                labels += labels[-2:]
            options = [dict(id=f'o{i}', label=label) for i, label in enumerate(shuffled(labels, rng))]
            answer = [o['id'] for o in options if o['label'] == word['label']]
        elif game in {'syllables', 'recall'}:
            pieces = [dict(id=f'p{i}', label=label) for i, label in enumerate(units)]
            item['pieces'] = shuffled(pieces, rng)
            if len(pieces) > 1 and item['pieces'] == pieces:
                item['pieces'] = pieces[1:] + pieces[:1]
            answer = [p['id'] for p in pieces]
        elif game == 'gap':
            missing = index % len(units)
            item['gap'] = [label if i != missing else '' for i, label in enumerate(units)]
            labels = list(dict.fromkeys(units))
            # Não incluir outro valor fonético: pede-se a peça gráfica do
            # modelo. O áudio lê a palavra inteira, nunca sílabas isoladas.
            options = [dict(id=f'o{i}', label=label) for i, label in enumerate(shuffled(labels, rng))]
            answer = [o['id'] for o in options if o['label'] == units[missing]]
        item.update(options=options, answer=answer, unit='letter' if len(word['syllables']) == 1 else 'syllable')
        rounds.append(item)
    return rounds


def content_for(word, game, words):
    title, instruction, criterion = GAMES[game]
    slug = f"m28p-v3-{word['slug']}-{game}"
    return dict(slug=slug, word=illustrated(word), game=game, title=title,
                instruction=instruction, criteria=[criterion],
                audio={name: data_audio(key) for name, key in {
                    'start': 'start', 'instruction': game, 'word': word['slug'],
                    'hint': 'hint', 'success': 'success', 'retry': 'retry', 'finish': 'finish'}.items()},
                rounds=rounds_for(word, game, words))


def spec_for(data, word):
    hints = {
        'match': [('Olha para a palavra do modelo.', 'Olhem para a palavra do modelo.'), ('Compara o início e o fim.', 'Comparem o início e o fim.')],
        'pairs': [('Toca primeiro num desenho.', 'Toquem primeiro num desenho.'), ('Olha para o cartão da palavra.', 'Olhem para o cartão da palavra.')],
        'hunt': [('Compara um cartão de cada vez.', 'Comparem um cartão de cada vez.'), ('Procura também na linha seguinte.', 'Procurem também na linha seguinte.')],
        'syllables': [('Olha para a primeira peça do modelo.', 'Olhem para a primeira peça do modelo.'), ('Toca numa peça para a retirar.', 'Toquem numa peça para a retirar.')],
        'gap': [('Olha para o espaço vazio.', 'Olhem para o espaço vazio.'), ('Compara com a palavra inteira.', 'Comparem com a palavra inteira.')],
        'recall': [('Ouve a palavra outra vez.', 'Ouçam a palavra outra vez.'), ('Experimenta juntar as peças.', 'Experimentem juntar as peças.')],
    }
    units = []
    for item in data['rounds']:
        units.append(dict(summary=data['title'], textDescription=data['instruction'], duration=1,
            interaction=dict(state=[dict(name='resposta', type='matching' if data['game'] == 'pairs' else 'sorting' if data['game'] in {'syllables','recall'} else 'quiz', default=None)],
                render='Imagem original, cartões grandes e exemplo visual recuperável; áudio PT-PT incorporado por pedido.',
                transition='Selecionar, confirmar, receber pista e continuar após resposta, mesmo incorreta.',
                constraint='Comparar a escrita e o significado; conservar a ordem gráfica das peças.',
                assessment=data['criteria'][0] + ' Registar a resposta e o apoio, sem inferir leitura oral ou domínio.'),
            differentiation=dict(support='Modelo e peças comparáveis; primeira pista visual sempre disponível.',
                standard='Modelo nos jogos de associação e montagem apoiada; demonstração recuperável.',
                challenge='Retirar modelo opcional sem alterar as respostas nem introduzir palavras futuras.'),
            support=dict(objective=data['instruction'], criteria=data['criteria'], obstacles=[dict(id='comparar', label={'pt':'Quero uma pista'},
                hints=[dict(id=f'pista-{i}', text={'pt':{'individual':ind,'group':group}}) for i,(ind,group) in enumerate(hints[data['game']],1)])])))
    spec = dict(slug=data['slug'], topic=f"{data['title']} · {word['label']}", years=[1,2], order=word['order'],
        tags=['m28p','m28p-v3','tic','leitura','1ano','2ano'], ageRange='6-8 anos', duration=5,
        objectives=[data['criteria'][0], 'Usar a demonstração e as pistas para continuar com apoio pontual.'],
        curriculum={'ae':[],'competencies':['PA-A: Linguagens e textos','PA-F: Desenvolvimento pessoal e autonomia']},
        curriculumNote='Consolidação complementar ao método trabalhado com o professor titular; sem pretender substituir esse ensino.',
        materials=['Computador ou tablet', 'Auscultadores opcionais'], sessionFlow='Exemplo visual, quatro rondas curtas, reflexão facultativa.',
        support={'version':'m28p-tic-v3','languages':['pt'],'automaticAfterFailures':0}, units=units)
    Draft202012Validator(json.loads((ROOT/'server/pipeline/schemas/docspec.schema.json').read_text())).validate(spec)
    return spec


def bridge():
    source=(ROOT/'server/pipeline/prompts/template-base.html').read_text()
    return source[source.index('    window.PageCraftBridge = (function () {'):source.index('    /* Ouvir o embutidor')]


def render(data, spec):
    encoded=json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c').replace('\u2028','\\u2028').replace('\u2029','\\u2029')
    output=(ROOT/'scripts/templates/m28p-tic.html').read_text().replace('@@TITLE@@',html.escape(spec['topic'])).replace('@@CONTENT@@',encoded).replace('@@BRIDGE@@',bridge())
    return embed_activity_typography(ensure_bridge_lite(embed_activity_support(output,spec,data['slug'])))


def save_json(path, value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')


def build(word, game, words, check=False):
    data=content_for(word,game,words)
    spec=spec_for(data,word)
    output=render(data,spec)
    stem=data['slug']
    folder=BASE/word['slug']
    evidence_path=BASE/'evaluation.json'
    evidence=json.loads(evidence_path.read_text()) if evidence_path.exists() else {}
    verified=evidence.get('activities',{}).get(stem,{}).get('htmlSha256')==hashlib.sha256(output.encode()).hexdigest()
    artifacts={stem+'.html':output, stem+'-docspec.json':spec,
        stem+'-design-spec.json':dict(version=3, direction='Imagem, palavra e ação; uma ronda visível.',bodyPx=22,touchTargetPx=56,
            instructions='Áudio PT-PT incluído e demonstração por gestos, sem leitura obrigatória.',
            assets='SVG originais e áudio em data URLs; fonte incorporada; sem rede.',
            support='Com pistas, Passo a passo, Mais desafios; respostas preservadas.',game=game),
        stem+'-activity.json':dict(slug=stem,title=spec['topic'],year=1,duration=5,group='m28p-v3',languages=['pt'],requires_completion=True,
            criteria=[dict(id='criterio-1',pt=data['criteria'][0])]),
        stem+'-run-manifest.json':dict(slug=stem,status='draft-generated',word=word['label'],game=game,
            checks=dict(docspecSchema='passed',offlineAssets='embedded',browserEvaluation='passed' if verified else 'pending',teacherReview='pending'),publication='not-published')}
    if not check:
        folder.mkdir(parents=True,exist_ok=True)
        for name,value in artifacts.items():
            path=folder/name
            path.write_text(value) if isinstance(value,str) else save_json(path,value)
            alias=ROOT/'drafts'/name
            target=Path('m28p-v3')/word['slug']/name
            if alias.is_symlink() and alias.readlink()==target:
                continue
            if alias.exists() or alias.is_symlink():
                raise ValueError(f'Preservar ficheiro existente: {alias}')
            alias.symlink_to(target)
        guide=folder/'guia-docente.md'
        guide.write_text(f"# {word['label']} nas aulas de TIC\n\nSeis jogos de cerca de cinco minutos, para 1.º/2.º ano. O professor escolhe a palavra e confirma o repertório anterior. Podem ser repetidos ao longo do ano; não é uma sessão de duas horas num único jogo.\n\nComeçar por Palavra igual, Ligar pares e Procurar palavras. Seguir para Montar com modelo e A peça que falta. Montar de memória retira o modelo por defeito; ouvir é apoio declarado. Cada jogo tem quatro rondas com posições variadas. Na primeira palavra, pares trabalha um par e as escolhas usam fragmentos da própria palavra. Flor usa letras móveis por ter uma só sílaba.\n\nPreparação pontual: abrir o jogo, identificar a criança no host e mostrar os botões de ouvir, exemplo e continuar. O áudio incluído funciona sem voz instalada. Durante o jogo, não há conversa nem ditado obrigatório ao adulto. A reflexão é facultativa. A conclusão admite erros; observar as respostas e o apoio antes de decidir o próximo jogo.\n\nNota linguística: {word['phonologyNotes']}\n\nA voz lê palavras inteiras e instruções, nunca fonemas isolados. O jogo não avalia pronúncia nem comprova fluência. Montar peças é reconstrução gráfica, não escrita livre. O ensino de correspondências novas e a leitura de textos continuam com o professor titular.\n\nRever as imagens, ouvir as gravações e experimentar com a criança antes de aprovar cada atividade. Princípios e fontes em docs/m28p-principios-implementacao.md e docs/research/m28p-tic-autonomia-2026.md.\n")
        guide_alias=ROOT/'drafts'/(stem+'.md')
        if not guide_alias.exists():
            guide_alias.symlink_to(Path('m28p-v3')/word['slug']/'guia-docente.md')
    return dict(slug=stem,word=word['label'],game=game,rounds=len(data['rounds']),bytes=len(output.encode()))


def build_index(words):
    cards=[]
    for word in words:
        links=''.join(f'<a href="{word["slug"]}/m28p-v3-{word["slug"]}-{game}.html">{html.escape(title)}</a>' for game,(title,_,__) in GAMES.items())
        cards.append(f'<section><h2>{word["order"]}. {html.escape(word["label"])}</h2><div class="image">{illustrated(word)["image"]}</div><nav>{links}</nav></section>')
    output='''<!doctype html><html lang="pt-PT"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>28 palavras · revisão TIC</title><style>body{margin:auto;max-width:1200px;padding:24px;font:22px/1.5 "Century Gothic","Didact Gothic",sans-serif;background:#f8faf5;color:#243d48}h1{font-size:38px}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:20px}section{background:white;border:1px solid #b3c6c7;border-radius:24px;padding:20px}.image{height:140px;text-align:center}.image svg{height:100%;width:180px}a{display:flex;min-height:56px;align-items:center;color:#1b5265}a:focus-visible{outline:4px solid #315d9e}p{max-width:65ch}</style><h1>28 palavras nas aulas de TIC</h1><p>168 miniatividades para revisão docente. Seis jogos por palavra, com imagem, áudio incluído e demonstração. Cada jogo dura cerca de cinco minutos e pode ser repetido. Estes rascunhos aguardam a tua aprovação.</p><main>'''+''.join(cards)+'</main></html>'
    (BASE/'index.html').write_text(embed_activity_typography(output))
    # A página docente resolve os códigos pelo serviço, em vez de publicar
    # endereços locais de drafts ou guardar um segundo catálogo de códigos.
    teacher=output[:output.index('<main>')]+'''<p><a href="/teacher/activities.html">Atividades, aprovação e registos</a></p><details><summary>Preparar e escolher o próximo jogo</summary><p>Abre a palavra combinada com o professor titular. Mostra os botões de ouvir, exemplo e continuar uma vez. Usa auscultadores quando possível. Cada jogo pode ser repetido noutra aula; não precisas de fazer todos de seguida.</p><p>Começa por Palavra igual e Procurar palavras; apresenta Ligar pares com as palavras já trabalhadas. Passa a Montar com modelo e A peça que falta, e depois a Montar de memória. Flor usa letras móveis. Os pares da primeira palavra têm um único par.</p><p>A conclusão mostra respostas, incluindo erros. As ajudas usadas ficam nos registos. Reconstruir uma palavra não comprova leitura oral, escrita livre ou fluência. O ensino e a observação com o professor titular continuam fora destes jogos.</p></details><p id="status" role="status">A carregar os rascunhos…</p><main id="collection"></main><script type="application/json" id="words">@@WORDS@@</script><script>
const words=JSON.parse(document.getElementById('words').textContent);
const games=@@GAMES@@;
fetch('/api/learning/activities').then(r=>{if(!r.ok)throw Error('Entra na área do professor para rever.');return r.json()}).then(items=>{
const bySlug=new Map(items.map(item=>[item.slug,item]));let total=0;
for(const word of words){const section=document.createElement('section'),title=document.createElement('h2'),picture=document.createElement('div'),nav=document.createElement('nav');title.textContent=word.order+'. '+word.label;picture.className='image';picture.innerHTML=word.image;section.append(title,picture,nav);
for(const [game,label] of games){const item=bySlug.get('m28p-v3-'+word.slug+'-'+game);if(!item)continue;const link=document.createElement('a');link.textContent=label+' · '+(item.published?'Aprovada':'Rever');link.href='/'+item.code;nav.append(link);total++;}document.getElementById('collection').append(section);}
document.getElementById('status').textContent=total+' jogos disponíveis para rever. A aprovação de cada jogo faz-se em Atividades e progressos.';
}).catch(error=>document.getElementById('status').textContent=error.message);
</script>'''
    encoded=json.dumps([dict(slug=w['slug'],label=w['label'],order=w['order'],image=illustrated(w)['image']) for w in words],ensure_ascii=False).replace('<','\\u003c')
    teacher=teacher.replace('@@WORDS@@',encoded).replace('@@GAMES@@',json.dumps([[g,t[0]] for g,t in GAMES.items()],ensure_ascii=False))
    (ROOT/'server/static/teacher/m28p-tic.html').write_text(embed_activity_typography(teacher))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--word',choices=[w['slug'] for w in read_words()])
    parser.add_argument('--game',choices=list(GAMES))
    parser.add_argument('--validate-only',action='store_true')
    args=parser.parse_args()
    words=read_words()
    results=[build(w,g,words,args.validate_only) for w in words if not args.word or w['slug']==args.word for g in GAMES if not args.game or g==args.game]
    if not args.validate_only and not args.word and not args.game:
        build_index(words)
    print(json.dumps(dict(activities=len(results),rounds=sum(r['rounds'] for r in results),bytes=sum(r['bytes'] for r in results)),ensure_ascii=False))


if __name__=='__main__':
    main()
