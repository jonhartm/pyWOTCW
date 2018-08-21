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
})

function swap_values(sender) {
  var old_val = sender.find("span").text();
  var new_val = sender.find("input").val();

  sender.find("span").text(new_val);
  sender.find("input").val(old_val);
}
