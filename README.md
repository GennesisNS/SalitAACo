# SalitAACo

A Filipino AAC (augmentative and alternative communication) web app. A child taps picture tiles to build a sentence, which the app speaks aloud. Their guardian sets the board up for them: which boards they see, favorite words, family voices, their own pictures and recordings. Admins run the site: accounts, boards and words, feedback and settings. A public website at `/` introduces the app.

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

Open <http://localhost:8000/>: the public website, with "Magsimula" leading to sign-up. Use `localhost`, not an IP address: recording a sound needs microphone access, and browsers only allow that on `localhost` or HTTPS.

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

| Account | Who it is for | How it is made | What it can do | Lands on |
| --- | --- | --- | --- | --- |
| Guardian | A parent or carer | Signing up on `/register/` | Create and manage their children's accounts, choose each child's boards, favorite words and voice, see their usage, record family voices, write to support | Buod (`/dashboard/overview/`) |
| Child | The child who talks with the board | By their guardian, on the "Mga Bata" page | Log in with their own username and password and use their own board | The board (`/dashboard/board/`) |
| Admin | Whoever runs the app | `python manage.py make_admin` (below), or by another admin on System Settings > Access control | Everything under "Admin" in [URLs](#urls) | Dashboard (`/dashboard/analytics/`) |

Each kind has its own model (`GuardianAccount`, `ChildAccount`, `AdminAccount`) holding the name and picture, and its own group (`Guardian`, `Child`, `Administrator`) deciding which pages it may open.

Things to know:

- A guardian cannot delete their own account while they still have children; the children's accounts are deleted first.
- Accounts that existed before guardians were introduced became child accounts with no guardian. They work as before.
- An account is active or inactive. An admin makes one inactive on Mga User: it cannot log in, and nothing of it is deleted. Making a guardian inactive leaves their children's accounts active.

### Make yourself an admin

The admin dashboard is only for accounts in the `Administrator` group. Sign up in the app first, then run:

```
python manage.py make_admin your_username_here
```

It takes effect on the next page load. `python manage.py make_admin your_username_here --remove` takes it away again.

The command adds an admin account next to the one you signed up with, so a guardian who becomes an admin keeps their children. Once there is one admin, more can be added and removed in the app, on System Settings > Access control.

## URLs

Addresses without a leading slash are under `/dashboard/`. Guardian and child pages are in Filipino; so are the admin pages.

| Address | What it is | Who can open it |
| --- | --- | --- |
| `/` | The public website: hero, what the app does, About Us, plans, footer. Someone logged in is sent to their own first page instead | Everyone |
| `/login/`, `/register/` | Log in and sign up | Everyone |
| `board/` | The board: Home, Mga Board, Paborito (`#home`, `#boards`, `#boards/<board>`, `#favorites`), sentence builder, edit mode, rating | Logged-in users |
| `profile/` | Profile: name, picture, password, delete account (and age, for a child) | Logged-in users |
| `settings/` | Tile editing, dark theme, tile size, and for a child their voice | Logged-in users |
| `overview/` | Buod: a guardian's children as a table, and their plan | Guardians |
| `children/` | Mga Bata: the children, and the form that adds one | Guardians |
| `children/<uuid>/` | Edit a child: name, age, picture, password, delete | The child's guardian |
| `children/<uuid>/board/` | The child's board, for setting up tiles | The child's guardian |
| `children/<uuid>/boards/` | Mga Board: which boards the child sees | The child's guardian |
| `children/<uuid>/favorites/` | Mga Paborito: words put on the child's Paborito screen *(may be removed)* | The child's guardian |
| `children/<uuid>/voice/` | Boses: which voice the child hears | The child's guardian |
| `children/<uuid>/usage/` | Paggamit: boards opened and words tapped, by 7 days, 30 days or all time | The child's guardian |
| `family-voices/` | Boses ng Pamilya: family members' cloned voices | Guardians |
| `plan/`, `plan/transactions/` | Plano at Subscription and the history of payments *(frontend only, see [Plans and payments](#plans-and-payments))* | Guardians |
| `support/` | Tulong at Suporta: guides, and a form for writing to the admins | Guardians |
| `analytics/` | Admin dashboard | Admins |
| `reports/`, `reports/export/` | Analytics at Ulat, and its CSV reports | Admins |
| `users/` | Mga User: every account, by status; make one inactive or active | Admins |
| `vocabulary/boards/` | Mga Board: publish a board or hide it from everyone | Admins |
| `vocabulary/words/` | Mga Salita at Simbolo: every word, and adding words to boards | Admins |
| `institutions/` | Mga Paaralan at Institusyon *(may be removed)* | Admins |
| `revenue/`, `subscriptions/` | Kita and Mga Subscription *(frontend only)* | Admins |
| `feedback/` | Feedback at mga Isyu: support messages and ratings *(may be removed)* | Admins |
| `system/general/` | Support contact details, maintenance mode | Admins |
| `system/access/` | Who is an admin | Admins |
| `system/privacy/` | What is kept, consent versions, deleting old usage counts *(may be removed)* | Admins |
| `system/status/` | Health checks and the latest log errors *(may be removed)* | Admins |

The PHP application's `/home` address redirects to the board.

A guardian's pages about one child are reached from the sidebar for the "selected child": the child whose page was opened last. The picker above them opens the same page for another child.

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

The project package, `salitaaco/`, is the app itself. Each layer is a folder, divided by feature. The public website is a second, small app in `public/`.

```
manage.py
requirements.txt        Exact versions of the Python libraries
.env.example            Every setting the app reads, with safe example values
ruff.toml               Lint settings

salitaaco/
  settings.py           Reads .env
  urls.py               The public website's URLs, login, sign-up, logout, old-address redirects
  routes/               The views, one folder per feature
    dashboard/__init__.py   Every address under /dashboard/
    auth.py  board/  account/  settings/  error_handler.py
    overview/  children/  family_voices/  favorites/  plan/  support/        (guardian)
    analytics/  reports/  users/  vocabulary/  institutions/  revenue/
    subscriptions/  feedback/  system/  privacy/  technical_status/          (admin)
  models/               One model per file (account_base.py is shared by the three account models)
  forms/                One form per file, one folder per feature
    validators.py       Reusable validation rules
    helpers.py          The base form
  templates/
    layouts/            dashboard.html (guardian and admin) and child.html
    auth/               Login and sign-up
    dashboard/          One folder per feature
    components/         Pieces shared between pages
    maintenance.html    What everyone but admins sees in maintenance mode
  middleware/           Maintenance mode
  backends/             SearchModel and QuerysetSorter, for list pages
    text_to_speech/     The ElevenLabs client: speech and voice cloning
  utils/                Permission checks, pagination, boards, usage and admin numbers, import helpers
  defaults/             The tile vocabulary, how it is laid out on the board, the navigation, the plans, the role names
  context_processors/   Values every template receives: the account, its layout, its navigation
  authentication/       Log in by username, ignoring letter case
  templatetags/         Template filters
  management/commands/  make_admin, import_php_data, generate_tile_audio
  migrations/
  tests/                One folder per feature

public/                 The public website at "/": its view, URLs, template, CSS, JavaScript and tests

static/
  css/tokens.css        The colour palettes
  css/base.css          Shared by every page: buttons, fields, the toggle switch, cards, modals, tables, tiles
  css/dashboard.css     The guardian and admin layout and their pages
  css/child.css         The child layout and the board
  js/main.js            Loaded on every page: toasts, sidebar, modals, voice samples, theme
  js/board.js           The board
  js/account.js  settings.js  family_voices.js  child_boards.js  plan.js   One page each

media/                  Uploaded pictures and recordings (not in Git)
docs/feature-map.md     Which PHP route became which Django view, and what was added since
.vscode/settings.json   Makes VS Code activate .venv in new terminals
legacy/                 The PHP application
```

Uploaded files are private to the account that owns them. They are served by login-protected views, never from a public `/media/` address, so do not configure a web server to expose the `media/` folder.

## Design

### Layouts and palettes

There are two layouts. Guardians and admins share `layouts/dashboard.html`: a sidebar and a bar across the top. Children get `layouts/child.html`: large rounded tiles, big touch targets and navigation along the bottom. The board uses the child layout whoever opens it. Pages every role opens (Profile, Settings) extend the `layout_template` variable, which names the right one.

The colours are in `static/css/tokens.css`, one block per palette:

| Palette | Used by | Colours |
| --- | --- | --- |
| `navy` (Navy + White) | Guardian and admin pages, login, sign-up, error pages | `#0F1E3A` `#1E2F4F` `#A7B4D0` `#FFFFFF` |
| `ocean` (Ocean Royale) | The child's pages and the board | `#03045E` `#023EBA` `#00B4D8` `#CAF0F8` `#FBB02D` |

A palette block gives every colour twice, `--l-*` for the light theme and `--d-*` for the dark one, and one block at the end of the file turns them into the names the rest of the CSS uses (`--bg`, `--card`, `--ink`, `--accent`…). To add a palette, copy a block, rename it and change its values; an element carrying `data-palette="<name>"` then draws itself and everything inside it in those colours. Text must keep a contrast of 4.5:1 or more against what it sits on.

The dark theme is the `data-theme` attribute on `<html>`, set before the page paints by `components/head_scripts.html`: the choice made in Settings (remembered per browser), or the device's.

The public website has its own stylesheet in `public/` and does not use these files.

### Toggle switch

Every checkbox that turns something on or off is drawn as a switch. Its CSS is in `base.css`, and its "on" colour is the palette's `--switch-on`:

```html
<label class="switch">
  <input type="checkbox">
  <span class="slider"></span>
</label>
```

## Boards and words

`salitaaco/defaults/vocabulary.py` is the default vocabulary and is never edited by the app. A **board** is one of its categories. `defaults/board.py` says how the vocabulary is laid out: the quick words on the Home screen, which board is the "feelings" board, and each board's picture.

What admins and guardians change is stored in the database on top of it:

| What | Who | Model |
| --- | --- | --- |
| A board hidden from everyone | Admin, on Mga Board | `BoardStatus` |
| A word added to a board | Admin, on Mga Salita at Simbolo | `AddedWord` |
| A board turned off for one child | Guardian, on the child's Mga Board | `HiddenBoard` |
| A favorite word of one child | Guardian, on Mga Paborito | `FavoriteWord` |

At least one board always stays published, and each child always has at least one board on. An added word appears at the end of its board for everyone. It has no recording in the shared voice until `python manage.py generate_tile_audio` is run again; until then the device's voice speaks it.

Language modes (English and Taglish labels) are not built: the feature has not been decided.

## Plans and payments

**These pages are frontend only for now.** They show the design; nothing is saved.

- The plans (Free at ₱0, SalitAACo Plus at ₱149 a month) are in `salitaaco/defaults/plans.py`. The guardian's Plano at Subscription page, the admin's Mga Subscription page and the public website all read them from there, so they will follow the database once plans are stored in it.
- Paying is by QR code: the guardian scans it, pays, and uploads a picture of the successful payment. The page shows a labelled stand-in for the QR code, and the button that sends the picture is disabled.
- With no payments saved, the lists of payments are empty. To look at the design of a full table during development, open the page with `?halimbawa=1`: it shows made-up payments from `defaults/payment_examples.py` under a notice saying so. This works only while `DJANGO_DEBUG` is on.

Still to build: plan and payment models, saving the proof of payment as a private upload, approving and rejecting, starting the plan on approval, and editing plans.

## Maintenance mode

An admin turns it on at System Settings > General. While it is on, everyone but admins gets the maintenance page (with the admin's message) instead of the app, **including children on their boards**, and the public website is closed too. Logging in and out stay open, so an admin can get in to turn it off; someone logged in to another account uses the button on the maintenance page to log out first.

## Pages that may be removed

Some pages were built so that each can be deleted cleanly. Each is its own routes folder, templates folder, tests folder, sidebar item in `defaults/navigations.py`, and addresses in `routes/dashboard/__init__.py`. Beyond those:

| Page | Routes folder | Also delete |
| --- | --- | --- |
| Mga Paborito (guardian) | `routes/favorites/` | `forms/favorites/`, `models/favorite_word.py` and its line in `models/__init__.py`, migration `0011` |
| Mga Paaralan at Institusyon | `routes/institutions/` | `forms/institutions/`, `templates/components/institutions/`, `models/institution.py` and its line in `models/__init__.py`, migration `0016` |
| Feedback at mga Isyu | `routes/feedback/` | Nothing more |
| Privacy | `routes/privacy/` | `forms/privacy/` |
| Technical status | `routes/technical_status/` | Nothing more |

If a migration being deleted has already been applied somewhere, add a migration that deletes the model instead of deleting the file. A few tests elsewhere list these pages among the sidebar's items and need the name taken out.

## Tests and checks

```
python manage.py test
ruff check
python manage.py check
python manage.py makemigrations --check
```

GitHub Actions runs all four on every push and pull request to `main`.

## Voices for the tiles (ElevenLabs)

A tile with no recording of its own can still speak. For each word the board plays the first of these that exists:

1. The family's own recording of that tile (edit mode on the board).
2. The child's **family voice**: a family member's voice cloned with ElevenLabs.
3. The app's **shared Filipino voice**, generated once with ElevenLabs.
4. The browser's own voice.

Both voices need an ElevenLabs API key in `.env` as `ELEVENLABS_API_KEY`. `ELEVENLABS_MODEL` defaults to `eleven_multilingual_v2`, a model that lists Filipino. Cloning voices needs an ElevenLabs plan that includes voice cloning.

### The shared Filipino voice

1. Pick a Filipino voice in ElevenLabs' voice library and put its ID in `.env` as `ELEVENLABS_VOICE_ID`.
2. Try a few words and listen to the files in `static/audio/text-to-speech/`:
   ```
   python manage.py generate_tile_audio --words kumain "gusto ko" "tawagan si Nanay" opo
   ```
3. When it sounds right, voice every tile word: the 105 default ones (all three forms of each verb included) and any an admin added. Words that already have a file are skipped:
   ```
   python manage.py generate_tile_audio
   ```
4. Commit the MP3s. The app never calls ElevenLabs for them while it runs. To change the voice, set the new ID and run the command again with `--overwrite`. After an admin adds a word, run it again to voice the new word.

### Family voices

Guardians add them on the **Boses ng Pamilya** page: one or several family members (Nanay, Tatay, Lola…).

1. The guardian reads the **Paalala at Kasunduan**, the notice and consent terms in `templates/components/family_voice_terms.html`, and agrees to them. This is a step of its own: nothing can be recorded or uploaded before it, and the server refuses a voice without it. The date and the terms version (`TERMS_VERSION` in `defaults/family_voice.py`) are saved with the voice; change the version whenever the wording changes.
2. The guardian names the family member, who reads a provided Filipino paragraph for about a minute. It is recorded in the browser or uploaded as an audio file.
3. ElevenLabs clones the voice. The recording is sent to ElevenLabs once and is not kept by the app.
4. While the page is open, the tile words are generated in the voice, a few at a time, with a progress bar. If it stops, reopening the page carries on.
5. Which family voice a child hears can be chosen by the guardian, on the child's Boses page, or by the child, on their Settings page under Hitsura, where ▶ plays each voice first. Whoever changes it last wins. A new voice is given to the children who do not have one yet.

Deleting a voice deletes it at ElevenLabs as well, with its generated words. Deleting a guardian's account deletes all their voices. The generated words are private uploads under `media/family-voices/`, heard only by that guardian and their children.

The terms are a plain-language notice, not legal advice. Have them reviewed against the Philippine Data Privacy Act before real families use the feature.

The ElevenLabs client is in `salitaaco/backends/text_to_speech/elevenlabs.py`.

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
| An admin page sends you back to your own first page        | The account is not an admin. Run `python manage.py make_admin your_username_here`.                      |
| Everyone sees "Inaayos namin ang app"                     | Maintenance mode is on. Log in as an admin and turn it off at System Settings > General.               |
| "Hindi aktibo ang account na ito" at login                | An admin made the account inactive. An admin makes it active again on Mga User.                        |
| `no such table` after pulling new code                    | New migrations were added. Run `python manage.py migrate`.                                             |
| Recording a sound does nothing                            | Open the app through `localhost` or HTTPS and allow the microphone in the browser.                      |
| "CSRF verification failed" in production                  | Add the site's address, with `https://`, to `CSRF_TRUSTED_ORIGINS`.                                     |

## The PHP application

`legacy/` holds the PHP application exactly as it was, with its own [README](legacy/README.md). It still runs from inside that folder (`cd legacy`, then `php -S localhost:8001`), which is useful for comparing behaviour. Nothing in the Django project depends on it. Delete the folder once the conversion has been checked.
