function auth(){
    var email = document.getElementById('email').value
    var senha = document.getElementById('senha').value

    // cria objeto para autenticação
    const auth_obj = {
        "email": email,
        "senha": senha
    }
  
    // stringify object
    const auth = JSON.stringify(auth_obj);

    // Cria formData para armazenar os dados
    var formData = new FormData();
    formData.append('auth', auth);

    // request ajax
    $.ajax({
        url: '/auth/',  // URL da sua view Django para processar a requisição
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        success: function(response) {
          // Get next url
          // Cria um objeto URLSearchParams com a string de consulta da URL
          const params = new URLSearchParams(window.location.search);

          // Obtém o valor da variável "next_url"
          const next_url = params.get('next');

          // Lógica para lidar com a resposta da requisição AJAX
          console.log(response);
          if (response.status === 200){
            if(next_url){
              window.location.href = next_url
            }else{
              window.location.href = '/noticias/'
            }
          }else{
            toastr.error('Email ou senha inválidos.')
          }
        },
        error: function(xhr, status, error) {
          // Lógica para lidar com erros na requisição AJAX
          toastr.error('Erro na autenticação. Por favor, verifique sua conexão com a internet.');
          //console.log(xhr.responseText);
        }
      });
}

$(function() {
  $('#form-login').submit(function(e){
      e.preventDefault();
  })
});