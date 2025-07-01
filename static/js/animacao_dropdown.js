/* Código JQuery para abrir e fechar lentamente os dropdowns */

$(document).ready(function() {
  $('.open-modal').click(function(e) {
    e.stopPropagation(); // Impede a propagação do evento de clique para o body

    var dropdownMenu = $(this).find('.dropdown-menu');

    if (dropdownMenu.is(':visible')) {
      dropdownMenu.slideUp(300);
    } else {
      $('.dropdown-menu').not(dropdownMenu).slideUp(300); // Fecha outros dropdowns
      dropdownMenu.slideDown(300);
    }
  });

  $('body').click(function() {
    $('.dropdown-menu').slideUp(300);
  });
});


