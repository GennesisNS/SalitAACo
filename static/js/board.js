// The AAC board: tabs, tile grid, sentence builder, edit mode and the rating stars.
// The vocabulary and this user's data arrive in the page as JSON (#board-data).

const boardData = JSON.parse(document.getElementById("board-data").textContent);
const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;

const FREQ_CAT = boardData.frequent_category;
const VERB_CAT = boardData.verb_category;
const TAB_KEY = "salitaaco-board-tab";
const EDIT_KEY = "salitaaco-board-edit";

const categories = {};
boardData.categories.forEach((category) => {
  categories[category.name] = category.items;
});

const customList = {}; // { word: {has_image, has_sound, image_url, sound_url, reset_url} }
boardData.customizations.forEach((it) => {
  customList[it.word] = it;
});

/* ============================================================
   APP STATE
============================================================ */
let currentCat = FREQ_CAT,
  currentAspect = "past",
  words = [];
let editMode = false;
let frequentItems = boardData.frequent_words; // [{word, use_count}, ...]
let _frequentRefreshTimer = null;

// Saving a tile reloads the page, so the open tab and edit mode are remembered.
function remember(key, value) {
  try {
    sessionStorage.setItem(key, value);
  } catch (e) {}
}
function recall(key) {
  try {
    return sessionStorage.getItem(key);
  } catch (e) {
    return null;
  }
}
const rememberedTab = recall(TAB_KEY);
if (rememberedTab && (rememberedTab === FREQ_CAT || categories[rememberedTab])) currentCat = rememberedTab;
editMode = recall(EDIT_KEY) === "1";

// The Settings page links here with ?edit=1 to open the board in edit mode.
const pageUrl = new URL(location.href);
if (pageUrl.searchParams.get("edit") === "1") {
  editMode = true;
  remember(EDIT_KEY, "1");
  pageUrl.searchParams.delete("edit");
  history.replaceState(null, "", pageUrl);
}

async function loadFrequent(limit = 40) {
  try {
    const res = await fetch(`${boardData.frequent_words_url}?limit=${limit}`).then((r) => r.json());
    frequentItems = res.ok ? res.items || [] : [];
  } catch (e) {
    frequentItems = [];
  }
}

function incrementUsage(word) {
  // Fire-and-forget: don't block the UI on accounting.
  try {
    fetch(boardData.increment_usage_url, {
      method: "POST",
      headers: { "X-CSRFToken": csrfToken },
      body: new URLSearchParams({ word }),
    }).catch(() => {});
  } catch (e) {}
  // If user is on the Frequent tab, refresh it soon so rankings stay current.
  if (currentCat === FREQ_CAT) {
    if (_frequentRefreshTimer) clearTimeout(_frequentRefreshTimer);
    _frequentRefreshTimer = setTimeout(() => {
      loadFrequent().then(renderGrid);
    }, 700);
  }
}

/* ============================================================
   TABS / GRID
============================================================ */
const tabsEl = document.getElementById("tabs"),
  gridEl = document.getElementById("grid"),
  aspectBar = document.getElementById("aspectBar");

function buildTabs() {
  tabsEl.innerHTML = "";
  const tabLabels = [FREQ_CAT, ...Object.keys(categories)];
  tabLabels.forEach((cat) => {
    const b = document.createElement("button");
    b.type = "button";
    b.textContent = cat;
    if (cat === currentCat) b.classList.add("active");
    b.onclick = async () => {
      currentCat = cat;
      remember(TAB_KEY, cat);
      if (cat === FREQ_CAT) {
        await loadFrequent();
      }
      render();
    };
    tabsEl.appendChild(b);
  });
}
document.querySelectorAll("#aspectBar button").forEach((b) => {
  b.onclick = () => {
    currentAspect = b.dataset.a;
    document.querySelectorAll("#aspectBar button").forEach((x) => x.classList.remove("active"));
    b.classList.add("active");
    renderGrid();
  };
});

