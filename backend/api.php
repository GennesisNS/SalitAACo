<?php

// Handles: save_image, save_sound, reset, list, image, sound,
//          increment_usage, frequent_list, submit_rating, get_my_rating
// All actions require an active login session.

use Illuminate\Database\Capsule\Manager as DB;
use SalitAACo\Models\Customization;
use SalitAACo\Models\Rating;
use SalitAACo\Models\WordUsage;

require __DIR__ . "/config.php";

if (!isset($_SESSION["user_id"])) {
    header("Content-Type: application/json");
    echo json_encode(["ok" => false, "error" => "Kailangan mag-log in."]);
    exit;
}

$userId = $_SESSION["user_id"];
$action = $_POST["action"] ?? $_GET["action"] ?? "";

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

    // Insert the (user_id, word) row, or only replace its image if it already exists.
    Customization::upsert(
        [["user_id" => $userId, "word" => $word, "image_data" => $data, "image_mime" => $mime]],
        ["user_id", "word"],
        ["image_data", "image_mime"],
    );

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

    // Insert the (user_id, word) row, or only replace its sound if it already exists.
    Customization::upsert(
        [["user_id" => $userId, "word" => $word, "sound_data" => $data, "sound_mime" => $mime]],
        ["user_id", "word"],
        ["sound_data", "sound_mime"],
    );

    echo json_encode(["ok" => true]);
    exit;
}

// ---------- Reset a cell's customization back to default ----------
if ($action === "reset") {
    header("Content-Type: application/json");
    $word = trim($_POST["word"] ?? "");
    Customization::where("user_id", $userId)->where("word", $word)->delete();
    echo json_encode(["ok" => true]);
    exit;
}

// ---------- List which words have a custom image/sound for this user ----------
if ($action === "list") {
    header("Content-Type: application/json");
    $items = Customization::where("user_id", $userId)
        ->select("word")
        ->selectRaw("(image_data IS NOT NULL) AS has_image")
        ->selectRaw("(sound_data IS NOT NULL) AS has_sound")
        ->get();
    echo json_encode(["ok" => true, "items" => $items]);
    exit;
}

// ---------- Serve the stored image binary for a word ----------
if ($action === "image") {
    $word = $_GET["word"] ?? "";
    $row = Customization::where("user_id", $userId)
        ->where("word", $word)
        ->first(["image_data", "image_mime"]);
    if ($row && $row->image_data) {
        header("Content-Type: " . $row->image_mime);
        header("Cache-Control: private, max-age=86400");
        echo $row->image_data;
    } else {
        http_response_code(404);
    }
    exit;
}

// ---------- Serve the stored sound binary for a word ----------
if ($action === "sound") {
    $word = $_GET["word"] ?? "";
    $row = Customization::where("user_id", $userId)
        ->where("word", $word)
        ->first(["sound_data", "sound_mime"]);
    if ($row && $row->sound_data) {
        header("Content-Type: " . $row->sound_mime);
        header("Cache-Control: private, max-age=86400");
        echo $row->sound_data;
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

    // Bump the existing count, or start the (user_id, word) row at 1. Not an upsert:
    // this runs on every tap, and an upsert would use up an auto-increment id each time.
    $bumped = WordUsage::where("user_id", $userId)
        ->where("word", $word)
        ->increment("use_count", 1, ["last_used" => DB::raw("CURRENT_TIMESTAMP")]);
    if (!$bumped) {
        WordUsage::insert(["user_id" => $userId, "word" => $word, "use_count" => 1]);
    }

    echo json_encode(["ok" => true]);
    exit;
}

// ---------- List this user's most-used words, highest count first ----------
if ($action === "frequent_list") {
    header("Content-Type: application/json");
    $limit = (int) ($_GET["limit"] ?? 40);
    if ($limit < 1) {
        $limit = 1;
    }
    if ($limit > 200) {
        $limit = 200;
    }

    $items = WordUsage::from("word_usage AS wu")
        ->leftJoin("customizations AS c", function ($join) {
            $join->on("c.user_id", "=", "wu.user_id")->on("c.word", "=", "wu.word");
        })
        ->where("wu.user_id", $userId)
        ->orderByDesc("wu.use_count")
        ->orderByDesc("wu.last_used")
        ->limit($limit)
        ->get([
            "wu.word",
            "wu.use_count",
            "wu.last_used",
            DB::raw("(c.image_data IS NOT NULL) AS has_image"),
            DB::raw("(c.sound_data IS NOT NULL) AS has_sound"),
        ]);
    echo json_encode(["ok" => true, "items" => $items]);
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

    Rating::upsert(
        [["user_id" => $userId, "rating" => $rating, "comment" => $comment]],
        ["user_id"],
        ["rating", "comment"],
    );

    echo json_encode(["ok" => true]);
    exit;
}

// ---------- Get this user's own rating (to prefill the stars) ----------
if ($action === "get_my_rating") {
    header("Content-Type: application/json");
    $row = Rating::where("user_id", $userId)->first(["rating", "comment"]);
    echo json_encode([
        "ok" => true,
        "rating" => $row ? (int) $row->rating : null,
        "comment" => $row->comment ?? "",
    ]);
    exit;
}

header("Content-Type: application/json");
echo json_encode(["ok" => false, "error" => "Unknown action."]);
