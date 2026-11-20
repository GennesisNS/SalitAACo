# SalitAACo screenshots

Every page of SalitAACo at desktop size (1920×1080, light theme), with made-up data. A `-full.png` next to a shot is the whole page, for pages taller than the screen.

## Making them again

From the repository root, with the virtual environment's Python:

```
pip install -r screenshots/requirements.txt
python -m playwright install chromium
python screenshots/capture.py
```

`capture.py` reseeds its own database (`screenshots.sqlite3`, with `manage.py seed_screenshots --reset`), starts the app on a free port with its own uploads folder (`screenshots/_media/`) and no ElevenLabs key, logs in through `/login/` as each role, takes the shots, rewrites this file and stops the app. It never touches `db.sqlite3` or `media/`. `--only admin,guardian` takes one side again; `--no-seed` keeps the current screenshot database.

Every made-up account's password is `Salita#2026`:

| Role | Username | Notes |
| --- | --- | --- |
| Admin | `andrea.villanueva` | The demo admin; `paolo.mendoza` and `kristine.bautista` are admins too |
| Guardian | `maricel.santos` | SalitAACo Plus, three children, two family voices, own boards and tiles |
| Guardian | `joel.dizon` | SalitAACo Plus with two children (the add-a-child window) |
| Guardian | `cristina.lopez` | Free, with a payment waiting for an admin |
| Child | `migo.santos` | Miguel Santos, 7, Maricel's child |

The data is made up: names, payments and ratings. The GCash QR code and every proof of payment are generated pictures labelled SAMPLE. The family voices' words are copies of the app's shared voice.

## Public website

| File | Page | URL | Role | What it shows |
| --- | --- | --- | --- | --- |
| [01-public/01-landing-hero-full.png](01-public/01-landing-hero-full.png) | Public website | `/` | Logged out | The hero and the tile demo, as the page opens (whole page) |
| [01-public/01-landing-hero.png](01-public/01-landing-hero.png) | Public website | `/` | Logged out | The hero and the tile demo, as the page opens |
| [01-public/02-features.png](01-public/02-features.png) | Public website | `/` | Logged out | “Ano ang nagagawa ng SalitAACo” |
| [01-public/03-about-us.png](01-public/03-about-us.png) | Public website | `/` | Logged out | Tungkol sa Amin |
| [01-public/04-plans.png](01-public/04-plans.png) | Public website | `/` | Logged out | Mga Plano, from the plan rows, with the footer |
| [01-public/05-landing-demo-sentence.png](01-public/05-landing-demo-sentence.png) | Public website | `/` | Logged out | The hero's tile demo after tapping two tiles |

## Log in and sign up

| File | Page | URL | Role | What it shows |
| --- | --- | --- | --- | --- |
| [02-auth/01-login.png](02-auth/01-login.png) | Log in | `/login/` | Logged out | The login form |
| [02-auth/02-login-wrong-password.png](02-auth/02-login-wrong-password.png) | Log in | `/login/` | Logged out | The message for a wrong password |
| [02-auth/03-register.png](02-auth/03-register.png) | Sign up | `/register/` | Logged out | The guardian sign-up form |
| [02-auth/04-register-privacy-terms.png](02-auth/04-register-privacy-terms.png) | Sign up | `/register/` | Logged out | Paalala sa Privacy, opened from the form |
| [02-auth/05-register-errors-full.png](02-auth/05-register-errors-full.png) | Sign up | `/register/` | Logged out | The messages for an empty form (whole page) |
| [02-auth/05-register-errors.png](02-auth/05-register-errors.png) | Sign up | `/register/` | Logged out | The messages for an empty form |

## Child

