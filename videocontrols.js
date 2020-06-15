var myVideo;

function setVideo(video) {
  myVideo = document.getElementById(video); 
  captionsOn();
  myVideo.width = window.innerWidth*.50;
  myVideo.controls = true;
}

function jumpTo(time) {
  myVideo.currentTime = time;
  myVideo.play();
}

function captionsOn() {
  for (var i = 0; i < myVideo.textTracks.length; i++) {
      myVideo.textTracks[i].mode = 'showing';
    }
}

function captionsOff() {
  for (var i = 0; i < myVideo.textTracks.length; i++) {
      myVideo.textTracks[i].mode = 'hidden';
    }
}

function makeBig() { 
    myVideo.width = window.innerWidth*.9;
} 

function makeSmall() { 
    myVideo.width = window.innerWidth*.5; 
} 

function fasterSpeed() {
    myVideo.playbackRate *= 1.25;
}

function slowerSpeed() {
    myVideo.playbackRate *= .75;
}

function normalSpeed() {
    myVideo.playbackRate = 1.0;
}

function includeHTML() {
  var z, i, elmnt, file, xhttp;
  /* Loop through a collection of all HTML elements: */
  z = document.getElementsByTagName("*");
  for (i = 0; i < z.length; i++) {
    elmnt = z[i];
    /*search for elements with a certain atrribute:*/
    file = elmnt.getAttribute("w3-include-html");
    if (file) {
      /* Make an HTTP request using the attribute value as the file name: */
      xhttp = new XMLHttpRequest();
      xhttp.onreadystatechange = function() {
        if (this.readyState == 4) {
          if (this.status == 200) {elmnt.innerHTML = this.responseText;}
          if (this.status == 404) {elmnt.innerHTML = "Page not found.";}
          /* Remove the attribute, and call this function once more: */
          elmnt.removeAttribute("w3-include-html");
          includeHTML();
        }
      } 
      xhttp.open("GET", file, true);
      xhttp.send();
      /* Exit the function: */
      return;
    }
  }
}