function render() {
  document.querySelectorAll("#tabs button").forEach((b) => b.classList.toggle("active", b.textContent === currentCat));
  aspectBar.style.display = currentCat === VERB_CAT ? "flex" : "none";
  renderGrid();
}

function findEmojiForWord(word) {
  for (const cat of Object.keys(categories)) {
    for (const item of categories[cat]) {
      const baseLabel = item.verb ? item.verb[currentAspect] : item.w;
      if (item.w === word || baseLabel === word) return item.e || "📝";
      if (item.verb) {
        if (item.verb.past === word || item.verb.present === word || item.verb.future === word) {
          return item.e || "📝";
        }
      }
    }
  }
  return "📝";
}

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function renderGrid() {
  gridEl.innerHTML = "";
  let items;
  if (currentCat === FREQ_CAT) {
    if (frequentItems.length === 0) {
      gridEl.innerHTML = `<div style="grid-column:1/-1;text-align:center;padding:36px 18px;color:var(--sub);">
        <div style="font-size:40px;margin-bottom:8px;">🔁</div>
        <div style="font-size:15px;margin-bottom:4px;font-weight:600;color:var(--ink);">Wala pang madalas gamitin</div>
        <div style="font-size:12px;line-height:1.5;">Pindutin ang mga tile sa ibang tab para mabuo ang listahang ito.<br>Nakaayos ang mga tile dito ayon sa kung ilang beses mo na itong nagamit.</div>
      </div>`;
      return;
    }
    items = frequentItems.map((it) => {
      return {
        w: it.word,
        e: findEmojiForWord(it.word),
        _useCount: it.use_count,
        _fromFrequent: true,
      };
    });
  } else {
    items = categories[currentCat];
  }

  items.forEach((item) => {
    let label = item.w;
    if (item.verb) label = item.verb[currentAspect];
    const custom = customList[label] || {};
    // In edit mode the tile holds buttons, so it cannot be a button itself.
    const c = el(editMode ? "div" : "button", "cell");

    if (item._fromFrequent && item._useCount) {
      const useCountMark = el("span", "usecount", `×${item._useCount}`);
      useCountMark.title = `Ginamit nang ${item._useCount} na beses`;
      c.appendChild(useCountMark);
    }
    if (custom.has_sound) c.appendChild(el("span", "soundmark", "🎙️"));
    if (custom.has_image) {
      const img = el("img", "customimg");
      img.src = custom.image_url;
      img.alt = label;
      c.appendChild(img);
    } else {
      c.appendChild(el("span", "emoji", item.e));
    }
    c.appendChild(el("span", "", label));

    if (editMode) {
      const editRow = el("div", "editRow");
      const imgBtn = el("button", "", "🖼️");
      imgBtn.type = "button";
      imgBtn.title = "Palitan ang larawan";
      imgBtn.onclick = () => pickImage(label);
      const recBtn = el("button", "", "🎙️");
      recBtn.type = "button";
      recBtn.title = "Mag-record ng tunog";
      recBtn.onclick = () => toggleRecord(label, recBtn);
      const resetBtn = el("button", "", "↺");
      resetBtn.type = "button";
      resetBtn.title = "I-reset";
      resetBtn.onclick = () => resetTile(label);
      editRow.append(imgBtn, recBtn, resetBtn);
      c.appendChild(editRow);
    } else {
      c.type = "button";
      c.onclick = () => addWord(label);
    }
    gridEl.appendChild(c);
  });
}

document.getElementById("editModeBtn").onclick = () => {
  setEditMode(!editMode);
};
function setEditMode(next) {
  editMode = next;
  remember(EDIT_KEY, editMode ? "1" : "0");
  const barBtn = document.getElementById("editModeBtn");
  barBtn.classList.toggle("editing", editMode);
  barBtn.textContent = editMode ? "✓ Tapos na mag-edit" : "✏️ I-edit ang mga cell";
  renderGrid();
}

