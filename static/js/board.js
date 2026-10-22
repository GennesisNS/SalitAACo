// The AAC board: its screens, tile grids, sentence builder, edit mode and the rating stars.
// The vocabulary and this user's data arrive in the page as JSON (#board-data).

const boardData = JSON.parse(document.getElementById("board-data").textContent);
const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;

const VERB_BOARD = boardData.verb_category;
const FEELINGS_BOARD = boardData.feelings_board;
const SCREEN_KEY = "salitaaco-board-screen";
const RESTORE_KEY = "salitaaco-board-restore";
const EDIT_KEY = "salitaaco-board-edit";

const boards = {}; // { name: {name, icon, items} }
boardData.categories.forEach((board) => {
  boards[board.name] = board;
});

const customList = {}; // { word: {has_image, has_sound, image_url, sound_url, reset_url} }
boardData.customizations.forEach((it) => {
  customList[it.word] = it;
});

/* ============================================================
   APP STATE
============================================================ */
// The board is one page with four screens. Which one shows is the part of the
// address after the "#": "home", "boards", "boards/<board>" or "favorites".
// The navigation along the bottom and the board tiles are plain links to those.
const SECTION_SCREENS = ["home", "boards", "favorites"];
const SCREEN_TITLES = {
  home: "Ano ang gusto mong sabihin?",
  boards: "Pumili ng board",
  favorites: "Mga paborito kong salita",
};
let currentScreen = "home",
  currentAspect = "past",
  words = [];
let editMode = false;
let frequentItems = boardData.frequent_words; // [{word, use_count}, ...]
let _frequentRefreshTimer = null;

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

function isScreen(name) {
  if (!name) return false;
  if (SECTION_SCREENS.includes(name)) return true;
  return name.startsWith("boards/") && Boolean(boards[name.slice("boards/".length)]);
}
function screenInAddress() {
  try {
    const name = decodeURIComponent(location.hash.slice(1));
    return isScreen(name) ? name : null;
  } catch (e) {
    return null;
  }
}
// The board that is open, or null on the other screens.
function openBoard() {
  return currentScreen.startsWith("boards/") ? boards[currentScreen.slice("boards/".length)] : null;
}
// Saving a tile or a rating reloads the page at its plain address. The screen
// that was open is put back then, and only then: any other arrival starts at Home.
function keepScreenAcrossReload() {
  remember(RESTORE_KEY, "1");
}
const screenBeforeReload = recall(RESTORE_KEY) === "1" ? recall(SCREEN_KEY) : null;
remember(RESTORE_KEY, "0");

// A guardian who opened a child's board is there to set up its tiles, so it starts in edit mode.
editMode = boardData.managed || recall(EDIT_KEY) === "1";

// The Settings page links here with ?edit=1 to open the board in edit mode.
const pageUrl = new URL(location.href);
if (pageUrl.searchParams.get("edit") === "1") {
  editMode = true;
  remember(EDIT_KEY, "1");
  pageUrl.searchParams.delete("edit");
  history.replaceState(null, "", pageUrl);
}

async function loadFrequent(limit = 40) {
  // On a child's board opened by their guardian nothing is counted, so the list cannot have changed.
  if (!boardData.frequent_words_url) return;
  try {
    const res = await fetch(`${boardData.frequent_words_url}?limit=${limit}`).then((r) => r.json());
    frequentItems = res.ok ? res.items || [] : [];
  } catch (e) {
    frequentItems = [];
  }
}

// How often each board is opened is counted for the guardian's usage page.
function recordBoardOpen(board) {
  // A guardian looking at a child's board is not the child using it.
  if (!boardData.board_open_url) return;
  try {
    fetch(boardData.board_open_url, {
      method: "POST",
      headers: { "X-CSRFToken": csrfToken },
      body: new URLSearchParams({ board }),
    }).catch(() => {});
  } catch (e) {}
}

