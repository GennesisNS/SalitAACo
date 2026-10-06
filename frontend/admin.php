<?php

// Served at /admin through routes.php, so every link below is relative to the project root.
// If this file is the only one loaded, it was opened directly: forward to the real address.
if (count(get_included_files()) === 1) {
    header("Location: ../admin");
    exit;
}

require __DIR__ . "/../backend/config.php";
$loggedIn = isset($_SESSION["user_id"]);
$isAdmin = $loggedIn && !empty($_SESSION["is_admin"]);
?>
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>SalitAACo - Admin Dashboard</title>
    <link rel="stylesheet" href="frontend/css/admin.css" />
  </head>
  <body>
    <?php if (!$loggedIn): ?>
    <div class="centerScreen">
      <div class="box">
        <h1>Admin dashboard</h1>
        <p class="sub">Mag-log in gamit ang admin account</p>
        <label>Username</label>
        <input id="aUser" autocomplete="username" />
        <label>Password</label>
        <input id="aPass" type="password" autocomplete="current-password" />
        <div class="err" id="aErr"></div>
        <button class="go" id="aLoginBtn">Mag-log in</button>
      </div>
    </div>
    <script>
      document.getElementById("aLoginBtn").onclick = async () => {
        const errEl = document.getElementById("aErr");
        errEl.textContent = "";
        const username = document.getElementById("aUser").value.trim();
        const password = document.getElementById("aPass").value;
        if (!username || !password) {
          errEl.textContent = "Punan ang username at password.";
          return;
        }
        const body = new URLSearchParams({ action: "login", username, password });
        const raw = await fetch("api/auth", { method: "POST", body });
        let res;
        try {
          res = JSON.parse(await raw.text());
        } catch {
          res = { ok: false, error: "Server error." };
        }
        if (!res.ok) {
          errEl.textContent = res.error;
          return;
        }
        location.reload();
      };
    </script>

    <?php elseif (!$isAdmin): ?>
    <div class="centerScreen">
      <div class="box denied">
        <div class="big">🔒</div>
        <h1>Access denied</h1>
        <p class="sub">
          Naka-log in ka pero hindi admin ang account na ito.<br />
          Para gawing admin, patakbuhin ito sa phpMyAdmin:<br />
          <code>UPDATE users SET is_admin = 1 WHERE username = 'yourusername';</code>
        </p>
        <button
          class="go"
          onclick="
            fetch('api/auth', { method: 'POST', body: new URLSearchParams({ action: 'logout' }) }).then(
              () => (location.href = './'),
            )
          "
        >
          Bumalik sa app
        </button>
      </div>
    </div>

    <?php else: ?>

    <header class="top">
      <h1>📊 SalitAACo - Admin dashboard</h1>
      <div class="right">
        <span>👤 <?php echo htmlspecialchars($_SESSION["display_name"]); ?></span>
        <a href="./">Buksan ang app</a>
        <button id="logoutBtn">Log out</button>
      </div>
    </header>

    <main>
      <div class="statsGrid" id="statsGrid">
        <div class="statCard"><div class="label">Loading...</div></div>
      </div>

      <div class="section">
        <h2>📈 Mga bagong sign-up (huling 14 araw)</h2>
        <div id="signupsChart"><p class="loadingNote">Loading...</p></div>
      </div>

      <div class="section">
        <h2>⭐ Mga rating</h2>
        <div id="ratingSummary"></div>
        <h3>Distribution</h3>
        <div id="ratingDist"></div>
        <h3>Pinakabagong feedback</h3>
        <table class="scroll-wrap" id="ratingsTable">
          <thead>
            <tr>
              <th>User</th>
              <th>Rating</th>
              <th>Comment</th>
              <th>Updated</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td colspan="4" class="emptyNote">Loading...</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="section">
        <h2>🔥 Pinaka-madalas gamitin na salita (lahat ng users)</h2>
        <div id="topWords"></div>
      </div>

      <div class="section">
        <h2>👥 Mga users</h2>
        <table class="scroll-wrap" id="usersTable">
          <thead>
            <tr>
              <th>Username</th>
              <th>Pangalan</th>
              <th>Edad</th>
              <th>Larawan</th>
              <th>Tunog</th>
              <th>Taps</th>
              <th>Rating</th>
              <th>Admin</th>
              <th>Sign-up</th>
              <th>Huling login</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td colspan="10" class="emptyNote">Loading...</td>
            </tr>
          </tbody>
        </table>
      </div>
    </main>

    <script>
      document.getElementById("logoutBtn").onclick = async () => {
        await fetch("api/auth", { method: "POST", body: new URLSearchParams({ action: "logout" }) });
        location.href = "./";
      };

      function fmtBytes(n) {
        if (n < 1024) return n + " B";
        if (n < 1024 * 1024) return (n / 1024).toFixed(1) + " KB";
        return (n / (1024 * 1024)).toFixed(1) + " MB";
      }
      function fmtDate(s) {
        if (!s) return "—";
        return s.replace("T", " ").substring(0, 16);
      }
      function stars(n) {
        if (!n) return "—";
        return `<span class="stars">${"★".repeat(n)}${"☆".repeat(5 - n)}</span>`;
      }
      function esc(s) {
        const d = document.createElement("div");
        d.textContent = s ?? "";
        return d.innerHTML;
      }

      async function loadOverview() {
        const res = await fetch("api/admin?action=overview").then((r) => r.json());
        if (!res.ok) return;
        const cards = [
          ["Kabuuang users", res.totalUsers, `+${res.newToday} ngayong araw`],
          ["Bago sa linggo", res.newThisWeek, ""],
          ["Aktibo ngayong araw", res.activeToday, `${res.activeThisWeek} sa linggo`],
          ["Average rating", res.avgRating ?? "—", `${res.ratingCount} na rating`],
          ["Custom na larawan", res.totalImages, ""],
          ["Custom na tunog", res.totalSounds, ""],
          ["Kabuuang taps", res.totalTaps, ""],
          ["Storage na ginamit", fmtBytes(res.storageBytes), "larawan + tunog + avatar"],
        ];
        document.getElementById("statsGrid").innerHTML = cards
          .map(
            ([label, val, sub]) => `
    <div class="statCard">
      <div class="label">${label}</div>
      <div class="value">${val}</div>
      ${sub ? `<div class="sub2">${sub}</div>` : ""}
    </div>
  `,
          )
          .join("");
      }

      async function loadSignups() {
        const res = await fetch("api/admin?action=signups_by_day").then((r) => r.json());
        if (!res.ok) return;
        const max = Math.max(1, ...res.series.map((s) => s.count));
        document.getElementById("signupsChart").innerHTML = res.series
          .map(
            (s) => `
    <div class="barRow">
      <div class="barLabel">${s.date.substring(5)}</div>
      <div class="barTrack"><div class="barFill" style="width:${((s.count / max) * 100).toFixed(0)}%"></div></div>
      <div class="barCount">${s.count}</div>
    </div>
  `,
          )
          .join("");
      }

      async function loadRatings() {
        const [sumRes, distRes] = await Promise.all([
          fetch("api/admin?action=overview").then((r) => r.json()),
          fetch("api/admin?action=rating_distribution").then((r) => r.json()),
        ]);
        if (sumRes.ok) {
          document.getElementById("ratingSummary").innerHTML =
            sumRes.ratingCount > 0
              ? `<p style="margin:0;font-size:14px;">${stars(Math.round(sumRes.avgRating))} <b>${sumRes.avgRating}</b> / 5 (${sumRes.ratingCount} na rating)</p>`
              : `<p class="emptyNote">Walang rating pa.</p>`;
        }
        if (distRes.ok) {
          const dist = distRes.distribution;
          const max = Math.max(1, ...Object.values(dist));
          document.getElementById("ratingDist").innerHTML = [5, 4, 3, 2, 1]
            .map(
              (n) => `
      <div class="barRow">
        <div class="barLabel">${n} ★</div>
        <div class="barTrack"><div class="barFill" style="width:${((dist[n] / max) * 100).toFixed(0)}%"></div></div>
        <div class="barCount">${dist[n]}</div>
      </div>
    `,
            )
            .join("");
        }

        const listRes = await fetch("api/admin?action=ratings").then((r) => r.json());
        const tbody = document.querySelector("#ratingsTable tbody");
        if (!listRes.ok || listRes.items.length === 0) {
          tbody.innerHTML = `<tr><td colspan="4" class="emptyNote">Walang feedback pa.</td></tr>`;
          return;
        }
        tbody.innerHTML = listRes.items
          .map(
            (it) => `
    <tr>
      <td>${esc(it.display_name)} <span class="badge">@${esc(it.username)}</span></td>
      <td>${stars(it.rating)}</td>
      <td class="comment">${esc(it.comment) || "—"}</td>
      <td>${fmtDate(it.updated_at)}</td>
    </tr>
  `,
          )
          .join("");
      }

      async function loadTopWords() {
        const res = await fetch("api/admin?action=top_words&limit=15").then((r) => r.json());
        if (!res.ok) return;
        if (res.items.length === 0) {
          document.getElementById("topWords").innerHTML = `<p class="emptyNote">Wala pang datos.</p>`;
          return;
        }
        const max = Math.max(1, ...res.items.map((i) => parseInt(i.total_uses)));
        document.getElementById("topWords").innerHTML = res.items
          .map(
            (it) => `
    <div class="barRow">
      <div class="barLabel">${esc(it.word)}</div>
      <div class="barTrack"><div class="barFill" style="width:${((it.total_uses / max) * 100).toFixed(0)}%"></div></div>
      <div class="barCount">${it.total_uses}</div>
    </div>
  `,
          )
          .join("");
      }

      async function loadUsers() {
        const res = await fetch("api/admin?action=users").then((r) => r.json());
        const tbody = document.querySelector("#usersTable tbody");
        if (!res.ok || res.items.length === 0) {
          tbody.innerHTML = `<tr><td colspan="10" class="emptyNote">Walang users.</td></tr>`;
          return;
        }
        tbody.innerHTML = res.items
          .map(
            (u) => `
    <tr>
      <td>@${esc(u.username)}</td>
      <td>${esc(u.display_name)}</td>
      <td>${u.age ?? "—"}</td>
      <td>${u.image_count}</td>
      <td>${u.sound_count}</td>
      <td>${u.total_taps}</td>
      <td>${stars(u.rating)}</td>
      <td>${u.is_admin ? '<span class="badge admin">admin</span>' : "—"}</td>
      <td>${fmtDate(u.created_at)}</td>
      <td>${fmtDate(u.last_login)}</td>
    </tr>
  `,
          )
          .join("");
      }

      loadOverview();
      loadSignups();
      loadRatings();
      loadTopWords();
      loadUsers();
    </script>

    <?php endif; ?>
  </body>
</html>
