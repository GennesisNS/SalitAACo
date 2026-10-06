# SalitAACo

A Filipino AAC (augmentative and alternative communication) web app. Users tap picture tiles to build a sentence, can replace a tile's picture or record their own voice for it, and can rate the app. Admins get an analytics dashboard.

This is a Django project. It was converted from a PHP application, which is kept in [`legacy/`](legacy/) for reference until the conversion has been checked against it (see [The PHP application](#the-php-application)).

## What you need

| Tool   | Version      | What it is for                                    |
| ------ | ------------ | ------------------------------------------------- |
| Python | 3.13         | Runs the app                                      |
| MySQL  | 8, or MariaDB 10.5 or newer | Production database. Development uses SQLite, which needs no setup |

There is no Node or build step: the CSS and JavaScript in `static/` are served as they are.

XAMPP's MariaDB (10.4) is too old to be this app's database: Django 5.2 refuses it. Keep `DB_ENGINE=sqlite` on a XAMPP machine. XAMPP's MariaDB is fine as the *source* for [importing the old data](#importing-data-from-the-php-application).

## Installation

Run these in the project folder.

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py runserver
```

On macOS and Linux, use `source .venv/bin/activate` and `cp .env.example .env` instead.

Open <http://localhost:8000/>. Use `localhost`, not an IP address: recording a sound needs microphone access, and browsers only allow that on `localhost` or HTTPS.

`.env` holds the settings for your machine. The defaults work for development. Every setting is listed in [`.env.example`](.env.example).

### Make yourself an admin

The admin dashboard is only for accounts in the `Administrator` group. Sign up in the app first, then run:

```
python manage.py make_admin your_username_here
```

It takes effect on the next page load. `python manage.py make_admin your_username_here --remove` takes it away again.

## URLs

| Address                 | What it is                                                    | Who can open it |
| ----------------------- | ------------------------------------------------------------- | --------------- |
| `/login/`, `/register/` | Log in and sign up                                            | Everyone        |
| `/dashboard/board/`     | The app: tiles, sentence builder, edit mode, rating           | Logged-in users |
| `/dashboard/account/`   | Settings: name, age, profile picture, password, delete account | Logged-in users |
| `/dashboard/analytics/` | Admin dashboard                                               | Administrators  |

`/` goes to the board, or to the login page when nobody is logged in. The PHP application's `/home` address redirects to the board.

### `/admin` and Django's admin site

There are two different "admin" pages:

- **The admin dashboard** at `/dashboard/analytics/` is the app's own page, for accounts in the `Administrator` group.
- **Django's admin site** edits database rows directly. It is off by default and is for accounts with staff status, which is separate from the `Administrator` group.

What `/admin` does depends on `SHOW_ADMIN_ROUTES` in `.env`:

| `SHOW_ADMIN_ROUTES` | `/admin` |
| --- | --- |
| `False` (default) | Redirects to the admin dashboard, as the PHP application's `/admin` address did |
| `True` | Django's admin site |

To let an account log in to Django's admin site as well, add `--staff`:

```
python manage.py make_admin your_username_here --staff
```

## Project layout

The project package, `salitaaco/`, is also the one Django app. Each layer is a folder, divided by feature.

```
manage.py
requirements.txt        Exact versions of the Python libraries
.env.example            Every setting the app reads, with safe example values
ruff.toml               Lint settings

salitaaco/
  settings.py           Reads .env
  urls.py               Login, sign-up, logout, old-address redirects
  routes/               The views, one folder per feature
    dashboard/__init__.py   Every address under /dashboard/
    auth.py  board/  account/  analytics/  error_handler.py
  models/               One model per file
  forms/                One form per file, one folder per feature
    validators.py       Reusable validation rules
    helpers.py          The base form
  templates/
    auth/               Login and sign-up
    dashboard/          base.html (sidebar) and one folder per feature
    components/         Pieces shared between pages
  backends/             SearchModel and QuerysetSorter, for list pages
  utils/                Permission checks, pagination, analytics numbers, import helpers
  defaults/             The tile vocabulary, the sidebar, the role names
  context_processors/   Values every template receives
  authentication/       Log in by username, ignoring letter case
  templatetags/         Template filters
  management/commands/  make_admin, import_php_data
  migrations/
  tests/

static/
  css/index.css         Styles for the app (unchanged from the PHP application)
  css/admin.css         Styles for the admin dashboard (unchanged from the PHP application)
  css/dashboard.css     Sidebar, toast messages, form fields, pagination
  js/main.js            Loaded on every page: toasts, sidebar, modals, theme
  js/board.js           The board
  js/account.js         The settings page

media/                  Uploaded pictures and recordings (not in Git)
docs/feature-map.md     Which PHP route became which Django view
legacy/                 The PHP application
```

Uploaded files are private to the account that owns them. They are served by login-protected views, never from a public `/media/` address, so do not configure a web server to expose the `media/` folder.

## Tests and checks

```
python manage.py test
ruff check
python manage.py check
python manage.py makemigrations --check
```

GitHub Actions runs all four on every push and pull request to `main`.

## Importing data from the PHP application

`import_php_data` copies accounts, profile pictures, custom tile pictures and recordings, usage counts and ratings from the PHP application's MySQL database into this one. Existing passwords keep working.

1. Start the MySQL server that holds the old database (`salitaaco_db`). If the data is on another machine, export it there (phpMyAdmin, **Export** tab) and import the `.sql` file here first.
2. In `.env`, set `LEGACY_DB_NAME=salitaaco_db` and the other `LEGACY_DB_*` values.
3. Run `python manage.py migrate`.
4. Run `python manage.py import_php_data --dry-run`. It reports how many rows it finds and changes nothing.
5. Run `python manage.py import_php_data`.

Things to know:

- An account whose username already exists here is skipped, so the command can be run again safely.
- Old admins (`is_admin = 1`) are added to the `Administrator` group.
- The old database stored local times. They are read as `TIME_ZONE` times (`Asia/Manila` by default), so set `TIME_ZONE` to the old server's time zone before importing.
- The old database is only read, never changed.
- To start over, delete `db.sqlite3` and the files inside the `media/` subfolders, then run `migrate` and the import again.

## Deployment

To run the app on a server:

1. In `.env`, set `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=False`, `DJANGO_ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`, and the `DB_*` values for MySQL 8 or MariaDB 10.5 or newer.
2. Run `python manage.py migrate`, then `python manage.py collectstatic`.
3. Run the app with a WSGI server. The entry point is `salitaaco.wsgi:application`; `gunicorn` is in `requirements.txt` for Linux servers.
4. Have the web server in front serve the `staticfiles/` folder at `/static/` and pass everything else to the app. Do not give it the `media/` folder.

## Troubleshooting

| What you see                                              | What to do                                                                                             |
| --------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| `'python' is not recognized`                              | Install Python 3.13 from <https://www.python.org/downloads/> and tick "Add python.exe to PATH".         |
| `ModuleNotFoundError: No module named 'django'`           | The virtual environment is not active. Run `.venv\Scripts\activate`, then `pip install -r requirements.txt`. |
| `no such table` or `Table ... doesn't exist`              | Run `python manage.py migrate`.                                                                         |
| `pip install` fails on `mysqlclient` (macOS or Linux)     | Install the MySQL client library first, for example `sudo apt install default-libmysqlclient-dev pkg-config`. |
| The admin dashboard sends you back to the board            | The account is not an admin. Run `python manage.py make_admin your_username_here`.                      |
| Recording a sound does nothing                            | Open the app through `localhost` or HTTPS and allow the microphone in the browser.                      |
| "CSRF verification failed" in production                  | Add the site's address, with `https://`, to `CSRF_TRUSTED_ORIGINS`.                                     |

## The PHP application

`legacy/` holds the PHP application exactly as it was, with its own [README](legacy/README.md). It still runs from inside that folder (`cd legacy`, then `php -S localhost:8001`), which is useful for comparing behaviour. Nothing in the Django project depends on it. Delete the folder once the conversion has been checked.
