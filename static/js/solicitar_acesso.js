const phone_mask = document.getElementsByClassName('phone-mask');
Inputmask({
    mask: '(99) 99999-9999', 
    placeholder: '', 
    clearIncomplete: true,
    oncleared: function() {
        phone_mask.value = '';
    }
}).mask(phone_mask);

const cpf_mask = document.getElementsByClassName('cpf-mask');
Inputmask({
    mask: '999.999.999-99', 
    placeholder: '', 
    clearIncomplete: true,
    oncleared: function() {
        cpf_mask.value = '';
    }
}).mask(cpf_mask);

function cadastrarDoador() {
    event.preventDefault();

    // Obtém os valores do formulário
    let nome = document.getElementById('nome').value.trim();
    //let cpf = document.getElementById('cpf').value.trim();
    let email = document.getElementById('email').value.trim();
    let telefone = document.getElementById('telefone').value.trim();
    let senha = document.getElementById('senha').value;
    let confirmarSenha = document.getElementById('confirmar-senha').value;

    // Validação de campos obrigatórios
    if (!nome || !email || !telefone || !senha || !confirmarSenha) {
        toastr.warning('Por favor, preencha todos os campos.');
        return;
    }

    // Verifica se as senhas coincidem
    if (senha !== confirmarSenha) {
        toastr.error('As senhas não coincidem. Verifique e tente novamente.');
        return;
    }

    // Desativa o botão para evitar múltiplos envios
    let botao = document.getElementById("botao-cadastrar");
    botao.disabled = true;

    // Estrutura os dados para envio
    let dados = {
        nome: nome,
        email: email,
        telefone: telefone,
        senha: senha,
        tipo_usuario: "analista"
    };

    // Envia a requisição para a API de cadastro
    fetch('/cadastrar_usuario/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken') // Obtém o token CSRF
        },
        body: JSON.stringify(dados)
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 201) {
            toastr.success('Cadastro realizado com sucesso! Redirecionando...');
            setTimeout(() => window.location.href = '/login/', 2000);
        } else {
            toastr.error(data.message || 'Erro ao cadastrar. Tente novamente.');
            botao.disabled = false; // Reabilita o botão se houver erro
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        toastr.error('Falha na conexão com o servidor. Verifique sua internet.');
        botao.disabled = false;
    });
}


const cnpj_mask = document.getElementsByClassName('cnpj-mask');
Inputmask({
    mask: '99.999.999/9999-99', 
    placeholder: '', 
    clearIncomplete: true,
    oncleared: function() {
        cnpj_mask.value = '';
    }
}).mask(cnpj_mask);

function cadastrarInstituicao() {
    event.preventDefault();

    // Obtém os valores do formulário
    let supervisor = document.getElementById('instituicao').value.trim();
    //let cnpj = document.getElementById('cnpj').value.trim();
    //let nome_responsavel = document.getElementById('nome_responsavel').value.trim();
    //let cpf_responsavel = document.getElementById('cpf_responsavel').value.trim();
    let cpf = document.getElementById('cpf').value.trim();
    let email = document.getElementById('email').value.trim();
    let telefone = document.getElementById('telefone').value.trim();
    let senha = document.getElementById('senha').value;
    let confirmarSenha = document.getElementById('confirmar-senha').value;

    // Validação de campos obrigatórios
    if (!supervisor || !cpf || !email || !telefone || !senha || !confirmarSenha) {
        toastr.warning('Por favor, preencha todos os campos.');
        return;
    }

    // Verifica se as senhas coincidem
    if (senha !== confirmarSenha) {
        toastr.error('As senhas não coincidem. Verifique e tente novamente.');
        return;
    }

    // Desativa o botão para evitar múltiplos envios
    let botao = document.getElementById("botao-cadastrar");
    botao.disabled = true;

    // Estrutura os dados para envio
    let dados = {
        tipo_usuario: "supervisor",
        nome: supervisor,
        cpf: cpf,
        email: email,
        telefone: telefone,
        senha: senha
    };

    // Envia a requisição para a API de cadastro
    fetch('/cadastrar_usuario/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken') // Obtém o token CSRF
        },
        body: JSON.stringify(dados)
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 201) {
            toastr.success('Cadastro realizado com sucesso! Redirecionando...');
            setTimeout(() => window.location.href = '/login/', 2000);
        } else {
            toastr.error(data.message || 'Erro ao cadastrar. Tente novamente.');
            botao.disabled = false; // Reabilita o botão em caso de erro
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        toastr.error('Falha na conexão com o servidor. Verifique sua internet.');
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
