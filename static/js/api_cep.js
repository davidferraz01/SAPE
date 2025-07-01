$(document).ready(function() {
    $("#cep").blur(function(event) {
      var cep = $("#cep").val();
      $.getJSON(`https://viacep.com.br/ws/${cep}/json/`, function(data) {
        if (!("erro" in data)) {
          $("#logradouro").val(data.logradouro);
          $("#bairro").val(data.bairro);
          $("#cidade").val(data.localidade);
          $("#estado").val(data.uf);
          $("#complemento").val(data.complemento);
        }
      });
    });
});

// Máscaras nos campos inteiros

new Cleave('#cep', {
blocks: [5, 3],
delimiters: ['-'],
numericOnly: true
});

new Cleave('#matricula', {
  blocks: [10],
  numericOnly: true
});



