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

  $("#sortable").sortable('disable');

  $('#sortorder').on('click',function(){
    $("#sortable").sortable('enable');
    $('#sortorder').hide();
    $('#saveorder').show();
  });

  $("#sortable").disableSelection();

  $('#saveorder').on('click',function(){
    var sortedItems = $sortables.sortable("toArray");
    var sortUrl;

    if (window.location.pathname.split( '/' )[1] == 'appsteps') {
      sortUrl = "/appsteps/sort";
    }

    if (window.location.pathname.split( '/' )[1] == 'steps') {
      sortUrl = "/steps/sort";
    }

    if (window.location.pathname.split( '/' )[1] == 'listings') {
      var listing_id = window.location.pathname.split( '/' )[2];
      sortUrl = "/listings/" + listing_id + "/steps/sort";
    }

    $("#sortable").sortable('disable');
    $('#sortorder').show();
    $('#saveorder').hide();
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
