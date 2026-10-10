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

### Activating the virtual environment automatically (VS Code)

The virtual environment must be active in every terminal that runs `python manage.py ...`. In VS Code this happens by itself: [`.vscode/settings.json`](.vscode/settings.json) points VS Code at `.venv` and tells it to activate it in each new terminal. It needs the Python extension (`ms-python.python`).

1. Create `.venv` first (the `python -m venv .venv` step above).
2. Close any open terminals in VS Code, then open a new one with **Ctrl+`**. The prompt should start with `(.venv)`.

If the prompt does not show `(.venv)`:

| What you see | What to do |
| --- | --- |
| No `(.venv)`, no error | VS Code is remembering another interpreter. Press **Ctrl+Shift+P**, run **Python: Select Interpreter**, pick the entry showing `.venv`, then open a new terminal. |
| `running scripts is disabled on this system` | PowerShell is blocking the activation script. Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, then open a new terminal. |

This only covers terminals inside VS Code. In a PowerShell or Command Prompt window opened elsewhere, run `.venv\Scripts\activate` yourself.

The path in the settings file is the Windows one. On macOS and Linux, choose the interpreter once with **Python: Select Interpreter** instead.

### The three kinds of account

| Account | Who it is for | How it is made | What it can do |
| --- | --- | --- | --- |
| Guardian | A parent or carer | Signing up on `/register/` | Create and manage their children's accounts, set up a child's tiles, see a child's most-used words, use the board themselves |
| Child | The child who talks with the board | By their guardian, on the "Mga Bata" page | Log in with their own username and password and use their own board |
| Admin | Whoever runs the app | `python manage.py make_admin` (below) | Open the admin dashboard, and use the board |

Each kind has its own model (`GuardianAccount`, `ChildAccount`, `AdminAccount`) holding the name and picture, and its own group (`Guardian`, `Child`, `Administrator`) deciding which pages it may open.

Things to know:

- A guardian cannot delete their own account while they still have children; the children's accounts are deleted first.
- Accounts that existed before guardians were introduced became child accounts with no guardian. They work as before.

### Make yourself an admin

The admin dashboard is only for accounts in the `Administrator` group. Sign up in the app first, then run:

```
python manage.py make_admin your_username_here
```

It takes effect on the next page load. `python manage.py make_admin your_username_here --remove` takes it away again.

The command adds an admin account next to the one you signed up with, so a guardian who becomes an admin keeps their children.

## URLs

| Address                 | What it is                                                    | Who can open it |
| ----------------------- | ------------------------------------------------------------- | --------------- |
| `/login/`, `/register/` | Log in and sign up                                            | Everyone        |
| `/dashboard/board/`     | The app: tiles, sentence builder, edit mode, rating           | Logged-in users |
| `/dashboard/profile/`   | Profile: name, profile picture, password, delete account (and age, for a child) | Logged-in users |
| `/dashboard/children/`  | Mga Bata: a guardian's children, and a page and a board for each | Guardians       |
| `/dashboard/settings/`  | Settings: tile editing, dark theme, tile size                  | Logged-in users |
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
    auth.py  board/  account/  children/  settings/  analytics/  error_handler.py
  models/               One model per file (account_base.py is shared by the three account models)
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
  js/account.js         The profile page

media/                  Uploaded pictures and recordings (not in Git)
docs/feature-map.md     Which PHP route became which Django view
.vscode/settings.json   Makes VS Code activate .venv in new terminals
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
- Old admins (`is_admin = 1`) become admin accounts in the `Administrator` group. Everyone else becomes a child account with no guardian.
- The old database stored local times. They are read as `TIME_ZONE` times (`Asia/Manila` by default), so set `TIME_ZONE` to the old server's time zone before importing.
- The old database is only read, never changed.
- To start over, delete `db.sqlite3` and the files inside the `media/` subfolders, then run `migrate` and the import again.

## Deployment

To run the app on a server:

1. In `.env`, set `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=False`, `DJANGO_ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`, and the `DB_*` values for MySQL 8 or MariaDB 10.5 or newer.
2. Run `python manage.py migrate`, then `python manage.py collectstatic`.
3. Run the app with a WSGI server. The entry point is `salitaaco.wsgi:application`; `gunicorn` is in `requirements.txt` for Linux servers.
4. Have the web server in front serve the `staticfiles/` folder at `/static/` and pass everything else to the app. Do not give it the `media/` folder.

## Using MySQL in production

Development and production each have their own `.env`, so nothing is converted: the same migrations build the tables on either database.

1. On the production MySQL server (MySQL 8, or MariaDB 10.5 or newer), create an empty database:
   ```sql
   CREATE DATABASE salitaaco CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```
2. In the production `.env`, set `DB_ENGINE=mysql` and the `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST` and `DB_PORT` values.
3. Run `python manage.py migrate`. This creates every table and the `Administrator`, `Guardian` and `Child` groups.

Production then starts empty. Sign up, and run `make_admin` for your account.

### Bringing data along from SQLite

Only needed if the SQLite database holds accounts you want to keep.

1. On the machine with the SQLite data, export it. `-Xutf8` is needed on Windows, or the export fails on emoji:
   ```
   python -Xutf8 manage.py dumpdata --natural-foreign --natural-primary --exclude contenttypes --exclude auth.permission --exclude sessions --exclude admin.logentry --indent 2 -o data.json
   ```
2. Copy `data.json` and the whole `media/` folder to the production machine. The database only stores the file names of pictures and recordings; the files themselves are in `media/`.
3. On production, after step 3 above and before anyone signs up:
   ```
   python manage.py loaddata data.json
   ```

Passwords, admin rights, pictures, recordings, usage counts and ratings come across. Sessions do not, so everyone logs in again. Delete `data.json` afterwards: it contains the password hashes.

To bring the PHP application's data to production instead, run `import_php_data` there (see above) rather than exporting from SQLite.

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
