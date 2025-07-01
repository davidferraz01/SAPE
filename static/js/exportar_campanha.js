function exportarCampanha(titulo, inicio_campanha) {
    // Obtém o elemento
    const element = document.getElementById('div-campanha');
    const foto = document.getElementById('imagem');
  
    var opt = {
      margin: [6, 10, 5, 10],
      filename: `${titulo}_${inicio_campanha}.pdf`,
      pagebreak: { mode: ['css', 'legacy'], avoid: '.tabela' },
      jsPDF: { format: 'a4', orientation: 'l' },
      html2canvas: { scale: 2 }
    };
  
    // Ajuste a largura da página no elemento antes de convertê-lo em PDF
    element.style.width = '1070px';
    foto.style.height = '250px';
    foto.style.width = 'auto';
    foto.style.display = 'block'; // Certifique-se de que a foto tenha a propriedade display definida como 'block'
    foto.style.margin = 'auto'; // Defina as margens esquerda e direita como 'auto' para centralizar a foto
  
    html2pdf().set(opt).from(element).save().catch(function (error) {
      console.error('Erro ao exportar a tabela:', error);
    }).finally(function () {
      // Restaure o estilo original do elemento após a conversão em PDF
      element.style.width = '';
      foto.style.height= '';
      foto.style.width= '';
      foto.style.display = '';
      foto.style.margin = '';
    });
  }
  
  
  
    
    