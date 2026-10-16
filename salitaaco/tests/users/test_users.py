from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.urls import reverse

from salitaaco.forms.users.set_user_status import SetUserStatusForm
from salitaaco.forms.users.user_status import ACTIVE, ALL, INACTIVE, UserStatusForm
from salitaaco.tests.users_base import GUARDIAN_PASSWORD, UserBase, make_guardian


def messages_of(response):
    return [str(message) for message in get_messages(response.wsgi_request)]


class UsersBase(UserBase):
    """Nanay is Miguel's guardian. Ana has no guardian. Developer is the admin."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.nanay = make_guardian("nanay", "Nanay Rosa", children=[cls.miguel])
        cls.url = reverse("users")

    def set_status(self, user, active, **extra):
        data = {"active": "on"} if active else {}
        return self.client.post(reverse("set_user_status", args=[user.pk]), {**data, **extra})

    def is_active(self, user):
        return User.objects.get(pk=user.pk).is_active


class UserStatusFormsTest(UsersBase):
    def test_no_status_or_an_unknown_one_means_everyone(self):
        for data in [None, {}, {"status": ""}, {"status": "pending"}]:
            self.assertEqual(UserStatusForm(data).chosen(), ALL, data)
        self.assertEqual(UserStatusForm({"status": "inactive"}).chosen(), INACTIVE)

    def test_there_are_only_two_statuses(self):
        self.assertEqual([value for value, label in UserStatusForm().fields["status"].choices], [ALL, ACTIVE, INACTIVE])

    def test_an_admin_cannot_make_their_own_account_inactive(self):
        form = SetUserStatusForm({}, acting_user=self.developer, target_user=self.developer)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.non_field_errors(), ["Hindi mo magagawang hindi aktibo ang sarili mong account."])
        self.assertTrue(SetUserStatusForm({"active": "on"}, acting_user=self.developer, target_user=self.developer).is_valid())
        self.assertTrue(SetUserStatusForm({}, acting_user=self.developer, target_user=self.miguel).is_valid())


class UsersPageTest(UsersBase):
    def test_only_admins_open_the_page(self):
        self.assertRedirects(self.client.get(self.url), f"/login/?next={self.url}")
        for username in ["miguel", "nanay"]:
            self.login_as(username)
            self.assertEqual(self.client.get(self.url).status_code, 302, username)
            self.assertEqual(self.set_status(self.ana, False).status_code, 302)
        self.assertTrue(self.is_active(self.ana))

        self.login_as("developer")
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_tabs_filter_by_status_and_count_what_the_search_found(self):
        User.objects.filter(pk=self.ana.pk).update(is_active=False)
        self.login_as("developer")

        def page(**query):
            response = self.client.get(self.url, query)
            return (
                sorted(user.username for user in response.context["users"]),
                [(tab["label"], tab["count"], tab["active"]) for tab in response.context["tabs"]],
            )

        self.assertEqual(page(), (
            ["ana", "developer", "miguel", "nanay"],
            [("Lahat", 4, True), ("Aktibo", 3, False), ("Hindi aktibo", 1, False)],
        ))
        self.assertEqual(page(status="inactive")[0], ["ana"])
        self.assertEqual(page(status="active")[0], ["developer", "miguel", "nanay"])
        # The counts follow the search, and an unknown status shows everyone.
        self.assertEqual(page(query="a", status="inactive"), (
            ["ana"], [("Lahat", 2, False), ("Aktibo", 1, False), ("Hindi aktibo", 1, True)],
        ))
        self.assertEqual(page(status="pending")[0], ["ana", "developer", "miguel", "nanay"])

    def test_each_row_has_its_status_and_the_action_that_fits_it(self):
        User.objects.filter(pk=self.ana.pk).update(is_active=False)
        self.login_as("developer")
        response = self.client.get(self.url)

        self.assertContains(response, '<span class="statusBadge approved">Aktibo</span>', count=3)
        self.assertContains(response, '<span class="statusBadge rejected">Hindi aktibo</span>', count=1)
        self.assertContains(response, "Gawing aktibo</button>", count=1)
        # Every active account but the admin's own can be made inactive.
        self.assertContains(response, "Gawing hindi aktibo</button>", count=2)
        self.assertContains(response, "Ikaw ito", count=1)
        self.assertNotContains(response, f'data-open-modal="deactivate-{self.developer.pk}"')


class SetUserStatusTest(UsersBase):
    def test_an_inactive_account_cannot_log_in_and_is_told_why(self):
        self.login_as("developer")
        response = self.set_status(self.miguel, False)

        self.assertRedirects(response, self.url)
        self.assertEqual(messages_of(response), ["Hindi na aktibo ang account na @miguel. Hindi na ito makakapag-log in."])
        self.assertFalse(self.is_active(self.miguel))

        self.client.post(reverse("logout"))
        response = self.client.post(reverse("login"), {"username": "miguel", "password": "lihim1234"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hindi aktibo ang account na ito. Makipag-ugnayan sa admin.")
        self.assertNotIn("_auth_user_id", self.client.session)
        # With the wrong password it is the usual error: the status is not given away.
        response = self.client.post(reverse("login"), {"username": "miguel", "password": "mali"})
        self.assertContains(response, "Maling username o password.")
        self.assertNotContains(response, "Hindi aktibo")

    def test_an_account_made_inactive_is_logged_out_where_it_is_logged_in(self):
        self.login_as("miguel")
        self.assertEqual(self.client.get(reverse("board")).status_code, 200)

        User.objects.filter(pk=self.miguel.pk).update(is_active=False)

        response = self.client.get(reverse("board"))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    def test_an_account_can_be_made_active_again_with_nothing_lost(self):
        self.login_as("developer")
        self.set_status(self.miguel, False)
        response = self.set_status(self.miguel, True)

        self.assertEqual(messages_of(response)[-1], "Aktibo na muli ang account na @miguel.")
        self.assertTrue(self.is_active(self.miguel))
        self.assertTrue(User.objects.get(pk=self.miguel.pk).child_account.guardian == self.nanay)
        self.client.post(reverse("logout"))
        self.assertTrue(self.client.login(username="miguel", password="lihim1234"))

    def test_a_guardians_children_stay_active(self):
        self.login_as("developer")
        self.set_status(self.nanay.user, False)

        self.assertFalse(self.is_active(self.nanay.user))
        self.assertTrue(self.is_active(self.miguel))
        self.client.post(reverse("logout"))
        self.assertFalse(self.client.login(username="nanay", password=GUARDIAN_PASSWORD))
        self.assertTrue(self.client.login(username="miguel", password="lihim1234"))

    def test_an_admin_cannot_lock_themselves_out(self):
        self.login_as("developer")
        response = self.set_status(self.developer, False)
        self.assertEqual(messages_of(response), ["Hindi mo magagawang hindi aktibo ang sarili mong account."])
        self.assertTrue(self.is_active(self.developer))

    def test_it_is_a_post_to_a_real_account_and_returns_to_the_list_as_it_was(self):
        self.login_as("developer")
        self.assertEqual(self.client.get(reverse("set_user_status", args=[self.miguel.pk])).status_code, 405)
        self.assertEqual(self.client.post(reverse("set_user_status", args=[999999])).status_code, 404)

        back = f"{self.url}?status=active&users_page=1"
        self.assertRedirects(self.set_status(self.miguel, False, next=back), back, fetch_redirect_response=False)
        # An address on another site is not followed.
        self.assertRedirects(self.set_status(self.miguel, True, next="https://example.com/"), self.url)
