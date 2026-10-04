<?php
// Analytics data for the developer dashboard (admin.php).
// Every action here requires an active session AND is_admin = 1.
require "config.php";
header("Content-Type: application/json");

if (!isset($_SESSION["user_id"]) || empty($_SESSION["is_admin"])) {
    http_response_code(403);
    echo json_encode(["ok" => false, "error" => "Admin access only."]);
    exit;
}

$action = $_GET["action"] ?? $_POST["action"] ?? "";

// ---------- Top-line stats for the overview cards ----------
if ($action === "overview") {
    $totalUsers = (int) $pdo->query("SELECT COUNT(*) FROM users")->fetchColumn();

    $newToday = (int) $pdo->query("SELECT COUNT(*) FROM users WHERE DATE(created_at) = CURDATE()")->fetchColumn();
    $newThisWeek = (int) $pdo->query("SELECT COUNT(*) FROM users WHERE created_at >= (CURDATE() - INTERVAL 7 DAY)")->fetchColumn();

    $activeToday = (int) $pdo->query("SELECT COUNT(*) FROM users WHERE DATE(last_login) = CURDATE()")->fetchColumn();
    $activeThisWeek = (int) $pdo->query("SELECT COUNT(*) FROM users WHERE last_login >= (CURDATE() - INTERVAL 7 DAY)")->fetchColumn();

    $totalImages = (int) $pdo->query("SELECT COUNT(*) FROM customizations WHERE image_data IS NOT NULL")->fetchColumn();
    $totalSounds = (int) $pdo->query("SELECT COUNT(*) FROM customizations WHERE sound_data IS NOT NULL")->fetchColumn();
    $totalTaps = (int) $pdo->query("SELECT COALESCE(SUM(use_count),0) FROM word_usage")->fetchColumn();

    $avgRatingRow = $pdo->query("SELECT ROUND(AVG(rating),2) AS avg_r, COUNT(*) AS cnt FROM ratings")->fetch();
    $avgRating = $avgRatingRow["avg_r"] !== null ? (float) $avgRatingRow["avg_r"] : null;
    $ratingCount = (int) $avgRatingRow["cnt"];

    $storageRow = $pdo->query(
        "SELECT
            COALESCE(SUM(LENGTH(image_data)),0) AS img_bytes,
            COALESCE(SUM(LENGTH(sound_data)),0) AS snd_bytes
         FROM customizations"
    )->fetch();
    $avatarBytesRow = $pdo->query("SELECT COALESCE(SUM(LENGTH(avatar_data)),0) AS avatar_bytes FROM users")->fetch();

    echo json_encode([
        "ok" => true,
        "totalUsers" => $totalUsers,
        "newToday" => $newToday,
        "newThisWeek" => $newThisWeek,
        "activeToday" => $activeToday,
        "activeThisWeek" => $activeThisWeek,
        "totalImages" => $totalImages,
        "totalSounds" => $totalSounds,
        "totalTaps" => $totalTaps,
        "avgRating" => $avgRating,
        "ratingCount" => $ratingCount,
        "storageBytes" => (int)$storageRow["img_bytes"] + (int)$storageRow["snd_bytes"] + (int)$avatarBytesRow["avatar_bytes"],
    ]);
    exit;
}

// ---------- Signups per day, last 14 days (for a simple bar chart) ----------
if ($action === "signups_by_day") {
    $stmt = $pdo->query(
        "SELECT DATE(created_at) AS d, COUNT(*) AS c
         FROM users
         WHERE created_at >= (CURDATE() - INTERVAL 13 DAY)
         GROUP BY DATE(created_at)
         ORDER BY d ASC"
    );
    $rows = $stmt->fetchAll();
    $byDate = [];
    foreach ($rows as $r) $byDate[$r["d"]] = (int) $r["c"];

    $series = [];
    for ($i = 13; $i >= 0; $i--) {
        $d = date("Y-m-d", strtotime("-$i day"));
        $series[] = ["date" => $d, "count" => $byDate[$d] ?? 0];
    }
    echo json_encode(["ok" => true, "series" => $series]);
    exit;
}

// ---------- User list with per-user counts ----------
if ($action === "users") {
    $stmt = $pdo->query(
        "SELECT
            u.id, u.username, u.display_name, u.age, u.is_admin,
            u.created_at, u.last_login,
            (SELECT COUNT(*) FROM customizations c WHERE c.user_id = u.id AND c.image_data IS NOT NULL) AS image_count,
            (SELECT COUNT(*) FROM customizations c WHERE c.user_id = u.id AND c.sound_data IS NOT NULL) AS sound_count,
            (SELECT COALESCE(SUM(use_count),0) FROM word_usage w WHERE w.user_id = u.id) AS total_taps,
            (SELECT rating FROM ratings r WHERE r.user_id = u.id) AS rating
         FROM users u
         ORDER BY u.created_at DESC"
    );
    echo json_encode(["ok" => true, "items" => $stmt->fetchAll()]);
    exit;
}

// ---------- All ratings/feedback, newest first ----------
if ($action === "ratings") {
    $stmt = $pdo->query(
        "SELECT r.rating, r.comment, r.created_at, r.updated_at, u.username, u.display_name
         FROM ratings r
         JOIN users u ON u.id = r.user_id
         ORDER BY r.updated_at DESC"
    );
    echo json_encode(["ok" => true, "items" => $stmt->fetchAll()]);
    exit;
}

// ---------- Rating distribution (how many gave 1,2,3,4,5 stars) ----------
if ($action === "rating_distribution") {
    $stmt = $pdo->query("SELECT rating, COUNT(*) AS c FROM ratings GROUP BY rating");
    $rows = $stmt->fetchAll();
    $dist = [1=>0,2=>0,3=>0,4=>0,5=>0];
    foreach ($rows as $r) $dist[(int)$r["rating"]] = (int)$r["c"];
    echo json_encode(["ok" => true, "distribution" => $dist]);
    exit;
}

// ---------- Most-used words across ALL users (aggregate) ----------
if ($action === "top_words") {
    $limit = (int) ($_GET["limit"] ?? 15);
    if ($limit < 1) $limit = 1;
    if ($limit > 100) $limit = 100;
    $stmt = $pdo->prepare(
        "SELECT word, SUM(use_count) AS total_uses, COUNT(DISTINCT user_id) AS user_count
         FROM word_usage
         GROUP BY word
         ORDER BY total_uses DESC
         LIMIT $limit"
    );
    $stmt->execute();
    echo json_encode(["ok" => true, "items" => $stmt->fetchAll()]);
    exit;
}

echo json_encode(["ok" => false, "error" => "Unknown action."]);
