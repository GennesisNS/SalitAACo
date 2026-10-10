# Feature map: PHP application to Django

The record of what each route of the PHP application became. The PHP application is in [`legacy/`](../legacy/).

## Decisions

| Question | Decision |
| --- | --- |
| Existing data | Fresh schema; a one-off import command (`import_php_data`) copies the old data |
| Existing passwords | Imported as `bcrypt$<php hash>`; Django's bcrypt hasher checks them and re-hashes on next login |
| URLs | Redesigned; `/home` redirects to the board; `/admin` redirects to the admin dashboard unless Django's admin site is turned on (`SHOW_ADMIN_ROUTES`), which then takes `/admin/`; the `/api/...` endpoints are gone |
| Page flow | Full MYO style: forms, post/redirect/get, toast messages, sidebar dashboard |
| Frontend | The PHP application's CSS and vanilla JavaScript; no Tailwind, DaisyUI, Alpine or Node build |
| Real time | None in the PHP application, so plain WSGI and no `websockets` app |
| Site settings | None in the PHP application, so no settings store |

## Models

| PHP table | Django model | Notes |
| --- | --- | --- |
| `users` | `auth.User` + one of `ChildAccount`, `GuardianAccount`, `AdminAccount` | `User` holds username, password, `date_joined` (was `created_at`), `last_login`. The account holds display name and avatar; a child's also holds age and the link to their guardian. `is_admin` became an `AdminAccount` in the `Administrator` group; every other old user becomes a `ChildAccount` with no guardian. (A single `Profile` model did this job until migration 0005.) |
| `customizations` | `Customization` | Blobs became files under `media/customization-images/` and `media/customization-sounds/` |
| `word_usage` | `WordUsage` | |
| `ratings` | `Rating` | The 1 to 5 check constraint is kept |

## Routes

URL names are given with their path. Paths without a leading slash are under `/dashboard/`.

| PHP route | Django view | URL name and path | Form | Template | Status |
| --- | --- | --- | --- | --- | --- |
| `/home` (logged out) and `auth: login` | `auth.login_view` | `login` `/login/` | `LoginForm` | `auth/login.html` | Done |
| `auth: signup` | `auth.register_view` | `register` `/register/` | `RegisterForm` | `auth/register.html` | Done |
| `auth: logout` | `auth.logout_view` | `logout` `/logout/` | | | Done |
| `auth: check` | none | | | | Dropped: no page called it, and server-rendered pages know who is logged in |
| `/home` (logged in) | `board.view_board` | `board` `board/` | | `dashboard/board/board.html` | Done |
| `app: list` | part of `view_board` | | | sent to the page as JSON | Done |
| `app: save_image` | `view_board` (`tile_image_form`) | `board` | `UploadTileImageForm` | | Done |
| `app: save_sound` | `view_board` (`tile_sound_form`) | `board` | `UploadTileSoundForm` | | Done |
| `app: reset` | `customizations.reset_customization` | `reset_customization` `board/customizations/reset/<uuid>/` | | | Done |
| `app: image` | `customizations.view_customization_image` | `view_customization_image` `board/customizations/<uuid>/image/` | | | Done |
| `app: sound` | `customizations.view_customization_sound` | `view_customization_sound` `board/customizations/<uuid>/sound/` | | | Done |
| `app: increment_usage` | `usage.increment_word_usage` | `increment_word_usage` `board/usage/increment/` | `TileWordForm` | JSON | Done |
| `app: frequent_list` | `usage.list_frequent_words`, and part of `view_board` | `list_frequent_words` `board/usage/frequent/` | | JSON | Done |
| `app: get_my_rating` | part of `view_board` (prefills the form) | | | | Done |
| `app: submit_rating` | `view_board` (`rating_form`) | `board` | `SubmitRatingForm` | modal on the board | Done |
| `auth: get_profile` | part of `account.manage_account` | | | | Done |
| `auth: update_profile` | `manage_account` (`profile_form`) | `profile` `profile/` | `ProfileInformationForm` | `dashboard/account/account.html` | Done |
| `auth: upload_avatar` | `manage_account` (`avatar_form`) | `profile` | `UploadAvatarForm` | | Done |
| `auth: remove_avatar` | `account.remove_avatar` | `remove_avatar` `profile/avatar/remove/` | | | Done |
| `auth: avatar` | `account.view_avatar` | `view_avatar` `profile/avatar/` | | | Done |
| `auth: change_password` | `manage_account` (`password_form`) | `profile` | `ChangePasswordForm` | | Done |
| `auth: delete_account` | `manage_account` (`delete_account_form`) | `profile` | `DeleteAccountForm` | modal on the profile page | Done |
| Settings modal, "Mga Tile" tab | `settings.view_settings` | `settings` `settings/` | | `dashboard/settings/settings.html` | Done |
| `/admin` | `analytics.view_analytics` | `analytics` `analytics/` | `SearchUserForm` | `dashboard/analytics/analytics.html` | Done |
| `admin: overview`, `signups_by_day`, `rating_distribution`, `top_words` | functions in `utils/analytics.py`, called by `view_analytics` | | | rendered by the server | Done |
| `admin: users`, `admin: ratings` | queries in `view_analytics` | | | rendered by the server, ten rows per page | Done |

