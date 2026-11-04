// Sign-up page: the privacy notice is read before it is agreed to. Ticking the
// box opens the notice instead; "Sumasang-ayon ako" in it ticks the box, and
// closing it any other way leaves the box as it was. Unticking needs no notice.

const privacyConsent = document.getElementById("id_privacy_consent");
const privacyAgreeBtn = document.getElementById("privacyAgreeBtn");

// A click on the box or its label is about to tick it: open the notice instead.
privacyConsent.addEventListener("click", (e) => {
  if (!privacyConsent.checked) return;
  e.preventDefault();
  open_modal("privacy-terms");
});

privacyAgreeBtn.onclick = () => {
  privacyConsent.checked = true;
  close_modal("privacy-terms");
  privacyConsent.focus();
};
