// Settings page: the demo tiles redraw at the size that is picked, before it is saved.

const tileDemoGrid = document.getElementById("tileDemoGrid");
document.querySelectorAll("#tileSizeOptions input[type=radio]").forEach((radio) => {
  radio.addEventListener("change", () => {
    tileDemoGrid.className = `grid tiles-${radio.value}`;
  });
});
