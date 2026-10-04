<?php
// Handles: save_image, save_sound, reset, list, image, sound,
//          increment_usage, frequent_list
// All actions require an active login session.
require "config.php";

if (!isset($_SESSION["user_id"])) {
    header("Content-Type: application/json");
    echo json_encode(["ok" => false, "error" => "Kailangan mag-log in."]);
    exit;
}

$userId = $_SESSION["user_id"];
$action = $_POST["action"] ?? $_GET["action"] ?? "";

function salitaaco_upsert(PDO $pdo, $userId, $word) {
    $stmt = $pdo->prepare("SELECT id FROM customizations WHERE user_id = ? AND word = ?");
    $stmt->execute([$userId, $word]);
    if ($stmt->fetch()) return;
    $stmt = $pdo->prepare("INSERT INTO customizations (user_id, word) VALUES (?, ?)");
    $stmt->execute([$userId, $word]);
}

// ---------- Save an uploaded / replaced image for a word ----------
if ($action === "save_image") {
    header("Content-Type: application/json");
    $word = trim($_POST["word"] ?? "");
    if ($word === "" || !isset($_FILES["image"]) || $_FILES["image"]["error"] !== UPLOAD_ERR_OK) {
        echo json_encode(["ok" => false, "error" => "Walang natanggap na larawan."]);
        exit;
    }
    $data = file_get_contents($_FILES["image"]["tmp_name"]);
    $mime = $_FILES["image"]["type"] ?: "image/png";

    salitaaco_upsert($pdo, $userId, $word);
    $stmt = $pdo->prepare("UPDATE customizations SET image_data = ?, image_mime = ? WHERE user_id = ? AND word = ?");
    $stmt->execute([$data, $mime, $userId, $word]);

    echo json_encode(["ok" => true]);
    exit;
}

// ---------- Save a recorded sound clip for a word ----------
if ($action === "save_sound") {
    header("Content-Type: application/json");
    $word = trim($_POST["word"] ?? "");
    if ($word === "" || !isset($_FILES["sound"]) || $_FILES["sound"]["error"] !== UPLOAD_ERR_OK) {
        echo json_encode(["ok" => false, "error" => "Walang natanggap na tunog."]);
        exit;
    }
    $data = file_get_contents($_FILES["sound"]["tmp_name"]);
    $mime = $_FILES["sound"]["type"] ?: "audio/webm";

    salitaaco_upsert($pdo, $userId, $word);
    $stmt = $pdo->prepare("UPDATE customizations SET sound_data = ?, sound_mime = ? WHERE user_id = ? AND word = ?");
    $stmt->execute([$data, $mime, $userId, $word]);

    echo json_encode(["ok" => true]);
    exit;
}

// ---------- Reset a cell's customization back to default ----------
if ($action === "reset") {
    header("Content-Type: application/json");
    $word = trim($_POST["word"] ?? "");
    $stmt = $pdo->prepare("DELETE FROM customizations WHERE user_id = ? AND word = ?");
    $stmt->execute([$userId, $word]);
    echo json_encode(["ok" => true]);
    exit;
}

// ---------- List which words have a custom image/sound for this user ----------
if ($action === "list") {
    header("Content-Type: application/json");
    $stmt = $pdo->prepare(
        "SELECT word, (image_data IS NOT NULL) AS has_image, (sound_data IS NOT NULL) AS has_sound
         FROM customizations WHERE user_id = ?"
    );
    $stmt->execute([$userId]);
    echo json_encode(["ok" => true, "items" => $stmt->fetchAll()]);
    exit;
}

// ---------- Serve the stored image binary for a word ----------
if ($action === "image") {
    $word = $_GET["word"] ?? "";
    $stmt = $pdo->prepare("SELECT image_data, image_mime FROM customizations WHERE user_id = ? AND word = ?");
    $stmt->execute([$userId, $word]);
    $row = $stmt->fetch();
    if ($row && $row["image_data"]) {
        header("Content-Type: " . $row["image_mime"]);
        header("Cache-Control: private, max-age=86400");
        echo $row["image_data"];
    } else {
        http_response_code(404);
    }
    exit;
}

