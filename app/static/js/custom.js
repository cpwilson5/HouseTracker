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
    var listing_id = window.location.pathname.split( '/' )[2];
    $("#sortable").sortable('disable');
    $('#sortorder').show();
    $('#saveorder').hide();
    $.ajax({
      type: "POST",
      url: "/listings/" + listing_id + "/steps/sort",
      data: 'order=' + sortedItems,
      cache: false,
      success: function (data) { console.log(data); }
    });
  });
});
