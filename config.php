<?php
// Database connection settings.
// Default values match a typical XAMPP / phpMyAdmin local setup.
// Edit these if your MySQL username, password, or host is different.

session_start();

$DB_HOST = "localhost";
$DB_NAME = "salitaaco_db";
$DB_USER = "root";
$DB_PASS = "";

try {
    $pdo = new PDO(
        "mysql:host=$DB_HOST;dbname=$DB_NAME;charset=utf8mb4",
        $DB_USER,
        $DB_PASS,
        [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        ]
    );
} catch (PDOException $e) {
    http_response_code(500);
    header("Content-Type: application/json");
    echo json_encode([
        "ok" => false,
        "error" => "Hindi ma-connect sa database. Siguraduhing tumakbo ang MySQL at na-import ang database.sql. (" . $e->getMessage() . ")"
    ]);
    exit;
}
