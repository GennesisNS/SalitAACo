# php-database

PHP application with database integration

## What you need

| Tool             | Version      | What it is for                                                |
| ---------------- | ------------ | ------------------------------------------------------------- |
| PHP              | 8.2 or newer | Runs the app                                                  |
| MySQL or MariaDB | any recent   | Stores accounts, custom images and sounds, usage, and ratings |
| Composer         | 2.x          | Downloads the PHP libraries the app depends on (Eloquent ORM) |
| A web browser    | any modern   | Opens the app                                                 |

On Windows, **XAMPP** gives you PHP, MariaDB, Apache, and phpMyAdmin in one installer, so you only need to install two things: XAMPP and Composer.

## Installation (Windows)

### 1. Install XAMPP

1. Download XAMPP from <https://www.apachefriends.org/download.html>. Choose the build with **PHP 8.2 or newer**.
2. Run the installer and keep the default folder, `C:\xampp`.

If you prefer the command line, this installs the same thing:

```
winget install ApacheFriends.Xampp.8.2
```

### 2. Install Composer

1. Download `Composer-Setup.exe` from <https://getcomposer.org/download/>.
2. Run it. When it asks for the PHP executable, choose `C:\xampp\php\php.exe`.
3. Finish the installer. It adds `php` and `composer` to your PATH.

If you have Chocolatey, `choco install composer` does the same thing.

### 3. Check the tools

Close any open terminals (including the one in VS Code) and open a new one, so it picks up the new PATH. Then run:

```
php -v
composer -V
```

`php -v` must report 8.2 or newer. If either command is "not recognized", see [Troubleshooting](#troubleshooting).

### 4. Install the project's PHP libraries

In the project folder, run:

```
composer install
```

This reads `composer.json` and `composer.lock` and downloads the libraries into a `vendor/` folder. Run it again whenever `composer.lock` changes.

Composer is PHP's package manager, the same role `pip` has for Python. `pip` cannot install PHP libraries, so `composer install` is the command to use here.

The `vendor/` folder is ignored by Git on purpose. Do not commit it; everyone runs `composer install` to create their own.

### 5. Create the database

1. Open the **XAMPP Control Panel** and click **Start** next to **MySQL** (and **Apache**, which phpMyAdmin needs).
2. Open <http://localhost/phpmyadmin> in your browser.
3. Click the **Import** tab, choose `database.sql` from the project's `database` folder, and click **Import**.

This creates a database named `salitaaco_db` with all the tables.

From the command line instead:

```
C:\xampp\mysql\bin\mysql -u root < database\database.sql
```

### 6. Check the connection settings

`backend/config.php` is set up for a default XAMPP install:

| Setting    | Default        |
| ---------- | -------------- |
| `$DB_HOST` | `localhost`    |
| `$DB_NAME` | `salitaaco_db` |
| `$DB_USER` | `root`         |
| `$DB_PASS` | (empty)        |

Edit those values only if your MySQL host, username, or password are different.

### 7. Run the app

MySQL must be running (step 5). Then use either option.

**Option A: PHP's built-in server.** Works from any folder. In the project folder, run:

```
php -S localhost:8000
```

Open <http://localhost:8000/>. Press `Ctrl+C` in the terminal to stop the server.

**Option B: XAMPP's Apache.** Copy the project folder into `C:\xampp\htdocs\`, start **Apache** in the XAMPP Control Panel, and open <http://localhost/SalitAACo/> (use your folder's name in place of `SalitAACo`).

