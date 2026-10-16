// The public website: the menu on small screens, and the small working board in the hero.

/* ---------- Menu (folds away under a button on small screens) ---------- */
const navToggle = document.getElementById("navToggle");
const navLinks = document.getElementById("navLinks");

function setMenu(open) {
  navLinks.classList.toggle("open", open);
  navToggle.setAttribute("aria-expanded", open ? "true" : "false");
  navToggle.setAttribute("aria-label", open ? "Isara ang menu" : "Buksan ang menu");
}
navToggle.onclick = () => setMenu(!navLinks.classList.contains("open"));
// A link has been followed: the menu has done its job.
navLinks.querySelectorAll("a").forEach((link) => {
  link.addEventListener("click", () => setMenu(false));
});

/* ---------- The board in the hero: tapping a tile adds its word, as in the app ---------- */
const demoSentence = document.getElementById("demoSentence");
// Held here because emptying the sentence takes the placeholder off the page.
const demoPlaceholder = document.getElementById("demoPlaceholder");
const MAX_DEMO_WORDS = 6;
let demoWords = [];

function drawDemoSentence() {
  demoSentence.innerHTML = "";
  if (demoWords.length === 0) {
    demoSentence.appendChild(demoPlaceholder);
    return;
  }
  demoWords.forEach((word) => {
    const chip = document.createElement("span");
    chip.className = "demoChip";
    chip.textContent = word;
    demoSentence.appendChild(chip);
  });
}

document.querySelectorAll("#demoGrid .demoTile").forEach((tile) => {
  tile.onclick = () => {
    // A picture of the board, not the board: a short sentence is enough to show how it works.
    if (demoWords.length >= MAX_DEMO_WORDS) demoWords.shift();
    demoWords.push(tile.dataset.word);
    drawDemoSentence();
  };
});
document.getElementById("demoClear").onclick = () => {
  demoWords = [];
  drawDemoSentence();
};
