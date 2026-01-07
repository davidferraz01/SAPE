// static/js/filtros.js
(function ($) {
  const $menu = $('#filtroMenuLista');
  const $cards = $('.flex-item');
  const $noData = $('#no-cadastros');
  const selected = new Set();

  // 👇 NOVO: badge do total de notícias (se existir na página)
  const $newsCount = $('#qtd-noticias');

  if (!$menu.length) {
    $('#pesquisar').on('input', applyFilters);
    applyFilters();
    return;
  }

  const isNewsPage = $cards.find('#fonte').length > 0;
  const EMPTY_SOURCES_MATCHES_ALL = false;

  const norm = (s) => (s || '').toString().trim().toLowerCase();

  function getCardSources($card) {
    if (isNewsPage) {
      const v = ($card.find('#fonte').text() || '').trim();
      return v ? [norm(v)] : [];
    }

    const raw = ($card.attr('data-sources') || '').toString().trim();
    if (!raw) return [];
    return raw.split('|').map(norm).filter(Boolean);
  }

  // 👇 NOVO: atualiza o badge do título
  function updateNewsCount(count) {
    if (!$newsCount.length) return;
    $newsCount.text(count);
  }

  function applyFilters() {
    const q = norm($('#pesquisar').val());
    let anyVisible = false;

    // 👇 NOVO
    let visibleCount = 0;

    $cards.each(function () {
      const $c = $(this);

      const title = norm($c.find('#titulo').text());
      const desc = norm($c.find('#descricao').text());
      const sources = getCardSources($c);

      let matchSource = true;

      if (selected.size > 0) {
        if (isNewsPage) {
          matchSource = sources.some(s => selected.has(s));
        } else {
          if (sources.length === 0) {
            matchSource = EMPTY_SOURCES_MATCHES_ALL;
          } else {
            matchSource = Array.from(selected).every(sel => sources.includes(sel));
          }
        }
      }

      const sourcesText = sources.join(' ');
      const matchText = !q || title.includes(q) || desc.includes(q) || sourcesText.includes(q);

      if (matchSource && matchText) {
        $c.show();
        anyVisible = true;

        // 👇 NOVO
        visibleCount += 1;
      } else {
        $c.hide();
      }
    });

    $noData.toggle(!anyVisible);

    // 👇 NOVO: atualiza quantidade ao lado de "Notícias"
    updateNewsCount(visibleCount);

    updateBadge();
  }

  $menu.on('click', function (e) {
    e.stopPropagation();
  });

  $menu.on('click', 'a.dropdown-item', function (e) {
    e.preventDefault();

    const $a = $(this);
    const label = ($a.text() || '').trim();
    const key = norm(label);
    if (!key) return;

    if (selected.has(key)) {
      selected.delete(key);
      $a.removeClass('active').find('.check').remove();
    } else {
      selected.add(key);
      $a.addClass('active');
      if (!$a.find('.check').length) {
        $a.prepend('<i class="fas fa-check check mr-2"></i>');
      }
    }

    applyFilters();
  });

  function updateBadge() {
    const count = selected.size;
    const $btn = $('#filtroMenu');
    if (!$btn.length) return;

    $btn.attr('aria-label', count ? `Filtros (${count})` : 'Filtros');

    let $badge = $btn.find('.filter-badge');
    if (!$badge.length) {
      $badge = $('<span class="filter-badge badge badge-primary ml-1" style="vertical-align: middle;"></span>');
      $btn.append($badge);
    }

    if (count) $badge.text(count).show();
    else $badge.hide();
  }

  $('#pesquisar').on('input', applyFilters);

  applyFilters();
})(jQuery);
