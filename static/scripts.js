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
    tier = tier.split(" ")[1];
    data[tier] = [];
    $.each($(this).find("input"), function() {
      data[tier].push($(this).val());
    })
  });

  var flashMessage = $(".flash");
  // make a post request to set_meta_tanks to store the settings
  $.ajax({
    url:'/set_meta_tanks',
    data: JSON.stringify(data),
    contentType: "application/json",
    datatype: "json",
    type: 'POST',
    success: function(response) {
      flashMessage.addClass("success");
      flashMessage.fadeIn();
      flashMessage.text("Database Updated");
    },
    error: function(error) {
      console.log(error);
      flashMessage.addClass("error");
      flashMessage.fadeIn();
      flashMessage.text("Error Updating Database");
    }
  })
});

function swap_values(sender) {
  var old_val = sender.find("span").text();
  var new_val = sender.find("input").val();

  sender.find("span").text(new_val);
  sender.find("input").val(old_val);
}