// ---------- Serve the stored sound binary for a word ----------
if ($action === "sound") {
    $word = $_GET["word"] ?? "";
    $stmt = $pdo->prepare("SELECT sound_data, sound_mime FROM customizations WHERE user_id = ? AND word = ?");
    $stmt->execute([$userId, $word]);
    $row = $stmt->fetch();
    if ($row && $row["sound_data"]) {
        header("Content-Type: " . $row["sound_mime"]);
        header("Cache-Control: private, max-age=86400");
        echo $row["sound_data"];
    } else {
        http_response_code(404);
    }
    exit;
}

// ---------- Record that a word was used (powers "Madalas Gamitin") ----------
if ($action === "increment_usage") {
    header("Content-Type: application/json");
    $word = trim($_POST["word"] ?? "");
    if ($word === "") {
        echo json_encode(["ok" => false, "error" => "Walang word."]);
        exit;
    }
    $stmt = $pdo->prepare("SELECT id FROM word_usage WHERE user_id = ? AND word = ?");
    $stmt->execute([$userId, $word]);
    if ($stmt->fetch()) {
        $stmt = $pdo->prepare("UPDATE word_usage SET use_count = use_count + 1, last_used = CURRENT_TIMESTAMP WHERE user_id = ? AND word = ?");
        $stmt->execute([$userId, $word]);
    } else {
        $stmt = $pdo->prepare("INSERT INTO word_usage (user_id, word, use_count) VALUES (?, ?, 1)");
        $stmt->execute([$userId, $word]);
    }
    echo json_encode(["ok" => true]);
    exit;
}

// ---------- List this user's most-used words, highest count first ----------
if ($action === "frequent_list") {
    header("Content-Type: application/json");
    $limit = (int) ($_GET["limit"] ?? 40);
    if ($limit < 1) $limit = 1;
    if ($limit > 200) $limit = 200;

    $stmt = $pdo->prepare(
        "SELECT wu.word, wu.use_count, wu.last_used,
                (c.image_data IS NOT NULL) AS has_image,
                (c.sound_data IS NOT NULL) AS has_sound
         FROM word_usage wu
         LEFT JOIN customizations c ON c.user_id = wu.user_id AND c.word = wu.word
         WHERE wu.user_id = ?
         ORDER BY wu.use_count DESC, wu.last_used DESC
         LIMIT $limit"
    );
    $stmt->execute([$userId]);
    echo json_encode(["ok" => true, "items" => $stmt->fetchAll()]);
    exit;
}

// ---------- Submit or update this user's app rating ----------
if ($action === "submit_rating") {
    header("Content-Type: application/json");
    $rating = (int) ($_POST["rating"] ?? 0);
    $comment = trim($_POST["comment"] ?? "");
    if ($rating < 1 || $rating > 5) {
        echo json_encode(["ok" => false, "error" => "Pumili ng 1 hanggang 5 bituin."]);
        exit;
    }
    $comment = $comment === "" ? null : mb_substr($comment, 0, 1000);

    $stmt = $pdo->prepare(
        "INSERT INTO ratings (user_id, rating, comment) VALUES (?, ?, ?)
         ON DUPLICATE KEY UPDATE rating = VALUES(rating), comment = VALUES(comment)"
    );
    $stmt->execute([$userId, $rating, $comment]);

    echo json_encode(["ok" => true]);
    exit;
}

// ---------- Get this user's own rating (to prefill the stars) ----------
if ($action === "get_my_rating") {
    header("Content-Type: application/json");
    $stmt = $pdo->prepare("SELECT rating, comment FROM ratings WHERE user_id = ?");
    $stmt->execute([$userId]);
    $row = $stmt->fetch();
    echo json_encode(["ok" => true, "rating" => $row ? (int)$row["rating"] : null, "comment" => $row["comment"] ?? ""]);
    exit;
}

header("Content-Type: application/json");
echo json_encode(["ok" => false, "error" => "Unknown action."]);
