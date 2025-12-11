from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock
from .models import TbUser, TbChat, TbAPI
import json
import os

User = get_user_model()

class PublicAccessTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_landing_page_status(self):
        response = self.client.get(reverse('landingpage'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'landingpage.html')

    def test_kritik_saran_get(self):
        response = self.client.get(reverse('kritiksaran'))
        self.assertEqual(response.status_code, 200)

    def test_kritik_saran_post_success(self):
        data = {
            'name': 'Tester',
            'phone': '08123456789',
            'gmail': 'test@gmail.com',
            'questions': 'Ini testing'
        }
        response = self.client.post(reverse('kritiksaran'), data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')
        self.assertTrue(TbChat.objects.filter(name='Tester').exists())

    def test_kritik_saran_post_empty_field(self):
        data = {'name': '', 'phone': '123', 'gmail': 'a@a.com', 'questions': 'q'}
        response = self.client.post(reverse('kritiksaran'), data)
        self.assertEqual(response.json()['status'], 'error')
        self.assertEqual(response.json()['message'], 'Semua field wajib diisi!')

class AuthTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.photo = SimpleUploadedFile("avatar.jpg", b"file_content", content_type="image/jpeg")

    def test_signup_success(self):
        data = {
            'username': 'newuser',
            'password': 'password123',
            'gmail': 'new@gmail.com',
            'filephoto': self.photo
        }
        response = self.client.post(reverse('signup'), data)
        self.assertEqual(response.json()['status'], 'success')
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_signup_duplicate_username(self):
        # PERBAIKAN: Tambahkan gmail agar tidak IntegrityError
        User.objects.create_user(username='exist', password='123', gmail='e@e.com')
        
        data = {'username': 'exist', 'password': '123', 'gmail': 'other@e.com'}
        response = self.client.post(reverse('signup'), data)
        self.assertEqual(response.json()['status'], 'error')
        self.assertIn('sudah digunakan', response.json()['message'])

    def test_login_success(self):
        User.objects.create_user(username='loginuser', password='password123', gmail='l@l.com')
        data = {'username': 'loginuser', 'password': 'password123'}
        response = self.client.post(reverse('login'), data)
        
        self.assertEqual(response.json()['status'], 'success')
        self.assertEqual(self.client.session['username'], 'loginuser')

    def test_login_fail(self):
        # PERBAIKAN: Tambahkan gmail unik
        User.objects.create_user(username='loginfail', password='password123', gmail='fail@l.com')
        data = {'username': 'loginfail', 'password': 'wrongpassword'}
        response = self.client.post(reverse('login'), data)
        self.assertEqual(response.json()['status'], 'error')

    @patch('mywebsite.views.send_mail')
    def test_forgot_password_send_otp(self, mock_mail):
        # PERBAIKAN: Pastikan user dibuat dengan benar
        user = User.objects.create_user(username='forgot', password='123', gmail='forgot@test.com')
        
        data = {'email': 'forgot@test.com'}
        response = self.client.post(reverse('forgotpassword'), data)
        
        user.refresh_from_db()
        self.assertEqual(response.json()['status'], 'success')
        self.assertTrue(user.email_otp) # Cek OTP terisi
        mock_mail.assert_called_once() 

    def test_replace_password_logic(self):
        user = User.objects.create_user(username='replace', password='old', gmail='r@r.com')
        user.email_otp = '123456'
        user.save()

        # Case: Password pendek
        response = self.client.post(reverse('replacepassword'), {
            'email': 'r@r.com', 'otp': '123456', 'password': 'short'
        })
        self.assertEqual(response.json()['status'], 'error')

        # Case: Sukses
        response = self.client.post(reverse('replacepassword'), {
            'email': 'r@r.com', 'otp': '123456', 'password': 'newlongpassword'
        })
        self.assertEqual(response.json()['status'], 'success')

class DataManagementTest(TestCase):
    def setUp(self):
        self.client = Client()
        # PERBAIKAN: Tambahkan gmail unik
        self.user = User.objects.create_user(username='apiuser', password='123', gmail='api@test.com')
        self.client.force_login(self.user)
        self.file = SimpleUploadedFile("doc.pdf", b"dummy content", content_type="application/pdf")
        
        # PERBAIKAN KRUSIAL: Setup Session Manual
        # View Anda bergantung pada session['user_id'], bukan hanya request.user
        session = self.client.session
        session['user_id'] = str(self.user.id)
        session['username'] = self.user.username
        session['gmail'] = self.user.gmail
        session['profile'] = None
        session.save()

    @patch('mywebsite.views.async_task')
    def test_form_new_data_save(self, mock_async):
        data = {
            'title': 'Test PDF',
            'file': self.file,
            'note': 'Test Note',
            'language': 'id',
            'toxic': 'no'
        }
        response = self.client.post(reverse('formnewdatasave'), data)
        
        # Debugging jika masih error
        if response.json()['status'] == 'error':
            print("Form Error Message:", response.json().get('message'))

        self.assertEqual(response.json()['status'], 'success')
        self.assertTrue(TbAPI.objects.filter(title='Test PDF').exists())
        mock_async.assert_called_once()

    @patch('os.remove')
    @patch('mywebsite.views.delete_qdrant_data') # Sesuaikan path views Anda
    def test_delete_column_api(self, mock_qdrant_del, mock_os_remove):
        api_obj = TbAPI.objects.create(
            user=self.user, 
            title="To Delete", 
            file=self.file, 
            language='en', 
            toxic='no',
            api_key='unique-key-123' # Pastikan field unique terisi jika ada
        )
        
        with patch('os.path.exists', return_value=True):
            response = self.client.post(reverse('deletecoloumnapi'), {'id': api_obj.id})
            
            # Debugging
            if response.status_code != 200:
                print("Delete Error:", response.content)

            self.assertEqual(response.json()['status'], 'success')
            self.assertFalse(TbAPI.objects.filter(id=api_obj.id).exists())
            mock_qdrant_del.assert_called_once()

class ChatProcessTest(TestCase):
    def setUp(self):
        self.client = Client()
        # PERBAIKAN: Tambahkan gmail unik
        self.user = User.objects.create_user(username='chatuser', password='123', gmail='chat@test.com')
        self.client.force_login(self.user)
        self.api_obj = TbAPI.objects.create(
            user=self.user, title="Doc", file="x.pdf", language="id", toxic="yes", api_key="test-api-key"
        )

    @patch('mywebsite.views.MarianMTModel')
    @patch('mywebsite.views.MarianTokenizer')
    @patch('mywebsite.views.mainhatespeechdetection')
    @patch('mywebsite.views.qdrant_answer')
    def test_proses_chat_toxic_detected(self, mock_qdrant, mock_hate, mock_tok, mock_model):
        mock_hate.return_value = (1, "Ini kata kasar")
        
        mock_tok_instance = MagicMock()
        mock_tok.from_pretrained.return_value = mock_tok_instance
        mock_tok_instance.decode.return_value = "Translated text"
        
        payload = {
            'api_key': self.api_obj.api_key,
            'message': 'Kata kasar'
        }
        
        response = self.client.post(
            reverse('proseschat'), 
            json.dumps(payload), 
            content_type="application/json"
        )
        
        self.assertEqual(response.json()['status'], 'success')
        self.assertEqual(response.json()['message'], "1")
        mock_qdrant.assert_not_called()

    @patch('mywebsite.views.qdrant_answer')
    def test_proses_chat_normal(self, mock_qdrant):
        self.api_obj.toxic = "no" 
        self.api_obj.save()
        
        mock_qdrant.return_value = ("Jawaban AI", "Kutipan Dokumen", "TopK Data")
        
        payload = {
            'api_key': self.api_obj.api_key,
            'message': 'Apa isi dokumen?'
        }
        
        response = self.client.post(
            reverse('proseschat'), 
            json.dumps(payload), 
            content_type="application/json"
        )
        
        self.assertEqual(response.json()['status'], 'success')
        self.assertEqual(response.json()['message'], "Jawaban AI")
        mock_qdrant.assert_called_once()

class SuperUserTest(TestCase):
    def setUp(self):
        self.client = Client()
        # PERBAIKAN: Gmail unik untuk superuser dan normal user
        self.superuser = User.objects.create_superuser(username='admin', password='123', gmail='admin@a.com')
        self.normaluser = User.objects.create_user(username='warga', password='123', gmail='warga@w.com')
        
        # Setup Session untuk superuser (jika diperlukan oleh view)
        session = self.client.session
        session['user_id'] = str(self.superuser.id)
        session.save()

    def test_login_superuser_check(self):
        # Case Login User Biasa (Error)
        response = self.client.post(reverse('loginsuperuser'), {
            'username': 'warga', 'password': '123'
        })
        self.assertEqual(response.json()['status'], 'error')

        # Case Login Admin (Sukses)
        response = self.client.post(reverse('loginsuperuser'), {
            'username': 'admin', 'password': '123'
        })
        self.assertEqual(response.json()['status'], 'success')

    def test_dashboard_superuser_access(self):
        # Login user biasa
        self.client.force_login(self.normaluser)
        response = self.client.get(reverse('dashboardsuperuser'))
        self.assertRedirects(response, reverse('dashboard'))
        
        # Login superuser
        self.client.force_login(self.superuser)
        # Refresh session for superuser
        session = self.client.session
        session['user_id'] = str(self.superuser.id)
        session['username'] = self.superuser.username
        session['gmail'] = self.superuser.gmail
        session['profile'] = None
        session.save()

        response = self.client.get(reverse('dashboardsuperuser'))
        self.assertEqual(response.status_code, 200)

    @patch('mywebsite.views.send_mail')
    def test_usermanagemessage_reply(self, mock_mail):
        self.client.force_login(self.superuser)
        # Pastikan session ada
        session = self.client.session
        session['user_id'] = str(self.superuser.id)
        session.save()

        chat = TbChat.objects.create(name='U', gmail='u@u.com', questions='Q', status='no')
        
        data = {
            'type': 'tambahfeedback',
            'id': chat.id,
            'name': chat.name,
            'questions': chat.questions,
            'gmail': chat.gmail,
            'feedback': 'Terima kasih'
        }
        
        response = self.client.post(reverse('usermanagemessage'), data)
        self.assertEqual(response.json()['status'], 'success')
        
        chat.refresh_from_db()
        self.assertEqual(chat.status, 'finish')
        mock_mail.assert_called_once()