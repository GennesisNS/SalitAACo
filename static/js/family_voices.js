// Boses ng Pamilya page: agreeing to the terms, recording a family member's voice,
// and generating the tile words of each voice while the page is open.
// (▶ Subukan is main.js's doing: the buttons carry data-preview.)

const csrfInput = document.querySelector("[name=csrfmiddlewaretoken]");
const MAX_RECORDING_SECONDS = 120;

/* ---------- Consent first: the recording step opens only once the terms are agreed to ---------- */
const consentBox = document.querySelector("#addVoiceForm input[name=consent]");
const consentStep = document.getElementById("voiceConsentStep");
const recordStep = document.getElementById("voiceRecordStep");
const consentNext = document.getElementById("voiceConsentNext");

function showVoiceStep(recording) {
  consentStep.classList.toggle("hidden", recording);
  recordStep.classList.toggle("hidden", !recording);
}
if (consentBox) {
  consentNext.disabled = !consentBox.checked;
  consentBox.onchange = () => {
    consentNext.disabled = !consentBox.checked;
  };
  consentNext.onclick = () => showVoiceStep(true);
  document.getElementById("voiceConsentBack").onclick = () => showVoiceStep(false);
  // A form the server sent back with the consent given reopens where the guardian was.
  showVoiceStep(consentBox.checked);
}

/* ---------- Recording the voice sample in the browser ---------- */
const recordBtn = document.getElementById("recordVoiceBtn");
const recordTimer = document.getElementById("recordTimer");
const recordPreview = document.getElementById("recordPreview");
const sampleInput = document.getElementById("voiceSampleFile");
let recorder = null,
  recordedChunks = [],
  recordStartedAt = 0,
  timerInterval = null;

function showElapsed() {
  const seconds = Math.floor((Date.now() - recordStartedAt) / 1000);
  recordTimer.textContent = `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`;
  if (seconds >= MAX_RECORDING_SECONDS) recorder.stop();
}

async function startRecording() {
  // Nothing is recorded without the consent, however this was reached.
  if (!consentBox.checked) return showVoiceStep(false);
  let stream;
  try {
    stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  } catch (e) {
    alert("Hindi ma-access ang mikropono. Payagan ang mic permission sa browser, o mag-upload na lang ng audio file.");
    return;
  }
  recordedChunks = [];
  recorder = new MediaRecorder(stream);
  recorder.ondataavailable = (e) => recordedChunks.push(e.data);
  recorder.onstop = () => {
    clearInterval(timerInterval);
    stream.getTracks().forEach((track) => track.stop());
    recordBtn.textContent = "⏺ Mag-record muli";

    const type = (recorder.mimeType || "audio/webm").split(";")[0];
    const file = new File(recordedChunks, `boses.${type.split("/")[1] || "webm"}`, { type });
    recordPreview.src = URL.createObjectURL(file);
    recordPreview.classList.remove("hidden");
    try {
      // The recording becomes the form's file, as if it had been uploaded.
      const transfer = new DataTransfer();
      transfer.items.add(file);
      sampleInput.files = transfer.files;
    } catch (e) {
      alert("Hindi magamit ng browser na ito ang recording. Mag-upload na lang ng audio file.");
    }
  };
  recorder.start();
  recordStartedAt = Date.now();
  timerInterval = setInterval(showElapsed, 250);
  recordBtn.textContent = "⏹ Itigil ang pag-record";
}

if (recordBtn) {
  recordBtn.onclick = () => (recorder && recorder.state === "recording" ? recorder.stop() : startRecording());
}

/* ---------- Generating the tile words of each voice ---------- */
function showProgress(row, done, total) {
  row.querySelector(".fill").style.width = `${Math.round((done / total) * 100)}%`;
  row.querySelector(".progressText").textContent = `${done} / ${total} salita`;
  // Every word is made by then, the one ▶ Subukan plays included.
  if (done === total) row.querySelector("[data-preview]").disabled = false;
}

async function generateWords(row) {
  let done = parseInt(row.dataset.done),
    total = parseInt(row.dataset.total);
  while (done < total) {
    let result;
    try {
      const response = await fetch(row.dataset.generateUrl, {
        method: "POST",
        headers: { "X-CSRFToken": csrfInput.value },
      });
      result = await response.json();
    } catch (e) {
      result = { ok: false, error: "Natigil ang paggawa ng mga salita. Buksan muli ang pahina para ituloy." };
    }
    if (!result.ok) {
      row.querySelector(".voiceError").textContent = result.error;
      return;
    }
    done = result.done;
    total = result.total;
    showProgress(row, done, total);
  }
}

(async () => {
  // One voice at a time, so the voice service gets a steady trickle of requests.
  for (const row of document.querySelectorAll(".voiceRow")) {
    await generateWords(row);
  }
})();
