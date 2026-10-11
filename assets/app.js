(() => {
  'use strict';
  const grid = document.getElementById('recipeGrid');
  const filters = document.getElementById('categoryFilters');
  const search = document.getElementById('searchInput');
  const favoritesToggle = document.getElementById('favoriteToggle');
  const empty = document.getElementById('emptyState');
  const counter = document.getElementById('recipeCount');
  let recipes = [];
  let category = 'Alle';
  let favoritesOnly = false;
  const KEY = 'unsere-kueche-favorites-v1';
  const getFavorites = () => { try { return JSON.parse(localStorage.getItem(KEY) || '[]').filter(x => typeof x === 'string'); } catch { return []; } };
  const setFavorites = values => { try { localStorage.setItem(KEY, JSON.stringify(values)); } catch { /* storage not available */ } };
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const normalize = value => String(value ?? '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('de-CH');
  const heart = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20.8 8.4c0 4.3-8.8 10.1-8.8 10.1S3.2 12.7 3.2 8.4a4.7 4.7 0 0 1 8.8-2.2 4.7 4.7 0 0 1 8.8 2.2Z"/></svg>';
  const clock = '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3.5 2"/></svg>';

  function updateFavoriteCount() {
    const count = getFavorites().length;
    const pill = document.getElementById('favoritesCount');
    pill.textContent = String(count);
    pill.hidden = count === 0;
  }
  function drawCategories() {
    const categories = ['Alle', ...new Set(recipes.map(r => r.category))];
    filters.innerHTML = categories.map(c => `<button type="button" class="chip" data-category="${esc(c)}" aria-pressed="${c === category}">${esc(c)}</button>`).join('');
  }
  function draw() {
    const favorites = getFavorites();
    const query = normalize(search.value.trim());
    const shown = recipes.filter(r => {
      if (category !== 'Alle' && r.category !== category) return false;
      if (favoritesOnly && !favorites.includes(r.slug)) return false;
      return !query || normalize([r.title, r.subtitle, r.category, ...(r.tags || []), ...r.ingredients.map(i => i.name)].join(' ')).includes(query);
    });
    grid.innerHTML = shown.map(r => {
      const liked = favorites.includes(r.slug);
      const href = `rezepte/${encodeURIComponent(r.slug)}/`;
      return `<article class="recipe-card"><div class="recipe-image-wrap"><a href="${href}" aria-label="${esc(r.title)} ansehen"><img class="recipe-image" src="${esc(r.image)}" alt="Illustration: ${esc(r.title)}" loading="lazy"></a><button class="save-btn" type="button" data-favorite="${esc(r.slug)}" aria-label="${liked?'Aus Favoriten entfernen':'Als Favorit speichern'}" aria-pressed="${liked}">${heart}</button></div><div class="recipe-card-body"><div class="card-meta">${esc(r.category)} · ${esc(r.tags[0] || 'Rezept')}</div><h3 class="card-title"><a href="${href}">${esc(r.title)}</a></h3><p class="card-desc">${esc(r.subtitle)}</p><div class="card-footer"><strong>${clock} ${Number(r.minutes)} Min. <span aria-hidden="true">·</span> ${esc(r.difficulty)}</strong><a href="${href}" class="card-open" aria-label="${esc(r.title)} öffnen">↗</a></div></div></article>`;
    }).join('');
    counter.textContent = `${shown.length} ${shown.length === 1 ? 'Rezept' : 'Rezepte'}`;
    empty.hidden = shown.length !== 0;
    favoritesToggle.setAttribute('aria-pressed', String(favoritesOnly));
    filters.querySelectorAll('[data-category]').forEach(btn => btn.setAttribute('aria-pressed', String(btn.dataset.category === category)));
    updateFavoriteCount();
  }
  filters.addEventListener('click', ev => {
    const btn = ev.target.closest('[data-category]');
    if (!btn) return;
    category = btn.dataset.category;
    draw();
  });
  grid.addEventListener('click', ev => {
    const btn = ev.target.closest('[data-favorite]');
    if (!btn) return;
    const slug = btn.dataset.favorite;
    const items = getFavorites();
    setFavorites(items.includes(slug) ? items.filter(x => x !== slug) : [...items, slug]);
    draw();
  });
  search.addEventListener('input', draw);
  favoritesToggle.addEventListener('click', () => { favoritesOnly = !favoritesOnly; draw(); });
  document.getElementById('favoritesNav').addEventListener('click', () => { favoritesOnly = true; draw(); });
  document.getElementById('resetFilters').addEventListener('click', () => { favoritesOnly = false; category = 'Alle'; search.value = ''; draw(); });

  let deferredInstall;
  const installButton = document.getElementById('installBtn');
  const dialog = document.getElementById('installDialog');
  window.addEventListener('beforeinstallprompt', e => { e.preventDefault(); deferredInstall = e; });
  installButton.addEventListener('click', async () => {
    if (deferredInstall) {
      deferredInstall.prompt();
      try { await deferredInstall.userChoice; } catch { /* dismissed */ }
      deferredInstall = null;
    } else if (typeof dialog.showModal === 'function') dialog.showModal();
    else alert('Android: Im Browsermenü «App installieren» wählen. iPhone: In Safari «Teilen» → «Zum Home-Bildschirm».');
  });
  document.getElementById('closeDialog').addEventListener('click', () => dialog.close());
  document.getElementById('okDialog').addEventListener('click', () => dialog.close());
  dialog.addEventListener('click', e => { if (e.target === dialog) dialog.close(); });

  fetch('data/recipes.json', { cache: 'no-cache' }).then(res => {
    if (!res.ok) throw new Error('Rezeptdaten nicht erreichbar');
    return res.json();
  }).then(data => {
    recipes = Array.isArray(data) ? data : [];
    drawCategories(); draw();
  }).catch(() => {
    counter.textContent = 'Rezepte nicht verfügbar';
    empty.hidden = false;
    empty.querySelector('p').textContent = 'Die Rezeptdaten konnten nicht geladen werden. Bitte prüfe deine Verbindung.';
  });
  updateFavoriteCount();
  if ('serviceWorker' in navigator && location.protocol.startsWith('http')) {
    window.addEventListener('load', () => navigator.serviceWorker.register('./sw.js').catch(() => {}));
  }
})();
