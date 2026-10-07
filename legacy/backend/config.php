<?php

// Database connection settings.
// Default values match a typical XAMPP / phpMyAdmin local setup.
// Edit these if your MySQL username, password, or host is different.

use Illuminate\Database\Capsule\Manager as Capsule;

session_start();

$DB_HOST = "localhost";
$DB_NAME = "salitaaco_db";
$DB_USER = "root";
$DB_PASS = "";

if (!is_file(dirname(__DIR__) . "/vendor/autoload.php")) {
    http_response_code(500);
    header("Content-Type: application/json");
    echo json_encode([
        "ok" => false,
        "error" => "Hindi pa naka-install ang mga dependency. Patakbuhin ang `composer install` sa folder ng project.",
    ]);
    exit;
}
require dirname(__DIR__) . "/vendor/autoload.php";

// Eloquent ORM (illuminate/database). The models live in backend/Models.
$capsule = new Capsule();
$capsule->addConnection([
    "driver" => "mysql",
    "host" => $DB_HOST,
    "database" => $DB_NAME,
    "username" => $DB_USER,
    "password" => $DB_PASS,
    "charset" => "utf8mb4",
    "collation" => "utf8mb4_unicode_ci",
]);
$capsule->setAsGlobal();
$capsule->bootEloquent();

try {
    // Eloquent connects lazily; connect now so a bad setup fails here with a readable message.
    $capsule->getConnection()->getPdo();
} catch (PDOException $e) {
    http_response_code(500);
    header("Content-Type: application/json");
    echo json_encode([
        "ok" => false,
        "error" => "Hindi ma-connect sa database. Siguraduhing tumakbo ang MySQL at na-import ang database.sql. (" . $e->getMessage() . ")",
    ]);
    exit;
}
