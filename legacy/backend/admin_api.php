<?php

// Analytics data for the developer dashboard (frontend/admin.php).
// Every action here requires an active session AND is_admin = 1.

use Illuminate\Database\Capsule\Manager as DB;
use SalitAACo\Models\Customization;
use SalitAACo\Models\Rating;
use SalitAACo\Models\User;
use SalitAACo\Models\WordUsage;

require __DIR__ . "/config.php";
header("Content-Type: application/json");

if (!isset($_SESSION["user_id"]) || empty($_SESSION["is_admin"])) {
    http_response_code(403);
    echo json_encode(["ok" => false, "error" => "Admin access only."]);
    exit;
}

$action = $_GET["action"] ?? $_POST["action"] ?? "";

// ---------- Top-line stats for the overview cards ----------
if ($action === "overview") {
    // Date comparisons use MySQL's clock (CURDATE()), the same clock that stamps the rows.
    $today = DB::raw("CURDATE()");
    $weekAgo = DB::raw("(CURDATE() - INTERVAL 7 DAY)");

    $totalUsers = User::count();

    $newToday = User::whereDate("created_at", $today)->count();
    $newThisWeek = User::where("created_at", ">=", $weekAgo)->count();

    $activeToday = User::whereDate("last_login", $today)->count();
    $activeThisWeek = User::where("last_login", ">=", $weekAgo)->count();

    $totalImages = Customization::whereNotNull("image_data")->count();
    $totalSounds = Customization::whereNotNull("sound_data")->count();
    $totalTaps = (int) WordUsage::sum("use_count");

    $avgRating = Rating::avg("rating");
    $ratingCount = Rating::count();

    $mediaBytes = Customization::sum(DB::raw("COALESCE(LENGTH(image_data), 0) + COALESCE(LENGTH(sound_data), 0)"));
    $avatarBytes = User::sum(DB::raw("LENGTH(avatar_data)"));

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
        "avgRating" => $avgRating !== null ? round((float) $avgRating, 2) : null,
        "ratingCount" => $ratingCount,
        "storageBytes" => (int) $mediaBytes + (int) $avatarBytes,
    ]);
    exit;
}

// ---------- Signups per day, last 14 days (for a simple bar chart) ----------
if ($action === "signups_by_day") {
    $byDate = User::where("created_at", ">=", DB::raw("(CURDATE() - INTERVAL 13 DAY)"))
        ->selectRaw("DATE(created_at) AS d, COUNT(*) AS c")
        ->groupBy("d")
        ->orderBy("d")
        ->pluck("c", "d");

    $series = [];
    for ($i = 13; $i >= 0; $i--) {
        $d = date("Y-m-d", strtotime("-$i day"));
        $series[] = ["date" => $d, "count" => (int) ($byDate[$d] ?? 0)];
    }
    echo json_encode(["ok" => true, "series" => $series]);
    exit;
}

// ---------- User list with per-user counts ----------
if ($action === "users") {
    $items = User::query()
        ->select(["id", "username", "display_name", "age", "is_admin", "created_at", "last_login"])
        ->withCount([
            "customizations as image_count" => fn($query) => $query->whereNotNull("image_data"),
            "customizations as sound_count" => fn($query) => $query->whereNotNull("sound_data"),
        ])
        ->addSelect([
            "total_taps" => WordUsage::selectRaw("COALESCE(SUM(use_count), 0)")->whereColumn("user_id", "users.id"),
            "rating" => Rating::select("rating")->whereColumn("user_id", "users.id"),
        ])
        ->orderByDesc("created_at")
        ->get();
    echo json_encode(["ok" => true, "items" => $items]);
    exit;
}

// ---------- All ratings/feedback, newest first ----------
if ($action === "ratings") {
    $items = Rating::query()
        ->join("users", "users.id", "=", "ratings.user_id")
        ->orderByDesc("ratings.updated_at")
        ->get([
            "ratings.rating",
            "ratings.comment",
            "ratings.created_at",
            "ratings.updated_at",
            "users.username",
            "users.display_name",
        ]);
    echo json_encode(["ok" => true, "items" => $items]);
    exit;
}

// ---------- Rating distribution (how many gave 1,2,3,4,5 stars) ----------
if ($action === "rating_distribution") {
    $counts = Rating::selectRaw("rating, COUNT(*) AS c")->groupBy("rating")->pluck("c", "rating");
    $dist = [1 => 0, 2 => 0, 3 => 0, 4 => 0, 5 => 0];
    foreach ($counts as $rating => $count) {
        $dist[(int) $rating] = (int) $count;
    }
    echo json_encode(["ok" => true, "distribution" => $dist]);
    exit;
}

// ---------- Most-used words across ALL users (aggregate) ----------
if ($action === "top_words") {
    $limit = (int) ($_GET["limit"] ?? 15);
    if ($limit < 1) {
        $limit = 1;
    }
    if ($limit > 100) {
        $limit = 100;
    }
    $items = WordUsage::selectRaw("word, SUM(use_count) AS total_uses, COUNT(DISTINCT user_id) AS user_count")
        ->groupBy("word")
        ->orderByDesc("total_uses")
        ->limit($limit)
        ->get();
    echo json_encode(["ok" => true, "items" => $items]);
    exit;
}

echo json_encode(["ok" => false, "error" => "Unknown action."]);
