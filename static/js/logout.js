function logout(){
    $.ajax({
        url: '/logout/', 
        processData: false,
        contentType: false,
        beforeSend: function(xhr, settings) {
          xhr.setRequestHeader("X-CSRFToken", document.cookie.match(/csrftoken=([\w-]+)/)[1]);
        },
        success: function(response) {
         
          window.location.href = '/login/'
        },
        error: function(xhr, status, error) {
          toastr.error('Erro no logout. Por favor, verifique sua conexão com a internet.');
          //console.log(xhr.responseText);
        }
      });
}