// The payment pages: picking the picture of a payment and seeing it before it
// is sent, and saying whose proof the "Patunay ng bayad" window is showing.
//
// FRONTEND ONLY FOR NOW: the picture is looked at in the browser and goes nowhere.

/* ---------- The proof of payment a guardian picks ---------- */
const proofUpload = document.getElementById("proofUpload");
if (proofUpload) {
  const proofFile = document.getElementById("proofFile");
  const proofError = document.getElementById("proofError");
  const proofPreview = document.getElementById("proofPreview");
  const PROOF_TYPES = ["image/jpeg", "image/png", "image/webp"];
  const maxMegabytes = Number(proofUpload.dataset.maxMegabytes);

  function refuse(reason) {
    proofFile.value = "";
    proofError.textContent = reason;
    proofPreview.classList.add("hidden");
    proofPreview.removeAttribute("src");
  }

  proofFile.onchange = () => {
    const file = proofFile.files[0];
    if (!file) return refuse("");
    // The server will check these again; saying so here spares a wasted upload.
    if (!PROOF_TYPES.includes(file.type)) return refuse("JPEG, PNG o WebP lang ang puwedeng larawan.");
    if (file.size > maxMegabytes * 1024 * 1024) return refuse(`Masyadong malaki ang larawan (max ${maxMegabytes}MB).`);

    proofError.textContent = "";
    if (proofPreview.src) URL.revokeObjectURL(proofPreview.src);
    proofPreview.src = URL.createObjectURL(file);
    proofPreview.classList.remove("hidden");
  };
}

/* ---------- Whose proof of payment is being looked at ---------- */
const proofCaption = document.getElementById("proofCaption");
document.querySelectorAll("[data-proof]").forEach((button) => {
  button.addEventListener("click", () => {
    proofCaption.textContent = button.dataset.proof;
  });
});
