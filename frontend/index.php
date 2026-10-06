<?php

// Served at / through routes.php, so every link below is relative to the project root.
// If this file is the only one loaded, it was opened directly: forward to the real address.
if (count(get_included_files()) === 1) {
    header("Location: ../");
    exit;
}

require __DIR__ . "/../backend/config.php";
$loggedIn = isset($_SESSION["user_id"]);
$displayName = $_SESSION["display_name"] ?? "";
?>
<!DOCTYPE html>
<html lang="tl">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
    <title>SalitAACo - Filipino AAC</title>
    <link rel="stylesheet" href="frontend/css/index.css" />
  </head>
  <body>
    <div id="authScreen" class="<?php echo $loggedIn ? 'hidden' : ''; ?>">
      <div class="authBox">
        <h1>SalitAACo</h1>
        <p class="sub">Filipino AAC - Mag-log in para simulan</p>

        <div id="loginForm">
          <label>Username</label>
          <input id="loginUser" autocomplete="username" placeholder="username" />
          <label>Password</label>
          <input id="loginPass" type="password" autocomplete="current-password" placeholder="••••••••" />
          <div class="err" id="loginErr"></div>
          <button class="go" id="loginBtn">Mag-log in</button>
          <div class="switch">Wala ka pang account? <a id="toSignup">Mag-sign up</a></div>
        </div>

        <div id="signupForm" class="hidden">
          <label>Pangalan ng bata / user</label>
          <input id="suName" placeholder="hal. Miguel" />
          <label>Username</label>
          <input id="suUser" autocomplete="username" placeholder="username" />
          <label>Password</label>
          <input id="suPass" type="password" autocomplete="new-password" placeholder="min. 4 characters" />
          <div class="err" id="suErr"></div>
          <button class="go" id="signupBtn">Gumawa ng account</button>
          <div class="switch">May account ka na? <a id="toLogin">Mag-log in</a></div>
        </div>
      </div>
    </div>

    <div id="app" class="<?php echo $loggedIn ? '' : 'hidden'; ?>">
      <header>
        <div class="headtop">
          <h1>SalitAACo <span style="font-size: 12px; color: var(--sub); font-weight: 400">Filipino AAC</span></h1>
          <div class="userbadge">
            <span id="miniAvatar" class="miniAvatar">👤</span>
            <span id="whoami"><?php echo $loggedIn ? htmlspecialchars($displayName) : ""; ?></span>
            <button id="settingsBtn">⚙️ Settings</button>
            <button id="logoutBtn">Log out</button>
          </div>
        </div>
        <div class="sentence-row">
          <div id="sentence"><span id="placeholder" style="color: var(--sub)">Pindutin ang mga salita...</span></div>
          <button class="iconbtn" id="clearBtn">✕ Burahin</button>
        </div>
        <div class="toggles">
          <label><input type="checkbox" id="darkToggle" /> Madilim na tema</label>
          <button class="iconbtn" id="editModeBtn" style="padding: 6px 12px; min-height: auto">
            ✏️ I-edit ang mga cell
          </button>
          <button class="iconbtn" id="rateBtn" style="padding: 6px 12px; min-height: auto">⭐ I-rate ang app</button>
        </div>
      </header>
      <main>
        <div class="tabs" id="tabs"></div>
        <div class="aspect" id="aspectBar" style="display: none">
          <button data-a="past" class="active">nangyari na</button>
          <button data-a="present">ngayon</button>
          <button data-a="future">mamaya</button>
        </div>
        <div class="grid" id="grid"></div>
      </main>
      <footer>Gawa para sa mga batang Pilipino na nangangailangan ng tulong sa pakikipag-usap.</footer>
    </div>

    <input type="file" id="imgFileInput" accept="image/*" class="hidden" />
    <input type="file" id="avatarFileInput" accept="image/*" class="hidden" />

    <!-- ============== SETTINGS MODAL ============== -->
    <div id="settingsModal" class="settingsBackdrop hidden">
      <div class="settingsBox" role="dialog" aria-modal="true" aria-labelledby="settingsTitle">
        <div class="settingsHeader">
          <h2 id="settingsTitle">⚙️ Settings</h2>
          <button class="closeBtn" id="settingsCloseBtn" aria-label="Isara">&times;</button>
        </div>
        <div class="settingsTabs">
          <button data-stab="tiles" class="active">🧩 Mga Tile</button>
          <button data-stab="account">👤 Account</button>
        </div>
        <div class="settingsBody">
          <!-- TILES TAB -->
          <div id="stab-tiles">
            <h3>Pag-edit ng mga Tile / Cell</h3>
            <p class="desc">
              Dito matatagpuan ang toggle para mag-edit ng mga tile. Kapag naka-on, lalabas sa bawat tile ang mga button
              para: magpalit ng larawan (🖼️), mag-record ng tunog (🎙️), o ibalik sa default (↺).
            </p>
            <div class="tilesCard">
              <button
                class="iconbtn"
                id="settingsEditModeBtn"
                style="width: 100%; justify-content: center; padding: 12px; font-weight: 600"
              >
                ✏️ Buksan ang Edit Mode
              </button>
              <p style="margin: 10px 0 0; font-size: 12px; color: var(--sub); line-height: 1.5">
                💡 Tips: <br />
                • 🖼️ <b>Larawan</b> – Mag-upload ng litrato para sa salita (hal. totoong larawan ng "Nanay").<br />
                • 🎙️ <b>Tunog</b> – Mag-record ng sariling boses para sa salita (awto-ni-play kapag pinindot ang
                tile).<br />
                • ↺ <b>I-reset</b> – Ibalik ang default na emoji at gamitin ang boses ng TTS.
              </p>
            </div>
          </div>

          <!-- ACCOUNT TAB -->
          <div id="stab-account" class="hidden">
            <h3>Impormasyon ng Account</h3>
            <p class="desc">Baguhin ang pangalan, edad, at larawan ng profile na nakikita sa itaas.</p>

            <div class="avatarRow">
              <div class="avatarPrev" id="setAvatarPrev">👤</div>
              <div class="avatarActions">
                <button class="secondaryBtn" id="setAvatarBtn">📸 Mag-upload ng larawan</button>
                <button
                  class="secondaryBtn"
                  id="setRemoveAvatarBtn"
                  style="color: var(--danger); border-color: #f2c1bc"
                >
                  🗑️ Alisin ang larawan
                </button>
              </div>
            </div>

            <label>Pangalan (Display Name)</label>
            <input type="text" id="setName" placeholder="hal. Miguel" />

            <div class="row">
              <div>
                <label>Username</label>
                <input type="text" id="setUsername" disabled style="opacity: 0.7; cursor: not-allowed" />
              </div>
              <div>
                <label>Edad (opsiyonal)</label>
                <input type="number" id="setAge" min="0" max="150" placeholder="hal. 7" />
              </div>
            </div>

            <div class="err" id="setProfErr"></div>
            <div class="ok" id="setProfOk"></div>
            <button class="primaryBtn" id="setSaveProfBtn" style="margin-top: 14px">💾 I-save ang profile</button>

            <hr class="sectionDivider" />

            <h3>Palitan ang Password</h3>
            <p class="desc">Para sa kaligtasan, kailangang ilagay ang kasalukuyang password bago magpalit.</p>

            <label>Kasalukuyang Password</label>
            <input type="password" id="setCurPass" placeholder="••••••••" />
            <div class="row">
              <div>
                <label>Bagong Password (min. 4)</label>
                <input type="password" id="setNewPass" placeholder="min. 4 characters" />
              </div>
              <div>
                <label>Kumpirmahin ang Bagong Password</label>
                <input type="password" id="setConfPass" placeholder="ulitin ang bago" />
              </div>
            </div>

            <div class="err" id="setPwErr"></div>
            <div class="ok" id="setPwOk"></div>
            <button class="primaryBtn" id="setSavePwBtn" style="margin-top: 14px">🔑 I-save ang bagong password</button>

            <hr class="sectionDivider" />

            <h3 style="color: var(--danger)">Burahin ang Account</h3>
            <p class="desc">
              Permanenteng mabubura ang account, lahat ng custom na larawan, at mga recording. Hindi na ito mababalik.
            </p>
            <button class="dangerBtn" id="setDelBtn">⚠️ Permanente nang burahin ang account na ito</button>
          </div>
        </div>
      </div>
    </div>

    <!-- ============== DELETE CONFIRM DIALOG ============== -->
    <div id="deleteConfirmModal" class="confirmBackdrop hidden">
      <div class="confirmBox" role="dialog" aria-modal="true">
        <h3>⚠️ Sigurado ka na ba?</h3>
        <p>
          Ang lahat ng datos ng account (mga larawan, recording, at mismong account) ay mabubura na <b>permanente</b> at
          hindi na maibabalik. I-type ang password para kumpirmahin:
        </p>
        <input
          type="password"
          id="delConfirmPass"
          placeholder="Ilagay ang password"
          style="
            width: 100%;
            padding: 11px 12px;
            border: 1px solid var(--line);
            border-radius: 10px;
            background: var(--bg);
            color: var(--ink);
            font-size: 15px;
            margin-top: 6px;
          "
        />
        <div class="err" id="delErr"></div>
        <div class="confirmRow">
          <button class="secondaryBtn" id="delCancelBtn">Huwag muna</button>
          <button class="dangerBtn solid" id="delProceedBtn">Oo, burahin na</button>
        </div>
      </div>
    </div>

    <!-- ============== RATE THE APP MODAL ============== -->
    <div id="rateModal" class="settingsBackdrop hidden">
      <div class="settingsBox" role="dialog" aria-modal="true" aria-labelledby="rateTitle" style="max-width: 420px">
        <div class="settingsHeader">
          <h2 id="rateTitle">⭐ I-rate ang SalitAACo</h2>
          <button class="closeBtn" id="rateCloseBtn" aria-label="Isara">&times;</button>
        </div>
        <div class="settingsBody ratingBox">
          <p class="desc">
            Tumulong ito sa mga developer na mapaganda pa ang app. Makikita ng mga developer ang iyong rating at komento
            sa admin dashboard.
          </p>
          <div class="starPicker" id="starPicker">
            <span data-v="1">★</span>
            <span data-v="2">★</span>
            <span data-v="3">★</span>
            <span data-v="4">★</span>
            <span data-v="5">★</span>
          </div>
          <label style="margin-top: 0">Komento (opsiyonal)</label>
          <textarea id="rateComment" placeholder="Ano ang magagandang bahagi? Ano pa ang dapat idagdag?"></textarea>
          <div class="err" id="rateErr"></div>
          <div class="ok" id="rateOk"></div>
          <button class="primaryBtn" id="rateSubmitBtn" style="margin-top: 14px; width: 100%">
            💾 I-submit ang rating
          </button>
        </div>
      </div>
    </div>

    <script>
      /* ============================================================
   DATA
============================================================ */
      const verbs = [
        { w: "kain", e: "🍚", past: "kumain", present: "kumakain", future: "kakain" },
        { w: "inom", e: "🥤", past: "uminom", present: "umiinom", future: "iinom" },
        { w: "laro", e: "⚽", past: "naglaro", present: "naglalaro", future: "maglalaro" },
        { w: "tulog", e: "😴", past: "natulog", present: "natutulog", future: "matutulog" },
        { w: "ligo", e: "🚿", past: "naligo", present: "naliligo", future: "maliligo" },
        { w: "punta", e: "🚶", past: "pumunta", present: "pumupunta", future: "pupunta" },
        { w: "kuha", e: "🤲", past: "kumuha", present: "kumukuha", future: "kukuha" },
        { w: "bili", e: "🛍️", past: "bumili", present: "bumibili", future: "bibili" },
        { w: "sulat", e: "✏️", past: "sumulat", present: "sumusulat", future: "susulat" },
        { w: "basa", e: "📖", past: "nagbasa", present: "nagbabasa", future: "magbabasa" },
        { w: "tawag", e: "📞", past: "tumawag", present: "tumatawag", future: "tatawag" },
        { w: "hingi", e: "🙏", past: "humingi", present: "humihingi", future: "hihingi" },
        { w: "tigil", e: "✋", past: "tumigil", present: "tumitigil", future: "titigil" },
        { w: "lakad", e: "🚶‍♂️", past: "lumakad", present: "lumalakad", future: "lalakad" },
        { w: "takbo", e: "🏃", past: "tumakbo", present: "tumatakbo", future: "tatakbo" },
      ];
      const FREQ_CAT = "🔁 Madalas Gamitin";
      const categories = {
        Tao: [
          { w: "ako", e: "🙋" },
          { w: "ko", e: "✋" },
          { w: "ikaw", e: "👉" },
          { w: "ka", e: "🫵" },
          { w: "siya", e: "🧍" },
          { w: "tayo", e: "👨‍👩‍👧" },
          { w: "sila", e: "👥" },
          { w: "mama", e: "👩" },
          { w: "papa", e: "👨" },
          { w: "ate", e: "👧" },
          { w: "kuya", e: "👦" },
          { w: "lola", e: "👵" },
          { w: "lolo", e: "👴" },
          { w: "tita", e: "🧑‍🦰" },
          { w: "tito", e: "🧔" },
        ],
        Bagay: [
          { w: "pera", e: "💵" },
          { w: "sukli", e: "🪙" },
          { w: "gamot", e: "💊" },
          { w: "doktor", e: "🩺" },
          { w: "magkano", e: "❓" },
          { w: "tulad nito", e: "👆" },
          { w: "jeep", e: "🚙" },
          { w: "para", e: "🛑" },
          { w: "tawagan si Nanay", e: "📱" },
          { w: "tawagan si Tatay", e: "📱" },
          { w: "oo", e: "✅" },
          { w: "hindi", e: "❌" },
          { w: "po", e: "🙇" },
          { w: "opo", e: "🙇" },
          { w: "ay", e: "✨" },
          { w: "na", e: "⏳" },
          { w: "gusto ko", e: "❤️" },
          { w: "ayaw ko", e: "🚫" },
          { w: "salamat", e: "🙏" },
          { w: "pasensya na", e: "😔" },
          { w: "tulong", e: "🆘" },
          { w: "sakit", e: "🚨" },
          { w: "masakit dito", e: "👇" },
        ],
        Pagkain: [
          { w: "bigas", e: "🍚" },
          { w: "isda", e: "🐟" },
          { w: "gulay", e: "🥬" },
          { w: "prutas", e: "🍌" },
        ],
        Lugar: [
          { w: "bahay", e: "🏠" },
          { w: "sala", e: "🛋️" },
          { w: "kwarto", e: "🚪" },
          { w: "banyo", e: "🚽" },
          { w: "kusina", e: "🍳" },
          { w: "paaralan", e: "🏫" },
          { w: "labas", e: "🌳" },
          { w: "loob", e: "🏡" },
        ],
        Pandiwa: verbs.map((v) => ({ w: v.w, e: v.e, verb: v })),
        Pakiramdam: [
          { w: "masaya", e: "😄" },
          { w: "malungkot", e: "😢" },
          { w: "galit", e: "😠" },
          { w: "takot", e: "😨" },
          { w: "gutom", e: "🍽️" },
          { w: "uhaw", e: "💧" },
          { w: "pagod", e: "😩" },
          { w: "masakit", e: "🤕" },
          { w: "mainit", e: "🥵" },
          { w: "malamig", e: "🥶" },
        ],
      };

      /* ============================================================
   AUTH (talks to auth.php)
============================================================ */
      document.getElementById("toSignup").onclick = () => {
        document.getElementById("loginForm").classList.add("hidden");
        document.getElementById("signupForm").classList.remove("hidden");
      };
      document.getElementById("toLogin").onclick = () => {
        document.getElementById("signupForm").classList.add("hidden");
        document.getElementById("loginForm").classList.remove("hidden");
      };

      document.getElementById("signupBtn").onclick = async () => {
        const btn = document.getElementById("signupBtn");
        const errEl = document.getElementById("suErr");
        errEl.textContent = "";
        btn.disabled = true;
        const origText = btn.textContent;
        btn.textContent = "Nagpoproseso...";
        try {
          const username = document.getElementById("suUser").value.trim();
          const password = document.getElementById("suPass").value;
          const displayName = document.getElementById("suName").value.trim();
          if (!displayName) {
            errEl.textContent = "Ilagay ang pangalan ng bata / user.";
            return;
          }
          if (!username) {
            errEl.textContent = "Ilagay ang username.";
            return;
          }
          if (password.length < 4) {
            errEl.textContent = "Ang password ay dapat may hindi bababa sa 4 na character.";
            return;
          }
          const body = new URLSearchParams({ action: "signup", username, password, displayName });
          const raw = await fetch("api/auth", { method: "POST", body });
          const text = await raw.text();
          let res;
          try {
            res = JSON.parse(text);
          } catch {
            res = {
              ok: false,
              error:
                "Hindi maunawaan ang tugon ng server. Siguraduhing tumatakbo ang MySQL at na-import ang database.sql.",
            };
          }
          if (!res.ok) {
            errEl.textContent = res.error;
            return;
          }
          location.reload();
        } catch (e) {
          errEl.textContent = "Hindi makontak ang server. Tingnan kung naka-on ang XAMPP Apache at MySQL.";
        } finally {
          btn.disabled = false;
          btn.textContent = origText;
        }
      };

      document.getElementById("loginBtn").onclick = async () => {
        const btn = document.getElementById("loginBtn");
        const errEl = document.getElementById("loginErr");
        errEl.textContent = "";
        btn.disabled = true;
        const origText = btn.textContent;
        btn.textContent = "Nagpoproseso...";
        try {
          const username = document.getElementById("loginUser").value.trim();
          const password = document.getElementById("loginPass").value;
          if (!username) {
            errEl.textContent = "Ilagay ang username.";
            return;
          }
          if (!password) {
            errEl.textContent = "Ilagay ang password.";
            return;
          }
          const body = new URLSearchParams({ action: "login", username, password });
          const raw = await fetch("api/auth", { method: "POST", body });
          const text = await raw.text();
          let res;
          try {
            res = JSON.parse(text);
          } catch {
            res = {
              ok: false,
              error:
                "Hindi maunawaan ang tugon ng server. Siguraduhing tumatakbo ang MySQL at na-import ang database.sql.",
            };
          }
          if (!res.ok) {
            errEl.textContent = res.error;
            return;
          }
          location.reload();
        } catch (e) {
          errEl.textContent = "Hindi makontak ang server. Tingnan kung naka-on ang XAMPP Apache at MySQL.";
        } finally {
          btn.disabled = false;
          btn.textContent = origText;
        }
      };

      document.getElementById("logoutBtn").onclick = async () => {
        try {
          await fetch("api/auth", { method: "POST", body: new URLSearchParams({ action: "logout" }) });
        } catch (e) {}
        location.reload();
      };

      /* ============================================================
   APP STATE
============================================================ */
      let currentCat = FREQ_CAT,
        currentAspect = "past",
        words = [];
      let editMode = false;
      let customList = {}; // { word: {has_image, has_sound} }
      let frequentItems = []; // [{word, use_count, has_image, has_sound, last_used}, ...]
      let _frequentRefreshTimer = null;

      const isLoggedIn = <?php echo $loggedIn ? 'true' : 'false'; ?>;

      async function loadCustomList() {
        const res = await fetch("api/app?action=list").then((r) => r.json());
        customList = {};
        if (res.ok) {
          res.items.forEach((it) => {
            customList[it.word] = it;
          });
        }
      }

      async function loadFrequent(limit = 40) {
        try {
          const res = await fetch(`api/app?action=frequent_list&limit=${limit}`).then((r) => r.json());
          frequentItems = res.ok ? res.items || [] : [];
        } catch (e) {
          frequentItems = [];
        }
      }

      function incrementUsage(word) {
        // Fire-and-forget: don't block the UI on accounting.
        try {
          fetch("api/app", {
            method: "POST",
            body: new URLSearchParams({ action: "increment_usage", word }),
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

      if (isLoggedIn) {
        Promise.all([loadCustomList(), loadFrequent()]).then(() => {
          buildTabs();
          render();
        });
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
          b.textContent = cat;
          if (cat === currentCat) b.classList.add("active");
          b.onclick = async () => {
            currentCat = cat;
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
        document
          .querySelectorAll("#tabs button")
          .forEach((b) => b.classList.toggle("active", b.textContent === currentCat));
        aspectBar.style.display = currentCat === "Pandiwa" ? "flex" : "none";
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
          const c = document.createElement("button");
          c.className = "cell";
          const visual = custom.has_image
            ? `<img class="customimg" src="api/app?action=image&word=${encodeURIComponent(label)}" alt="${label}">`
            : `<span class="emoji">${item.e}</span>`;
          const soundMark = custom.has_sound ? `<span class="soundmark">🎙️</span>` : "";
          const useCountMark =
            item._fromFrequent && item._useCount
              ? `<span class="usecount" title="Ginamit nang ${item._useCount} na beses">×${item._useCount}</span>`
              : "";
          c.innerHTML = `${useCountMark}${soundMark}${visual}<span>${label}</span>`;

          if (editMode) {
            const editRow = document.createElement("div");
            editRow.className = "editRow";
            editRow.innerHTML = `
        <button data-act="img" title="Palitan ang larawan">🖼️</button>
        <button data-act="rec" title="Mag-record ng tunog">🎙️</button>
        <button data-act="reset" title="I-reset">↺</button>`;
            editRow.querySelector('[data-act="img"]').onclick = (ev) => {
              ev.stopPropagation();
              pickImage(label);
            };
            editRow.querySelector('[data-act="rec"]').onclick = (ev) => {
              ev.stopPropagation();
              toggleRecord(label, editRow.querySelector('[data-act="rec"]'));
            };
            editRow.querySelector('[data-act="reset"]').onclick = async (ev) => {
              ev.stopPropagation();
              await fetch("api/app", {
                method: "POST",
                body: new URLSearchParams({ action: "reset", word: label }),
              });
              await loadCustomList();
              if (currentCat === FREQ_CAT) await loadFrequent();
              renderGrid();
            };
            c.appendChild(editRow);
            c.onclick = null;
          } else {
            c.onclick = () =>
              addWord(label, custom.has_sound ? `api/app?action=sound&word=${encodeURIComponent(label)}` : null);
          }
          gridEl.appendChild(c);
        });
      }

      document.getElementById("editModeBtn").onclick = () => {
        setEditMode(!editMode);
      };
      function setEditMode(next) {
        editMode = next;
        const barBtn = document.getElementById("editModeBtn");
        const setBtn = document.getElementById("settingsEditModeBtn");
        const labelOn = "✓ Tapos na mag-edit";
        const labelOff = "✏️ I-edit ang mga cell";
        barBtn.classList.toggle("editing", editMode);
        barBtn.textContent = editMode ? labelOn : labelOff;
        if (setBtn) {
          setBtn.classList.toggle("editing", editMode);
          setBtn.textContent = editMode ? "✓ Tapos na mag-edit (tapusin)" : "✏️ Buksan ang Edit Mode";
        }
        renderGrid();
      }
      if (document.getElementById("settingsEditModeBtn")) {
        document.getElementById("settingsEditModeBtn").onclick = () => {
          setEditMode(!editMode);
        };
      }

      /* ---- editable images (uploads to api.php -> stored in MySQL) ---- */
      const imgFileInput = document.getElementById("imgFileInput");
      let pendingImgWord = null;
      function pickImage(word) {
        pendingImgWord = word;
        imgFileInput.click();
      }
      imgFileInput.onchange = async () => {
        const file = imgFileInput.files[0];
        if (!file || !pendingImgWord) return;
        const fd = new FormData();
        fd.append("action", "save_image");
        fd.append("word", pendingImgWord);
        fd.append("image", file);
        await fetch("api/app", { method: "POST", body: fd });
        await loadCustomList();
        renderGrid();
        imgFileInput.value = "";
      };

      /* ---- recordable sounds (uploads to api.php -> stored in MySQL) ---- */
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
            const blob = new Blob(recChunks, { type: "audio/webm" });
            const fd = new FormData();
            fd.append("action", "save_sound");
            fd.append("word", word);
            fd.append("sound", blob, "sound.webm");
            await fetch("api/app", { method: "POST", body: fd });
            await loadCustomList();
            renderGrid();
            stream.getTracks().forEach((t) => t.stop());
            recordingWord = null;
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

      /* ============================================================
   SENTENCE BUILDER
============================================================ */
      function addWord(w, customSoundUrl) {
        words.push(w);
        renderSentence();
        incrementUsage(w);
        if (customSoundUrl) {
          const a = new Audio(customSoundUrl);
          a.play().catch(() => {});
        }
      }
      function renderSentence() {
        const s = document.getElementById("sentence");
        const ph = document.getElementById("placeholder");
        s.innerHTML = "";
        if (words.length === 0) {
          s.appendChild(ph);
          return;
        }
        words.forEach((w, i) => {
          const t = document.createElement("span");
          t.className = "tag";
          t.textContent = w;
          t.onclick = () => {
            words.splice(i, 1);
            renderSentence();
          };
          s.appendChild(t);
        });
      }
      document.getElementById("clearBtn").onclick = () => {
        words = [];
        renderSentence();
      };
      window.addEventListener("load", () => {
        renderSentence();
      });
      document.getElementById("darkToggle").onchange = (e) => {
        document.documentElement.setAttribute("data-theme", e.target.checked ? "dark" : "light");
      };

      /* ============================================================
   SETTINGS MODAL + ACCOUNT SETTINGS
============================================================ */
      const avatarFileInput = document.getElementById("avatarFileInput");
      const settingsModal = document.getElementById("settingsModal");
      const delConfirmModal = document.getElementById("deleteConfirmModal");

      async function authJson(body, opts = {}) {
        const raw = await fetch("api/auth", { method: "POST", body, ...opts });
        const text = await raw.text();
        try {
          return JSON.parse(text);
        } catch {
          return { ok: false, error: "Hindi maunawaan ang tugon ng server." };
        }
      }
      function clearMsgs(...ids) {
        ids.forEach((id) => {
          const el = document.getElementById(id);
          if (el) el.textContent = "";
        });
      }
      function setBtnState(btn, loading, origText, loadingText = "Nagpoproseso...") {
        if (!btn) return;
        btn.disabled = loading;
        btn.textContent = loading ? loadingText : origText;
      }
      function avatarUrl() {
        return `api/auth?action=avatar&_t=${Date.now()}`;
      }
      function refreshAvatars(hasAvatar) {
        const mini = document.getElementById("miniAvatar");
        const prev = document.getElementById("setAvatarPrev");
        const render = (container) => {
          if (!container) return;
          if (hasAvatar) {
            container.innerHTML = `<img src="${avatarUrl()}" alt="avatar">`;
          } else {
            container.innerHTML = "👤";
          }
        };
        render(mini);
        render(prev);
      }
      function openSettings() {
        settingsModal.classList.remove("hidden");
        switchSettingsTab("tiles");
        loadProfileToSettings();
      }
      function closeSettings() {
        settingsModal.classList.add("hidden");
      }
      function switchSettingsTab(name) {
        document.querySelectorAll(".settingsTabs button").forEach((b) => {
          b.classList.toggle("active", b.dataset.stab === name);
        });
        ["tiles", "account"].forEach((t) => {
          const el = document.getElementById("stab-" + t);
          if (el) el.classList.toggle("hidden", t !== name);
        });
      }
      document.querySelectorAll(".settingsTabs button").forEach((b) => {
        b.onclick = () => switchSettingsTab(b.dataset.stab);
      });
      document.getElementById("settingsBtn").onclick = openSettings;
      document.getElementById("settingsCloseBtn").onclick = closeSettings;
      settingsModal.onclick = (e) => {
        if (e.target === settingsModal) closeSettings();
      };

      async function loadProfileToSettings() {
        clearMsgs("setProfErr", "setProfOk", "setPwErr", "setPwOk", "delErr");
        const res = await authJson(new URLSearchParams({ action: "get_profile" }));
        if (!res.ok) return;
        const p = res.profile;
        document.getElementById("setName").value = p.displayName || "";
        document.getElementById("setUsername").value = p.username || "";
        document.getElementById("setAge").value = (p.age ?? "").toString();
        refreshAvatars(p.hasAvatar);
        document.getElementById("setCurPass").value = "";
        document.getElementById("setNewPass").value = "";
        document.getElementById("setConfPass").value = "";
      }

      /* Save profile (name + age) */
      const setSaveProfBtn = document.getElementById("setSaveProfBtn");
      const setSaveProfBtnOrig = setSaveProfBtn.textContent;
      setSaveProfBtn.onclick = async () => {
        clearMsgs("setProfErr", "setProfOk");
        const displayName = document.getElementById("setName").value.trim();
        const age = document.getElementById("setAge").value.trim();
        if (!displayName) {
          document.getElementById("setProfErr").textContent = "Ilagay ang pangalan.";
          return;
        }
        setBtnState(setSaveProfBtn, true, setSaveProfBtnOrig);
        try {
          const res = await authJson(new URLSearchParams({ action: "update_profile", displayName, age }));
          if (!res.ok) {
            document.getElementById("setProfErr").textContent = res.error;
            return;
          }
          document.getElementById("whoami").textContent = displayName;
          document.getElementById("setProfOk").textContent = "✓ Naka-save na ang profile.";
        } finally {
          setBtnState(setSaveProfBtn, false, setSaveProfBtnOrig);
        }
      };

      /* Upload avatar */
      document.getElementById("setAvatarBtn").onclick = () => avatarFileInput.click();
      avatarFileInput.onchange = async () => {
        const f = avatarFileInput.files[0];
        if (!f) return;
        clearMsgs("setProfErr", "setProfOk");
        const fd = new FormData();
        fd.append("action", "upload_avatar");
        fd.append("avatar", f);
        const orig = setSaveProfBtn.textContent;
        setBtnState(setSaveProfBtn, true, orig, "Nag-uupload...");
        try {
          const res = await authJson(fd);
          if (!res.ok) {
            document.getElementById("setProfErr").textContent = res.error;
            return;
          }
          refreshAvatars(true);
          document.getElementById("setProfOk").textContent = "✓ Nai-save na ang larawan.";
        } finally {
          setBtnState(setSaveProfBtn, false, orig);
          avatarFileInput.value = "";
        }
      };
      document.getElementById("setRemoveAvatarBtn").onclick = async () => {
        clearMsgs("setProfErr", "setProfOk");
        const res = await authJson(new URLSearchParams({ action: "remove_avatar" }));
        if (!res.ok) {
          document.getElementById("setProfErr").textContent = res.error;
          return;
        }
        refreshAvatars(false);
        document.getElementById("setProfOk").textContent = "✓ Naalis na ang larawan.";
      };

      /* Change password */
      const setSavePwBtn = document.getElementById("setSavePwBtn");
      const setSavePwBtnOrig = setSavePwBtn.textContent;
      setSavePwBtn.onclick = async () => {
        clearMsgs("setPwErr", "setPwOk");
        const cur = document.getElementById("setCurPass").value;
        const nw = document.getElementById("setNewPass").value;
        const cf = document.getElementById("setConfPass").value;
        if (!cur) {
          document.getElementById("setPwErr").textContent = "Ilagay ang kasalukuyang password.";
          return;
        }
        if (nw.length < 4) {
          document.getElementById("setPwErr").textContent =
            "Ang bagong password ay dapat may hindi bababa sa 4 na character.";
          return;
        }
        if (nw !== cf) {
          document.getElementById("setPwErr").textContent = "Hindi magkatugma ang bagong password at kumpirmasyon.";
          return;
        }
        setBtnState(setSavePwBtn, true, setSavePwBtnOrig);
        try {
          const res = await authJson(
            new URLSearchParams({
              action: "change_password",
              currentPassword: cur,
              newPassword: nw,
              confirmPassword: cf,
            }),
          );
          if (!res.ok) {
            document.getElementById("setPwErr").textContent = res.error;
            return;
          }
          document.getElementById("setCurPass").value = "";
          document.getElementById("setNewPass").value = "";
          document.getElementById("setConfPass").value = "";
          document.getElementById("setPwOk").textContent = "✓ Nabago na ang password.";
        } finally {
          setBtnState(setSavePwBtn, false, setSavePwBtnOrig);
        }
      };

      /* Delete account flow */
      document.getElementById("setDelBtn").onclick = () => {
        document.getElementById("delConfirmPass").value = "";
        clearMsgs("delErr");
        delConfirmModal.classList.remove("hidden");
      };
      document.getElementById("delCancelBtn").onclick = () => delConfirmModal.classList.add("hidden");
      delConfirmModal.onclick = (e) => {
        if (e.target === delConfirmModal) delConfirmModal.classList.add("hidden");
      };
      const delProceedBtn = document.getElementById("delProceedBtn");
      const delProceedBtnOrig = delProceedBtn.textContent;
      delProceedBtn.onclick = async () => {
        clearMsgs("delErr");
        const pw = document.getElementById("delConfirmPass").value;
        if (!pw) {
          document.getElementById("delErr").textContent = "Ilagay ang password para kumpirmahin.";
          return;
        }
        setBtnState(delProceedBtn, true, delProceedBtnOrig, "Binubura...");
        try {
          const res = await authJson(new URLSearchParams({ action: "delete_account", password: pw }));
          if (!res.ok) {
            document.getElementById("delErr").textContent = res.error;
            return;
          }
          delConfirmModal.classList.add("hidden");
          location.reload();
        } finally {
          setBtnState(delProceedBtn, false, delProceedBtnOrig);
        }
      };

      /* Load profile + header avatar on app start */
      if (isLoggedIn) {
        (async () => {
          const res = await authJson(new URLSearchParams({ action: "get_profile" }));
          if (res.ok) {
            refreshAvatars(res.profile.hasAvatar);
            if (res.profile.displayName) document.getElementById("whoami").textContent = res.profile.displayName;
          }
        })();
      }

      /* ============================================================
   RATE THE APP
============================================================ */
      const rateModal = document.getElementById("rateModal");
      const starPicker = document.getElementById("starPicker");
      let selectedStars = 0;

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
          paintStars(selectedStars);
        };
      });

      async function apiJson(body) {
        const raw = await fetch("api/app", { method: "POST", body });
        const text = await raw.text();
        try {
          return JSON.parse(text);
        } catch {
          return { ok: false, error: "Hindi maunawaan ang tugon ng server." };
        }
      }

      document.getElementById("rateBtn").onclick = async () => {
        clearMsgs("rateErr", "rateOk");
        selectedStars = 0;
        document.getElementById("rateComment").value = "";
        paintStars(0);
        rateModal.classList.remove("hidden");
        try {
          const res = await apiJson(new URLSearchParams({ action: "get_my_rating" }));
          if (res.ok && res.rating) {
            selectedStars = res.rating;
            paintStars(selectedStars);
            document.getElementById("rateComment").value = res.comment || "";
          }
        } catch (e) {}
      };
      document.getElementById("rateCloseBtn").onclick = () => rateModal.classList.add("hidden");
      rateModal.onclick = (e) => {
        if (e.target === rateModal) rateModal.classList.add("hidden");
      };

      const rateSubmitBtn = document.getElementById("rateSubmitBtn");
      const rateSubmitBtnOrig = rateSubmitBtn.textContent;
      rateSubmitBtn.onclick = async () => {
        clearMsgs("rateErr", "rateOk");
        if (selectedStars < 1) {
          document.getElementById("rateErr").textContent = "Pumili ng bituin bago i-submit.";
          return;
        }
        setBtnState(rateSubmitBtn, true, rateSubmitBtnOrig, "Nagpoproseso...");
        try {
          const res = await apiJson(
            new URLSearchParams({
              action: "submit_rating",
              rating: String(selectedStars),
              comment: document.getElementById("rateComment").value.trim(),
            }),
          );
          if (!res.ok) {
            document.getElementById("rateErr").textContent = res.error;
            return;
          }
          document.getElementById("rateOk").textContent = "✓ Salamat sa iyong rating!";
        } finally {
          setBtnState(rateSubmitBtn, false, rateSubmitBtnOrig);
        }
      };
    </script>
  </body>
</html>
