// Pega os ids dos campos de valores em R$ e coloca mascara ao digitar
const money_mask = document.getElementsByClassName('money-mask');
Inputmask({
    alias: 'numeric',
    radixPoint: ',',
    groupSeparator: '.',
    autoGroup: true,
    prefix: '',
    placeholder: '0',
    numericInput: true,
    rightAlign: false,
    oncleared: function() {
        money_mask.value = '';
    }
    }).mask(money_mask);


const phone_mask = document.getElementsByClassName('phone-mask');
Inputmask({
    mask: '(99) 99999-9999', 
    placeholder: '', 
    clearIncomplete: true,
    oncleared: function() {
        phone_mask.value = '';
    }
}).mask(phone_mask);


function visualizarCadastro(){
    let titulo = document.getElementById('titulo-campanha').value.trim();
    let descricao = document.getElementById('objetivo').value.trim();
    let cep = document.getElementById('cep').value.trim();
    let estado = document.getElementById('estado').value;
    let cidade = document.getElementById('cidade').value.trim();
    let bairro = document.getElementById('bairro').value.trim();
    let logradouro = document.getElementById('logradouro').value.trim();
    let numero = document.getElementById('numero').value.trim();
    let complemento = document.getElementById('complemento').value.trim();
    let telefone = document.getElementById('telefone').value.trim();
    let email = document.getElementById('email').value.trim();
    let instagram = document.getElementById('instagram').value.trim();
    let facebook = document.getElementById('facebook').value.trim();
    let twitter = document.getElementById('twitter').value.trim();
    let chavepix = document.getElementById('chave-pix').value.trim();
    let categorias = Array.from(document.getElementById('select_categoria').selectedOptions).map(option => option.value);
    let metaDeArrecadacao = document.getElementById('meta_de_arrecadacao').value.trim();
    let valorArrecadado = document.getElementById('valor_arrecadado').value.trim();
    let inicioCampanha = document.getElementById('inicio-campanha').value;
    let fimCampanha = document.getElementById('fim-campanha').value;

    let visual_titulo = document.getElementById('visual-titulo');
    visual_titulo.innerHTML = "Campanha " + titulo;

    let visual_descricao = document.getElementById('visual-descricao');
    visual_descricao.innerHTML = descricao;

    let visual_meta_de_arrecadacao = document.getElementById('visual-meta-de-arrecadacao');
    visual_meta_de_arrecadacao.innerHTML = metaDeArrecadacao;

    let visual_valor_arrecadado = document.getElementById('visual-valor-arrecadado');
    visual_valor_arrecadado.innerHTML = valorArrecadado;

    let visual_pix = document.getElementById('visual-pix');
    visual_pix.innerHTML = chavepix;

    let visual_data_inicio = document.getElementById('visual-data-inicio');
    visual_data_inicio.innerHTML = inicioCampanha;

    let visual_data_termino = document.getElementById('visual-data-termino');
    visual_data_termino.innerHTML = fimCampanha;

    let visual_telefone = document.getElementById('visual-telefone');
    visual_telefone.innerHTML = telefone;

    let visual_email = document.getElementById('visual-email');
    visual_email.innerHTML = email;

    visual_instagram = document.getElementById('visual-instagram');
    visual_instagram.innerHTML = `<a href="https://instagram.com/${instagram}" target="_blank">Abrir</a>`;

    visual_facebook = document.getElementById('visual-facebook');
    visual_facebook.innerHTML = `<a href="https://facebook.com/${facebook}" target="_blank">Abrir</a>`;

    visual_twitter = document.getElementById('visual-twitter');
    visual_twitter.innerHTML = `<a href="https://twitter.com/${twitter}" target="_blank">Abrir</a>`;

    visual_cep = document.getElementById('visual-cep');
    visual_cep.innerHTML = cep;

    visual_estado = document.getElementById('visual-estado');
    visual_estado.innerHTML = estado;

    visual_cidade = document.getElementById('visual-cidade');
    visual_cidade.innerHTML = cidade;

    visual_bairro = document.getElementById('visual-bairro');
    visual_bairro.innerHTML = bairro;

    visual_logradouro = document.getElementById('visual-logradouro');
    visual_logradouro.innerHTML = logradouro;

    visual_numero = document.getElementById('visual-numero');
    visual_numero.innerHTML = numero;

    visual_complemento = document.getElementById('visual-complemento');
    visual_complemento.innerHTML = complemento;

    visual_categoria = document.getElementById('visual-categorias');
    visual_categoria.innerHTML = categorias.join(', ');
}

