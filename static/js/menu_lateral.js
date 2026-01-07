function active_menu_noticias(){
    $(document).ready(function() { 
        // Adiciona as classes para ativar o menu
        $('.nav-item a[href="/noticias/"]').addClass('active');
        $('#a-avaliacao').addClass('active')
        $('#li-avaliacao').addClass('menu-open')
        $('#a-noticias').addClass('active')
        $('body').addClass('sidebar-mini sidebar-collapse');
      });
}

function active_menu_monitoramento(){
    $(document).ready(function() { 
        // Adiciona as classes para ativar o menu
        $('.nav-item a[href="/monitoramento/"]').addClass('active');
        $('#a-avaliacao').addClass('active')
        $('#li-avaliacao').addClass('menu-open')
        $('#a-monitoramento').addClass('active')
        $('body').addClass('sidebar-mini sidebar-collapse');
      });
}

function active_menu_perfil(){
    $(document).ready(function() {
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

