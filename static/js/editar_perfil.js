function handleEditar() {
    // Tratamento de erros
    if (verifica_campos() === false) {
        return;
    }

    // get inputs
    var nome = document.getElementById('nome').value;
    var telefone = document.getElementById('telefone').value;

    // get foto
    var formData = new FormData();
    var fileInput = document.getElementById('foto').files[0];
    if (fileInput) {
        formData.append('foto', fileInput);
    }

    const usuario_obj = {
        "first_name": nome,
        "telefone": telefone
    };

    // Stringify obj
    const usuario = JSON.stringify(usuario_obj);
    formData.append('usuario', usuario);

    // Request AJAX
    $.ajax({
        url: `/editar_perfil/`,  // URL da sua view Django para processar a requisição
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        beforeSend: function(xhr, settings) {
            xhr.setRequestHeader("X-CSRFToken", document.cookie.match(/csrftoken=([\w-]+)/)[1]);
        },
        success: function(response) {
            // Lógica para lidar com a resposta da requisição AJAX
            console.log(response);
            // Exibe mensagem de sucesso
            toastr.success('Perfil atualizado com sucesso.');
            setTimeout(function() {
                // Código a ser executado após o Toastr desaparecer
                window.location.href = '/perfil/';
            }, 2000); // 2000 milissegundos (2 segundos)
        },
        error: function(xhr, status, error) {
            // Lógica para lidar com erros na requisição AJAX
            toastr.error('Erro ao atualizar perfil. Por favor, verifique sua conexão com a internet.');
            //console.log(xhr.responseText);
        }
    });
}

function updateFileName(input) {
    var fileName = input.files[0].name;
    var label = input.nextElementSibling;
    label.innerHTML = fileName;
}

const handlePhone = (event) => {
    let input = event.target
    input.value = phoneMask(input.value)
}

function phoneMask(v) {
if(!v) return '';
let r = v.replace(/\D/g, "");
r = r.replace(/^0/, "");

if (r.length >= 11 && r.charAt(2) === '9') {
    r = r.replace(/^(\d\d)(\d)(\d{4})(\d{4}).*/, "($1) $2 $3-$4");
} else {
    r = r.replace(/^(\d\d)(\d{5})(\d{0,4}).*/, "($1) $2-$3");
}

return r;
}

function isElementVisible(element) {
  // Verifica se o elemento está visível diretamente
  var computedStyle = window.getComputedStyle(element);
  if (computedStyle.getPropertyValue('display') === 'none' || computedStyle.getPropertyValue('visibility') === 'hidden') {
    return false;
  }

  // Verifica se algum dos elementos pais está oculto
  var parent = element.parentElement;
  while (parent) {
    var parentComputedStyle = window.getComputedStyle(parent);
    if (parentComputedStyle.getPropertyValue('display') === 'none' || parentComputedStyle.getPropertyValue('visibility') === 'hidden') {
      return false;
    }
    parent = parent.parentElement;
  }

  return true;
}

function verifica_campos(){
  // Tratamento de erros
  var campos_validos = true
  var offset = Infinity

  // Seleciona todos os elementos de entrada (inputs)
  var inputs = document.getElementsByTagName("input");

  // Percorre todos os elementos de entrada
  for (var i = 0; i < inputs.length; i++) {
    // Verifica se o display é diferente de none
    if (isElementVisible(inputs[i]) && inputs[i].id && inputs[i].id != 'foto') {
      var id = '#' + inputs[i].id

      if (!$(id).val()) {
        // Avisa campo obrigatório não preenchido
        $(id).addClass('is-invalid');
        $(id).next('.invalid-feedback').show();
      
        // Rolar a página até o campo não preenchido
        if ($(id).offset().top < offset) {
          offset = $(id).offset().top;
        }
        // Altera flag para sinalizar campo inválido
        campos_validos = false;
      } else {
        // Retira aviso de campo obrigatório não preenchido
        $(id).removeClass('is-invalid');
        $(id).next('.invalid-feedback').hide();
      }
    }
  }

  if(campos_validos == false){
    // Rolar a página até o campo mais alto não preenchido
    $('html, body').animate({
      scrollTop: offset - 100 // Ajuste o valor 100 conforme necessário para o posicionamento desejado
    }, 500); // Ajuste o valor 500 para a velocidade de rolagem desejada
  }

  return campos_validos

}

