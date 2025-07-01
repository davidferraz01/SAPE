function removerCampanha(campanhaId) {
    if (confirm("Tem certeza que deseja remover esta campanha?")){
    fetch(`/remover_campanha/${campanhaId}/`, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'), // Importante para requisições protegidas
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(data.message);
            location.reload();  // Atualiza a página após remoção
        } else {
            alert("Erro ao remover: " + data.message);
        }
    })
    .catch(error => console.error("Erro:", error));
    }
}

// Função para obter o CSRF token necessário em requisições POST e DELETE
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
