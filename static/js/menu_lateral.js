function active_menu_doar(){
    $(document).ready(function() { 
        // Adiciona as classes para ativar o menu
        $('.nav-item a[href="/doar/"]').addClass('active');
        $('#a-doacao').addClass('active')
        $('#li-doacao').addClass('menu-open')
        $('body').addClass('sidebar-mini sidebar-collapse');
      });
}

function active_menu_minhas_doacoes(){
    $(document).ready(function() { 
        // Adiciona as classes para ativar o menu
        $('.nav-item a[href="/minhas_doacoes/"]').addClass('active');
        $('#a-doacao').addClass('active')
        $('#li-doacao').addClass('menu-open')
        $('body').addClass('sidebar-mini sidebar-collapse');
      });
}

function active_menu_minhas_campanhas(){
    $(document).ready(function() {       
        // Adiciona as classes para ativar o menu
        $('.nav-item a[href="/minhas_campanhas/"]').addClass('active');
        $('#a-minhas_campanhas').addClass('active')
        $('#li-minhas_campanhas').addClass('menu-open')
        $('body').addClass('sidebar-mini sidebar-collapse');
    });
}

