// Mga Ulat's "Gumawa ng ulat" window: the kind of report chosen shows its own form.

document.querySelectorAll("[data-report-chooser]").forEach((chooser) => {
  const kinds = chooser.querySelectorAll("input[name=report_type_choice]");

  function showChosenForm() {
    const chosen = ([...kinds].find((kind) => kind.checked) || kinds[0]).value;
    chooser.querySelectorAll("[data-report-form]").forEach((form) => {
      form.classList.toggle("hidden", form.dataset.reportForm !== chosen);
    });
  }

  kinds.forEach((kind) => kind.addEventListener("change", showChosenForm));
  showChosenForm();
});
