from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from unittest.mock import patch
from .models import TbChat, TbAPI
import json

User = get_user_model()


# ===============================
# PUBLIC ACCESS TEST
# ===============================
class PublicAccessTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_landing_page_status(self):
        print("\n[TEST] test_landing_page_status")
        response = self.client.get(reverse('landingpage'))
        print("Expected HTTP Status: 200")
        print("Actual HTTP Status:", response.status_code)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'landingpage.html')
        print("Status: PASSED")

    def test_kritik_saran_get(self):
        print("\n[TEST] test_kritik_saran_get")
        response = self.client.get(reverse('kritiksaran'))
        print("Expected HTTP Status: 200")
        print("Actual HTTP Status:", response.status_code)

        self.assertEqual(response.status_code, 200)
        print("Status: PASSED")

    def test_kritik_saran_post_success(self):
        data = {
            'name': 'Tester',
            'phone': '08123456789',
            'gmail': 'test@gmail.com',
            'questions': 'Ini testing'
        }

        print("\n[TEST] test_kritik_saran_post_success")
        print("Input data pengguna:", data)

        response = self.client.post(reverse('kritiksaran'), data)
        print("Expected status: success")
        print("Actual status:", response.json()['status'])

        self.assertEqual(response.json()['status'], 'success')
        self.assertTrue(TbChat.objects.filter(name='Tester').exists())
        print("Status: PASSED")

    def test_kritik_saran_post_empty_field(self):
        data = {
            'name': '',
            'phone': '123',
            'gmail': 'a@a.com',
            'questions': 'q'
        }

        print("\n[TEST] test_kritik_saran_post_empty_field")
        print("Input data pengguna:", data)

        response = self.client.post(reverse('kritiksaran'), data)

        print("Expected status: error")
        print("Actual status:", response.json()['status'])
        print("Message:", response.json()['message'])

        self.assertEqual(response.json()['status'], 'error')
        print("Status: PASSED")


# ===============================
# AUTHENTICATION TEST
# ===============================
class AuthTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.photo = SimpleUploadedFile(
            "avatar.jpg", b"file_content", content_type="image/jpeg"
        )

    def test_signup_success(self):
        data = {
            'username': 'newuser',
            'password': 'password123',
            'gmail': 'new@gmail.com',
            'filephoto': self.photo
        }

        print("\n[TEST] test_signup_success")
        print("Input data signup:", data)

        response = self.client.post(reverse('signup'), data)

        print("Expected status: success")
        print("Actual status:", response.json()['status'])

        self.assertEqual(response.json()['status'], 'success')
        self.assertTrue(User.objects.filter(username='newuser').exists())
        print("Status: PASSED")

    def test_login_success(self):
        User.objects.create_user(
            username='loginuser',
            password='password123',
            gmail='l@l.com'
        )

        data = {'username': 'loginuser', 'password': 'password123'}

        print("\n[TEST] test_login_success")
        print("Input login:", data)

        response = self.client.post(reverse('login'), data)

        print("Expected status: success")
        print("Actual status:", response.json()['status'])
        print("Session username:", self.client.session.get('username'))

        self.assertEqual(response.json()['status'], 'success')
        self.assertEqual(self.client.session['username'], 'loginuser')
        print("Status: PASSED")

class FormNewDataSaveTest(TestCase):
    def setUp(self):
        self.client = Client()

        # buat user login
        self.user = User.objects.create_user(
            username='tester',
            password='123456',
            gmail='tester@test.com',
            profile='x.jpg'
        )
        self.client.force_login(self.user)

        # dummy pdf
        self.file = SimpleUploadedFile(
            "test.pdf",
            b"%PDF-1.4 dummy content",
            content_type="application/pdf"
        )

    @patch('mywebsite.views.async_task')
    def test_formnewdatasave_success(self, mock_async):
        data = {
            'title': 'Dokumen Test',
            'note': 'Catatan',
            'language': 'id',
            'toxic': 'no',
            'file': self.file
        }

        response = self.client.post(
            reverse('formnewdatasave'),
            data
        )

        # RESPONSE CHECK
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')

        # DATABASE CHECK
        self.assertTrue(
            TbAPI.objects.filter(title='Dokumen Test').exists()
        )

        api = TbAPI.objects.get(title='Dokumen Test')

        # API KEY TERGENERATE
        self.assertIsNotNone(api.api_key)
        self.assertGreater(len(api.api_key), 20)

        # ASYNC TASK DIPANGGIL (TAPI TIDAK DIEKSEKUSI)
        mock_async.assert_called_once()

        print("[PASSED] test_formnewdatasave_success")


# ===============================
# SUPERUSER / ADMIN TEST
# ===============================
class SuperUserTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.superuser = User.objects.create_superuser(
            username='admin', password='123', gmail='admin@a.com'
        )
        self.normaluser = User.objects.create_user(
            username='warga', password='123', gmail='warga@w.com'
        )

    def test_login_superuser_check(self):
        print("\n[TEST] test_login_superuser_check")

        response = self.client.post(reverse('loginsuperuser'), {
            'username': 'warga', 'password': '123'
        })
        self.assertEqual(response.json()['status'], 'error')

        response = self.client.post(reverse('loginsuperuser'), {
            'username': 'admin', 'password': '123'
        })
        self.assertEqual(response.json()['status'], 'success')

        print("Status: PASSED")

    def test_dashboard_superuser_access(self):
        print("\n[TEST] test_dashboard_superuser_access")

        self.client.force_login(self.normaluser)
        response = self.client.get(reverse('dashboardsuperuser'))
        self.assertRedirects(response, reverse('dashboard'))

        self.client.force_login(self.superuser)
        session = self.client.session
        session['user_id'] = str(self.superuser.id)
        session.save()

        response = self.client.get(reverse('dashboardsuperuser'))
        self.assertEqual(response.status_code, 200)

        print("Status: PASSED")

    @patch('mywebsite.views.send_mail')
    def test_usermanagemessage_reply(self, mock_mail):
        print("\n[TEST] test_usermanagemessage_reply")

        self.client.force_login(self.superuser)
        session = self.client.session
        session['user_id'] = str(self.superuser.id)
        session.save()

        chat = TbChat.objects.create(
            name='U', gmail='u@u.com', questions='Q', status='no'
        )

        response = self.client.post(reverse('usermanagemessage'), {
            'type': 'tambahfeedback',
            'id': chat.id,
            'name': chat.name,
            'questions': chat.questions,
            'gmail': chat.gmail,
            'feedback': 'Terima kasih'
        })

        self.assertEqual(response.json()['status'], 'success')
        chat.refresh_from_db()
        self.assertEqual(chat.status, 'finish')
        mock_mail.assert_called_once()

        print("Status: PASSED")