| File | Page | URL | Role | What it shows |
| --- | --- | --- | --- | --- |
| [03-child/01-board-home/01-home.png](03-child/01-board-home/01-home.png) | Board: Home | `/dashboard/board/#home` | Child (migo.santos) | Mabilis na Salita and Ang Nararamdaman Ko |
| [03-child/01-board-home/02-home-sentence.png](03-child/01-board-home/02-home-sentence.png) | Board: Home | `/dashboard/board/#home` | Child (migo.santos) | A sentence built from two tiles |
| [03-child/01-board-home/03-home-edit-mode.png](03-child/01-board-home/03-home-edit-mode.png) | Board: Home | `/dashboard/board/#home` | Child (migo.santos) | Edit mode: 🎙️ on each tile, ↺ on recorded ones |
| [03-child/02-board-mga-board/01-mga-board.png](03-child/02-board-mga-board/01-mga-board.png) | Board: Mga Board | `/dashboard/board/#boards` | Child (migo.santos) | Every board the child sees, the family's own included |
| [03-child/03-board-single-board/01-pagkain.png](03-child/03-board-single-board/01-pagkain.png) | Board: one board | `/dashboard/board/#boards/Pagkain` | Child (migo.santos) | The Pagkain board, with an admin's added words at the end |
| [03-child/03-board-single-board/02-pandiwa.png](03-child/03-board-single-board/02-pandiwa.png) | Board: one board | `/dashboard/board/#boards/Pandiwa` | Child (migo.santos) | The verbs board, with nangyari na / ngayon / mamaya |
| [03-child/03-board-single-board/03-custom-pamilya-namin.png](03-child/03-board-single-board/03-custom-pamilya-namin.png) | Board: one board | `/dashboard/board/#boards/Pamilya%20Namin` | Child (migo.santos) | The family's own board |
| [03-child/03-board-single-board/04-pandiwa-mamaya.png](03-child/03-board-single-board/04-pandiwa-mamaya.png) | Board: one board | `/dashboard/board/#boards/Pandiwa` | Child (migo.santos) | The verbs in their future form (mamaya) |
| [03-child/03-board-single-board/05-pagkain-edit-mode.png](03-child/03-board-single-board/05-pagkain-edit-mode.png) | Board: one board | `/dashboard/board/#boards/Pagkain` | Child (migo.santos) | Edit mode on a board |
| [03-child/04-paborito/01-paborito-full.png](03-child/04-paborito/01-paborito-full.png) | Board: Paborito | `/dashboard/board/#favorites` | Child (migo.santos) | The child's most-used words, most used first (whole page) |
| [03-child/04-paborito/01-paborito.png](03-child/04-paborito/01-paborito.png) | Board: Paborito | `/dashboard/board/#favorites` | Child (migo.santos) | The child's most-used words, most used first |
| [03-child/05-profile/01-profile-full.png](03-child/05-profile/01-profile-full.png) | Profile | `/dashboard/profile/` | Child (migo.santos) | The child's profile: name, age, picture, password (whole page) |
| [03-child/05-profile/01-profile.png](03-child/05-profile/01-profile.png) | Profile | `/dashboard/profile/` | Child (migo.santos) | The child's profile: name, age, picture, password |
| [03-child/05-profile/02-delete-account-confirm.png](03-child/05-profile/02-delete-account-confirm.png) | Profile | `/dashboard/profile/` | Child (migo.santos) | Delete-account confirmation (not confirmed) |
| [03-child/06-settings/01-settings-full.png](03-child/06-settings/01-settings-full.png) | Settings | `/dashboard/settings/` | Child (migo.santos) | Tile editing, theme, tile size and the child's voice (whole page) |
| [03-child/06-settings/01-settings.png](03-child/06-settings/01-settings.png) | Settings | `/dashboard/settings/` | Child (migo.santos) | Tile editing, theme, tile size and the child's voice |
| [03-child/07-rating/01-rating-modal.png](03-child/07-rating/01-rating-modal.png) | Board: rate the app | `/dashboard/board/#home` | Child (migo.santos) | I-rate ang SalitAACo: stars and a comment |

## Guardian

