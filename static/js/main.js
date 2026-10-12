// Small helpers loaded on every page: toasts, the sidebar, modals, voice samples and the theme.

const THEME_KEY = "salitaaco-theme";

/* ---------- Toast messages: dismiss on click, or by themselves after a while ---------- */
document.querySelectorAll(".toast").forEach((toast) => {
  const dismiss = () => toast.remove();
  toast.querySelector("button").onclick = dismiss;
  setTimeout(dismiss, 5000);
});

/* ---------- Sidebar (slides in on small screens) ---------- */
const sidebar = document.getElementById("sidebar");
const menuBtn = document.getElementById("menuBtn");
const sidebarBackdrop = document.getElementById("sidebarBackdrop");
if (sidebar && menuBtn) {
  menuBtn.onclick = () => sidebar.classList.toggle("open");
  sidebarBackdrop.onclick = () => sidebar.classList.remove("open");
}

/* ---------- Modals ----------
   A modal is an element with data-modal="name". Elements with
   data-open-modal="name" / data-close-modal="name" open and close it, and so
   does a click on its backdrop. data-open="true" opens it on page load, which
   is how the server reopens a modal whose form failed validation. */
function open_modal(name) {
  document.querySelector(`[data-modal="${name}"]`).classList.remove("hidden");
}
function close_modal(name) {
  document.querySelector(`[data-modal="${name}"]`).classList.add("hidden");
}
document.querySelectorAll("[data-modal]").forEach((modal) => {
  modal.addEventListener("click", (e) => {
    if (e.target === modal) close_modal(modal.dataset.modal);
  });
  if (modal.dataset.open === "true") open_modal(modal.dataset.modal);
});
document.querySelectorAll("[data-open-modal]").forEach((el) => {
  el.addEventListener("click", () => open_modal(el.dataset.openModal));
});
document.querySelectorAll("[data-close-modal]").forEach((el) => {
  el.addEventListener("click", () => close_modal(el.dataset.closeModal));
});
document.addEventListener("keydown", (e) => {
  if (e.key !== "Escape") return;
  document.querySelectorAll("[data-modal]:not(.hidden)").forEach((modal) => close_modal(modal.dataset.modal));
});

/* ---------- The sidebar's child picker: each choice is the address of that child's page ---------- */
const childPicker = document.getElementById("childPicker");
if (childPicker) {
  childPicker.onchange = () => {
    location.href = childPicker.value;
  };
}

/* ---------- ▶ buttons that play a voice saying a word (data-preview is the sound's address) ---------- */
const previewAudio = new Audio();
document.querySelectorAll("[data-preview]").forEach((button) => {
  button.addEventListener("click", () => {
    previewAudio.src = button.dataset.preview;
    previewAudio.play().catch(() => {});
  });
});

/* ---------- Dark theme toggle on the Settings page (remembered across page loads) ---------- */
const darkToggle = document.getElementById("darkToggle");
if (darkToggle) {
  // On whenever the page is showing dark colours: because the user chose them
  // here, or, with no choice made yet, because the device prefers dark. Either
  // way the page already carries the answer (see components/head_scripts.html).
  darkToggle.checked = document.documentElement.getAttribute("data-theme") === "dark";
  darkToggle.onchange = (e) => {
    const theme = e.target.checked ? "dark" : "light";
    document.documentElement.setAttribute("data-theme", theme);
    try {
      localStorage.setItem(THEME_KEY, theme);
    } catch (err) {}
  };
}
