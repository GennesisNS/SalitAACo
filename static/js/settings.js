// Settings page: the demo tiles redraw at the size that is picked, before it is
// saved, and each voice can be heard before it is picked.

const tileDemoGrid = document.getElementById("tileDemoGrid");
document.querySelectorAll("#tileSizeOptions input[type=radio]").forEach((radio) => {
  radio.addEventListener("change", () => {
    tileDemoGrid.className = `grid tiles-${radio.value}`;
  });
});

const previewAudio = new Audio();
document.querySelectorAll("[data-preview]").forEach((button) => {
  button.addEventListener("click", () => {
    previewAudio.src = button.dataset.preview;
    previewAudio.play().catch(() => {});
  });
});
