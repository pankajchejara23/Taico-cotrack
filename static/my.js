$(document).ready(function(){
  $("#id_editq-questionnaire_language").on('change', function(){
    var lang = $(this).val()


    if (lang == 'Pt')
    {
     $("#id_editq-title").val('Avaliação de {PRODUCT_NAME}');

     $("#id_editq-paragraph").val('Com sua ajuda, gostaríamos de examinar como os usuários percebem a usabilidade e a estética do {PRODUCT_NAME}. Esperamos identificar áreas para otimização. Isso nos permitirá otimizar o produto de forma que seja o mais eficiente e compreensível possível.');
   } else if (lang =='Est') {
     $("#id_editq-title").val('Hinnang teenusele {PRODUCT_NAME}');

     $("#id_editq-paragraph").val('Teie abiga soovime uurida, kuidas kasutajad tajuvad toote {PRODUCT_NAME} kasutatavust ja esteetikat. Loodame kindlaks teha optimeerimise valdkonnad. See võimaldab meil toodet optimeerida nii, et see oleks võimalikult tõhus ja arusaadav.');
   } else {
     $("#id_editq-title").val('Assessment of {PRODUCT_NAME}');
    
     $("#id_editq-paragraph").val('With your help, we would like to examine how users perceive the usability and aesthetics of {PRODUCT_NAME}. We hope to identify areas for optimization. This will enable us to optimize the product in such a way that it is as efficient and comprehensible as possible.');

   }





  });
});
