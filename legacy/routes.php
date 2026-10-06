<?php

// URL routes: the address on the left opens the file on the right.
// This is the one place that decides what each address is called.
// If you rename an "api/..." route, update the fetch() calls in frontend/ to match.

return [
    "home" => "frontend/index.php", // the app
    "admin" => "frontend/admin.php", // admin analytics dashboard

    "api/auth" => "backend/auth.php", // sign up, log in, profile, account
    "api/app" => "backend/api.php", // custom images and sounds, word usage, ratings
    "api/admin" => "backend/admin_api.php", // data for the admin dashboard
];
