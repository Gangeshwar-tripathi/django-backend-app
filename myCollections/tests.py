from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status


class UserAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpassword'
        }
        self.user = User.objects.create_user(**self.user_data)
        self.client.force_authenticate(user=self.user)

    def test_create_user(self):
        response = self.client.post('/create/', data=self.user_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 1)

        self.user_data = {
            "username": "dhsvjf",
            "password": "Dtanurag12@",
            "email": "jsdjf@gmail.com",
            "first_name": "dfdg",
            "last_name": "cxvcv"

        }

        response = self.client.post('/create/', data=self.user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 2)

        # Assuming there's already one user from setUp
        response = self.client.post('/create/', data=self.user_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 2)


    def test_list_users(self):
        response = self.client.get('/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), User.objects.count())

    def test_delete_user(self):
        response = self.client.delete(f'/delete/user/{self.user.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(id=self.user.id).exists())
