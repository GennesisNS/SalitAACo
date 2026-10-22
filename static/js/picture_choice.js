// The picture of a board or a word (components/picture_choice.html): only the chosen kind's
// fields show, and a picked picture is checked and shown small beside its button.
// The server checks the picture again; this only says so sooner.

const PICTURE_TYPES = ["image/jpeg", "image/png", "image/webp"];

document.querySelectorAll("[data-icon-choice]").forEach((editor) => {
  const kinds = editor.querySelectorAll("input[type=radio]");
  // Without the choice (a picture is not the user's to upload) the picture is the emoji.
  const chosenKind = () => ([...kinds].find((kind) => kind.checked) || { value: "emoji" }).value;

  function showChosenPart() {
    const kind = chosenKind();
    editor.querySelectorAll("[data-icon-for]").forEach((part) => {
      part.classList.toggle("hidden", part.dataset.iconFor !== kind);
    });
  }
  kinds.forEach((kind) => kind.addEventListener("change", showChosenPart));
  showChosenPart();

  const file = editor.querySelector("input[type=file]");
  if (!file) return;
  const pickedImage = editor.querySelector("[data-picked-image]");
  const fileName = editor.querySelector("[data-file-name]");
  const clear = editor.querySelector("[data-icon-clear]");
  const error = editor.querySelector("[data-icon-error]");
  const savedImage = pickedImage.dataset.savedImage || "";
  const noFileText = savedImage ? "Ang kasalukuyang larawan" : "Wala pang napili";
  const maxMegabytes = Number(editor.dataset.maxMegabytes);
  let pickedUrl = "";

  // The picture picked, or the one it already has, shows small by the button.
  function showPicked() {
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
    showPicked();
  }

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
    showPicked();
  });
  clear.addEventListener("click", () => clearPicked());

  showPicked();
});
