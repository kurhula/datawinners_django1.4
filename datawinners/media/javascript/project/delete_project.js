$(document).ready(function(){

    $("#delete_project_block").dialog({
        title: gettext("Delete this Questionnaire?"),
        modal: true,
        autoOpen: false,
        height: 150,
            width: 'auto',
        closeText: 'hide'
      }
   );

   $("#delete_poll_block").dialog({
        title: gettext("Delete this Poll?"),
        modal: true,
        autoOpen: false,
        height: 150,
        width: 'auto',
        closeText: 'hide'
      }
   );

   $("#delete_project_block .cancel_link").bind("click", function() {
       $("#delete_project_block").dialog("close");
       return false;
   });

   $("#delete_poll_block .cancel_link").bind("click", function() {
       $("#delete_poll_block").dialog("close");
       return false;
   });
});
