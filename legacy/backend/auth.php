<?php

// Handles: signup, login, logout, check, get_profile, update_profile,
//          upload_avatar, remove_avatar, avatar (GET), change_password,
//          delete_account

use Illuminate\Database\Capsule\Manager as DB;
use SalitAACo\Models\User;

require __DIR__ . "/config.php";

$action = $_POST["action"] ?? $_GET["action"] ?? "";

// ---------- avatar is a raw image response, not JSON ----------
if ($action === "avatar") {
    if (!isset($_SESSION["user_id"])) {
        http_response_code(401);
        exit;
    }
    $row = User::whereKey($_SESSION["user_id"])->first(["avatar_data", "avatar_mime"]);
    if ($row && $row->avatar_data) {
        header("Content-Type: " . $row->avatar_mime);
        header("Cache-Control: private, max-age=86400");
        echo $row->avatar_data;
    } else {
        http_response_code(404);
    }
    exit;
}

header("Content-Type: application/json");

if ($action === "signup") {
    $username = trim($_POST["username"] ?? "");
    $password = $_POST["password"] ?? "";
    $displayName = trim($_POST["displayName"] ?? "") ?: $username;

    if ($username === "" || strlen($password) < 4) {
        echo json_encode(["ok" => false, "error" => "Punan nang tama ang username at password (min. 4 characters)."]);
        exit;
    }

    if (User::where("username", $username)->exists()) {
        echo json_encode(["ok" => false, "error" => "Ginagamit na ang username na ito."]);
        exit;
    }

    $user = User::create([
        "username" => $username,
        "password_hash" => password_hash($password, PASSWORD_DEFAULT),
        "display_name" => $displayName,
    ]);

    $_SESSION["user_id"] = $user->id;
    $_SESSION["username"] = $username;
    $_SESSION["display_name"] = $displayName;

    echo json_encode(["ok" => true, "user" => ["username" => $username, "displayName" => $displayName]]);
    exit;
}

if ($action === "login") {
    $username = trim($_POST["username"] ?? "");
    $password = $_POST["password"] ?? "";

    $u = User::where("username", $username)
        ->first(["id", "username", "password_hash", "display_name", "is_admin"]);

    if (!$u || !password_verify($password, $u->password_hash)) {
        echo json_encode(["ok" => false, "error" => "Maling username o password."]);
        exit;
    }

    $_SESSION["user_id"] = $u->id;
    $_SESSION["username"] = $u->username;
    $_SESSION["display_name"] = $u->display_name;
    $_SESSION["is_admin"] = (bool) $u->is_admin;

    User::whereKey($u->id)->update(["last_login" => DB::raw("CURRENT_TIMESTAMP")]);

    echo json_encode(["ok" => true, "user" => ["username" => $u->username, "displayName" => $u->display_name]]);
    exit;
}

if ($action === "logout") {
    $_SESSION = [];
    session_destroy();
    echo json_encode(["ok" => true]);
    exit;
}

if ($action === "check") {
    if (isset($_SESSION["user_id"])) {
        echo json_encode([
            "ok" => true,
            "loggedIn" => true,
            "user" => ["username" => $_SESSION["username"], "displayName" => $_SESSION["display_name"]],
        ]);
    } else {
        echo json_encode(["ok" => true, "loggedIn" => false]);
    }
    exit;
}

// ---------- everything below requires an active login session ----------
if (!isset($_SESSION["user_id"])) {
    echo json_encode(["ok" => false, "error" => "Kailangan mag-log in."]);
    exit;
}
$userId = $_SESSION["user_id"];

if ($action === "get_profile") {
    $u = User::whereKey($userId)
        ->select(["username", "display_name", "age"])
        ->selectRaw("(avatar_data IS NOT NULL) AS has_avatar")
        ->first();
    if (!$u) {
        echo json_encode(["ok" => false, "error" => "Hindi mahanap ang account."]);
        exit;
    }
    echo json_encode([
        "ok" => true,
        "profile" => [
            "username" => $u->username,
            "displayName" => $u->display_name,
            "age" => $u->age,
            "hasAvatar" => (bool) $u->has_avatar,
        ],
    ]);
    exit;
}