// Verifica se os campos do modal de alterar senha estão preenchidos
function verifica_campos_senhas(){
  // Tratamento de erros
  var campos_validos = true
  var offset = Infinity

  // Seleciona todos os elementos de entrada (inputs)
  var inputs = document.getElementsByTagName("input");

  // Percorre todos os elementos de entrada
  for (var i = 0; i < inputs.length; i++) {
    // Verifica se o display é diferente de none
    if (inputs[i].id && (inputs[i].id == 'senha-atual' || inputs[i].id == 'nova-senha')) {
      var id = '#' + inputs[i].id

      if (!$(id).val()) {
        // Avisa campo obrigatório não preenchido
        $(id).addClass('is-invalid');
        $(id).next('.invalid-feedback').show();
      
        // Altera flag para sinalizar campo inválido
        campos_validos = false;
      } else {
        // Retira aviso de campo obrigatório não preenchido
        $(id).removeClass('is-invalid');
        $(id).next('.invalid-feedback').hide();
      }
    }
  }

  return campos_validos
}

// Request para alterar senha
function alterarSenha(){
  // Tratamento de erros
  if (verifica_campos_senhas() === false){
    return
  }

  // Get variáveis do form
  let senhaAtual = document.getElementById('senha-atual').value;
  let novaSenha = document.getElementById('nova-senha').value;

  // Verifica tamanho da senha
  if(novaSenha.length < 8 || novaSenha.length > 12){
    toastr.error("A senha deve conter entre 8 e 12 caracteres.");
    return;
  }

  // Pelo menos uma letra maiúscula
  if (!/[A-Z]/.test(novaSenha)) {
    toastr.error("A senha deve conter pelo menos uma letra maiúscula.");
    return;
  }

  // Pelo menos uma letra minúscula
  if (!/[a-z]/.test(novaSenha)) {
    toastr.error("A senha deve conter pelo menos uma letra minúscula.");
    return;
  }

  // Pelo menos um número
  if (!/[0-9]/.test(novaSenha)) {
    toastr.error("A senha deve conter pelo menos um número.");
    return;
  }

  // cria objeto para cadastro 
  const usuario_obj = {
    "senha_atual": senhaAtual,
    "nova_senha": novaSenha
  }

  // Stringify obj
  const usuario = JSON.stringify(usuario_obj);
  let formData = new FormData();
  formData.append('usuario', usuario)

  // Request AJAX
  $.ajax({
      url: `/alterar_senha/`,  // URL da sua view Django para processar a requisição
      type: 'POST',
      data: formData,
      processData: false,
      contentType: false,
      beforeSend: function(xhr, settings) {
        xhr.setRequestHeader("X-CSRFToken", document.cookie.match(/csrftoken=([\w-]+)/)[1]);
      },
      success: function(response) {
        // Lógica para lidar com a resposta da requisição AJAX
        console.log(response);
        if(response.status === 200){
          // Exibe mensagem de sucesso
          toastr.success('Senha atualizada com sucesso.');
          $("#janela-senha").modal("hide");
        }else{
          // Autenticação inválida
          toastr.error('Senha atual incorreta.');
        }
      },
      error: function(xhr, status, error) {
        toastr.error('Erro ao atualizar senha. Por favor, verifique sua conexão com a internet.');
        //console.log(xhr.responseText);
      }
    });

}

// JS para pop-up de alterar senha
$(document).ready(function() {
  $("#abrir-senha").click(function(e) {
    e.preventDefault();
    $("#janela-senha").modal("show");
  });
});