function incrementUsage(word) {
  // A guardian trying out a child's board is not the child talking: their taps are not counted.
  if (!boardData.increment_usage_url) return;
  // Fire-and-forget: don't block the UI on accounting.
  try {
    fetch(boardData.increment_usage_url, {
      method: "POST",
      headers: { "X-CSRFToken": csrfToken },
      body: new URLSearchParams({ word }),
    }).catch(() => {});
  } catch (e) {}
  // On the favorites screen, refresh it soon so rankings stay current.
  if (currentScreen === "favorites") {
    if (_frequentRefreshTimer) clearTimeout(_frequentRefreshTimer);
    _frequentRefreshTimer = setTimeout(() => {
      loadFrequent().then(renderGrid);
    }, 700);
  }
}

/* ============================================================
   SCREENS / GRIDS
============================================================ */
const titleEl = document.getElementById("screenTitle"),
  hintEl = document.getElementById("screenHint"),
  backToBoards = document.getElementById("backToBoards"),
  gridTitleEl = document.getElementById("gridTitle"),
  gridEl = document.getElementById("grid"),
  feelingsEl = document.getElementById("feelings"),
  feelingsGridEl = document.getElementById("feelingsGrid"),
  aspectBar = document.getElementById("aspectBar");

document.querySelectorAll("#aspectBar button").forEach((b) => {
  b.onclick = () => {
    currentAspect = b.dataset.a;
    document.querySelectorAll("#aspectBar button").forEach((x) => x.classList.remove("active"));
    b.classList.add("active");
    renderGrid();
  };
});

// Light the navigation item of the open screen. Links to other pages (Profile) are left alone.
function markNavigation() {
  const section = currentScreen.startsWith("boards") ? "boards" : currentScreen;
  document.querySelectorAll(".bottomNav a").forEach((link) => {
    const url = new URL(link.href);
    if (url.pathname !== location.pathname || !url.hash) return;
    const active = url.hash === `#${section}`;
    link.classList.toggle("active", active);
    if (active) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  });
}

function render() {
  const board = openBoard();
  const onHome = currentScreen === "home";
  titleEl.textContent = board ? `${board.icon_url ? "" : `${board.icon} `}${board.name}` : SCREEN_TITLES[currentScreen];
  // A family's own board may have an uploaded picture in place of an emoji.
  if (board && board.icon_url) titleEl.prepend(boardIcon(board, "titleIcon"));
  backToBoards.classList.toggle("hidden", !board);
  aspectBar.style.display = board && board.name === VERB_BOARD ? "flex" : "none";
  gridTitleEl.classList.toggle("hidden", !onHome);
  feelingsEl.classList.toggle("hidden", !onHome || !boards[FEELINGS_BOARD]);
  markNavigation();
  renderGrid();
}

function showScreen(name) {
  currentScreen = name;
  remember(SCREEN_KEY, name);
  render();
  // The list of favorites may have changed since the page loaded.
  if (name === "favorites") loadFrequent().then(renderGrid);
}
window.addEventListener("hashchange", () => {
  showScreen(screenInAddress() || "home");
  window.scrollTo(0, 0);
  // Opened by the child just now, not put back after a save.
  const board = openBoard();
  if (board) recordBoardOpen(board.name);
});

// The tile on this user's boards that says `word` (a verb in any of its forms), or null.
function findTile(word) {
  for (const board of Object.values(boards)) {
    for (const item of board.items) {
      if (item.w === word) return item;
      if (item.verb && [item.verb.past, item.verb.present, item.verb.future].includes(word)) return item;
    }
  }
  return null;
}

function findEmojiForWord(word) {
  const tile = findTile(word);
  return (tile && tile.e) || "📝";
}

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function renderGrid() {
  gridEl.innerHTML = "";
  feelingsGridEl.innerHTML = "";
  hintEl.classList.add("hidden");

  const board = openBoard();
  if (board) {
    renderTiles(gridEl, board.items);
  } else if (currentScreen === "boards") {
    renderBoards();
  } else if (currentScreen === "favorites") {
    renderFavorites();
  } else {
    renderTiles(gridEl, boardData.quick_words);
    if (boards[FEELINGS_BOARD]) renderTiles(feelingsGridEl, boards[FEELINGS_BOARD].items);
  }
}

