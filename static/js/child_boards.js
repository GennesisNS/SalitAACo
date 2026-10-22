// A child's Mga Board page: the last board that is on cannot be turned off, and
// a custom board's picture is an emoji or a picture the guardian picks.
// The server checks both again; this only says so sooner.

const boardSwitches = document.querySelectorAll("#boardsForm input[name=boards]");
const boardsError = document.getElementById("boardsError");

boardSwitches.forEach((boardSwitch) => {
  boardSwitch.addEventListener("change", () => {
    const anyOn = [...boardSwitches].some((other) => other.checked);
    if (!anyOn) boardSwitch.checked = true;
    boardsError.textContent = anyOn ? "" : "Kailangang may kahit isang board na naka-on para sa bata.";
  });
});

/* ---------- A custom board's window: its picture as chosen ---------- */
const PICTURE_TYPES = ["image/jpeg", "image/png", "image/webp"];

document.querySelectorAll("[data-icon-choice]").forEach((editor) => {
  const kinds = editor.querySelectorAll("input[type=radio]");
  const file = editor.querySelector("input[type=file]");
  const pickedImage = editor.querySelector("[data-picked-image]");
  const fileName = editor.querySelector("[data-file-name]");
  const clear = editor.querySelector("[data-icon-clear]");
  const error = editor.querySelector("[data-icon-error]");
  const savedImage = pickedImage.dataset.savedImage || "";
  const noFileText = savedImage ? "Ang kasalukuyang larawan" : "Wala pang napili";
  const maxMegabytes = Number(editor.dataset.maxMegabytes);
  let pickedUrl = "";

  const chosenKind = () => ([...kinds].find((kind) => kind.checked) || {}).value;

  // Only the chosen kind's fields show; the picture picked, or the board's own, shows small by the button.
  function showPreview() {
    const kind = chosenKind();
    editor.querySelectorAll("[data-icon-for]").forEach((part) => {
      part.classList.toggle("hidden", part.dataset.iconFor !== kind);
    });
    const picture = pickedUrl || savedImage;
    if (picture) pickedImage.src = picture;
    pickedImage.classList.toggle("hidden", !picture);
  }

  function clearPicked(reason) {
    file.value = "";
    error.textContent = reason || "";
    if (pickedUrl) URL.revokeObjectURL(pickedUrl);
    pickedUrl = "";
    fileName.textContent = noFileText;
    clear.classList.add("hidden");
    showPreview();
  }

  kinds.forEach((kind) => kind.addEventListener("change", showPreview));

  file.addEventListener("change", () => {
    const picture = file.files[0];
    if (!picture) return clearPicked();
    if (!PICTURE_TYPES.includes(picture.type)) return clearPicked("JPEG, PNG o WebP lang ang puwedeng larawan.");
    if (picture.size > maxMegabytes * 1024 * 1024) return clearPicked(`Masyadong malaki ang larawan (max ${maxMegabytes}MB).`);
    error.textContent = "";
    if (pickedUrl) URL.revokeObjectURL(pickedUrl);
    pickedUrl = URL.createObjectURL(picture);
    fileName.textContent = picture.name;
    clear.classList.remove("hidden");
    showPreview();
  });
  clear.addEventListener("click", () => clearPicked());

  showPreview();
});
