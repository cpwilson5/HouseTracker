// fades the "flash alert banners after 3 seconds"
window.setTimeout(function() {
  $(".alert").fadeTo(500, 0).slideUp(500, function(){
      $(this).remove();
  });
}, 3000);

// allows for sorting, creates array then updates upon clicking save
$(document).ready(function(){
  var $sortables = $("#sortable").sortable({
      stop: function() {
        var sortedItems = $sortables.sortable("toArray");
      }
  });

  // sets the csrf token using a meta tag
  var csrf_token = $('meta[name=csrf-token]').attr('content');
  $.ajaxSetup({
      beforeSend: function(xhr, settings) {
          if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
              xhr.setRequestHeader("X-CSRFToken", csrf_token);
          }
      }
  });

  $("#sortable").sortable('disable');

  $('#sortorder, #sortordermobile').on('click',function(){
    $("#sortable").sortable('enable');
    $('#sortorder, #sortordermobile').hide();
    $('#saveorder, #saveordermobile').show();
    $(".dragger").show();
    $("#sortable").wrap( "<div class='card mb-4 pl-4 pr-4 pt-4' style='border-style:dashed; color:gray; border-color:gray;'></div>" );
    $(".listingstep").hover(function () {
      $(this).toggleClass("hover");
    });
  });

  $("#sortable").disableSelection();

  $('#saveorder, #saveordermobile').on('click',function(){
    var sortedItems = $sortables.sortable("toArray");
    var sortUrl;

    if (window.location.pathname.split( '/' )[1] == 'apptemplates') {
      var app_template_id = window.location.pathname.split( '/' )[2];
      sortUrl = "/apptemplates/" + app_template_id + "/steps/sort";
    }

    if (window.location.pathname.split( '/' )[1] == 'templates') {
      var template_id = window.location.pathname.split( '/' )[2];
      sortUrl = "/templates/" + template_id + "/steps/sort";
    }

    if (window.location.pathname.split( '/' )[1] == 'listings') {
      var listing_id = window.location.pathname.split( '/' )[2];
      sortUrl = "/listings/" + listing_id + "/steps/sort";
    }

    $("#sortable").sortable('disable');
    $('#sortorder, #sortordermobile').show();
    $('#saveorder, #saveordermobile').hide();
    $(".dragger").hide();
    $("#sortable").unwrap();
    $(".listingstep").hover(function () {
      $(this).toggleClass("hover");
    });

    $.ajax({
      type: "POST",
      url: sortUrl,
      data: 'order=' + sortedItems,
      cache: false,
      success: function (data) { console.log(data); }
    });
  });
});

// toggles the browse button on listing photo edit
$(document).ready(function(){
    $(".edit_photo").click(function(){
        $("#browse").toggle();
    });
});

// shows tooltips for the whole page
$(document).ready(function(){
    $('[data-toggle="tooltip"]').tooltip();
});

// handles passing a variable to a modal on the templates collection/list page so I can use the trash icon
$(document).ready(function(){
  $('#deleteTemplateModal').on('show.bs.modal', function (event) {
    var templateId = $(event.relatedTarget).data('id');
    $("#deleteTemplate").attr("href", $('#deleteTemplate').attr('href') + templateId);
  });
});

// handles the show/hide verbiage toggle on listing steps
$('#showhide, #showhidemobile').click(function(){
    $(this).toggleClass('ButtonClicked');
    $(this).text(function(i,old){
        return old=='Show completed' ?  'Hide completed' : 'Show completed';
    });
});
