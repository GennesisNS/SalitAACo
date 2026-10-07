from django.db import IntegrityError, transaction
from django.urls import reverse

from salitaaco.forms.rating.submit_rating import SubmitRatingForm
from salitaaco.models.rating import Rating
from salitaaco.tests.users_base import UserBase


class SubmitRatingFormTest(UserBase):
    def test_valid(self):
        form = SubmitRatingForm({"rating": "4", "comment": "  Maganda!  "})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data, {"rating": 4, "comment": "Maganda!"})

    def test_rating_must_be_one_to_five(self):
        for rating in ["", "0", "6", "abc"]:
            form = SubmitRatingForm({"rating": rating, "comment": ""})
            self.assertFalse(form.is_valid(), rating)
            self.assertEqual(form.errors["rating"], ["Pumili ng 1 hanggang 5 bituin."])

    def test_empty_comment_is_stored_as_none(self):
        form = SubmitRatingForm({"rating": "5", "comment": "   "})
        self.assertTrue(form.is_valid())
        self.assertIsNone(form.cleaned_data["comment"])

    def test_long_comment_is_cut_to_a_thousand_characters(self):
        form = SubmitRatingForm({"rating": "5", "comment": "a" * 1500})
        self.assertTrue(form.is_valid())
        self.assertEqual(len(form.cleaned_data["comment"]), 1000)


class RatingRouteTest(UserBase):
    def submit(self, rating, comment=""):
        return self.client.post(reverse("board"), {"rating_form": "", "rating": rating, "comment": comment})

    def test_submit_then_update_keeps_one_rating_per_user(self):
        self.login_as("miguel")
        self.assertRedirects(self.submit("3", "Ayos lang"), reverse("board"))
        self.assertRedirects(self.submit("5"), reverse("board"))

        rating = Rating.objects.get(user=self.miguel)
        self.assertEqual(rating.rating, 5)
        self.assertIsNone(rating.comment)
        self.assertEqual(rating.stars, "★★★★★")

    def test_invalid_rating_reopens_the_modal_with_the_error(self):
        self.login_as("miguel")
        response = self.submit("9")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["show_rating_modal"])
        self.assertContains(response, "Pumili ng 1 hanggang 5 bituin.")
        self.assertFalse(Rating.objects.exists())

    def test_board_prefills_the_users_own_rating(self):
        Rating.objects.create(user=self.miguel, rating=4, comment="Salamat")
        Rating.objects.create(user=self.ana, rating=1)
        self.login_as("miguel")

        rating_form = self.client.get(reverse("board")).context["rating_form"]
        self.assertEqual(rating_form.initial, {"rating": 4, "comment": "Salamat"})

    def test_database_rejects_a_rating_out_of_range(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Rating.objects.create(user=self.miguel, rating=6)
