# isi:
1. [Untuk memulai Django silahkan masukkan](#1-untuk-memulai-django-silahkan-masukkan)
2. [Membuat env local di Django](#2-membuat-env-local-di-django)
3. [Membuat template](#3-membuat-template)
4. [Koneksi template](#4-koneksi-template)
5. [Setting URL](#5-setting-url)
6. [Untuk run server](#6-untuk-run-server)
7. [CSS/JS/Image](#7-cssjsimage)
8. [Database](#8-database)
9. [Untuk clear cache](#9-untuk-clear-cache)
10. [Untuk authenticated](#10-untuk-authenticated) -- penjelasan cara kerja silahkan masuk ke catatancoding.txt
11. [Cara menggunakan JsonResponse pada views.py](#11-cara-menggunakan-jsonresponse-pada-viewspy)
12. [Pagination (mengatur halaman)](#12-pagination-mengatur-halaman) -- penjelasan cara kerja silahkan masuk ke catatancoding.txt
13. [Cek versi dalam lingkungan virtual](#13-cek-versi-dalam-lingkungan-virtual)
14. [Membuat dan menggunakan requirements.txt](#14-membuat-dan-menggunakan-requirementstxt)
15. [Menggunakan shell python](#15-menggunakan-shell-python)
16. [Database save gambar dan file](#16-database-save-gambar-dan-file)
17. [OTP Email](#17-otp-email) -- penjelasan cara kerja silahkan masuk ke catatancoding.txt
18. [queue django-q](#18-queue-django)

---

## 1. untuk memulai django silahkan masukkan 
- ```"pip install Django"```
- ```"django-admin startproject ..... (nama file kamu)``` " contoh: ```django-admin startproject pemograman```
- ```"python manage.py startapp mywebsite"```

---

## 2. membuat env local di django
(buat secara promp)
- ```"python -m venv venv"```
- ```"venv\Scripts\activate"```
- silahkan lakukan pip yang diinginkan contoh ```"pip install django"```

(buat dengan vscode)
- Buka Command Palette dengan menekan Ctrl+Shift+P.
- Ketik dan pilih Python: Select Interpreter.
- ".venv\Scripts\activate"
- silahkan lakukan pip yang diinginkan contoh "pip install django"

(cara uninstall virtual env)  
```"Remove-Item -Recurse -Force .\venv\"```

---

## 3. membuat template
- buat folder baru secara manual (diluar mysite dan mywebsite) untuk menyimpan template
- pada settings.py ubah bagian templates dan installed apps
```
INSTALLED_APPS = [
    .....

    'mywebsite',
]
```
```
TEMPLATES = [
    {
        'BACKEND': ....,
        'DIRS': ['template'],
        'APP_DIRS': ....,
        'OPTIONS': {
            'context_processors': [
                ....
            ],
        },
    },
]
```

---

## 4. koneksi template
- buat folder baru secara manual di dalam mywebsite berupa "templates" untuk menyimpan isi dalam template html 
- pada setting.py ubah bagian templates 
```
TEMPLATES = [
    {
        'BACKEND': ...,
        'DIRS': ['template', 'mywebsite/templates'],
        'APP_DIRS': ...,
        'OPTIONS': {
            'context_processors': [
                ...,
            ],
        },
    },
]
```

---

## 5. setting url 
- masuk ke urls.py untuk setting url dan tambahkan alamat url 
```
urlpatterns = [
    path('', landingpage),
]
```

- setelah setting urls.py kita juga setting views.py

```
# Create your views here.
def landingpage(request):
    return render(request, 'landingpage.html')
```

- masuk ke 'mywebsite/templates' kemudian buat file 'landingpage.html'

isi html tersebut

---

## 6. untuk run server
- ```python manage.py runserver```

---

## 7. css/js/image
- masuk ke setting.py tambahkan staticfiles dan static_url ini digunakan untuk css, js, image, dll. (buat pada palng bawah)
```
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

STATIC_URL = '/static/'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]
```

- buat folder baru secara manual (diluar mysite dan mywebsite) untuk menyimpan static, dengan nama "static". di dalam folder berisikan "css", "js", dan "images" yang dibuat secara manual.
- buat contoh pada style.css yang akan kita setting backgorund collor. Setelah itu masuk kembali ke base.html dan edit bagian head dengan tambahkan link rel tersebut. Ingat juga tambahkan ```{% load static %}``` di bagian paling awal agar bisa akses css tersebut.
penulisan link pada django sebagai berikut:

```
<link rel="stylesheet" href="{% static 'landingpage/css/all.min.css' %}" />
data-image-src="{% static 'landingpage/img/bg-01.jpg' %}"
src="{% static 'landingpage/js/jquery.min.js' %}"
```

- anda juga bisa masukkan link js atau css langsung melalui base.html

---

## 8. database
- masuk ke setting.py 
- ubah bagian database {}

```
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'django',
        'USER': 'root',
        'PASSWORD': '',
        'HOST':'localhost',
        'PORT':'3306',
    }
}
```
- masukkan perintah ```"pip install mysqlclient"```
- masukkan perintah ```"python manage.py migrate"```

---

## 9. untuk clear cache
- masuk ke views.py dan tambahkan
```
from django.core.cache import cache
def clear_cache_view(request):
    cache.clear()  # Membersihkan semua data cache
    return HttpResponse("Cache cleared!")
```
- masuk ke urls.py dan tambahkan  
```
from mywebsite.views import clear_cache_view
urlpatterns = [
    path('clearcache/', clear_cache_view, name='clear_cache'),
]
```
- pengguna bisa masuk ke halaman ```".../clearcache"``` untuk clear cache 

---

## 10. untuk authenticated 
- masuk ke settings.py lalu tambahkan teks di baris paling akhir:
```
AUTH_USER_MODEL = 'mywebsite.TbUser'
LOGIN_URL = '/login/'
```
- masukkan perintah ```"python manage.py migrate"```
- ketik perintah ```"python manage.py createsuperuser"```
- pengguna akan disuruh masukkan username, email, dan password
```
username = admin
email = emailkamu@gmail.com
password = andreas123
```
- pengguna membuat form halaman untuk register, login.
- pada urls.py pengguna membuat rute login
```
path('login/', login, name='login'),
```
- pengguna membuat tabel database untuk data user login pada models.py
```
import uuid
from django.contrib.auth.models import make_password
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
class UserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError('The Username field must be set')
        user = self.model(username=username, **extra_fields)
        user.set_password(password)  # Hash password
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if not extra_fields.get('is_staff'):
            raise ValueError('Superuser must have is_staff=True.')
        if not extra_fields.get('is_superuser'):
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(username, password, **extra_fields)

class TbUser(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=255)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.password.startswith('pbkdf2'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)
        
    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.username
```
- pengguna membuat views.py 
```
from django.contrib.auth import authenticate, login as django_login, logout as django_logout
from django.contrib.auth.decorators import login_required
def login(request):
    if request.method == 'POST':
        username = request.POST.get('username', None)
        password = request.POST.get('password', None)

        user = authenticate(request, username=username, password=password)
        if user:
            django_login(request, user)
            request.session['user_id'] = str(user.id)
            request.session['username'] = user.username
            return JsonResponse({
                'status': 'success',
                'message': "Berhasil login!",
                'user': {
                    'username': user.username,
                }
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': "Username atau password salah!"
            })

    return render(request, 'login.html')
```
- jalankan ```"python manage.py makemigration"```
- jalankan ```"python manage.py migrate"```
- untuk authenticated halaman lain pengguna dapat memberikan ```@login_required``` pada awal setiap views.py yang dirasa perlu untuk ditambahkan authenticate
```
@login_required
def dashboard(request):
    session_data = session_data_login(request)
    
    return render(request, 'dashboard/index.html', session_data)
```

penyebab error library
- biasanya karna menggunakan versi terlalu baru, coba sesuaikan dengan versi anaconda caranya
 - buka anaconda promp lalu ketikkan perintah, contoh 
 ```conda list numpy```
 - setelah lihat versionnya kemudian masuk ke terminal dan lakukan ubah dengan cara 
 ```pip install numpy==1.24.3```
- cara cek versi yang telah di download di terminal dengan cara  
```python --version```  
```pip freeze```

---

## 11. cara menggunakan JsonResponse pada views.py
- masuk ke views.py 
contoh:
```
def newcoloumn(request):
    if request.method == 'POST':
        coloumn_name = request.POST.get('namakolom', None)
        type_column = request.POST.get('tipekolom', None)

        kolom = TbAdditional(user_id=request.user, name_column=coloumn_name, type_column=type_column)
        kolom.save()
        if kolom.pk:
            return JsonResponse({
                'status':'success',
                'message': f"Berhasil menambahkan kolom {coloumn_name}!"
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': "Nama kolom harus diisi!"
            })
```

---

## 12. pagination mengatur halaman
- masuk ke views.py dan masuk ke def yang ingin diberikan Pagignation
```
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
def newcoloumn(request):
    kolom_data = TbAdditional.objects.filter(user_id=request.user)
    halaman = Paginator(kolom_data, 1)

    page_number = request.GET.get('page',1)
    try:
        data = halaman.page(page_number)
    except PageNotAnInteger:
        data = halaman.page(1)
    except EmptyPage:
        data = halaman.page(halaman.num_pages)
    context = {
        'kolom_data': data,
    }

    return render(request, 'kolom/index.html', context)
```

- kemudian masuk ke halaman html yang ingin diberikan pageination kemudian ketik:
```
    {% if kolom_data.has_other_pages %}
        <div class="card-footer clearfix">
            <ul class="pagination justify-content-center">
                {% if kolom_data.has_previous %}
                    <li class="page-item"><a class="page-link" href="?page={{ kolom_data.previous_page_number }}">«</a></li>
                {% else %}
                    <li class="page-item disabled"><span class="page-link">«</span></li>
                {% endif %}

                {% if kolom_data.number|add:'-4' > 1 %}
                    <li class="page-item"><a class="page-link" href="?page={{ kolom_data.number|add:'-5' }}">&hellip;</a></li>
                {% endif %}
                
                {% for i in kolom_data.paginator.page_range %}
                    {% if kolom_data.number == i %}
                        <li class="page-item active"><span class="page-link">{{ i }} <span class="sr-only">(current)</span></span></li>
                    {% elif i > kolom_data.number|add:'-5' and i < kolom_data.number|add:'5' %}
                        <li class="page-item"><a class="page-link" href="?page={{ i }}">{{ i }}</a></li>
                    {% elif i > kolom_data.number and i <= kolom_data.number|add:'4' %} 
                        <li class="page-item"><a class="page-link" href="?page={{ i }}">{{ i }}</a></li>
                    {% endif %}
                {% endfor %}
                {% if kolom_data.paginator.num_pages > kolom_data.number|add:'4' %}
                    <li class="page-item disabled"><a class="page-link" href="?page={{ kolom_data.number|add:'5' }}">&hellip;</a></li>
                {% endif %}
                {% if kolom_data.has_next %}
                    <li class="page-item"><a class="page-link" href="?page={{ kolom_data.next_page_number }}">»</a></li>
                {% else %}
                    <li class="page-item disabled"><span class="page-link">»</span></li>
                {% endif %}
            </ul>
        </div>
    {% endif %}
```

---

## 13. cek versi dalam lingkungan virtual
```"pip list"```

---

## 14. membuat dan menggunakan requiments.txt
- aktivasi terlebih dahulu lingkungan virutal (cara di point 2)
- lakukan pip untuk masukkan library seperti biasanya
- buat pip freeze untuk memasukkan semua library yang sudah digunakan ke dalam requirements.txt ```"pip freeze > requirements.txt"```
- jika sebelumnya sudah ada pip libary maka pustaka sudah ada di dalam file ```"requerements.txt"``` yang sudah dibuat ini
- untuk menggunakan di kemudian hari, pengguna cukup mengetikkan ```"pip install -r requirements.txt"```

---

## 15. menggunakan shell python --shell untuk mencoba hal baru
- ketik ```"python manage.py shell"```
- coba paste yang diinginkan misalnya coba dengan
```
from keras.models import load_model

model_path = 'mywebsite/processing/finalized_model_kanker_otak.h5'
print("Memuat model di Django shell...")
model = load_model(model_path)
print("Model berhasil dimuat!")
```

coba cek versi tensor dan keras di anaconda kemudian latih ulang dan sesuaikan versi tersebut dengan versi yang ada di django

---

## 16. database save gambar dan file
- masuk ke models.py dan buat tabel yang berisi gambar, contoh:
```
class TbUser(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=255)
    gmail = models.CharField(max_length=255, unique=True)
    profile = models.FileField(upload_to='profile_images/', blank=False)  
    date_joined = models.DateTimeField(auto_now_add=True)
    email_otp = models.CharField(max_length=6, null=True, blank=True)
```

- masuk ke settings.py lalu tambahkan ini di baris paling bawah
```
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
```

- untuk penggunaan di views.py cukup gunakan seperti biasanya, contoh:  
```photo = request.FILES.get('filephoto')```  
```name = request.POST.get('name')```

---

## 17. otp email  
- ketikkan perintah ```pip install django-otp pyotp```

- masuk ke setting.py lalu tambahkan
```
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'masukkanemailkamu@disini'
EMAIL_HOST_PASSWORD = 'dapatkan kode security google'
```

- masuk models.py lalu buat tabel seperti contoh:
```
class TbUser(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    gmail = models.CharField(max_length=255, unique=True)
    email_otp = models.CharField(max_length=6, null=True, blank=True)
```

- buat file 'utils.py' (sejajar dengan views.py, models.py, dll) dan masukkan code berikut
```
import pyotp
from datetime import datetime, timedelta

def generate_otp():
    totp = pyotp.TOTP(pyotp.random_base32(), interval=300)  # 5 minutes validasi
    return totp.now()

def verify_otp(otp, user_otp):
    return otp == user_otp
```

- masuk ke views.py dan lakukan sebagai berikut untuk generate otp:
```
from .utils import generate_otp, verify_otp


user = TbUser.objects.get(gmail=email)
email_otp = generate_otp()

user.email_otp = email_otp
user.save()
```

- masuk ke views.py dan buat fungsi untuk mengecek otp:
```
from .utils import generate_otp, verify_otp


if verify_otp(email_otp, user.email_otp):
    user.email_otp = None
    user.save()
```

---

## 18. queue django
- Install library ```pip install django-q redis```, jika django-q tidak berfungsi maka dapat diganti ke ```pip uninstall django-q``` dan ```pip install django-q2```.
- Apabila tidak ingin install redis manual maka anda dapat menggunakan docker (untuk docker redis dapat dilihat di **.md** yang tela dibuat).
- Masuk ke ```setting.py```, tambahkan di baris paling akhir
```
Q_CLUSTER = {
    "name": "qcluster",
    "workers": 4,
    "recycle": 500,
    "timeout": 300,
    "queue_limit": 50,
    "bulk": 10,
    "broker_class": "django_q.brokers.redis_broker.Redis",
    "retry": 120,
    "ack_failures": True,
    "catch_up": False,
    "redis": {
        "host": "localhost",
        "port": 6379,
        "db": 0,
    }
}
```
tambahkan juga di ```manage.py``` pada bagian INSTALLED_APPS
```
INSTALLED_APPS = [
    ...
    "django_q",
]
```

- Buat file ```task.py``` yang berlokasi/sejajar dengan ```views.py```/```models.py```/dll.
- Isi file ```taks.py``` contoh:
```
from django_q.tasks import async_task

def contoh_task(x, y):
    return x + y
```

- Lakukan perintah dari ```views.py```
```
from django_q.tasks import async_task

# kirim task ke queue
async_task("{mywebsite}.tasks.contoh_task", 5, 7)
```

- Jalankan migrasi dengan ```python manage.py migrate```
- Buka terminal yang sudah terkoneksi dengan **.env** atau enviroment django, lalu masukkan perintah ```python manage.py qcluster```
- Jalankan server anda dengan perintah ```python manage.py runserver```


---
catatan khusus 
- pemanggilan error dari form kemudian masuk ke views.py kemudian masuk ke forms.py kemudian dikembalikan ke views.py kemudian dikembalikan ke form bagian js