The app is at that address, and the admin dashboard is at the same address followed by `admin`. See [URLs](#urls) for the full list.

Open the app through `localhost`. Recording a sound needs microphone access, and browsers only allow that on `localhost` or HTTPS.

### 8. Make yourself an admin (optional)

The analytics dashboard at `/admin` is only for admin accounts. Sign up in the app first, then run this in phpMyAdmin's **SQL** tab, with your own username:

```sql
UPDATE users SET is_admin = 1 WHERE username = 'your_username_here';
```

Log out and log in again for it to take effect, then add `admin` to the end of the app's address, for example <http://localhost:8000/admin>.

## Installation (macOS and Linux)

Install PHP 8.2 or newer (with the `pdo_mysql` and `mbstring` extensions), MariaDB or MySQL, and Composer using your package manager, for example `brew install php mariadb composer` on macOS. Then follow steps 4 to 8 above, using `mysql -u root -p < database/database.sql` to create the database.

## Troubleshooting

| What you see                                                              | What to do                                                                                                                                                                   |
| ------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `'php' is not recognized` or `'composer' is not recognized`               | Open a new terminal. If it still fails, add `C:\xampp\php` to your PATH, or run the Composer installer again.                                                                |
| `Hindi pa naka-install ang mga dependency...`                             | The `vendor/` folder is missing. Run `composer install` in the project folder (step 4).                                                                                      |
| `Hindi ma-connect sa database...`                                         | Start MySQL in the XAMPP Control Panel, make sure `database.sql` was imported (step 5), and check the settings in `backend/config.php` (step 6).                             |
| `composer install` says your PHP version does not satisfy a requirement   | Your PHP is older than 8.2. Run `php -v` to check, then install a newer XAMPP.                                                                                               |
| Apache or MySQL will not start in XAMPP                                   | Another program is using port 80 or 3306. Close it, or skip Apache and use Option A in step 7.                                                                               |
| The app opens but logging in fails, or `/admin` gives a 404 (Apache only) | Apache is ignoring `.htaccess`. In `httpd.conf`, make sure the `rewrite_module` line is not commented out and the folder has `AllowOverride All`. XAMPP has both by default. |
| `could not find driver`                                                   | The `pdo_mysql` extension is off. In `php.ini`, remove the `;` in front of `extension=pdo_mysql`. XAMPP has it on by default.                                                |

## URLs

Addresses are set in one file, `routes.php`, the same idea as `urls.py` in Django. Each line maps an address to the file that handles it:

| Address      | Opens                   | What it is                                        |
| ------------ | ----------------------- | ------------------------------------------------- |
| `/`          | `frontend/index.php`    | The app                                           |
| `/admin`     | `frontend/admin.php`    | Admin analytics dashboard                         |
| `/api/auth`  | `backend/auth.php`      | Sign up, log in, profile, and account actions     |
| `/api/app`   | `backend/api.php`       | Custom images and sounds, word usage, and ratings |
| `/api/admin` | `backend/admin_api.php` | Data for the admin dashboard                      |

To add a page, create its file and add a line to `routes.php`:

```php
"about" => "frontend/about.php",
```

To rename an address, change the left side of its line. If you rename one of the `api/...` addresses, also update the `fetch()` calls in `frontend/` that use it.

How it works: `.htaccess` tells Apache to send every address that is not a real file to `index.php`, and `index.php` looks the address up in `routes.php`. PHP's built-in server does the same thing without `.htaccess`. CSS files are real files, so they are served directly.

## Project layout

```
routes.php           The list of addresses (see URLs above)
index.php            Receives every request and opens the file routes.php points to
.htaccess            Tells Apache to send requests to index.php

frontend/            What the browser shows
  index.php          The app itself
  admin.php          Admin analytics dashboard
  css/
    index.css        Styles for the app
    admin.css        Styles for the admin dashboard

backend/             What talks to the database
  config.php         Database settings and Eloquent setup
  auth.php           Sign up, log in, profile, and account actions
  api.php            Custom images and sounds, word usage, and ratings
  admin_api.php      Data for the admin dashboard
  Models/            Eloquent models, one per database table

database/
  database.sql       Creates the database and tables

composer.json        Lists the PHP libraries the app needs
composer.lock        Exact versions of those libraries
vendor/              Downloaded libraries (created by composer install, not in Git)
```

The pages in `frontend/` call the endpoints in `backend/`, and those are the only files that query the database. The files at the top level stay there because the web server, Composer, Git, and GitHub look for them in the project root.
