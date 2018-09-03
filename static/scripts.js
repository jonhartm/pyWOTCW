$(document).ready(function() {
  $(".chng-view").click(function() {
    if (!$(this).hasClass("active")) {
      // Toggle the active state for all buttons in this group
      $(this).parent().children().each(function() { $(this).toggleClass("active"); });
      $("td[class^='rank-']").each(function() {
        swap_values($(this));
      });
    }
  });

  $( function() {
    $( ".sortable" ).sortable({
      connectWith: ".sortable"
    }).disableSelection();
  });
})

$("#btn_submit").click(function() {
  // roll through the lists on the page and pull the rank and all the tank ids under them
  var data = {}
  $.each($(".tank-list-container"), function() {
    var tier = $(this).find("h1").text();
    data[tier] = [];
    $.each($(this).find("input"), function() {
      data[tier].push($(this).val());
    })
  });
  console.log(data);

  $.ajax({
    url:'/meta_tanks',
    data: data,
    type: 'POST',
    success: function(response) {
      console.log(response);
    },
    error: function(error) {
      console.log(error);
    }
  })
});

function swap_values(sender) {
  var old_val = sender.find("span").text();
  var new_val = sender.find("input").val();

  sender.find("span").text(new_val);
  sender.find("input").val(old_val);
}
