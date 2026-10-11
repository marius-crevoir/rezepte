(() => {
  'use strict';
  const slug = document.body.dataset.slug;
  const servings = Number(document.body.dataset.servings);
  const KEY = 'unsere-kueche-favorites-v1';
  const getFavorites = () => { try { return JSON.parse(localStorage.getItem(KEY) || '[]'); } catch { return []; } };
  const setFavorites = values => { try { localStorage.setItem(KEY, JSON.stringify(values)); } catch { /* ignore */ } };
  const favorite = document.getElementById('favoriteRecipe');
  const isFavorite = () => getFavorites().includes(slug);
  function syncFavorite() {
    const liked = isFavorite();
    favorite.setAttribute('aria-pressed', String(liked));
    favorite.querySelector('span').textContent = liked ? 'Gespeichert' : 'Merken';
  }
  favorite.addEventListener('click', () => {
    const values = getFavorites();
    setFavorites(isFavorite() ? values.filter(v => v !== slug) : [...values, slug]);
    syncFavorite();
  });
  syncFavorite();

  const maxServings = 20;
  let currentServings = servings;
  const output = document.getElementById('servingsOutput');
  const formatter = new Intl.NumberFormat('de-CH', { maximumFractionDigits: 2 });
  function formatAmount(amount) { return formatter.format(Math.round(amount * 100) / 100); }
  function refresh() {
    output.textContent = String(currentServings);
    document.getElementById('decreaseServings').disabled = currentServings <= 1;
    document.getElementById('increaseServings').disabled = currentServings >= maxServings;
    document.querySelectorAll('[data-base-amount]').forEach(span => {
      const value = Number(span.dataset.baseAmount) * currentServings / servings;
      span.textContent = `${formatAmount(value)}${span.dataset.unit ? ' ' + span.dataset.unit : ''} `;
    });
  }
  document.getElementById('decreaseServings').addEventListener('click', () => { currentServings = Math.max(1, currentServings - 1); refresh(); });
  document.getElementById('increaseServings').addEventListener('click', () => { currentServings = Math.min(maxServings, currentServings + 1); refresh(); });
  refresh();
  if ('serviceWorker' in navigator && location.protocol.startsWith('http')) {
    window.addEventListener('load', () => navigator.serviceWorker.register('../../sw.js').catch(() => {}));
  }
})();