/* ---- editable images: the hidden upload form is submitted as soon as a file is picked ---- */
const tileImageForm = document.getElementById("tileImageForm");
const tileImageFile = document.getElementById("tileImageFile");
function pickImage(word) {
  document.getElementById("tileImageWord").value = word;
  tileImageFile.click();
}
tileImageFile.onchange = () => {
  if (!tileImageFile.files[0] || !document.getElementById("tileImageWord").value) return;
  tileImageForm.submit();
};

/* ---- recordable sounds: the recording is placed in the hidden upload form and submitted ---- */
const tileSoundForm = document.getElementById("tileSoundForm");
let recordingWord = null,
  mediaRecorder = null,
  recChunks = [];
async function toggleRecord(word, btnEl) {
  if (recordingWord === word) {
    mediaRecorder.stop();
    return;
  }
  if (recordingWord) {
    return;
  }
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    recChunks = [];
    mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.ondataavailable = (e) => recChunks.push(e.data);
    mediaRecorder.onstop = async () => {
      stream.getTracks().forEach((t) => t.stop());
      recordingWord = null;
      const file = new File(recChunks, "sound.webm", { type: "audio/webm" });
      document.getElementById("tileSoundWord").value = word;
      try {
        const transfer = new DataTransfer();
        transfer.items.add(file);
        document.getElementById("tileSoundFile").files = transfer.files;
        tileSoundForm.submit();
      } catch (e) {
        // Browsers that cannot fill a file input from script: post the form, then reload for the result.
        const fd = new FormData(tileSoundForm);
        fd.set("sound", file);
        await fetch(tileSoundForm.action || location.href, { method: "POST", body: fd, redirect: "manual" });
        location.reload();
      }
    };
    mediaRecorder.start();
    recordingWord = word;
    btnEl.textContent = "⏹️";
    setTimeout(() => {
      if (recordingWord === word && mediaRecorder.state === "recording") {
        mediaRecorder.stop();
      }
    }, 5000);
  } catch (e) {
    alert("Hindi ma-access ang mikropono. Payagan ang mic permission sa browser.");
  }
}

/* ---- reset a tile back to its default emoji and voice ---- */
const resetTileForm = document.getElementById("resetTileForm");
function resetTile(word) {
  const custom = customList[word];
  if (!custom) return; // nothing was customised
  resetTileForm.action = custom.reset_url;
  resetTileForm.submit();
}

/* ============================================================
   SENTENCE BUILDER
============================================================ */
// Tapping a tile only adds its word; the sentence is heard with the play button.
function addWord(w) {
  words.push(w);
  stopPlayback();
  incrementUsage(w);
}
// Held here because emptying the sentence removes the placeholder from the page.
const sentencePlaceholder = document.getElementById("placeholder");
const playBtn = document.getElementById("playBtn");
function renderSentence() {
  const s = document.getElementById("sentence");
  s.innerHTML = "";
  playBtn.disabled = words.length === 0;
  playBtn.textContent = playingIndex >= 0 ? "■ Itigil" : "▶ Patugtugin";
  if (words.length === 0) {
    s.appendChild(sentencePlaceholder);
    return;
  }
  words.forEach((w, i) => {
    const t = document.createElement("span");
    t.className = i === playingIndex ? "tag playing" : "tag";
    t.textContent = w;
    t.onclick = () => {
      words.splice(i, 1);
      stopPlayback();
    };
    s.appendChild(t);
  });
}
document.getElementById("clearBtn").onclick = () => {
  words = [];
  stopPlayback();
};

/* ---- play the sentence: one word after another, each with its own recording
        if it has one, otherwise spoken by the device's Filipino voice ---- */