if ($action === "update_profile") {
    $displayName = trim($_POST["displayName"] ?? "");
    $ageRaw = trim($_POST["age"] ?? "");

    if ($displayName === "") {
        echo json_encode(["ok" => false, "error" => "Ilagay ang pangalan."]);
        exit;
    }

    $age = null;
    if ($ageRaw !== "") {
        if (!ctype_digit($ageRaw) || (int) $ageRaw < 0 || (int) $ageRaw > 150) {
            echo json_encode(["ok" => false, "error" => "Hindi tama ang edad."]);
            exit;
        }
        $age = (int) $ageRaw;
    }

    User::whereKey($userId)->update(["display_name" => $displayName, "age" => $age]);
    $_SESSION["display_name"] = $displayName;

    echo json_encode(["ok" => true]);
    exit;
}

if ($action === "upload_avatar") {
    if (!isset($_FILES["avatar"]) || $_FILES["avatar"]["error"] !== UPLOAD_ERR_OK) {
        echo json_encode(["ok" => false, "error" => "Walang natanggap na larawan."]);
        exit;
    }
    $allowed = ["image/jpeg", "image/png", "image/webp", "image/gif"];
    $mime = $_FILES["avatar"]["type"] ?: "image/png";
    if (!in_array($mime, $allowed, true)) {
        echo json_encode(["ok" => false, "error" => "Hindi suportadong file type ng larawan."]);
        exit;
    }
    if ($_FILES["avatar"]["size"] > 5 * 1024 * 1024) {
        echo json_encode(["ok" => false, "error" => "Masyadong malaki ang larawan (max 5MB)."]);
        exit;
    }
    $data = file_get_contents($_FILES["avatar"]["tmp_name"]);
    User::whereKey($userId)->update(["avatar_data" => $data, "avatar_mime" => $mime]);
    echo json_encode(["ok" => true]);
    exit;
}

if ($action === "remove_avatar") {
    User::whereKey($userId)->update(["avatar_data" => null, "avatar_mime" => null]);
    echo json_encode(["ok" => true]);
    exit;
}

if ($action === "change_password") {
    $current = $_POST["currentPassword"] ?? "";
    $new = $_POST["newPassword"] ?? "";
    $confirm = $_POST["confirmPassword"] ?? "";

    if (strlen($new) < 4) {
        echo json_encode(["ok" => false, "error" => "Ang bagong password ay dapat may hindi bababa sa 4 na character."]);
        exit;
    }
    if ($new !== $confirm) {
        echo json_encode(["ok" => false, "error" => "Hindi magkatugma ang bagong password at kumpirmasyon."]);
        exit;
    }

    $hash = User::whereKey($userId)->value("password_hash");
    if (!$hash || !password_verify($current, $hash)) {
        echo json_encode(["ok" => false, "error" => "Maling kasalukuyang password."]);
        exit;
    }

    User::whereKey($userId)->update(["password_hash" => password_hash($new, PASSWORD_DEFAULT)]);

    echo json_encode(["ok" => true]);
    exit;
}

if ($action === "delete_account") {
    $password = $_POST["password"] ?? "";

    $hash = User::whereKey($userId)->value("password_hash");
    if (!$hash || !password_verify($password, $hash)) {
        echo json_encode(["ok" => false, "error" => "Maling password."]);
        exit;
    }

    // customizations, word_usage and ratings rows cascade-delete via FOREIGN KEY ... ON DELETE CASCADE
    User::whereKey($userId)->delete();

    $_SESSION = [];
    session_destroy();

    echo json_encode(["ok" => true]);
    exit;
}

echo json_encode(["ok" => false, "error" => "Unknown action."]);
