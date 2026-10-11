#!/usr/bin/env python3
"""Generates public recipe pages and listing from content/recipes/*.json.

Run: python3 scripts/build.py
Site has no runtime/backend dependency. Works on GitHub Pages.
"""
import hashlib
import html
import json
import os
import re
import shutil
from pathlib import Path
from urllib.parse import quote, urljoin, urlencode

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'content' / 'recipes'
OUTPUT = ROOT / 'rezepte'
BASE_URL = os.environ.get('SITE_URL', 'https://marius-crevoir.github.io/rezepte/').rstrip('/') + '/'


def escape(value):
    return html.escape(str(value), quote=True)


def pretty_amount(num):
    if num is None:
        return ''
    return f'{num:g}'.replace('.', ',')


def ingredient_text(ingredient):
    qty = pretty_amount(ingredient.get('amount'))
    parts = [qty, ingredient.get('unit', ''), ingredient['name']]
    return ' '.join(str(p) for p in parts if p)


def safe_script_json(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c').replace('&', '\\u0026')


def validate_recipe(r, path):
    needed = ('slug', 'title', 'subtitle', 'category', 'minutes', 'servings', 'ingredients', 'steps', 'image', 'author')
    for key in needed:
        if key not in r:
            raise ValueError(f'{path.name}: missing {key}')
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', r['slug']):
        raise ValueError(f'{path.name}: invalid slug {r["slug"]}')
    if r['slug'] != path.stem:
        raise ValueError(f'{path.name}: filename must match slug')
    if not (isinstance(r['servings'], int) and 1 <= r['servings'] <= 20):
        raise ValueError(f'{path.name}: servings should be 1–20')
    if not (isinstance(r['minutes'], int) and r['minutes'] > 0):
        raise ValueError(f'{path.name}: minutes must be positive integer')
    if not r['ingredients'] or not r['steps']:
        raise ValueError(f'{path.name}: ingredients and steps cannot be empty')
    for i in r['ingredients']:
        if not isinstance(i.get('name'), str) or not i['name']:
            raise ValueError(f'{path.name}: ingredient missing name')
        amount = i.get('amount')
        if amount is not None and (not isinstance(amount, (float, int)) or amount <= 0):
            raise ValueError(f'{path.name}: amount must be positive or null')
    image = r['image']
    if not (image.startswith('https://') or (image.startswith('assets/') and '..' not in image)):
        raise ValueError(f'{path.name}: image must be a local assets/ path or https URL')
    if image.startswith('assets/') and not (ROOT / image).is_file():
        raise ValueError(f'{path.name}: missing image {image}')


def detail_html(r):
    slug = r['slug']
    canonical = urljoin(BASE_URL, 'rezepte/' + quote(slug) + '/')
    picture_url = r['image'] if r['image'].startswith('https://') else urljoin(BASE_URL, r['image'])
    img_source = r['image'] if r['image'].startswith('https://') else '../../' + r['image']
    structured = {
        '@context': 'https://schema.org', '@type': 'Recipe',
        'name': r['title'], 'description': r['subtitle'],
        'author': {'@type': 'Organization', 'name': r['author']},
        'image': [picture_url], 'url': canonical,
        'recipeYield': f'{r["servings"]} Portionen',
        'totalTime': f'PT{r["minutes"]}M',
        'recipeCategory': r['category'],
        'recipeIngredient': [ingredient_text(i) for i in r['ingredients']],
        'recipeInstructions': [{'@type': 'HowToStep', 'text': step} for step in r['steps']]
    }
    if r.get('tags'):
        structured['keywords'] = ', '.join(r['tags'])
    ingredient_rows = []
    for idx, i in enumerate(r['ingredients']):
        amount = i.get('amount')
        qty = '' if amount is None else '<span data-base-amount="' + escape(amount) + '" data-unit="' + escape(i.get('unit', '')) + '">' + escape(pretty_amount(amount) + (' ' + i['unit'] if i.get('unit') else '') + ' ') + '</span>'
        ingredient_rows.append(f'<li><input type="checkbox" class="ingredient-check" id="ingredient-{idx}"><label class="ingredient-label" for="ingredient-{idx}">{qty}{escape(i["name"])}</label></li>')
    steps = ''.join(f'<li><span class="step-number" aria-hidden="true">{idx}</span><div class="step-copy"><h3>Schritt {idx}</h3><p>{escape(step)}</p></div></li>' for idx, step in enumerate(r['steps'], 1))
    badges = ''.join(f'<span>{escape(s)}</span>' for s in r.get('tags', []))
    tip_html = f'<aside class="tip-box"><strong>Unser Tipp</strong><p>{escape(r["tip"])}</p></aside>' if r.get('tip') else ''
    bring_url = 'https://api.getbring.com/rest/bringrecipes/deeplink?' + urlencode({'url': canonical, 'source': 'web', 'baseQuantity': r['servings'], 'requestedQuantity': r['servings']})
    return f'''<!doctype html>
<html lang="de-CH">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <meta name="theme-color" content="#f7f5f0"><meta name="description" content="{escape(r['subtitle'])}">
  <link rel="canonical" href="{escape(canonical)}"><link rel="manifest" href="../../manifest.webmanifest">
  <link rel="icon" href="../../assets/icon.svg" type="image/svg+xml"><link rel="apple-touch-icon" href="../../assets/icon-192.png">
  <link rel="stylesheet" href="../../assets/styles.css">
  <meta property="og:title" content="{escape(r['title'])} | Unsere Küche"><meta property="og:description" content="{escape(r['subtitle'])}"><meta property="og:image" content="{escape(picture_url)}">
  <script type="application/ld+json">{safe_script_json(structured)}</script>
  <title>{escape(r['title'])} – Unsere Küche</title>
</head>
<body class="page-detail" data-slug="{escape(slug)}" data-servings="{r['servings']}">
  <header class="site-header shell"><a class="brand" href="../../" aria-label="Unsere Küche – Startseite"><span class="brand-mark" aria-hidden="true"><span></span></span><span>unsere <strong>küche.</strong></span></a><nav class="header-actions" aria-label="Navigation"><a class="text-action" href="../../#rezepte">← Alle Rezepte</a></nav></header>
  <main class="detail-shell shell">
    <div class="breadcrumb"><a href="../../">Startseite</a><span>/</span><a href="../../#rezepte">Rezepte</a><span>/</span><span>{escape(r['category'])}</span></div>
    <section class="detail-header"><div><div class="eyebrow eyebrow-sub">{escape(r['category'])} · {r['minutes']} Minuten</div><h1 class="detail-title">{escape(r['title'])}</h1><p class="detail-intro">{escape(r['subtitle'])}</p><div class="detail-badges"><span>{r['minutes']} Min.</span><span>{escape(r.get('difficulty','Einfach'))}</span><span>{r['servings']} Portionen</span>{badges}</div><div class="detail-actions"><button class="detail-action" id="favoriteRecipe" type="button" aria-pressed="false"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20.8 8.4c0 4.3-8.8 10.1-8.8 10.1S3.2 12.7 3.2 8.4a4.7 4.7 0 0 1 8.8-2.2 4.7 4.7 0 0 1 8.8 2.2Z"/></svg><span>Merken</span></button><button class="detail-action" type="button" onclick="window.print()"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 9V3h12v6M6 18H4V9h16v9h-2M6 15h12v6H6z"/></svg>Drucken</button><a class="detail-action bring-hero-action" data-bring-link href="{escape(bring_url)}">Zutaten zu Bring! →</a></div></div><img class="detail-image" src="{escape(img_source)}" alt="Rezeptbild zu {escape(r['title'])}"></section>
    <div class="content-columns"><div><section class="ingredients-card" aria-labelledby="ingredientsHeading"><h2 id="ingredientsHeading">Zutaten.</h2><p class="ingredients-subtitle">Alles, was du dafür brauchst.</p><div class="servings-row"><span>Portionen</span><div class="stepper"><button type="button" id="decreaseServings" aria-label="Eine Portion weniger">−</button><output id="servingsOutput" aria-live="polite">{r['servings']}</output><button type="button" id="increaseServings" aria-label="Eine Portion mehr">+</button></div></div><ul class="ingredients-list">{''.join(ingredient_rows)}</ul><p class="ingredients-note">Mengen werden automatisch an die Portionszahl angepasst. Häkchen bleiben nur auf diesem Gerät erhalten, solange die Seite geöffnet ist.</p></section><aside class="bring-panel" aria-labelledby="bringTitle"><h3 id="bringTitle">Einkaufen mit Bring!</h3><p>Übertrage die Zutaten für die gewählte Portionszahl in deine Bring!-Einkaufsliste.</p><a class="bring-cta" data-bring-link href="{escape(bring_url)}">Zutaten zu Bring! hinzufügen →</a><p class="bring-quantity-note">Import für <span id="bringServings">{r['servings']}</span> Portionen.</p></aside></div>
    <section class="method" aria-labelledby="methodHeading"><div class="eyebrow eyebrow-sub">LOS GEHT'S</div><h2 id="methodHeading">So geht's.</h2><p class="method-subtitle">Schritt für Schritt zum fertigen Gericht.</p><ol class="method-steps">{steps}</ol>{tip_html}<a href="../../#rezepte" class="back-link">← Zurück zu allen Rezepten</a></section></div>
  </main><footer class="site-footer shell"><span>unsere küche. <span class="footer-muted">– ein gemeinsames Rezeptbuch</span></span><span>Mit Liebe und gutem Hunger.</span></footer>
  <script src="../../assets/detail.js" defer></script>
</body>
</html>
'''


def write_service_worker(recipes):
    pages = ['index.html', 'data/recipes.json', 'assets/styles.css', 'assets/app.js', 'assets/detail.js', 'assets/icon.svg', 'assets/icon-192.png', 'assets/icon-512.png', 'manifest.webmanifest']
    pages += [r['image'] for r in recipes if r['image'].startswith('assets/')]
    pages += [f'rezepte/{r["slug"]}/' for r in recipes]
    pages = list(dict.fromkeys(pages))
    version_input = ''.join(sorted(pages)) + (ROOT / 'assets' / 'styles.css').read_text() + json.dumps(recipes, ensure_ascii=False)
    version = hashlib.sha256(version_input.encode('utf-8')).hexdigest()[:12]
    sw = '''// Generated by scripts/build.py. Network-first for pages and recipe data.
const CACHE = 'unsere-kueche-VERSION';
const ASSETS = ASSETS_LIST;
const BASE = self.registration.scope;
self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(ASSETS.map(path => new URL(path, BASE)))));
  self.skipWaiting();
});
self.addEventListener('activate', event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k.startsWith('unsere-kueche-') && k !== CACHE).map(k => caches.delete(k)))));
  self.clients.claim();
});
self.addEventListener('fetch', event => {
  const request = event.request;
  if (request.method !== 'GET') return;
  const url = new URL(request.url);
  if (url.origin !== self.location.origin || !url.href.startsWith(BASE)) return;
  const isDynamic = request.mode === 'navigate' || url.pathname.endsWith('/data/recipes.json');
  event.respondWith((async () => {
    const cache = await caches.open(CACHE);
    if (isDynamic) {
      try { const response = await fetch(request); if (response.ok) cache.put(request, response.clone()); return response; }
      catch { return (await cache.match(request)) || (request.mode === 'navigate' ? await cache.match(new URL('index.html', BASE)) : Response.error()); }
    }
    const cached = await cache.match(request);
    if (cached) return cached;
    const response = await fetch(request);
    if (response.ok) cache.put(request, response.clone());
    return response;
  })());
});
'''
    (ROOT / 'sw.js').write_text(sw.replace('VERSION', version).replace('ASSETS_LIST', json.dumps(pages, ensure_ascii=False)), encoding='utf-8')


def main():
    paths = sorted(SOURCE.glob('*.json'))
    if not paths:
        raise SystemExit('Add at least one recipe to content/recipes/*.json')
    recipes = []
    seen = set()
    for path in paths:
        recipe = json.loads(path.read_text(encoding='utf-8'))
        validate_recipe(recipe, path)
        if recipe['slug'] in seen:
            raise ValueError(f'Duplicate slug: {recipe["slug"]}')
        seen.add(recipe['slug'])
        recipe.setdefault('tags', [])
        recipes.append(recipe)
    recipes.sort(key=lambda r: r['title'].casefold())
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    OUTPUT.mkdir()
    for recipe in recipes:
        page_dir = OUTPUT / recipe['slug']
        page_dir.mkdir()
        (page_dir / 'index.html').write_text(detail_html(recipe), encoding='utf-8')
    directory = ROOT / 'data'
    directory.mkdir(exist_ok=True)
    (directory / 'recipes.json').write_text(json.dumps(recipes, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    write_service_worker(recipes)
    print(f'Built {len(recipes)} recipes for {BASE_URL}')


if __name__ == '__main__':
    main()
