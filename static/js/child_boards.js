// A child's Mga Board page: the last board that is on cannot be turned off.
// The server refuses a form with no board on as well; this only says so sooner.

const boardSwitches = document.querySelectorAll("#boardsForm input[name=boards]");
const boardsError = document.getElementById("boardsError");

boardSwitches.forEach((boardSwitch) => {
  boardSwitch.addEventListener("change", () => {
    const anyOn = [...boardSwitches].some((other) => other.checked);
    if (!anyOn) boardSwitch.checked = true;
    boardsError.textContent = anyOn ? "" : "Kailangang may kahit isang board na naka-on para sa bata.";
  });
});