const uploadInputMacro = document.getElementById('imagem_campanha');
const imagePreviewMacro = document.getElementById('visual-imagem');

uploadInputMacro.addEventListener('change', (event) => {
    const file = event.target.files[0];

    if (file) {
        const reader = new FileReader();

        reader.onload = (e) => {
            imagePreviewMacro.src = e.target.result;
            imagePreviewMacro.style.display = 'block';
        };

        reader.readAsDataURL(file);
    } else {
        imagePreviewMacro.style.display = 'none';
    }
}); 


function cadastrarCampanha() {
  event.preventDefault();

  // Obtendo os valores do formulário
  let titulo = document.getElementById('titulo-campanha').value.trim();
  let descricao = document.getElementById('objetivo').value.trim();
  let cep = document.getElementById('cep').value.trim();
  let estado = document.getElementById('estado').value;
  let cidade = document.getElementById('cidade').value.trim();
  let bairro = document.getElementById('bairro').value.trim();
  let logradouro = document.getElementById('logradouro').value.trim();
  let numero = document.getElementById('numero').value.trim();
  let complemento = document.getElementById('complemento').value.trim();
  let telefone = document.getElementById('telefone').value.trim();
  let email = document.getElementById('email').value.trim();
  let instagram = document.getElementById('instagram').value.trim();
  let facebook = document.getElementById('facebook').value.trim();
  let twitter = document.getElementById('twitter').value.trim();
  let chavepix = document.getElementById('chave-pix').value.trim();
  let categorias = Array.from(document.getElementById('select_categoria').selectedOptions).map(option => option.value);
  let metaDeArrecadacao = parseFloat(document.getElementById('meta_de_arrecadacao').value.replace(/\./g, '').replace(',', '.'));
  let valorArrecadado = parseFloat(document.getElementById('valor_arrecadado').value.replace(/\./g, '').replace(',', '.'));
  let inicioCampanha = document.getElementById('inicio-campanha').value;
  let fimCampanha = document.getElementById('fim-campanha').value;
  let imagem = document.getElementById('imagem_campanha').files[0];

  // Validação de campos obrigatórios
  if (!titulo || !descricao || !cep || !estado || !cidade || !bairro || !logradouro || !numero || !inicioCampanha || !fimCampanha) {
      toastr.warning('Por favor, preencha todos os campos.');
      return;
  }

  // Criando objeto FormData para envio de arquivos
  let formData = new FormData();
  formData.append('titulo', titulo);
  formData.append('descricao', descricao);
  formData.append('cep', cep);
  formData.append('estado', estado);
  formData.append('cidade', cidade);
  formData.append('bairro', bairro);
  formData.append('logradouro', logradouro);
  formData.append('numero', numero);
  formData.append('complemento', complemento);
  formData.append('telefone', telefone);
  formData.append('email', email);
  formData.append('instagram', instagram);
  formData.append('facebook', facebook);
  formData.append('twitter', twitter);
  formData.append('chave_pix', chavepix);
  formData.append('categorias', JSON.stringify(categorias));
  formData.append('meta_de_arrecadacao', metaDeArrecadacao);
  formData.append('valor_arrecadado', valorArrecadado);
  formData.append('inicio_campanha', inicioCampanha);
  formData.append('fim_campanha', fimCampanha);
  if (imagem) {
      formData.append('imagem', imagem);
  }

  // Desabilita o botão para evitar envios duplicados
  let botao = document.getElementById("botao-salvar");
  botao.disabled = true;

  // Enviando a requisição
  fetch('/cadastrar_campanha_request/', {
      method: 'POST',
      headers: {
          'X-CSRFToken': getCookie('csrftoken') // Token CSRF necessário para requisições POST no Django
      },
      body: formData
  })
  .then(response => response.json())
  .then(data => {
      if (data.status === 201) {
          toastr.success('Campanha cadastrada com sucesso!');
          setTimeout(() => window.location.href = '/minhas_campanhas/', 2000);
      } else {
          toastr.error(data.message || 'Erro ao cadastrar campanha.');
          botao.disabled = false;
      }
  })
  .catch(error => {
      console.error('Erro:', error);
      toastr.error('Falha na conexão com o servidor.');
      botao.disabled = false;
  });
}

// Função para obter o token CSRF dos cookies
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
      let cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
          let cookie = cookies[i].trim();
          if (cookie.startsWith(name + '=')) {
              cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
              break;
          }
      }
  }
  return cookieValue;
}