Not routes, but replaced: the SQL `UPDATE users SET is_admin = 1` became `python manage.py make_admin <username>`; `database/database.sql` became the migrations.

## Where the Django project behaves differently on purpose

| PHP application | Django project | Why |
| --- | --- | --- |
| One page; settings and rating saved in the background | Saving reloads the page and shows a toast; the sentence being built is cleared | Full MYO page flow was chosen |
| Settings in a modal over the board, with "Mga Tile" and "Account" tabs | Two pages: Settings (`/dashboard/settings/`: tile editing, theme) and Profile (`/dashboard/profile/`: account details, password, delete account; opened from the avatar at the bottom of the sidebar) | Same; split into two pages on request |
| Admin dashboard shows its own login box, and an "Access denied" screen to non-admins | Anonymous visitors go to `/login/`; non-admins are sent to the board with the message "Naka-log in ka pero hindi admin ang account na ito." | MYO's `multi_user_test` behaviour |
| Admin rights apply from the next login | Admin rights apply at once | The group is checked on every request |
| Users and feedback tables list every row | Ten rows per page; the users table can be searched and sorted | MYO listing convention |
| Tile pictures and recordings accepted without checks | Pictures must be JPEG, PNG, WebP or GIF up to 5 MB (the avatar rule); recordings must be audio up to 5 MB | The stored content type is sent back to the browser |
| A picture's type is whatever the browser claims | The type is read from the file itself | Same |
| Uploads stored in the database | Uploads stored as files with random names, served only to their owner | MYO stores uploads under `media/` |
| Tiles come in one size | Each account chooses small, medium or large tiles on the Settings page, with a demo. The choice is saved on the account (`tile_size`), so it follows the user to any device, unlike the theme, which is remembered per browser. Medium is the original size | Requested after the conversion |
| Tapping a tile played its recording at once | Tapping only adds the word. The **▶ Patugtugin** button plays the sentence in order: each word's recording if it has one, otherwise the device's Filipino voice | Requested after the conversion |
| A replaced tile picture could stay cached for a day | The picture's address changes when it is replaced | Bug in the PHP application |
| Emptying the sentence one word at a time raised a JavaScript error | Fixed | Bug in the PHP application |
| The dark theme toggle is in the board's header and is forgotten on reload | The toggle is on the Settings page, and the choice is remembered in the browser | Pages reload more often now; moved to Settings on request |
| No request forgery protection | Django's CSRF protection on every form and `fetch` | |
| `/` returns 404 | `/` goes to the board or the login page | |
| `last_login` is empty until the first log in after sign-up | Signing up counts as a login | Django records it when the session starts |
| "Today" and "this week" follow the MySQL server's clock | They follow `TIME_ZONE` (`Asia/Manila`) | |

## Added after the conversion: child, guardian and admin accounts

The PHP application had one kind of user. The Django project now has three, each with its own model and group.

| Feature | Django view | URL name and path | Form | Template |
| --- | --- | --- | --- | --- |
| Sign-up makes a guardian | `auth.register_view` | `register` `/register/` | `RegisterForm` | `auth/register.html` |
| A guardian's children; create a child | `children.view_children` | `children` `children/` | `CreateChildForm` | `dashboard/children/children.html` |
| A child's page: profile, usage, new password, delete | `children.manage_child` | `manage_child` `children/<uuid>/` | `ProfileInformationForm`, `UploadAvatarForm`, `ResetChildPasswordForm`, `DeleteChildForm` | `dashboard/children/child.html` |
| A child's picture | `children.view_child_avatar`, `children.remove_child_avatar` | `view_child_avatar` `children/<uuid>/avatar/`, `remove_child_avatar` `children/<uuid>/avatar/remove/` | | |
| A child's board, for the guardian to set up tiles | `board.view_board` | `child_board` `children/<uuid>/board/` | the board's tile forms | `dashboard/board/board.html` |

Rules:

- Only a child's own guardian reaches the child's page, board, pictures and recordings; anyone else gets 404.
- Taps a guardian makes on a child's board are not counted as the child's.
- A guardian confirms deleting a child with the guardian's own password.
- A guardian cannot delete their own account while they have children.
- A child keeps everything an account could do before: their board, edit mode, their profile and password.
- `make_admin` adds an admin account beside the user's existing one.

Kept from the PHP application against the MYO conventions, because behaviour wins:

- Records are deleted for real, not soft-deleted. The app tells the user that deleting an account is permanent.
- Login is by username, not email. The PHP application has no email addresses, so there is no email verification or password reset.
- The minimum password length is 4 characters.
- `django-auditlog` is not installed. Nothing in the PHP application shows change history, and an audit trail would keep data from accounts the app promises to erase.
- Resetting a tile and removing a profile picture are POST forms, not GET links.

## Not yet checked

- The import command has not been run against real data. It was run against a test database with the same tables on XAMPP's MariaDB 10.4.
- The pages were checked in screenshots at desktop and phone width. Recording a sound and picking a picture were not exercised in a real browser.
