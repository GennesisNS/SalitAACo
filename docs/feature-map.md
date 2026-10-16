# Feature map: PHP application to Django

The record of what each route of the PHP application became, and of what was added since. The PHP application is in [`legacy/`](../legacy/).

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
| `/admin` | `analytics.view_analytics` | `analytics` `analytics/` | | `dashboard/analytics/analytics.html` | Done; since the redesign it is the admin dashboard, and its lists have pages of their own |
| `admin: overview`, `signups_by_day`, `rating_distribution`, `top_words` | functions in `utils/analytics.py`, called by `view_analytics`, `reports.view_reports` and `feedback.view_feedback` | | | rendered by the server | Done |
| `admin: users` | `users.view_users` | `users` `users/` | `SearchUserForm`, `UserStatusForm` | `dashboard/users/users.html`, ten rows per page | Done |
| `admin: ratings` | `feedback.view_feedback` | `feedback` `feedback/` | | `dashboard/feedback/feedback.html`, ten rows per page | Done |

Not routes, but replaced: the SQL `UPDATE users SET is_admin = 1` became `python manage.py make_admin <username>`; `database/database.sql` became the migrations.

## Where the Django project behaves differently on purpose

| PHP application | Django project | Why |
| --- | --- | --- |
| One page; settings and rating saved in the background | Saving reloads the page and shows a toast; the sentence being built is cleared | Full MYO page flow was chosen |
| Settings in a modal over the board, with "Mga Tile" and "Account" tabs | Two pages: Settings (`/dashboard/settings/`: tile editing, theme) and Profile (`/dashboard/profile/`: account details, password, delete account). The name and picture at the top of every page lead to Profile; a child reaches Settings from their Profile | Same; split into two pages on request |
| Admin dashboard shows its own login box, and an "Access denied" screen to non-admins | Anonymous visitors go to `/login/`; someone logged in without permission for a page is sent to their own first page with the message "Naka-log in ka pero walang pahintulot ang account na ito sa pahinang iyon." | MYO's `multi_user_test` behaviour; the message was "…hindi admin…" until guardian pages outnumbered admin ones |
| Admin rights apply from the next login | Admin rights apply at once | The group is checked on every request |
| Users and feedback tables list every row | Ten rows per page; the users table can be searched and sorted | MYO listing convention |
| Tile pictures and recordings accepted without checks | Pictures must be JPEG, PNG, WebP or GIF up to 5 MB (the avatar rule); recordings must be audio up to 5 MB | The stored content type is sent back to the browser |
| A picture's type is whatever the browser claims | The type is read from the file itself | Same |
| Uploads stored in the database | Uploads stored as files with random names, served only to their owner | MYO stores uploads under `media/` |
| A tile without a recording used whatever voice the browser had | Each word plays, the first that exists: the family's recording, the child's family voice (a family member's voice cloned with ElevenLabs on the Boses ng Pamilya page, with consent terms), the shared Filipino voice (generated once with ElevenLabs by `manage.py generate_tile_audio`), the browser's voice | Requested after the conversion |
| Tiles come in one size | Each account chooses small, medium or large tiles on the Settings page, with a demo. The choice is saved on the account (`tile_size`), so it follows the user to any device, unlike the theme, which is remembered per browser. Medium is the original size | Requested after the conversion |
| Tapping a tile played its recording at once | Tapping only adds the word. The **▶ Patugtugin** button plays the sentence in order: each word's recording if it has one, otherwise the device's Filipino voice. **↩ Ibalik** takes back the last word | Requested after the conversion |
| One page of tiles with a tab for each category | The board has four screens along the bottom: Home (quick words and feelings), Mga Board (a board is a category), Paborito (favorite and most-used words) and, for a child, Profile. Screens change without reloading, so the sentence carries across them | The redesign |
| A replaced tile picture could stay cached for a day | The picture's address changes when it is replaced | Bug in the PHP application |
| Emptying the sentence one word at a time raised a JavaScript error | Fixed | Bug in the PHP application |
| The dark theme toggle is in the board's header and is forgotten on reload | The toggle is on the Settings page, and the choice is remembered in the browser | Pages reload more often now; moved to Settings on request |
| No request forgery protection | Django's CSRF protection on every form and `fetch` | |
| `/` returns 404 | `/` is the public website; someone logged in is sent to their own first page (a child's board, a guardian's Buod, an admin's dashboard) | |
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

## Added after the conversion: the redesign

The app was restyled and given three sides (child, guardian, admin) and a public website. Paths without a leading slash are under `/dashboard/`.

### Decisions

| Question | Decision |
| --- | --- |
| Colours | Two palettes as CSS variables in `static/css/tokens.css`: "Navy + White" for guardians and admins, "Ocean Royale" for children. Another palette is one more block |
| Layouts | `layouts/dashboard.html` for guardians and admins, `layouts/child.html` for children. The board is in the child layout whoever opens it |
| Language of the pages | Filipino on all three sides, the admin's included, and on the public website |
| Where each account lands | A child on the board, a guardian on Buod, an admin on the dashboard |
| What changes to the vocabulary are | `defaults/vocabulary.py` is never edited. Hidden boards, added words, a child's boards and favorites are database rows on top of it |
| Account status | Active or inactive only (`User.is_active`). There is no "pending": guardians sign up freely |
| Language modes (English, Taglish) | Not built: the feature has not been decided |
| Subscriptions and payments | Frontend only for now: the pages show the design and save nothing. Payment is by QR code and an uploaded proof, with no payment gateway |
| Audit log | Not built, in keeping with the decision below against an audit trail |
| New boards | Admins publish, hide and add words to the existing boards; they do not create boards |
| Reports | CSV only |
| On/off choices | Every one is the toggle switch in `static/css/base.css` |

### Child

| Feature | Django view | URL name and path | Form | Template |
| --- | --- | --- | --- | --- |
| The board's screens: Home, Mga Board, one board, Paborito | `board.view_board` | `board` `board/` (`#home`, `#boards`, `#boards/<board>`, `#favorites`) | the board's tile forms | `dashboard/board/board.html` |
| Counting a board being opened | `usage.record_board_open` | `record_board_open` `board/usage/board/` | `BoardNameForm` | JSON |
| My Profile, with no caretaker area or PIN | `account.manage_account` | `profile` `profile/` | as before | `dashboard/account/account.html` |

### Guardian

| Feature | Django view | URL name and path | Form | Template |
| --- | --- | --- | --- | --- |
| Buod: children as a table, the plan | `overview.view_overview` | `overview` `overview/` | | `dashboard/overview/overview.html` |
| Mga Bata: the table, and the add-a-child modal | `children.view_children` | `children` `children/` | `CreateChildForm` | `dashboard/children/children.html` |
| Which boards a child sees (at least one stays on) | `boards.manage_child_boards` | `child_boards` `children/<uuid>/boards/` | `ChildBoardsForm` | `dashboard/children/boards.html` |
| A child's favorite words *(may be removed)* | `favorites.manage_favorites`, `favorites.remove_favorite` | `favorites` `children/<uuid>/favorites/`, `remove_favorite` `…/favorites/<uuid>/remove/` | `AddFavoriteWordForm` | `dashboard/favorites/favorites.html` |
| Which voice a child hears | `voice.choose_child_voice` | `child_voice` `children/<uuid>/voice/` | `ChooseFamilyVoiceForm` | `dashboard/children/voice.html` |
| A child's usage, by 7 days, 30 days or all time | `usage.view_child_usage` | `child_usage` `children/<uuid>/usage/` | `UsageRangeForm` | `dashboard/children/usage.html` |
| Family voices, with consent as a step before recording | `family_voices.view_family_voices` | `family_voices` `family-voices/` | `AddFamilyVoiceForm` | `dashboard/family_voices/family_voices.html` |
| Plans, paying by QR code, history of payments *(frontend only)* | `plan.view_plan`, `plan.view_transactions` | `plan` `plan/`, `plan_transactions` `plan/transactions/` | | `dashboard/plan/` |
| Guides, and writing to support | `support.view_support` | `support` `support/` | `ContactSupportForm` | `dashboard/support/support.html` |

### Admin

| Feature | Django view | URL name and path | Form | Template |
| --- | --- | --- | --- | --- |
| Dashboard | `analytics.view_analytics` | `analytics` `analytics/` | | `dashboard/analytics/analytics.html` |
| Analytics at Ulat, and CSV reports | `reports.view_reports`, `reports.export_report` | `reports` `reports/`, `export_report` `reports/export/` | `ReportTabForm`, `ExportReportForm` | `dashboard/reports/reports.html` |
| Users by status; make an account inactive or active | `users.view_users`, `users.set_user_status` | `users` `users/`, `set_user_status` `users/<id>/status/` | `SearchUserForm`, `UserStatusForm`, `SetUserStatusForm` | `dashboard/users/users.html` |
| Boards: publish or hide (at least one stays published) | `boards.view_admin_boards`, `boards.set_board_status` | `admin_boards` `vocabulary/boards/`, `set_board_status` `vocabulary/boards/status/` | `SetBoardStatusForm` | `dashboard/vocabulary/boards.html` |
| Words: list, add, edit, delete | `words.view_words`, `words.edit_word`, `words.delete_word` | `words` `vocabulary/words/`, `edit_word` `…/<uuid>/`, `delete_word` `…/<uuid>/delete/` | `SearchWordForm`, `WordForm` | `dashboard/vocabulary/words.html`, `word.html` |
| Institutions *(may be removed)* | `institutions.view_institutions`, `edit_institution`, `delete_institution` | `institutions` `institutions/`, `edit_institution` `…/<uuid>/`, `delete_institution` `…/<uuid>/delete/` | `InstitutionForm` | `dashboard/institutions/` |
| Payments to approve *(frontend only)* | `revenue.view_revenue` | `revenue` `revenue/` | `TransactionStatusForm` | `dashboard/revenue/revenue.html` |
| Subscriptions and plans *(frontend only)* | `subscriptions.view_subscriptions` | `subscriptions` `subscriptions/` | | `dashboard/subscriptions/subscriptions.html` |
| Support messages and ratings *(may be removed)* | `feedback.view_feedback`, `feedback.resolve_support_message` | `feedback` `feedback/`, `resolve_support_message` `feedback/messages/<uuid>/resolve/` | | `dashboard/feedback/feedback.html` |
| System Settings: General (support contact, maintenance mode) | `general.view_general_settings` | `system_general` `system/general/` | `GeneralSettingsForm` | `dashboard/system/general.html` |
| System Settings: Access control | `access.view_access_control`, `access.remove_admin` | `system_access` `system/access/`, `remove_admin` `system/access/<id>/remove/` | `AddAdminForm`, `RemoveAdminForm` | `dashboard/system/access.html` |
| System Settings: Privacy *(may be removed)* | `privacy.view_privacy` | `system_privacy` `system/privacy/` | `PurgeUsageForm` | `dashboard/privacy/privacy.html` |
| System Settings: Technical status *(may be removed)* | `technical_status.view_technical_status` | `system_status` `system/status/` | | `dashboard/technical_status/technical_status.html` |

### Public website

| Feature | Django view | URL name and path | Template |
| --- | --- | --- | --- |
| Hero with "Magsimula" to sign-up, what the app does, About Us, plans, footer | `public.views.view_home` | `index` `/` | `public/templates/public/home.html` |

It is its own app in the top-level `public/` folder. The project lists it in `INSTALLED_APPS` and includes its URLs; the plans it shows are the same plan data the admin and guardian pages read.

### Models added

| Model | What it holds |
| --- | --- |
| `HiddenBoard` | A board a guardian turned off for one child |
| `FavoriteWord` | A word a guardian put on a child's Paborito screen *(belongs to a page that may be removed)* |
| `DailyUsage` | How many times, on one day, a user tapped a word or opened a board. Counts only |
| `SupportMessage` | What a guardian wrote to support, and when an admin marked it as dealt with |
| `BoardStatus` | Whether an admin has hidden a board from everyone |
| `AddedWord` | A word an admin added to a board |
| `SiteSetting` | The one row of site settings: support contact details, maintenance mode |
| `Institution` | The admin's record of a school or centre *(belongs to a page that may be removed)* |

### Rules

- Only a child's own guardian reaches the child's pages; anyone else gets 404.
- Neither a guardian's taps nor the boards they open on a child's board are counted as the child's.
- An inactive account cannot log in and is logged out where it is logged in. Nothing of it is deleted, and a guardian's children stay active, so that a child is not cut off from their board.
- An admin cannot make their own account inactive or take away their own admin access.
- A hidden board is shown to nobody, including guardians choosing a child's boards.
- No two tiles say the same thing: an added word cannot repeat a word, or the audio file name, of another tile.
- Family voices ask for consent as a step of its own before anything can be recorded.
- In maintenance mode everyone but admins gets the maintenance page, children included.
- Admins see counts of what is used, never the sentences built on a board; reports hold no names or usernames.

Kept from the PHP application against the MYO conventions, because behaviour wins:

- Records are deleted for real, not soft-deleted. The app tells the user that deleting an account is permanent.
- Login is by username, not email. The PHP application has no email addresses, so there is no email verification or password reset.
- The minimum password length is 4 characters.
- `django-auditlog` is not installed. Nothing in the PHP application shows change history, and an audit trail would keep data from accounts the app promises to erase. For the same reason the redesign's "Audit Logs & Security" page was not built.
- Resetting a tile and removing a profile picture are POST forms, not GET links.

## Not yet checked

- The import command has not been run against real data. It was run against a test database with the same tables on XAMPP's MariaDB 10.4.
- The redesigned pages were driven in a real browser (Edge) at desktop, tablet and phone width, in the light and dark themes, picking and resetting a tile's picture included. Not exercised: playing a sentence aloud, recording a sound, and cloning a family voice with a real ElevenLabs key.
- The pages have not been tried on an actual tablet, the main device for the board.
- The migrations were run on SQLite only. They use no database-specific SQL, but have not been run against MySQL.
- Subscriptions and payments have no backend yet, so nothing about them is tested beyond the pages opening and their controls being disabled.
- The contrast of text was checked by calculation for the palette's colour pairs, not with an accessibility tool on every page.
