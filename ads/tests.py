from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.test import Client, TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from ads.models import Ad, ExchangeProposal

from .forms import AdForm


class IndexViewTests(TestCase):
    def setUp(self):
        # Создаём пользователя
        self.user = User.objects.create_user(username="testuser", password="testpass123")

        # Создаём 3 объявления (чтобы проверить пагинацию по 1 на странице)
        for i in range(6):
            Ad.objects.create(
                user=self.user,
                title=f"Ad {i}",
                description="Test description",
                category="Test category",
                condition="new",
            )

        self.client = Client()

    def test_index_redirect_if_not_logged_in(self):
        response = self.client.get(reverse("index"))
        self.assertRedirects(
            response, "/login/?next=/"
        )  # По умолчанию путь к login, проверь если у тебя другой

    def test_index_logged_in(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "index.html")

        # Проверяем, что на странице есть page_obj с 1 объявлением (с пагинацией 1 на странице)
        page_obj = response.context["page_obj"]
        self.assertEqual(len(page_obj), 3)

        # Проверяем, что общее количество объявлений 3
        self.assertEqual(page_obj.paginator.count, 6)

    def test_index_pagination_page_2(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("index") + "?page=2")
        self.assertEqual(response.status_code, 200)
        page_obj = response.context["page_obj"]
        self.assertEqual(len(page_obj), 3)  # если на второй странице тоже 3 элемента
        self.assertEqual(page_obj.number, 2)


class MyAdsListViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username="user1", password="pass1234")
        self.user2 = User.objects.create_user(username="user2", password="pass1234")

        # Объявления для user1
        Ad.objects.create(
            user=self.user1, title="User1 Ad 1", description="Desc", category="Cat", condition="new"
        )
        Ad.objects.create(
            user=self.user1,
            title="User1 Ad 2",
            description="Desc",
            category="Cat",
            condition="used",
        )

        # Объявление для user2
        Ad.objects.create(
            user=self.user2, title="User2 Ad", description="Desc", category="Cat", condition="new"
        )

    def test_redirect_if_not_logged_in(self):
        response = self.client.get(reverse("ad_list"))  # имя роута my_ads_list
        self.assertRedirects(response, "/login/?next=" + reverse("ad_list"))

    def test_ads_belong_to_logged_in_user(self):
        self.client.login(username="user1", password="pass1234")
        response = self.client.get(reverse("ad_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "my_ads_list.html")

        ads = response.context["ads"]
        self.assertEqual(len(ads), 2)
        for ad in ads:
            self.assertEqual(ad.user, self.user1)

    def test_no_ads_for_user_without_ads(self):
        self.client.login(username="user2", password="pass1234")
        response = self.client.get(reverse("ad_list"))
        self.assertEqual(response.status_code, 200)
        ads = response.context["ads"]
        # Для user2 в базе 1 объявление, но тут мы имитируем проверку на user1 ads (по твоему view показываются только текущие)
        # Так что ads для user2 будет 1
        self.assertEqual(len(ads), 1)
        for ad in ads:
            self.assertEqual(ad.user, self.user2)


class CreateAdViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="user", password="pass1234")
        self.url = reverse("ad_create")

    def test_get_request_returns_form(self):
        self.client.login(username="user", password="pass1234")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "create_ad.html")
        self.assertIsInstance(response.context["form"], AdForm)

    def test_post_valid_data_creates_ad(self):
        self.client.login(username="user", password="pass1234")

        # Пример простого валидного POST без файла
        post_data = {
            "title": "Test Ad",
            "description": "Description",
            "category": "Test Category",
            "condition": "new",
        }

        response = self.client.post(self.url, data=post_data)

        # Проверяем редирект на index
        self.assertRedirects(response, reverse("index"))

        # Проверяем, что объявление создалось
        ad = Ad.objects.filter(title="Test Ad", user=self.user).first()
        self.assertIsNotNone(ad)
        self.assertEqual(ad.description, "Description")
        self.assertEqual(ad.category, "Test Category")
        self.assertEqual(ad.condition, "new")

    def test_post_invalid_data_shows_form_errors(self):
        self.client.login(username="user", password="pass1234")

        # Отправляем пустую форму (недостаточно данных)
        post_data = {}

        response = self.client.post(self.url, data=post_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "create_ad.html")
        form = response.context["form"]
        self.assertTrue(form.errors)  # Есть ошибки валидации

        # Объявление не создалось
        self.assertEqual(Ad.objects.filter(user=self.user).count(), 0)


class EditAdViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_owner = User.objects.create_user(username="owner", password="pass1234")
        self.user_other = User.objects.create_user(username="other", password="pass1234")
        self.ad = Ad.objects.create(
            user=self.user_owner,
            title="Original Title",
            description="Original description",
            category="Test Category",
            condition="new",
        )
        self.url = reverse("ad_edit", kwargs={"pk": self.ad.pk})
        self.not_exist_url = reverse("ad_edit", kwargs={"pk": 9999})

    def test_ad_not_found_returns_404(self):
        self.client.login(username="owner", password="pass1234")
        response = self.client.get(self.not_exist_url)
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, "not_found_ad.html")

    def test_forbidden_if_not_owner(self):
        self.client.login(username="other", password="pass1234")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, "forbidden_ad.html")

    def test_get_request_returns_form_with_ad_data(self):
        self.client.login(username="owner", password="pass1234")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "edit_ad.html")
        form = response.context["form"]
        self.assertIsInstance(form, AdForm)
        self.assertEqual(form.instance, self.ad)

    def test_post_valid_data_updates_ad_and_redirects(self):
        self.client.login(username="owner", password="pass1234")
        post_data = {
            "title": "Updated Title",
            "description": "Updated description",
            "category": "Test Category",
            "condition": "used",
        }
        response = self.client.post(self.url, data=post_data, follow=True)
        self.assertRedirects(response, reverse("index"))

        # Проверяем, что объявление обновилось
        self.ad.refresh_from_db()
        self.assertEqual(self.ad.title, "Updated Title")
        self.assertEqual(self.ad.description, "Updated description")
        self.assertEqual(self.ad.condition, "used")

    def test_post_invalid_data_shows_errors(self):
        self.client.login(username="owner", password="pass1234")
        post_data = {
            "title": "",  # Обычно поле title обязательно
            "description": "Updated description",
            "category": "Test Category",
            "condition": "used",
        }
        response = self.client.post(self.url, data=post_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "edit_ad.html")
        form = response.context["form"]
        self.assertTrue(form.errors)

        # Объявление не обновилось
        self.ad.refresh_from_db()
        self.assertNotEqual(self.ad.title, "")


class DeleteAdViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(username="owner", password="pass1234")
        self.other_user = User.objects.create_user(username="other", password="pass1234")
        self.ad = Ad.objects.create(
            user=self.owner,
            title="Test Ad",
            description="Test description",
            category="Test Category",
            condition="new",
        )
        self.url = reverse("ad_delete", kwargs={"pk": self.ad.pk})
        self.not_exist_url = reverse("ad_delete", kwargs={"pk": 9999})

    def test_ad_not_found_returns_404(self):
        self.client.login(username="owner", password="pass1234")
        response = self.client.get(self.not_exist_url)
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, "not_found_ad.html")

    def test_forbidden_if_not_owner(self):
        self.client.login(username="other", password="pass1234")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, "forbidden_ad.html")

    def test_get_request_shows_confirm_delete_page(self):
        self.client.login(username="owner", password="pass1234")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "delete_ad.html")
        self.assertEqual(response.context["ad"], self.ad)

    def test_post_request_deletes_ad_and_redirects(self):
        self.client.login(username="owner", password="pass1234")
        response = self.client.post(self.url, follow=True)
        self.assertRedirects(response, reverse("index"))
        with self.assertRaises(Ad.DoesNotExist):
            Ad.objects.get(pk=self.ad.pk)


class SearchAdsViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="pass1234")

        # Создадим тестовые объявления
        Ad.objects.create(
            user=self.user,
            title="iPhone 14",
            description="Good condition",
            category="Electronics",
            condition="new",
        )
        Ad.objects.create(
            user=self.user,
            title="Samsung TV",
            description="Used TV",
            category="Electronics",
            condition="used",
        )
        Ad.objects.create(
            user=self.user,
            title="Old Book",
            description="Very old",
            category="Books",
            condition="used",
        )

        self.url = reverse("ad_search")

    def test_login_required(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)  # Редирект на логин

    def test_search_no_filters_returns_all_ads_paginated(self):
        self.client.login(username="testuser", password="pass1234")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        # Поскольку пагинация 1 объявление на страницу, первая страница должна вернуть 1 объявление
        self.assertIn("page_obj", response.context)
        self.assertEqual(len(response.context["page_obj"]), 3)
        # Объявления упорядочены по created_at? В твоём коде нет сортировки, но можно проверить что результат есть

    def test_search_query_filter(self):
        self.client.login(username="testuser", password="pass1234")
        response = self.client.get(self.url, {"q": "iphone"})
        self.assertEqual(response.status_code, 200)
        ads = response.context["page_obj"].object_list
        self.assertTrue(
            all("iphone" in ad.title.lower() or "iphone" in ad.description.lower() for ad in ads)
        )

    def test_search_category_filter(self):
        self.client.login(username="testuser", password="pass1234")
        response = self.client.get(self.url, {"category": "electronics"})
        self.assertEqual(response.status_code, 200)
        ads = response.context["page_obj"].object_list
        self.assertTrue(all(ad.category.lower() == "electronics" for ad in ads))

    def test_search_condition_filter(self):
        self.client.login(username="testuser", password="pass1234")
        response = self.client.get(self.url, {"condition": "used"})
        self.assertEqual(response.status_code, 200)
        ads = response.context["page_obj"].object_list
        self.assertTrue(all(ad.condition.lower() == "used" for ad in ads))

    def test_combined_filters(self):
        self.client.login(username="testuser", password="pass1234")
        response = self.client.get(
            self.url, {"q": "tv", "category": "electronics", "condition": "used"}
        )
        self.assertEqual(response.status_code, 200)
        ads = response.context["page_obj"].object_list
        self.assertTrue(
            all(
                ("tv" in ad.title.lower() or "tv" in ad.description.lower())
                and ad.category.lower() == "electronics"
                and ad.condition.lower() == "used"
                for ad in ads
            )
        )

    def test_pagination(self):
        self.client.login(username="testuser", password="pass1234")
        # Запросим вторую страницу
        response = self.client.get(self.url, {"page": 2})
        self.assertEqual(response.status_code, 200)
        self.assertIn("page_obj", response.context)


class ProposalsToMeViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_receiver = User.objects.create_user(username="receiver", password="testpass")
        self.user_sender1 = User.objects.create_user(username="sender1", password="testpass")
        self.user_sender2 = User.objects.create_user(username="sender2", password="testpass")

        self.ad_receiver = Ad.objects.create(title="Receiver Ad", user=self.user_receiver)
        self.ad_sender1 = Ad.objects.create(title="Sender1 Ad", user=self.user_sender1)
        self.ad_sender2 = Ad.objects.create(title="Sender2 Ad", user=self.user_sender2)

        self.proposal1 = ExchangeProposal.objects.create(
            ad_sender=self.ad_sender1, ad_receiver=self.ad_receiver, status="pending"
        )
        self.proposal2 = ExchangeProposal.objects.create(
            ad_sender=self.ad_sender2, ad_receiver=self.ad_receiver, status="accepted"
        )

    def test_login_required(self):
        url = reverse("proposals-to-me-view")
        response = self.client.get(url)
        self.assertNotEqual(response.status_code, 200)  # должно редиректить на логин

    def test_view_without_filters(self):
        self.client.login(username="receiver", password="testpass")
        url = reverse("proposals-to-me-view")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Проверяем, что в контексте есть оба предложения
        proposals = response.context["proposals"]
        self.assertEqual(set(proposals), {self.proposal1, self.proposal2})

    def test_filter_by_status(self):
        self.client.login(username="receiver", password="testpass")
        url = reverse("proposals-to-me-view")
        response = self.client.get(url, {"status": "pending"})
        self.assertEqual(response.status_code, 200)
        proposals = response.context["proposals"]
        self.assertEqual(list(proposals), [self.proposal1])  # только с pending

    def test_filter_by_sender(self):
        self.client.login(username="receiver", password="testpass")
        url = reverse("proposals-to-me-view")
        response = self.client.get(url, {"sender": self.user_sender1.id})
        self.assertEqual(response.status_code, 200)
        proposals = response.context["proposals"]
        self.assertEqual(list(proposals), [self.proposal1])  # только от sender1

    def test_context_senders(self):
        self.client.login(username="receiver", password="testpass")
        url = reverse("proposals-to-me-view")
        response = self.client.get(url)
        senders = response.context["senders"]
        sender_ids = {s["ad_sender__user__id"] for s in senders}
        self.assertIn(self.user_sender1.id, sender_ids)
        self.assertIn(self.user_sender2.id, sender_ids)


class ProposalCreateViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_sender = User.objects.create_user(username="sender", password="testpass")
        self.user_receiver = User.objects.create_user(username="receiver", password="testpass")

        self.ad_receiver = Ad.objects.create(title="Receiver Ad", user=self.user_receiver)
        self.ad_sender1 = Ad.objects.create(title="Sender1 Ad", user=self.user_sender)
        self.ad_sender2 = Ad.objects.create(title="Sender2 Ad", user=self.user_sender)

    def test_login_required(self):
        url = reverse("proposal_create-view") + f"?ad_receiver={self.ad_receiver.pk}"
        response = self.client.get(url)
        self.assertNotEqual(response.status_code, 200)

    def test_get_request_renders_form(self):
        self.client.login(username="sender", password="testpass")
        url = reverse("proposal_create-view") + f"?ad_receiver={self.ad_receiver.pk}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("ad_receiver", response.context)
        self.assertIn("user_ads", response.context)
        # user_ads не должен содержать ad_receiver
        self.assertNotIn(self.ad_receiver, response.context["user_ads"])

    def test_post_creates_proposal(self):
        self.client.login(username="sender", password="testpass")
        url = reverse("proposal_create-view") + f"?ad_receiver={self.ad_receiver.pk}"

        data = {
            "ad_sender": self.ad_sender1.pk,
            "comment": "Test comment",
        }
        response = self.client.post(url, data)
        # Должен быть редирект после успешного создания
        self.assertEqual(response.status_code, 302)

        proposal = ExchangeProposal.objects.filter(
            ad_sender=self.ad_sender1, ad_receiver=self.ad_receiver
        ).first()
        self.assertIsNotNone(proposal)
        self.assertEqual(proposal.comment, "Test comment")
        self.assertEqual(proposal.status, "pending")

        # Проверка сообщения
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("успешно создано" in str(m) for m in messages))

    def test_post_with_invalid_sender(self):
        self.client.login(username="sender", password="testpass")
        url = reverse("proposal_create-view") + f"?ad_receiver={self.ad_receiver.pk}"

        # Попытка отправить чужое объявление (receiver - не sender)
        data = {
            "ad_sender": self.ad_receiver.pk,  # это объявление другого пользователя
            "comment": "Test comment",
        }
        response = self.client.post(url, data)
        # Ожидаем 404, т.к. get_object_or_404 вызовет исключение
        self.assertEqual(response.status_code, 404)


class ProposalCreateAPIViewTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_sender = User.objects.create_user(username="sender", password="testpass")
        self.user_receiver = User.objects.create_user(username="receiver", password="testpass")

        self.ad_receiver = Ad.objects.create(title="Receiver Ad", user=self.user_receiver)
        self.ad_sender = Ad.objects.create(title="Sender Ad", user=self.user_sender)

        self.url = reverse("proposals-create")  # Название твоего роута

    def test_authentication_required(self):
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_proposal_success(self):
        self.client.force_authenticate(user=self.user_sender)
        data = {
            "ad_sender": self.ad_sender.pk,
            "ad_receiver": self.ad_receiver.pk,
            "comment": "Test comment",
            "status": "pending",  # если поле статус нужно в сериализаторе
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ExchangeProposal.objects.count(), 1)
        proposal = ExchangeProposal.objects.first()
        self.assertEqual(proposal.comment, "Test comment")
        self.assertEqual(proposal.ad_sender, self.ad_sender)
        self.assertEqual(proposal.ad_receiver, self.ad_receiver)

    def test_create_proposal_invalid_data(self):
        self.client.force_authenticate(user=self.user_sender)
        data = {
            "ad_sender": 999,  # несуществующий id
            "ad_receiver": self.ad_receiver.pk,
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ProposalsToMeListViewTests(APITestCase):
    def setUp(self):
        self.client = APIClient()

        # Создаем пользователей
        self.user1 = User.objects.create_user(username="user1", password="pass1234")
        self.user2 = User.objects.create_user(username="user2", password="pass1234")

        # Создаем объявления для пользователей
        self.ad_receiver1 = Ad.objects.create(user=self.user1, title="Receiver Ad 1")
        self.ad_receiver2 = Ad.objects.create(user=self.user2, title="Receiver Ad 2")
        self.ad_sender = Ad.objects.create(user=self.user2, title="Sender Ad")

        # Создаем предложения обмена для user1 и user2
        self.proposal1 = ExchangeProposal.objects.create(
            ad_receiver=self.ad_receiver1,
            ad_sender=self.ad_sender,
            status="pending",
        )
        self.proposal2 = ExchangeProposal.objects.create(
            ad_receiver=self.ad_receiver2,
            ad_sender=self.ad_sender,
            status="accepted",
        )

        self.url = reverse("proposals-to-me")

    def test_authentication_required(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)  # или 401, см. выше

    def test_list_proposals_to_authenticated_user(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Должен получить только proposal1, потому что оно к user1
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.proposal1.id)

    def test_filter_by_status(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.url, {"status": "pending"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["status"], "pending")

        response = self.client.get(self.url, {"status": "accepted"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)  # Потому что accepted - не к user1

    def test_filter_by_ad_sender(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.url, {"ad_sender": self.ad_sender.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)


class ProposalsFromMeListViewTests(APITestCase):
    def setUp(self):
        self.client = APIClient()

        # Создаем пользователей
        self.user1 = User.objects.create_user(username="user1", password="pass1234")
        self.user2 = User.objects.create_user(username="user2", password="pass1234")

        # Создаем объявления для пользователей
        self.ad_sender1 = Ad.objects.create(user=self.user1, title="Sender Ad 1")
        self.ad_sender2 = Ad.objects.create(user=self.user2, title="Sender Ad 2")
        self.ad_receiver = Ad.objects.create(user=self.user2, title="Receiver Ad")

        # Создаем предложения обмена
        self.proposal1 = ExchangeProposal.objects.create(
            ad_sender=self.ad_sender1,
            ad_receiver=self.ad_receiver,
            status="pending",
        )
        self.proposal2 = ExchangeProposal.objects.create(
            ad_sender=self.ad_sender2,
            ad_receiver=self.ad_receiver,
            status="accepted",
        )

        self.url = reverse("proposals-from-me")

    def test_authentication_required(self):
        response = self.client.get(self.url)
        self.assertEqual(
            response.status_code, status.HTTP_403_FORBIDDEN
        )  # Или 401, зависит от настроек

    def test_list_proposals_from_authenticated_user(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Должен получить только proposal1, где он sender
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.proposal1.id)

    def test_filter_by_status(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.url, {"status": "pending"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["status"], "pending")

        response = self.client.get(self.url, {"status": "accepted"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)  # Потому что accepted - не к user1

    def test_filter_by_ad_receiver(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.url, {"ad_receiver": self.ad_receiver.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)


class ProposalStatusUpdateViewTests(APITestCase):
    def setUp(self):
        self.client = APIClient()

        self.sender = User.objects.create_user(username="sender", password="pass1234")
        self.receiver = User.objects.create_user(username="receiver", password="pass1234")
        self.other_user = User.objects.create_user(username="other", password="pass1234")

        self.ad_sender = Ad.objects.create(user=self.sender, title="Ad Sender")
        self.ad_receiver = Ad.objects.create(user=self.receiver, title="Ad Receiver")

        self.proposal = ExchangeProposal.objects.create(
            ad_sender=self.ad_sender,
            ad_receiver=self.ad_receiver,
            status="pending",
        )

        self.url = reverse("proposal-status-update", kwargs={"pk": self.proposal.pk})

    def test_authentication_required(self):
        response = self.client.patch(self.url, {"status": "accepted"})
        self.assertEqual(
            response.status_code, status.HTTP_403_FORBIDDEN
        )  # Или 401, зависит от настроек

    def test_receiver_can_update_status(self):
        self.client.force_authenticate(user=self.receiver)
        response = self.client.patch(self.url, {"status": "accepted"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.proposal.refresh_from_db()
        self.assertEqual(self.proposal.status, "accepted")

    def test_sender_cannot_update_status(self):
        self.client.force_authenticate(user=self.sender)
        response = self.client.patch(self.url, {"status": "accepted"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_other_user_cannot_update_status(self):
        self.client.force_authenticate(user=self.other_user)
        response = self.client.patch(self.url, {"status": "accepted"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_partial_update_only_status(self):
        self.client.force_authenticate(user=self.receiver)
        response = self.client.patch(self.url, {"status": "rejected"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.proposal.refresh_from_db()
        self.assertEqual(self.proposal.status, "rejected")
