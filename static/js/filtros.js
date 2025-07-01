window.addEventListener('DOMContentLoaded', (event) => {
  sincronizarFiltros();
});

function sincronizarFiltros() {
  // Obtém os elementos de filtro
  const filtroPesquisa = document.getElementById('pesquisar');
  const botaoLimpar = document.getElementById('limpar-input');

  // Obtém todas as divs que serão filtradas
  const divs = document.getElementsByClassName('flex-item');

  // Adiciona os event listeners para cada filtro
  filtroPesquisa.addEventListener('keyup', aplicarFiltros);
  botaoLimpar.addEventListener('click', clearInput);

  // Função para aplicar os filtros
  function aplicarFiltros() {
    // Obtém os valores selecionados nos filtros
    const valorFiltroPesquisa = filtroPesquisa.value;

    // Percorre todas as divs
    for (let i = 0; i < divs.length; i++) {
      const div = divs[i];

      // Verifica se a div atende aos critérios de filtro
      const atendeFiltroPesquisa = valorFiltroPesquisa === '' || div.querySelector('p#titulo').textContent.toLowerCase().includes(valorFiltroPesquisa.toLowerCase());

      // Define a visibilidade da div com base nos filtros
      if ( atendeFiltroPesquisa ) {
        div.style.display = 'block';
      } else {
        div.style.display = 'none';
      }
    }

    existe_cadastro();
  }

  // Limpa o valor do input e aplica os filtros
  function clearInput() {
    filtroPesquisa.value = '';
    aplicarFiltros();
  }

  aplicarFiltros();
}

function existe_cadastro() {
  const itens = $('.flex-item');
  if (itens.length === 0 || itens.filter(':visible').length === 0) {
    // Mostra a div centralizada caso não haja elementos
    $('#no-cadastros').show();
  } else {
    // Esconde a div centralizada caso haja elementos visíveis
    $('#no-cadastros').hide();
  }
}
