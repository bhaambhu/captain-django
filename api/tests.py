from django.conf.urls import url
from django.urls import reverse
from knowledge.models import Topic
from django.contrib.auth.models import User
from rest_framework.test import APIClient, APITestCase


class TopicTests(APITestCase):

    def test_post_update(self):
        client = APIClient()

        self.testuser1 = User.objects.create_user(
            username='test_user1', password='123456789')
        self.testuser2 = User.objects.create_user(
            username='test_user1', password='123456789')

        client.login(username=self.testuser2.username, password='123456789')

        url = reverse(('api:detailcreate'), kwargs={'pk': 7})

        response = client.put(
            url, {
                "id": 7,
                "title": "Updated via tests",
                "about": "The OG Subject",
                "author": 1,
                "status": "published",
                "explanation": ""
            }, format='json')

        print(response.data)
