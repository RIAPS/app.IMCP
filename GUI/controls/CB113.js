var color = $("#CB113_target")[0].style.fill;
var red = "rgb(255, 0, 0)";
var yellow = "rgb(247, 223, 30)";
var blue = "rgb(0, 0, 255)";
var green = "rgb(0, 255, 0)";
var requestedAction = "";
if (color == "red"){
    $("#CB113_target")[0].style.fill = "green";
    requestedAction = "OPEN";
}
else if (color == "green"){
    $("#CB113_target")[0].style.fill = "red";
    requestedAction = "CLOSE";
}

// color = $("#PCC1")[0].style.fill;

//$("#PCC1")[0].style.fill = color;
var payload = {
    "event": "relay_click",
    "requestedRelay": "CB113",
    "requestedAction": requestedAction,
    "color": $("#CB113_target")[0].style.fill
    };
$scope.send({payload: payload, topic: 'mg/event'})