// A board's uploaded picture (a family's own board may have one in place of an emoji).
function boardIcon(board, className) {
  const img = el("img", className);
  img.src = board.icon_url;
  img.alt = "";
  return img;
}

// The boards to choose from: each tile is a link to its board's screen.
function renderBoards() {
  Object.values(boards).forEach((board) => {
    const tile = el("a", "cell board");
    tile.href = `#boards/${encodeURIComponent(board.name)}`;
    tile.append(board.icon_url ? boardIcon(board, "customimg") : el("span", "emoji", board.icon), el("span", "", board.name));
    gridEl.appendChild(tile);
  });
}

// The words used most, most used first. Only words that are tiles on these boards
// now: not a tile that was deleted, on a board that was turned off, or a
// guardian's own tile while it is hidden.
function renderFavorites() {
  const frequent = frequentItems.filter((it) => findTile(it.word));
  if (frequent.length === 0) {
    const empty = el("div", "emptyBoard");
    empty.append(
      el("div", "emoji", "⭐"),
      el("b", "", "Wala pang paborito"),
      el("p", "", "Pindutin ang mga tile sa Home o sa mga board para mabuo ang listahang ito."),
    );
    gridEl.appendChild(empty);
    return;
  }
  hintEl.textContent = "Ang mga salitang pinakamadalas mong gamitin, ayon sa kung ilang beses mo na itong nagamit.";
  hintEl.classList.remove("hidden");
  renderTiles(
    gridEl,
    frequent.map((it) => ({
      w: it.word,
      e: findEmojiForWord(it.word),
      _useCount: it.use_count,
      _fromFrequent: true,
    })),
  );
}

function renderTiles(grid, items) {
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
    grid.appendChild(c);
  });
}

document.getElementById("editModeBtn").onclick = () => {
  setEditMode(!editMode);
};
function setEditMode(next) {
  editMode = next;
  // What a guardian does on a child's board must not change how their own board opens.
  if (!boardData.managed) remember(EDIT_KEY, editMode ? "1" : "0");
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
  keepScreenAcrossReload();
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
      keepScreenAcrossReload();
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
  keepScreenAcrossReload();
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
const undoBtn = document.getElementById("undoBtn");
function renderSentence() {
  const s = document.getElementById("sentence");
  s.innerHTML = "";
  playBtn.disabled = words.length === 0;
  undoBtn.disabled = words.length === 0;
  playBtn.textContent = playingIndex >= 0 ? "■ Itigil" : "▶ Patugtugin";
  if (words.length === 0) {
    s.appendChild(sentencePlaceholder);
    return;
  }
  words.forEach((w, i) => {
    const t = el("span", i === playingIndex ? "tag playing" : "tag");
    t.append(el("span", "tagEmoji", findEmojiForWord(w)), w);
    t.title = "Pindutin para alisin";
    t.onclick = () => {
      words.splice(i, 1);
      stopPlayback();
    };
    s.appendChild(t);
  });
}
// Takes back the last word only.
undoBtn.onclick = () => {
  words.pop();
  stopPlayback();
};
document.getElementById("clearBtn").onclick = () => {
  words = [];
  stopPlayback();
};

/* ---- play the sentence: one word after another. Each word plays, the first
        that exists: the family's own recording of the tile, the word in the
        child's family voice or the app's shared voice (boardData.tile_audio),
        and only failing those the device's own Filipino voice ---- */
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
    const audioUrl = custom && custom.has_sound ? custom.sound_url : boardData.tile_audio[queue[i]];
    await (audioUrl ? playRecording(audioUrl) : speakWord(queue[i]));
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
    return;
  }
  keepScreenAcrossReload();
};

/* ============================================================
   START
============================================================ */
paintStars(selectedStars);
renderSentence();
// The screen named in the address; after a save, the one that was open; otherwise Home.
currentScreen = screenInAddress() || (isScreen(screenBeforeReload) ? screenBeforeReload : "home");
if (!screenInAddress() && currentScreen !== "home") history.replaceState(null, "", `#${encodeURI(currentScreen)}`);
setEditMode(editMode);
showScreen(currentScreen);
