<?php

// Front controller: every address that is not a real file arrives here
// (see .htaccess) and is looked up in routes.php.

$routes = require __DIR__ . "/routes.php";

// The project may sit in a subfolder (e.g. /SalitAACo/ under XAMPP), so
// routes are matched against the part of the address after that folder.
$script = str_replace("\\", "/", $_SERVER["SCRIPT_NAME"]);
$base = str_ends_with($script, "/index.php") ? substr($script, 0, -strlen("/index.php")) : "";

$path = rawurldecode(parse_url($_SERVER["REQUEST_URI"], PHP_URL_PATH) ?: "/");
if ($base !== "" && str_starts_with($path, $base . "/")) {
    $path = substr($path, strlen($base));
}
$route = trim($path, "/");
if ($route === "index.php") {
    $route = "";
}

// "/admin/" would make the page's relative links point at the wrong folder,
// so send it to "/admin".
if ($route !== "" && str_ends_with($path, "/")) {
    $query = $_SERVER["QUERY_STRING"] ?? "";
    header("Location: $base/$route" . ($query !== "" ? "?$query" : ""));
    exit;
}

if (!isset($routes[$route])) {
    http_response_code(404);
    header("Content-Type: text/plain; charset=UTF-8");
    echo "404 - Walang ganitong pahina.";
    exit;
}

require __DIR__ . "/" . $routes[$route];
