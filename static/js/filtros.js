// static/js/filtros.js
(function ($) {
  const $menu = $('#filtroMenuLista');                  // dropdown-menu
  const $items = $menu.find('a.dropdown-item');         // opções de fonte
  const $cards = $('.flex-item');                       // cards das notícias
  const $noData = $('#no-cadastros');                   // "Não há novas Notícias."
  const selected = new Set();

  // Ajuda a obter a "fonte" de cada card (funciona com seu HTML atual).
  function getCardSource($card) {
    // Dentro de cada card há um <p id="fonte"> com a fonte
    const $p = $card.find('#fonte'); // id repetido, mas limitado ao card
    if ($p.length) return $p.text().trim();
    // fallback: se você optar por adicionar data-source no card
    return ($card.data('source') || '').toString().trim();
  }

  function applyFilters() {
    // (Opcional) Integração com busca por texto no título/fonte
    const q = ($('#pesquisar').val() || '').toLowerCase().trim();

    let anyVisible = false;

    $cards.each(function () {
      const $c = $(this);
      const title = ($c.find('#titulo').text() || '').toLowerCase();
      const src = getCardSource($c);
      const matchSource = selected.size === 0 || selected.has(src);
      const matchText = !q || title.includes(q) || src.toLowerCase().includes(q);

      if (matchSource && matchText) {
        $c.show();
        anyVisible = true;
      } else {
        $c.hide();
      }
    });

    $noData.toggle(!anyVisible);
    updateBadge();
  }

  // Mantém o dropdown aberto ao clicar dentro
  $menu.on('click', function (e) {
    e.stopPropagation();
  });

  // Alterna seleção de uma fonte
  $menu.on('click', 'a.dropdown-item', function (e) {
    e.preventDefault();
    const $a = $(this);
    const val = $a.text().trim();
    if (!val) return;

    if (selected.has(val)) {
      selected.delete(val);
      $a.removeClass('active').find('.check').remove();
    } else {
      selected.add(val);
      $a.addClass('active');
      if (!$a.find('.check').length) {
        $a.prepend('<i class="fas fa-check check mr-2"></i>');
      }
    }
    applyFilters();
  });

  // (Opcional) Atualiza um "badge" no botão do filtro com o nº de seleções
  function updateBadge() {
    const count = selected.size;
    const $btn = $('#filtroMenu'); // seu botão/anchor do dropdown

    // acessibilidade
    $btn.attr('aria-label', count ? `Filtros (${count})` : 'Filtros');

    // pequeno badge visual
    let $badge = $btn.find('.filter-badge');
    if (!$badge.length) {
      $badge = $('<span class="filter-badge badge badge-primary ml-1" style="vertical-align: middle;"></span>');
      $btn.append($badge);
    }
    if (count) $badge.text(count).show(); else $badge.hide();
  }

  // (Opcional) Integra com busca por texto
  $('#pesquisar').on('input', applyFilters);

  // Inicial
  applyFilters();
})(jQuery);