// Silence between one word and the next, in milliseconds (1000 = one second).
// 0 starts each word the moment the one before it ends.
const PAUSE_BETWEEN_WORDS_MS = 0;
// How fast the device's voice speaks words that have no recording: 1 is normal,
// 0.5 is half speed, 2 is double. Recordings always play at their own speed.
const SPEECH_RATE = 1;

// One audio element for every recording: browsers that only allow sound after
// a tap keep allowing it for an element that tap already started.
const sentenceAudio = new Audio();
let playingIndex = -1; // which word of the sentence is sounding; -1 when silent
let playRun = 0; // goes up whenever playback starts or stops, so an older run knows to give up
let finishWord = null; // ends the wait for the word that is sounding

function playRecording(url) {
  return new Promise((resolve) => {
    finishWord = resolve;
    sentenceAudio.onended = sentenceAudio.onerror = resolve;
    sentenceAudio.src = url;
    sentenceAudio.play().catch(resolve);
  });
}
function speakWord(word) {
  return new Promise((resolve) => {
    if (!window.speechSynthesis) return resolve();
    finishWord = resolve;
    const utterance = new SpeechSynthesisUtterance(word);
    utterance.lang = "fil-PH";
    utterance.rate = SPEECH_RATE;
    const voice = speechSynthesis.getVoices().find((v) => /^(fil|tl)([-_]|$)/i.test(v.lang));
    if (voice) utterance.voice = voice;
    utterance.onend = utterance.onerror = resolve;
    speechSynthesis.speak(utterance);
  });
}
function pauseBetweenWords() {
  return new Promise((resolve) => {
    finishWord = resolve; // so that stopping does not wait out the pause
    setTimeout(resolve, PAUSE_BETWEEN_WORDS_MS);
  });
}
async function playSentence() {
  const run = ++playRun;
  const queue = [...words];
  for (let i = 0; i < queue.length; i++) {
    playingIndex = i;
    renderSentence();
    const custom = customList[queue[i]];
    await (custom && custom.has_sound ? playRecording(custom.sound_url) : speakWord(queue[i]));
    if (run !== playRun) return; // stopped, or the sentence changed
    if (PAUSE_BETWEEN_WORDS_MS > 0 && i < queue.length - 1) {
      await pauseBetweenWords();
      if (run !== playRun) return;
    }
  }
  stopPlayback();
}
function stopPlayback() {
  playRun++;
  playingIndex = -1;
  sentenceAudio.pause();
  if (window.speechSynthesis) speechSynthesis.cancel();
  if (finishWord) finishWord();
  finishWord = null;
  renderSentence();
}
playBtn.onclick = () => (playingIndex >= 0 ? stopPlayback() : playSentence());
// Browsers load their list of voices in the background; asking now has it ready by the first play.
if (window.speechSynthesis) speechSynthesis.getVoices();

/* ============================================================
   RATE THE APP
============================================================ */
const starPicker = document.getElementById("starPicker");
const ratingInput = document.getElementById("id_rating");
let selectedStars = parseInt(ratingInput.value) || 0;
if (selectedStars < 1 || selectedStars > 5) selectedStars = 0;

function paintStars(n) {
  starPicker.querySelectorAll("span").forEach((s) => {
    s.classList.toggle("filled", parseInt(s.dataset.v) <= n);
  });
}
starPicker.querySelectorAll("span").forEach((s) => {
  s.onmouseenter = () => paintStars(parseInt(s.dataset.v));
  s.onmouseleave = () => paintStars(selectedStars);
  s.onclick = () => {
    selectedStars = parseInt(s.dataset.v);
    ratingInput.value = selectedStars;
    paintStars(selectedStars);
  };
});
document.getElementById("rateForm").onsubmit = (e) => {
  if (selectedStars < 1) {
    e.preventDefault();
    document.getElementById("rateErr").textContent = "Pumili ng bituin bago i-submit.";
  }
};

/* ============================================================
   START
============================================================ */
paintStars(selectedStars);
renderSentence();
buildTabs();
setEditMode(editMode);
render();
