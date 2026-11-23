#!/usr/bin/env python3
"""Gera miniatividades M28P para trabalho autónomo em TIC, sem publicar."""
from __future__ import annotations

import argparse
import base64
import html
import hashlib
import json
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from jsonschema import Draft202012Validator
from scripts.m28p_cycle import CYCLE_GAMES, MIN_ROUNDS, validate_cycle, image_choices, discover_rounds, near_syllables, newest_first, vocabulary_syllables, demo_word
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
    if not (ASSETS / 'audio' / f'{name}.mp3').is_file():
        raise ValueError(f'Áudio em falta: {name}. Executar prepare_m28p_tic_assets.py --audio.')
    return 'data:audio/mpeg;base64,' + base64.b64encode((ASSETS / 'audio' / f'{name}.mp3').read_bytes()).decode()


def svg(path):
    """SVG sem <title>: o nome acessível vem do template, e a dica nativa não revela a resposta."""
    text = path.read_text()
    text = re.sub(r'<title\b[^>]*>.*?</title>\s*', '', text, flags=re.S)
    return re.sub(r'\s(?:role="img"|aria-labelledby="[^"]*")', '', text)


def illustrated(word):
    return dict(slug=word['slug'], label=word['label'], syllables=word['syllables'],
                image=svg(ASSETS / 'images' / f"{word['slug']}.svg"))


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
        'listen-build': [('Toca em 🔊 e ouve outra vez.', 'Toquem em 🔊 e ouçam outra vez.'), ('Diz a palavra devagar. Qual é a primeira sílaba?', 'Digam a palavra devagar. Qual é a primeira sílaba?')],
        'read-choose': [('Lê a palavra devagar, sílaba a sílaba.', 'Leiam a palavra devagar, sílaba a sílaba.'), ('Olha para cada imagem. Qual é a imagem desta palavra?', 'Olhem para cada imagem. Qual é a imagem desta palavra?')],
        'sentence': [('Começa pela palavra com letra maiúscula.', 'Comecem pela palavra com letra maiúscula.'), ('Diz a frase em voz alta. Qual é a primeira palavra?', 'Digam a frase em voz alta. Qual é a primeira palavra?')],
        'discover': [('Junta sílabas e lê o que formaste.', 'Juntem sílabas e leiam o que formaram.'), ('Experimenta trocar a ordem das sílabas.', 'Experimentem trocar a ordem das sílabas.')],
    }
    units = []
    # As frases da turma podem levar Montar frases até quatro rondas: o apoio precisa de u1..u4.
    for item in data['rounds'] + [data['rounds'][-1]] * ((4 - len(data['rounds'])) if data['game'] == 'sentence' else 0):
        units.append(dict(summary=data['title'], textDescription=data['instruction'], duration=1,
            interaction=dict(state=[dict(name='resposta', type='matching' if data['game'] == 'pairs' else 'sorting' if data['game'] in {'syllables','recall','listen-build','sentence','discover'} else 'quiz', default=None)],
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
        materials=['Computador ou tablet', 'Auscultadores opcionais'], sessionFlow=f"Exemplo visual, {len(data['rounds'])} {'ronda curta' if len(data['rounds']) == 1 else 'rondas curtas'}, reflexão facultativa.",
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


def build(word, game, words, check=False, cycle_data=None):
    data=cycle_data if cycle_data is not None else content_for(word,game,words)
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
            support='Com ajuda, Sozinho, Consigo ajudar um amigo; respostas preservadas.',game=game),
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
        guide=folder/(stem+'-guia-docente.md' if cycle_data else 'guia-docente.md')
        guide.write_text(f"# {word['label']} nas aulas de TIC\n\nSeis jogos de cerca de cinco minutos, para 1.º/2.º ano. O professor escolhe a palavra e confirma o repertório anterior. Podem ser repetidos ao longo do ano; não é uma sessão de duas horas num único jogo.\n\nComeçar por Palavra igual, Ligar pares e Procurar palavras. Seguir para Montar com modelo e A peça que falta. Montar de memória retira o modelo por defeito; ouvir é apoio declarado. Cada jogo tem quatro rondas com posições variadas. Na primeira palavra, pares trabalha um par e as escolhas usam fragmentos da própria palavra. Flor usa letras móveis por ter uma só sílaba.\n\nPreparação pontual: abrir o jogo, identificar a criança no host e mostrar os botões de ouvir, exemplo e continuar. O áudio incluído funciona sem voz instalada. Durante o jogo, não há conversa nem ditado obrigatório ao adulto. A reflexão é facultativa. A conclusão admite erros; observar as respostas e o apoio antes de decidir o próximo jogo.\n\nNota linguística: {word['phonologyNotes']}\n\nA voz lê palavras inteiras e instruções, nunca fonemas isolados. O jogo não avalia pronúncia nem comprova fluência. Montar peças é reconstrução gráfica, não escrita livre. O ensino de correspondências novas e a leitura de textos continuam com o professor titular.\n\nRever as imagens, ouvir as gravações e experimentar com a criança antes de aprovar cada atividade. Princípios e fontes em docs/m28p-principios-implementacao.md e docs/research/m28p-tic-autonomia-2026.md.\n")
        if cycle_data:
            guide.write_text(cycle_guide(data, word))
        guide_alias=ROOT/'drafts'/(stem+'.md')
        if not guide_alias.exists():
            guide_alias.symlink_to(Path('m28p-v3')/word['slug']/guide.name)
    return dict(slug=stem,word=word['label'],game=game,rounds=len(data['rounds']),bytes=len(output.encode()))


def cycle_guide(data, word):
    """Guia docente de um jogo do ciclo, com o que cada nível mostra de facto."""
    game, rounds, demo = data['game'], data['rounds'], data['demo']
    count = f"{len(rounds)} {'ronda' if len(rounds) == 1 else 'rondas'}, cerca de cinco minutos."
    if game == 'listen-build':
        body = ("A criança ouve uma palavra e monta-a com sílabas, sem a ver escrita. Há duas ou três sílabas a mais, da mesma família. "
                "«Com ajuda» mostra a palavra dividida em sílabas; «Sozinho» mostra o botão de ouvir e um espaço por sílaba; «Consigo ajudar um amigo» mostra só o botão de ouvir. "
                f"Palavras, uma por ronda: {', '.join('«' + r['target']['label'] + '»' for r in rounds)}.")
    elif game == 'read-choose':
        body = ("A criança lê uma palavra e escolhe a imagem certa entre três. «Com ajuda» mostra a palavra dividida em sílabas e deixa ouvi-la; "
                "«Sozinho» mostra a palavra inteira e deixa ouvi-la; «Consigo ajudar um amigo» mostra só a palavra escrita. Ouvir fica registado como ajuda. "
                f"Palavras, uma por ronda: {', '.join('«' + r['target']['label'] + '»' for r in rounds)}.")
    elif game == 'sentence':
        listed = ' / '.join(f"«{r['target']['text']}»" for r in rounds)
        # A lista termina numa citação com pontuação própria: não acrescentar outro ponto.
        alternatives = [r for r in rounds if r.get('alternatives')]
        equivalent = ''
        if alternatives:
            example = ' '.join(alternatives[0]['alternatives'][0]) + alternatives[0]['target']['text'][-1]
            equivalent = f"Quando duas ordens dizem o mesmo (por exemplo, «{example}»), as duas contam como certas. "
        body = ("A criança ordena as palavras de uma frase. «Com ajuda» mostra a imagem, a frase escrita com as palavras separadas e o botão de ouvir; "
                "«Sozinho» mostra a imagem, o botão de ouvir e um espaço por palavra; «Consigo ajudar um amigo» mostra só o botão de ouvir. "
                f"Frases, uma por ronda: {listed} {equivalent}"
                "Na página da turma, podes guardar as frases ditadas pelas crianças e projetá-las no Quadro. Quando a turma joga numa sessão, até quatro frases da turma surgem primeiro, "
                "completadas pelas frases fixas. «Com ajuda» mostra as palavras da frase da turma. As frases da turma só têm leitura em voz alta "
                "quando o computador tem uma voz pt-PT instalada; sem essa voz, em «Sozinho» e «Consigo ajudar um amigo», o botão de ouvir é substituído "
                "por «Ver a frase», que mostra a frase escrita; essa ação fica registada.")
    else:
        hidden = ' / '.join(', '.join('«' + w['label'] + '»' for w in r['lexicon']) for r in rounds)
        body = ("Em cada ronda há duas ou três palavras escondidas; o tabuleiro tem só as sílabas dessas palavras e, quando possível, uma sílaba a mais. "
                f"Palavras escondidas (as rondas estão separadas por « / »): {hidden}. A criança vê quantas já encontrou na ronda (por exemplo, «Encontraste 1 de {len(rounds[0]['lexicon'])}.»; o total é o de cada ronda); "
                "a ronda acaba quando as encontra todas ou quando toca em «Não encontro mais palavras», que mostra as que faltavam. "
                "«Com ajuda» mostra a imagem (quando existe) e o som de cada palavra escondida; «Sozinho» mostra quantas sílabas tem cada uma; "
                "«Consigo ajudar um amigo» mostra só quantas são. Uma combinação fora da lista recebe «não está escondida».")
        used_new = [w['label'] for r in rounds for w in r['lexicon'] if w.get('newIn') == word['slug']]
        if not data.get('newWords'):
            body += f" «{word['label']}» não traz palavras novas: este jogo revê palavras de palavras-chave anteriores."
        elif not used_new:
            body += (f" As palavras novas de «{word['label']}» ({', '.join(data['newWords'])}) não cabem num tabuleiro honesto; "
                     "trabalha-as nos outros jogos.")
        without = sum(1 for r in rounds if not r.get('extra'))
        if without:
            body += ((" Nesta ronda" if len(rounds) == 1 else " Numa das rondas") + " não há sílaba a mais: qualquer sílaba disponível formaria outra palavra que não está escondida."
                     if without == 1 else f" Em {without} rondas não há sílaba a mais: qualquer sílaba disponível formaria outra palavra que não está escondida.")
        celebrated = sorted({seq.replace('·', '') for r in rounds for seq in r.get('celebrate', [])})
        if celebrated:
            body += (f" Se a criança formar {', '.join('«' + w + '»' for w in celebrated)}, recebe «é uma palavra! Não estava escondida, "
                     "mas descobriste-a.» (com ★), sem contar para o jogo.")
        extra = sorted({w for r in rounds for w in r.get('warnings', [])} - set(celebrated))
        if extra:
            body += (f" Com estas peças também se formam formas raras que o dicionário aceita ({', '.join(extra)}); "
                     "recebem a resposta neutra «não está escondida». "
                     "Podem não ser conhecidas das crianças. Se uma criança as encontrar, aproveita para conversar sobre o que significam, "
                     "por exemplo no Conselho de Cooperação ou no Texto Livre.")
    if game == 'sentence':
        example = f"A demonstração usa «{demo['target']['text']}.», que não é uma das frases, e mostra os mesmos botões do jogo."
    elif demo['target']['label'] != word['label']:
        example = (f"A demonstração usa a palavra-chave anterior «{demo['target']['label']}» («{word['label']}» não tem o número de sílabas "
                   "deste jogo); essa palavra não é uma das rondas, e a demonstração mostra os mesmos botões do jogo.")
    else:
        example = f"A demonstração usa a palavra-chave «{demo['target']['label']}», que não é uma das rondas, e mostra os mesmos botões do jogo."
    keeps = "Ouvir, ver a demonstração e mudar de ajuda conservam o trabalho." if game == 'read-choose' else \
        "Ouvir, ver a demonstração, desfazer e mudar de ajuda conservam o trabalho."
    return (f"# {data['title']} · {word['label']}\n\n{count} {body}\n\n{example} {keeps} "
            "A criança pode continuar depois de confirmar, mesmo com erro.\n\n"
            "Os registos descrevem ações e ajudas usadas; não certificam leitura nem fluência. No fim, em «Consigo ajudar um amigo», "
            "aparece um convite escrito facultativo para partilhar com um amigo, que não é registado. "
            "Revê as imagens e ouve as gravações antes de usar com a turma.\n")

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


def cycle_content(word, game, pool, lexicon=None):
    """Conteúdo de um jogo do ciclo. A palavra-chave fica reservada para a demonstração."""
    title, instruction, criterion = CYCLE_GAMES[game]
    slug = f"m28p-ciclo-{word['slug']}-{game}"
    seed = lambda index: random.Random(f'{slug}/{index}')
    def resource(item):
        result = dict(item, audio=data_audio(item['slug']))
        needs_image = item.get('picturable', False) or 'text' in item
        path = ASSETS/'images'/(item['slug']+'.svg')
        if needs_image and not path.is_file():
            raise ValueError(f"Imagem em falta: {path}")
        result['image'] = svg(path) if needs_image else ''
        return result
    def pieces_for(labels):
        """Peças identificadas pelo texto: uma republicação nunca troca o sentido de uma resposta guardada."""
        seen, result = {}, []
        for label in labels:
            seen[label] = seen.get(label, 0) + 1
            result.append(dict(id=f"{label}#{seen[label]}", label=label))
        return result
    def mixed(pieces, rng, answers):
        """Baralha sem deixar uma resposta aceite em peças seguidas, em qualquer posição."""
        result = list(pieces)
        def solved(order):
            labels = [p['label'] for p in order]
            return any(labels[i:i + len(answer)] == answer for answer in answers for i in range(len(labels) - len(answer) + 1))
        for _ in range(200):
            rng.shuffle(result)
            if not solved(result):
                break
        return result
    keyword = resource(dict(pool['keyword'], slug=word['slug']))
    syllables = vocabulary_syllables(pool)
    picturable = [resource(w) for w in pool['words'] if w['picturable']]
    conflicts = pool['visualConflicts']
    rounds, demo = [], None
    if game in ('listen-build', 'discover'):
        sample = demo_word(pool, 2, 3 if game == 'discover' else 6)
        example = keyword if sample['slug'] == word['slug'] else resource(sample)
    if game == 'listen-build':
        for index, item in enumerate(newest_first(pool, lambda w: len(w['syllables']) >= 2, {sample['slug']})[:4]):
            rng = seed(index)
            units = item['syllables']
            extra = near_syllables(units, pool['families'], rng, 3 if len(units) <= 2 else 2, syllables)
            pieces = pieces_for(units + extra)
            rounds.append(dict(id=f"ouvir-{item['slug']}", target=resource(item), unit='syllable', length=len(units),
                               answer=[p['id'] for p in pieces[:len(units)]], pieces=mixed(pieces, rng, [units])))
        extra = near_syllables(sample['syllables'], pool['families'], seed('demo'), 2, syllables)
        demo = dict(target=example, pieces=[p['label'] for p in mixed(pieces_for(sample['syllables'] + extra), seed('demo'), [sample['syllables']])],
                    audio=example['audio'])
    elif game == 'read-choose':
        usage = {}
        for item in newest_first(pool, lambda w: w['picturable']):
            if len(rounds) == 4:
                break
            rng = seed(len(rounds))
            choices = image_choices(resource(item), picturable, conflicts, rng, usage)
            if not choices:
                continue
            for other in choices[1:]:
                usage[other['slug']] = usage.get(other['slug'], 0) + 1
            usage[item['slug']] = usage.get(item['slug'], 0) + 1
            options = [dict(id=w['slug'], label=w['label'], image=w['image']) for w in choices]
            rng.shuffle(options)
            rounds.append(dict(id=f"ler-{item['slug']}", target=resource(item), unit='syllable', options=options, answer=[item['slug']]))
        choices = image_choices(keyword, picturable, conflicts, seed('demo'))
        demo = dict(target=keyword, options=[dict(label=w['label'], image=w['image']) for w in choices], audio=keyword['audio']) if choices else None
    elif game == 'sentence':
        own = [s for s in pool['sentences'] if s['newIn'] == word['slug']]
        earlier = [s for s in reversed(pool['sentences']) if s['newIn'] != word['slug']]
        for index, item in enumerate((own + earlier)[:4]):
            rng = seed(index)
            pieces = pieces_for(item['tokens'])
            answers = [item['tokens'], *item.get('alternatives', [])]
            rounds.append(dict(id=item['slug'], target=resource(item), unit='word', length=len(item['tokens']),
                               answer=[p['id'] for p in pieces],
                               alternatives=item.get('alternatives', []), pieces=mixed(pieces, rng, answers)))
        tokens = [pool['keyword']['article'].capitalize(), word['label']]
        demo = dict(target=dict(text=' '.join(tokens), tokens=tokens, image=keyword['image']), pieces=tokens[::-1],
                    audio=data_audio(f"exemplo-{word['slug']}"))
    else:
        groups = discover_rounds(pool, random.Random(word['slug']), lexicon, reserved={sample['slug']})
        for index, group in enumerate(groups):
            # Nenhuma palavra escondida aparece já montada em peças seguidas.
            pieces = mixed(pieces_for(group['pieces']), seed(index), [w['syllables'] for w in group['hidden']])
            excluded = {e['label'] for e in pool.get('excluded', [])}
            rounds.append(dict(id='descobrir-' + '-'.join(w['slug'] for w in group['hidden']), unit='syllable', extra=group['extra'],
                               target=resource(group['hidden'][0]), warnings=[w for w in group['warnings'] if w not in excluded],
                               # As exclusões do professor já não entram em real_words; o filtro só protege dados antigos.
                               celebrate=[seq for seq in group['celebrate'] if seq.replace('·', '') not in excluded],
                               lexicon=[resource(w) for w in group['hidden']], length=3, pieces=pieces))
        extra = near_syllables(sample['syllables'], pool['families'], seed('demo'), 1, syllables)
        demo = dict(target=example, pieces=[p['label'] for p in mixed(pieces_for(sample['syllables'] + extra), seed('demo'), [sample['syllables']])],
                    audio=example['audio'])
    if len(rounds) < MIN_ROUNDS[game] or demo is None:
        need = MIN_ROUNDS[game]
        why = " Cada alvo requer 2 distratores sem conflitos visuais entre as opções." if game == 'read-choose' else ''
        return None, f"Apenas {len(rounds)} rondas possíveis; são necessárias pelo menos {need}.{why}"
    for r in rounds:
        r.update(kind=game, prompt=instruction, model=False)
        r.setdefault('options', [])
        r.setdefault('answer', [])
    return dict(slug=slug, word=illustrated(word), game=game, title=title, instruction=instruction, criteria=[criterion],
                rounds=rounds, demo=demo, newWords=[w['label'] for w in pool['newWords']],
                audio={k: data_audio(v) for k, v in dict(start='start', instruction=game, word=word['slug'], hint='hint',
                                                          success='success', retry='retry', finish='finish', correct='correct',
                                                          tryagain='tryagain', found='found', allfound='allfound', realword='realword').items()}), None


def build_cycle(words, args, lexicon=None):
    pools=validate_cycle(json.loads((BASE/'cycle.json').read_text()),words,lexicon)
    report=[]
    for word in words:
        if word['slug'] not in pools or (args.word and args.word!=word['slug']):
            continue
        for game in CYCLE_GAMES:
            if args.game and args.game!=game:
                continue
            data,reason=cycle_content(word,game,pools[word['slug']],lexicon)
            if reason and not args.validate_only:
                stem=f"m28p-ciclo-{word['slug']}-{game}"
                for path in (BASE/word['slug']).glob(stem+'*'):
                    path.unlink()
                for path in (ROOT/'drafts').glob(stem+'*'):
                    if path.is_symlink():
                        path.unlink()
            entry=dict(word=word['slug'],game=game,status='omitted',reason=reason) if reason else dict(build(word,game,words,args.validate_only,data),status='generated')
            entry['keyword']=word['slug']
            warnings=sorted({w for r in (data or {}).get('rounds',[]) for w in r.get('warnings',[])})
            if warnings:
                entry['realWordsOnBoard']=warnings
            report.append(entry)
    if not args.validate_only:
        # Uma geração filtrada (--word, --game) só substitui as suas entradas; as outras ficam no relatório.
        path=BASE/'cycle-generation-report.json'
        done={(e['keyword'],e['game']) for e in report}
        filtered=bool(args.word or args.game)
        # Uma geração completa substitui o relatório: palavras-chave retiradas de cycle.json deixam de ser publicáveis.
        previous=[e for e in (json.loads(path.read_text()) if path.exists() and filtered else []) if (e.get('keyword'),e['game']) not in done and e.get('keyword')]
        order={w['slug']:w['order'] for w in words}
        games=list(CYCLE_GAMES)
        save_json(path,sorted(previous+report,key=lambda e:(order[e['keyword']],games.index(e['game']))))
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cycle',action='store_true',help='Gerar apenas o ciclo, preservando a v3.')
    parser.add_argument('--word',choices=[w['slug'] for w in read_words()])
    parser.add_argument('--game',choices=list(GAMES)+list(CYCLE_GAMES))
    parser.add_argument('--validate-only',action='store_true')
    args=parser.parse_args()
    words=read_words()
    if args.cycle:
        from scripts.m28p_lexicon import load
        print(json.dumps(build_cycle(words,args,load()),ensure_ascii=False,indent=2))
        return
    if args.game in CYCLE_GAMES:
        parser.error('Os jogos do ciclo requerem --cycle.')
    results=[build(w,g,words,args.validate_only) for w in words if not args.word or w['slug']==args.word for g in GAMES if not args.game or g==args.game]
    if not args.validate_only and not args.word and not args.game:
        build_index(words)
    print(json.dumps(dict(activities=len(results),rounds=sum(r['rounds'] for r in results),bytes=sum(r['bytes'] for r in results)),ensure_ascii=False))


if __name__=='__main__':
    main()
