function setRGB(r, g, b) {
  console.log("Sending: " + r + "," + g + "," + b);
  fetch("/set?r=" + r + "&g=" + g + "&b=" + b);
}

function sendColor(hex) {
  hex = hex.replace("#", "");
  var r = parseInt(hex.substring(0, 2), 16);
  var g = parseInt(hex.substring(2, 4), 16);
  var b = parseInt(hex.substring(4, 6), 16);
  setRGB(r, g, b);
}

function setRandom() {
  var r = Math.floor(Math.random() * 256);
  var g = Math.floor(Math.random() * 256);
  var b = Math.floor(Math.random() * 256);
  const btnRnd = document.getElementById("btn-rnd");
  btnRnd.style.backgroundColor = `rgb(${r}, ${g}, ${b})`;
  setRGB(r, g, b);
}

function changeBrightness(brightness) {
  console.log("Sending brightness: " + brightness);
  fetch("/brightness?val=" + brightness);
}

function setRainbow() {
  fetch("/mode?m=rainbow");
}

function setAmbilight() {
  fetch("/mode?m=ambilight");
}

// === Polling ===
function updateStatus() {
    fetch('status')
        .then(response => response.json())
        .then(data => {
            console.log("Status update:", data);

            const slider = document.getElementById("brightness");
            if (!document.activeElement.isSameNode(slider)) {
              slider.value = data.brightness;
            }

            if (data.mode == "static") {
              const picker = document.getElementById("colorPicker");
              picker.value = data.colorHex;
            }
        })
        .catch(err => console.error("Error polling:", err));
}

setInterval(updateStatus, 2500);