| File | Page | URL | Role | What it shows |
| --- | --- | --- | --- | --- |
| [04-guardian/01-dashboard-buod/01-buod.png](04-guardian/01-dashboard-buod/01-buod.png) | Buod | `/dashboard/overview/` | Guardian (maricel.santos) | The children as a table, and the plan |
| [04-guardian/02-mga-bata/01-mga-bata.png](04-guardian/02-mga-bata/01-mga-bata.png) | Mga Bata | `/dashboard/children/` | Guardian (maricel.santos) | Three children: the limit of SalitAACo Plus, so adding is closed |
| [04-guardian/02-mga-bata/02-mga-bata-room-for-more.png](04-guardian/02-mga-bata/02-mga-bata-room-for-more.png) | Mga Bata | `/dashboard/children/` | Guardian (joel.dizon) | A guardian with room for one more child |
| [04-guardian/02-mga-bata/03-add-child-modal.png](04-guardian/02-mga-bata/03-add-child-modal.png) | Mga Bata | `/dashboard/children/` | Guardian (joel.dizon) | ＋ Magdagdag ng bata |
| [04-guardian/03-child-details/01-child-details-full.png](04-guardian/03-child-details/01-child-details-full.png) | A child's page | `/dashboard/children/f005d83f-a6af-4a2e-93fc-611b48c390f0/` | Guardian (maricel.santos) | Name, age, picture, tiles, password (whole page) |
| [04-guardian/03-child-details/01-child-details.png](04-guardian/03-child-details/01-child-details.png) | A child's page | `/dashboard/children/f005d83f-a6af-4a2e-93fc-611b48c390f0/` | Guardian (maricel.santos) | Name, age, picture, tiles, password |
| [04-guardian/03-child-details/02-delete-child-confirm.png](04-guardian/03-child-details/02-delete-child-confirm.png) | A child's page | `/dashboard/children/f005d83f-a6af-4a2e-93fc-611b48c390f0/` | Guardian (maricel.santos) | Delete-child confirmation (not confirmed) |
| [04-guardian/04-child-board-setup/01-child-board-home.png](04-guardian/04-child-board-setup/01-child-board-home.png) | The child's board, for the guardian | `/dashboard/children/f005d83f-a6af-4a2e-93fc-611b48c390f0/board/#home` | Guardian (maricel.santos) | Opens in edit mode; taps here are not counted |
| [04-guardian/04-child-board-setup/02-child-board-mga-board.png](04-guardian/04-child-board-setup/02-child-board-mga-board.png) | The child's board, for the guardian | `/dashboard/children/f005d83f-a6af-4a2e-93fc-611b48c390f0/board/#boards` | Guardian (maricel.santos) | The boards the child sees |
| [04-guardian/04-child-board-setup/03-child-board-custom-board.png](04-guardian/04-child-board-setup/03-child-board-custom-board.png) | The child's board, for the guardian | `/dashboard/children/f005d83f-a6af-4a2e-93fc-611b48c390f0/board/#boards/Pamilya%20Namin` | Guardian (maricel.santos) | The family's own board, in edit mode |
| [04-guardian/05-napiling-bata-mga-board/01-mga-board.png](04-guardian/05-napiling-bata-mga-board/01-mga-board.png) | Napiling Bata › Mga Board | `/dashboard/children/f005d83f-a6af-4a2e-93fc-611b48c390f0/boards/` | Guardian (maricel.santos) | Which boards Miguel sees, and the family's own boards |
| [04-guardian/05-napiling-bata-mga-board/02-add-board-modal.png](04-guardian/05-napiling-bata-mga-board/02-add-board-modal.png) | Napiling Bata › Mga Board | `/dashboard/children/f005d83f-a6af-4a2e-93fc-611b48c390f0/boards/` | Guardian (maricel.santos) | ＋ Magdagdag ng board |
| [04-guardian/05-napiling-bata-mga-board/03-edit-board-modal.png](04-guardian/05-napiling-bata-mga-board/03-edit-board-modal.png) | Napiling Bata › Mga Board | `/dashboard/children/f005d83f-a6af-4a2e-93fc-611b48c390f0/boards/` | Guardian (maricel.santos) | I-edit on a custom board |
| [04-guardian/05-napiling-bata-mga-board/04-delete-board-confirm.png](04-guardian/05-napiling-bata-mga-board/04-delete-board-confirm.png) | Napiling Bata › Mga Board | `/dashboard/children/f005d83f-a6af-4a2e-93fc-611b48c390f0/boards/` | Guardian (maricel.santos) | Delete-board confirmation (not confirmed) |
| [04-guardian/05-napiling-bata-mga-board/05-child-picker-sofia.png](04-guardian/05-napiling-bata-mga-board/05-child-picker-sofia.png) | Napiling Bata › Mga Board | `/dashboard/children/40c9b8d6-4e8e-49c5-88af-b188eb3516fe/boards/` | Guardian (maricel.santos) | The child picker switched to Sofia: two of her boards are off |
| [04-guardian/06-napiling-bata-boses/01-boses.png](04-guardian/06-napiling-bata-boses/01-boses.png) | Napiling Bata › Boses | `/dashboard/children/f005d83f-a6af-4a2e-93fc-611b48c390f0/voice/` | Guardian (maricel.santos) | Which voice Miguel hears: Nanay |
| [04-guardian/07-napiling-bata-paggamit/01-last-7-days.png](04-guardian/07-napiling-bata-paggamit/01-last-7-days.png) | Napiling Bata › Paggamit | `/dashboard/children/f005d83f-a6af-4a2e-93fc-611b48c390f0/usage/?range=7` | Guardian (maricel.santos) | Words and boards used: Huling 7 araw |
| [04-guardian/07-napiling-bata-paggamit/02-last-30-days.png](04-guardian/07-napiling-bata-paggamit/02-last-30-days.png) | Napiling Bata › Paggamit | `/dashboard/children/f005d83f-a6af-4a2e-93fc-611b48c390f0/usage/?range=30` | Guardian (maricel.santos) | Words and boards used: Huling 30 araw |
| [04-guardian/07-napiling-bata-paggamit/03-all-time.png](04-guardian/07-napiling-bata-paggamit/03-all-time.png) | Napiling Bata › Paggamit | `/dashboard/children/f005d83f-a6af-4a2e-93fc-611b48c390f0/usage/?range=all` | Guardian (maricel.santos) | Words and boards used: Lahat |
| [04-guardian/08-boses-ng-pamilya/01-boses-ng-pamilya.png](04-guardian/08-boses-ng-pamilya/01-boses-ng-pamilya.png) | Boses ng Pamilya | `/dashboard/family-voices/` | Guardian (maricel.santos) | Nanay and Lola Remy, every word made |
| [04-guardian/08-boses-ng-pamilya/02-delete-voice-confirm.png](04-guardian/08-boses-ng-pamilya/02-delete-voice-confirm.png) | Boses ng Pamilya | `/dashboard/family-voices/` | Guardian (maricel.santos) | Delete-voice confirmation (not confirmed) |
| [04-guardian/09-sariling-tile/01-sariling-tile-full.png](04-guardian/09-sariling-tile/01-sariling-tile-full.png) | Sariling Tile | `/dashboard/tiles/` | Guardian (maricel.santos) | The family's own tiles and the form to add one (whole page) |
| [04-guardian/09-sariling-tile/01-sariling-tile.png](04-guardian/09-sariling-tile/01-sariling-tile.png) | Sariling Tile | `/dashboard/tiles/` | Guardian (maricel.santos) | The family's own tiles and the form to add one |
| [04-guardian/09-sariling-tile/02-edit-tile-modal.png](04-guardian/09-sariling-tile/02-edit-tile-modal.png) | Sariling Tile | `/dashboard/tiles/` | Guardian (maricel.santos) | I-edit on a tile |
| [04-guardian/09-sariling-tile/03-delete-tile-confirm.png](04-guardian/09-sariling-tile/03-delete-tile-confirm.png) | Sariling Tile | `/dashboard/tiles/` | Guardian (maricel.santos) | Delete-tile confirmation (not confirmed) |
| [04-guardian/10-mga-tile/01-own-board-home.png](04-guardian/10-mga-tile/01-own-board-home.png) | Mga Tile (the guardian's own board) | `/dashboard/board/#home` | Guardian (maricel.santos) | The guardian's own board |
| [04-guardian/10-mga-tile/02-own-board-mga-board.png](04-guardian/10-mga-tile/02-own-board-mga-board.png) | Mga Tile (the guardian's own board) | `/dashboard/board/#boards` | Guardian (maricel.santos) | Every board, the family's own included |
| [04-guardian/10-mga-tile/03-own-board-edit-mode.png](04-guardian/10-mga-tile/03-own-board-edit-mode.png) | Mga Tile (the guardian's own board) | `/dashboard/board/#home` | Guardian (maricel.santos) | Edit mode |
| [04-guardian/11-subscription-plano/01-plano.png](04-guardian/11-subscription-plano/01-plano.png) | Plano at Subscription | `/dashboard/plan/` | Guardian (maricel.santos) | The plans, on SalitAACo Plus with the paid date |
| [04-guardian/11-subscription-plano/02-pay-modal.png](04-guardian/11-subscription-plano/02-pay-modal.png) | Plano at Subscription | `/dashboard/plan/` | Guardian (maricel.santos) | Paying by GCash: the SAMPLE QR code and the proof upload |
| [04-guardian/12-subscription-transactions/01-transactions.png](04-guardian/12-subscription-transactions/01-transactions.png) | Kasaysayan ng bayad | `/dashboard/plan/transactions/` | Guardian (maricel.santos) | Approved and rejected payments, with the reason |
| [04-guardian/12-subscription-transactions/02-proof-viewer.png](04-guardian/12-subscription-transactions/02-proof-viewer.png) | Kasaysayan ng bayad | `/dashboard/plan/transactions/` | Guardian (maricel.santos) | A proof of payment (SAMPLE PROOF) |
| [04-guardian/13-tulong-at-suporta/01-tulong-at-suporta-full.png](04-guardian/13-tulong-at-suporta/01-tulong-at-suporta-full.png) | Tulong at Suporta | `/dashboard/support/` | Guardian (maricel.santos) | Guides, and the form to write to support (whole page) |
| [04-guardian/13-tulong-at-suporta/01-tulong-at-suporta.png](04-guardian/13-tulong-at-suporta/01-tulong-at-suporta.png) | Tulong at Suporta | `/dashboard/support/` | Guardian (maricel.santos) | Guides, and the form to write to support |
| [04-guardian/14-hitsura-at-tile/01-hitsura-at-tile.png](04-guardian/14-hitsura-at-tile/01-hitsura-at-tile.png) | Hitsura at Tile | `/dashboard/settings/` | Guardian (maricel.santos) | Tile editing, theme and tile size |
| [04-guardian/15-account/01-account-full.png](04-guardian/15-account/01-account-full.png) | Account | `/dashboard/profile/` | Guardian (maricel.santos) | Name, picture, age, password (whole page) |
| [04-guardian/15-account/01-account.png](04-guardian/15-account/01-account.png) | Account | `/dashboard/profile/` | Guardian (maricel.santos) | Name, picture, age, password |
| [04-guardian/15-account/02-delete-account-confirm.png](04-guardian/15-account/02-delete-account-confirm.png) | Account | `/dashboard/profile/` | Guardian (maricel.santos) | Delete-account confirmation (not confirmed) |

## Admin

| File | Page | URL | Role | What it shows |
| --- | --- | --- | --- | --- |
| [05-admin/01-dashboard/01-dashboard.png](05-admin/01-dashboard/01-dashboard.png) | Dashboard | `/dashboard/analytics/` | Admin (andrea.villanueva) | Taps per day, boards opened most, recent activity |
| [05-admin/02-analytics-at-ulat/01-paglago-ng-user.png](05-admin/02-analytics-at-ulat/01-paglago-ng-user.png) | Analytics at Ulat | `/dashboard/reports/?tab=growth` | Admin (andrea.villanueva) | Paglago ng user |
| [05-admin/02-analytics-at-ulat/02-paggamit-full.png](05-admin/02-analytics-at-ulat/02-paggamit-full.png) | Analytics at Ulat | `/dashboard/reports/?tab=usage` | Admin (andrea.villanueva) | Paggamit: top words and boards (whole page) |
| [05-admin/02-analytics-at-ulat/02-paggamit.png](05-admin/02-analytics-at-ulat/02-paggamit.png) | Analytics at Ulat | `/dashboard/reports/?tab=usage` | Admin (andrea.villanueva) | Paggamit: top words and boards |
| [05-admin/02-analytics-at-ulat/03-pagbabalik.png](05-admin/02-analytics-at-ulat/03-pagbabalik.png) | Analytics at Ulat | `/dashboard/reports/?tab=retention` | Admin (andrea.villanueva) | Pagbabalik |
| [05-admin/02-analytics-at-ulat/04-negosyo.png](05-admin/02-analytics-at-ulat/04-negosyo.png) | Analytics at Ulat | `/dashboard/reports/?tab=business` | Admin (andrea.villanueva) | Negosyo: plans, revenue by month, payments by status |
| [05-admin/03-mga-ulat/01-mga-ulat.png](05-admin/03-mga-ulat/01-mga-ulat.png) | Mga Ulat | `/dashboard/generated-reports/` | Admin (andrea.villanueva) | Three reports made by the app's own report code |
| [05-admin/03-mga-ulat/02-make-report-mga-user.png](05-admin/03-mga-ulat/02-make-report-mga-user.png) | Mga Ulat | `/dashboard/generated-reports/` | Admin (andrea.villanueva) | ＋ Gumawa ng ulat: mga user |
| [05-admin/03-mga-ulat/03-make-report-mga-bayad.png](05-admin/03-mga-ulat/03-make-report-mga-bayad.png) | Mga Ulat | `/dashboard/generated-reports/` | Admin (andrea.villanueva) | ＋ Gumawa ng ulat: mga bayad |
| [05-admin/03-mga-ulat/04-make-report-feedback.png](05-admin/03-mga-ulat/04-make-report-feedback.png) | Mga Ulat | `/dashboard/generated-reports/` | Admin (andrea.villanueva) | ＋ Gumawa ng ulat: feedback |
| [05-admin/03-mga-ulat/05-delete-report-confirm.png](05-admin/03-mga-ulat/05-delete-report-confirm.png) | Mga Ulat | `/dashboard/generated-reports/` | Admin (andrea.villanueva) | Delete-report confirmation (not confirmed) |
| [05-admin/03-mga-ulat/06-printable-users-report.png](05-admin/03-mga-ulat/06-printable-users-report.png) | Mga Ulat › printable report | `/dashboard/generated-reports/ad4f3004-92a6-420d-83b7-d65230619fd5/` | Admin (andrea.villanueva) | The page to print or save as PDF |
| [05-admin/03-mga-ulat/07-printable-payments-report-full.png](05-admin/03-mga-ulat/07-printable-payments-report-full.png) | Mga Ulat › printable report | `/dashboard/generated-reports/9f627679-64cf-4124-bcfd-a30caadf333f/` | Admin (andrea.villanueva) | The page to print or save as PDF (whole page) |
| [05-admin/03-mga-ulat/07-printable-payments-report.png](05-admin/03-mga-ulat/07-printable-payments-report.png) | Mga Ulat › printable report | `/dashboard/generated-reports/9f627679-64cf-4124-bcfd-a30caadf333f/` | Admin (andrea.villanueva) | The page to print or save as PDF |
| [05-admin/04-mga-user/01-lahat-full.png](05-admin/04-mga-user/01-lahat-full.png) | Mga User | `/dashboard/users/?status=` | Admin (andrea.villanueva) | Accounts: Lahat (whole page) |
| [05-admin/04-mga-user/01-lahat.png](05-admin/04-mga-user/01-lahat.png) | Mga User | `/dashboard/users/?status=` | Admin (andrea.villanueva) | Accounts: Lahat |
| [05-admin/04-mga-user/02-aktibo-full.png](05-admin/04-mga-user/02-aktibo-full.png) | Mga User | `/dashboard/users/?status=active` | Admin (andrea.villanueva) | Accounts: Aktibo (whole page) |
| [05-admin/04-mga-user/02-aktibo.png](05-admin/04-mga-user/02-aktibo.png) | Mga User | `/dashboard/users/?status=active` | Admin (andrea.villanueva) | Accounts: Aktibo |
| [05-admin/04-mga-user/03-hindi-aktibo.png](05-admin/04-mga-user/03-hindi-aktibo.png) | Mga User | `/dashboard/users/?status=inactive` | Admin (andrea.villanueva) | Accounts: Hindi aktibo |
| [05-admin/04-mga-user/04-search-santos.png](05-admin/04-mga-user/04-search-santos.png) | Mga User | `/dashboard/users/?status=&query=santos` | Admin (andrea.villanueva) | Searching for “santos” |
| [05-admin/04-mga-user/05-deactivate-confirm.png](05-admin/04-mga-user/05-deactivate-confirm.png) | Mga User | `/dashboard/users/` | Admin (andrea.villanueva) | Make-inactive confirmation (not confirmed) |
| [05-admin/05-mga-board/01-mga-board.png](05-admin/05-mga-board/01-mga-board.png) | Mga Board | `/dashboard/vocabulary/boards/` | Admin (andrea.villanueva) | Published boards, and Lugar hidden from everyone |
| [05-admin/05-mga-board/02-hide-board-confirm.png](05-admin/05-mga-board/02-hide-board-confirm.png) | Mga Board | `/dashboard/vocabulary/boards/` | Admin (andrea.villanueva) | Hide-board confirmation (not confirmed) |
| [05-admin/06-mga-salita-at-simbolo/01-mga-salita-full.png](05-admin/06-mga-salita-at-simbolo/01-mga-salita-full.png) | Mga Salita at Simbolo | `/dashboard/vocabulary/words/` | Admin (andrea.villanueva) | Every word, with the admin's added words (whole page) |
| [05-admin/06-mga-salita-at-simbolo/01-mga-salita.png](05-admin/06-mga-salita-at-simbolo/01-mga-salita.png) | Mga Salita at Simbolo | `/dashboard/vocabulary/words/` | Admin (andrea.villanueva) | Every word, with the admin's added words |
| [05-admin/06-mga-salita-at-simbolo/02-filter-pagkain.png](05-admin/06-mga-salita-at-simbolo/02-filter-pagkain.png) | Mga Salita at Simbolo | `/dashboard/vocabulary/words/?board=Pagkain` | Admin (andrea.villanueva) | Filtered to the Pagkain board |
| [05-admin/06-mga-salita-at-simbolo/03-add-word-modal.png](05-admin/06-mga-salita-at-simbolo/03-add-word-modal.png) | Mga Salita at Simbolo | `/dashboard/vocabulary/words/` | Admin (andrea.villanueva) | ＋ Magdagdag ng salita |
| [05-admin/06-mga-salita-at-simbolo/04-delete-word-confirm.png](05-admin/06-mga-salita-at-simbolo/04-delete-word-confirm.png) | Mga Salita at Simbolo | `/dashboard/vocabulary/words/?board=Pagkain` | Admin (andrea.villanueva) | Delete-word confirmation (not confirmed) |
| [05-admin/06-mga-salita-at-simbolo/05-edit-word-page.png](05-admin/06-mga-salita-at-simbolo/05-edit-word-page.png) | Mga Salita at Simbolo › I-edit | `/dashboard/vocabulary/words/f3a2dd75-58e6-4084-b47a-ce9bc0f90e7e/` | Admin (andrea.villanueva) | Editing an added word |
| [05-admin/07-kita/01-lahat.png](05-admin/07-kita/01-lahat.png) | Kita | `/dashboard/revenue/?status=` | Admin (andrea.villanueva) | Payments: Lahat |
| [05-admin/07-kita/02-naghihintay.png](05-admin/07-kita/02-naghihintay.png) | Kita | `/dashboard/revenue/?status=pending` | Admin (andrea.villanueva) | Payments: Naghihintay |
| [05-admin/07-kita/03-aprubado.png](05-admin/07-kita/03-aprubado.png) | Kita | `/dashboard/revenue/?status=approved` | Admin (andrea.villanueva) | Payments: Aprubado |
| [05-admin/07-kita/04-tinanggihan.png](05-admin/07-kita/04-tinanggihan.png) | Kita | `/dashboard/revenue/?status=rejected` | Admin (andrea.villanueva) | Payments: Tinanggihan |
| [05-admin/07-kita/05-proof-viewer.png](05-admin/07-kita/05-proof-viewer.png) | Kita | `/dashboard/revenue/` | Admin (andrea.villanueva) | A proof of payment (SAMPLE PROOF) |
| [05-admin/08-mga-subscription/01-mga-subscription.png](05-admin/08-mga-subscription/01-mga-subscription.png) | Mga Subscription | `/dashboard/subscriptions/` | Admin (andrea.villanueva) | Guardians per plan, this month's earnings, the waiting payments |
| [05-admin/08-mga-subscription/02-proof-viewer.png](05-admin/08-mga-subscription/02-proof-viewer.png) | Mga Subscription | `/dashboard/subscriptions/` | Admin (andrea.villanueva) | A waiting payment's proof (SAMPLE PROOF) |
| [05-admin/08-mga-subscription/03-approve-confirm.png](05-admin/08-mga-subscription/03-approve-confirm.png) | Mga Subscription | `/dashboard/subscriptions/` | Admin (andrea.villanueva) | Approve confirmation (not confirmed) |
| [05-admin/08-mga-subscription/04-reject-modal.png](05-admin/08-mga-subscription/04-reject-modal.png) | Mga Subscription | `/dashboard/subscriptions/` | Admin (andrea.villanueva) | Reject, asking for the reason (not sent) |
| [05-admin/09-feedback-at-mga-isyu/01-feedback-full.png](05-admin/09-feedback-at-mga-isyu/01-feedback-full.png) | Feedback at mga Isyu | `/dashboard/feedback/` | Admin (andrea.villanueva) | Support messages (open and resolved) and ratings (whole page) |
| [05-admin/09-feedback-at-mga-isyu/01-feedback.png](05-admin/09-feedback-at-mga-isyu/01-feedback.png) | Feedback at mga Isyu | `/dashboard/feedback/` | Admin (andrea.villanueva) | Support messages (open and resolved) and ratings |
| [05-admin/10-system-general/01-general-full.png](05-admin/10-system-general/01-general-full.png) | System Settings › General | `/dashboard/system/general/` | Admin (andrea.villanueva) | Support contact, maintenance mode (off), GCash with the SAMPLE QR (whole page) |
| [05-admin/10-system-general/01-general.png](05-admin/10-system-general/01-general.png) | System Settings › General | `/dashboard/system/general/` | Admin (andrea.villanueva) | Support contact, maintenance mode (off), GCash with the SAMPLE QR |
| [05-admin/10-system-general/02-general-saved-toast.png](05-admin/10-system-general/02-general-saved-toast.png) | System Settings › General | `/dashboard/system/general/` | Admin (andrea.villanueva) | The success toast after saving the same values |
| [05-admin/11-system-mga-plano/01-mga-plano-full.png](05-admin/11-system-mga-plano/01-mga-plano-full.png) | System Settings › Mga Plano | `/dashboard/system/plans/` | Admin (andrea.villanueva) | Free and SalitAACo Plus, and Mga Limit ng Plano (whole page) |
| [05-admin/11-system-mga-plano/01-mga-plano.png](05-admin/11-system-mga-plano/01-mga-plano.png) | System Settings › Mga Plano | `/dashboard/system/plans/` | Admin (andrea.villanueva) | Free and SalitAACo Plus, and Mga Limit ng Plano |
| [05-admin/11-system-mga-plano/02-add-plan-modal.png](05-admin/11-system-mga-plano/02-add-plan-modal.png) | System Settings › Mga Plano | `/dashboard/system/plans/` | Admin (andrea.villanueva) | ＋ Magdagdag ng plano |
| [05-admin/12-system-access-control/01-access-control.png](05-admin/12-system-access-control/01-access-control.png) | System Settings › Access control | `/dashboard/system/access/` | Admin (andrea.villanueva) | The three admins |
| [05-admin/12-system-access-control/02-add-admin-modal.png](05-admin/12-system-access-control/02-add-admin-modal.png) | System Settings › Access control | `/dashboard/system/access/` | Admin (andrea.villanueva) | ＋ Magdagdag ng admin |
| [05-admin/12-system-access-control/03-remove-admin-confirm.png](05-admin/12-system-access-control/03-remove-admin-confirm.png) | System Settings › Access control | `/dashboard/system/access/` | Admin (andrea.villanueva) | Remove-admin confirmation (not confirmed) |
| [05-admin/13-system-privacy/01-privacy.png](05-admin/13-system-privacy/01-privacy.png) | System Settings › Privacy | `/dashboard/system/privacy/` | Admin (andrea.villanueva) | What is kept, consent versions, old usage counts |
| [05-admin/13-system-privacy/02-purge-usage-confirm.png](05-admin/13-system-privacy/02-purge-usage-confirm.png) | System Settings › Privacy | `/dashboard/system/privacy/` | Admin (andrea.villanueva) | Delete-old-counts confirmation (not confirmed) |
| [05-admin/14-mga-tile/01-own-board-home.png](05-admin/14-mga-tile/01-own-board-home.png) | Mga Tile (the admin's own board) | `/dashboard/board/#home` | Admin (andrea.villanueva) | The admin's own board |
| [05-admin/15-hitsura-at-tile/01-hitsura-at-tile.png](05-admin/15-hitsura-at-tile/01-hitsura-at-tile.png) | Hitsura at Tile | `/dashboard/settings/` | Admin (andrea.villanueva) | Tile editing, theme and tile size |
| [05-admin/16-account/01-account-full.png](05-admin/16-account/01-account-full.png) | Account | `/dashboard/profile/` | Admin (andrea.villanueva) | Name, picture, password (whole page) |
| [05-admin/16-account/01-account.png](05-admin/16-account/01-account.png) | Account | `/dashboard/profile/` | Admin (andrea.villanueva) | Name, picture, password |
| [05-admin/16-account/02-delete-account-confirm.png](05-admin/16-account/02-delete-account-confirm.png) | Account | `/dashboard/profile/` | Admin (andrea.villanueva) | Delete-account confirmation (not confirmed) |

## Maintenance mode

| File | Page | URL | Role | What it shows |
| --- | --- | --- | --- | --- |
| [06-maintenance/01-maintenance-page.png](06-maintenance/01-maintenance-page.png) | Maintenance page | `/dashboard/board/` | Child (migo.santos) | What everyone but admins gets, children on their board included |
| [06-maintenance/02-maintenance-admin-general-full.png](06-maintenance/02-maintenance-admin-general-full.png) | System Settings › General | `/dashboard/system/general/` | Admin (andrea.villanueva) | Admins still get in, with maintenance mode on (whole page) |
| [06-maintenance/02-maintenance-admin-general.png](06-maintenance/02-maintenance-admin-general.png) | System Settings › General | `/dashboard/system/general/` | Admin (andrea.villanueva) | Admins still get in, with maintenance mode on |
