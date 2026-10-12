// Settings page: the demo tiles redraw at the size that is picked, before it is saved.
// (Hearing each voice before picking it is main.js's doing: the ▶ buttons carry data-preview.)

const tileDemoGrid = document.getElementById("tileDemoGrid");
document.querySelectorAll("#tileSizeOptions input[type=radio]").forEach((radio) => {
  radio.addEventListener("change", () => {
    tileDemoGrid.className = `grid tiles-${radio.value}`;
  });
});
