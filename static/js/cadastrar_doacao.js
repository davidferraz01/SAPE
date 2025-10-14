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

function cadastrarDoacao(campanhaId) {
    console.log("Cadastrando doação para a campanha", campanhaId);
    let dados = {
        campanha_id: campanhaId,
        alimentos: document.getElementById("alimentos").value.trim(),
        qtd_alimentos: parseInt(document.getElementById("qtd-alimentos").value) || 0,
        vestimentas: document.getElementById("vestimentas").value.trim(),
        qtd_vestimentas: parseInt(document.getElementById("qtd-vestimentas").value) || 0,
        moveis: document.getElementById("moveis").value.trim(),
        qtd_moveis: parseInt(document.getElementById("qtd-moveis").value) || 0,
        brinquedos: document.getElementById("brinquedos").value.trim(),
        qtd_brinquedos: parseInt(document.getElementById("qtd-brinquedos").value) || 0,
        livros: document.getElementById("livros").value.trim(),
        qtd_livros: parseInt(document.getElementById("qtd-livros").value) || 0,
        artigos_higiene: document.getElementById("artigos-higiene").value.trim(),
        qtd_artigos_higiene: parseInt(document.getElementById("qtd-artigos-higiene").value) || 0,
        cobertores: document.getElementById("cobertores").value.trim(),
        qtd_cobertores: parseInt(document.getElementById("qtd-cobertores").value) || 0,
        eletronicos: document.getElementById("eletronicos").value.trim(),
        qtd_eletronicos: parseInt(document.getElementById("qtd-eletronicos").value) || 0,
        artigos_escolares: document.getElementById("artigos-escolares").value.trim(),
        qtd_artigos_escolares: parseInt(document.getElementById("qtd-artigos-escolares").value) || 0,
        artigos_hospitalares: document.getElementById("artigos-hospitalares").value.trim(),
        qtd_artigos_hospitalares: parseInt(document.getElementById("qtd-artigos-hospitalares").value) || 0,
        outros: document.getElementById("outros").value.trim(),
        qtd_outros: parseInt(document.getElementById("qtd-outros").value) || 0,
        valor: parseFloat(document.getElementById("valor").value.replace(",", ".")) || 0,
        mensagem: document.getElementById("mensagem").value.trim()
    };

    // Verifica se pelo menos um campo foi preenchido
    let algumaDoacao = Object.keys(dados).some(key => {
        return (key.startsWith("qtd_") && dados[key] > 0) || (key !== "campanha_id" && key !== "mensagem" && dados[key] !== "");
    }) || dados.mensagem !== "";

    if (!algumaDoacao) {
        alert("Preencha pelo menos um campo para fazer a doação.");
        return;
    }

    // Envia os dados via fetch para a view Django
    fetch("/cadastrar_doacao_request/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCSRFToken()  // Função para obter o CSRF Token
        },
        body: JSON.stringify(dados)
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
          toastr.success('Doação enviada com sucesso!');
          setTimeout(() => window.location.href = '/noticias/', 2000);
      } else {
          toastr.error(data.message || 'Erro ao cadastrar campanha.');
      }
  })
    .catch(error => {
        console.error('Erro:', error);
        toastr.error('Falha na conexão com o servidor.');
        botao.disabled = false;
    });
}

// Função para obter o CSRF Token do cookie
function getCSRFToken() {
    let name = "csrftoken=";
    let decodedCookie = decodeURIComponent(document.cookie);
    let cookies = decodedCookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
        let cookie = cookies[i].trim();
        if (cookie.indexOf(name) === 0) {
            return cookie.substring(name.length, cookie.length);
        }
    }
    return "";
}
