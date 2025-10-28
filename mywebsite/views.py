from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.core.cache import cache
from django.contrib.auth.hashers  import check_password
from django.contrib.auth import authenticate, login as django_login, logout as django_logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.db.models import Count
from django.db import transaction
from django_q.tasks import async_task

from .process.save_pdf_to_embedding_vector import proses_dan_simpan_ke_qdrant
from .process.delete_data_qdrant import *
from .process.answer_qdrant import *
from .utils import generate_otp, verify_otp

from django.conf import settings

from .forms import UserRegistrationForm
from .models import *

import logging
import os
from uuid import UUID

logger = logging.getLogger(__name__)

# Create your views here.
def landingpage(request):
    return render(request, 'landingpage.html')

def kritiksaran(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        phone = request.POST.get("phone", "").strip()
        gmail = request.POST.get("gmail", "").strip()
        questions = request.POST.get("questions", "").strip()

        if not name or not phone or not gmail or not questions:
            return JsonResponse({
                "status": "error",
                "message": "Semua field wajib diisi!"
            })

        try:
            TbChat.objects.create(
                name=name,
                phone=phone,
                gmail=gmail,
                questions=questions,
            )
            return JsonResponse({
                "status": "success",
                "message": "Feedback berhasil disimpan!"
            })
        except Exception as e:
            print("Error saat menyimpan:", e)
            return JsonResponse({
                "status": "error",
                "message": "Gagal menyimpan data!"
            })
        
    return render(request, 'kritiksaran.html')

def signup(request):
    if request.method == 'POST':
        # form = UserRegistrationForm(request.POST)
        try: 
            username = request.POST.get('username', None)
            password = request.POST.get('password', None)
            gmail = request.POST.get('gmail', None)
            photo = request.FILES.get('filephoto')

            if TbUser.objects.filter(username=username).exists():
                return JsonResponse({
                    'status': 'error',
                    'message': f'username {username} sudah digunakan, harap ganti username lain!',
                })
            
            if TbUser.objects.filter(gmail=gmail).exists():
                return JsonResponse({
                    'status': 'error',
                    'message': f'email {gmail} sudah pernah digunakan!',
                })

            user = TbUser.objects.create_user(username=username, password=password, gmail=gmail, profile=photo)
            user.save()

            user_data = {
                'username': username,
                'password': password
            }

            return JsonResponse({
                'status': 'success',
                'message': f' berhasil didaftarkan',
                'users': user_data
            })
        except Exception as e:
            print("error karena = ", e)
            
            # error = form.errors.as_json()
            username = request.POST.get('username')
            password = request.POST.get('password')

            return JsonResponse({
                'status': 'error',
                'message': f'{username} tidak berhasil didaftarkan, harap sesuaikan format!',
                'errors': str(e)
            })
        
    return render(request, 'signup.html')

def login(request):
    if request.method == 'POST':
        username = request.POST.get('username', None)
        password = request.POST.get('password', None)

        user = authenticate(request, username=username, password=password)
        if user:
            if user.is_superuser:
                return JsonResponse({
                    'status': 'error',
                    'message': "Akun tidak ditemukan dan tidak dapat login!"
                })
            
            django_login(request, user)
            request.session['user_id'] = str(user.id)
            request.session['username'] = user.username
            request.session['gmail'] = user.gmail
            request.session['profile'] = user.profile.url if user.profile else None

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

def forgotpassword(request):
    if request.method == 'POST':
        try: 
            email = request.POST.get('email', None)

            if not email:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Email wajib diisi!'
                })

            try:
                user = TbUser.objects.get(gmail=email)
            except TbUser.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Email tidak ditemukan!'
                })
            
            email_otp = generate_otp()

            user.email_otp = email_otp
            user.save()

            send_mail(
                'Email Verification OTP',
                f'Your OTP for email verification is: {email_otp}',
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=False,
            )
            
            return JsonResponse({
                'status': 'success',
                'message': 'OTP berhasil dikirim ke email Anda.'
            })
        
        except Exception as e:
            print("error karena = ", e)
            
            return JsonResponse({
                'status': 'error',
                'message': f'Terjadi kesalahan {e}.'
            })

    return render(request, 'forgotpassword.html')

def replacepassword(request):
    if request.method == 'POST':
        try:
            email = request.POST.get('email', None)
            password = request.POST.get('password', '')
            otp = request.POST.get('otp', '')
            print(otp)

            if not email:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Email wajib diisi!'
                })
            
            if not password:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Password wajib diisi!'
                })
            
            if len(password) <= 7:
                return JsonResponse({
                    "status": "error",
                    "message": "Password minimal 8 karakter!"
                })
            if len(password) >= 25:
                return JsonResponse({
                    "status": "error",
                    "message": "Password maximal 25 karakter!"
                })
            
            if not otp:
                return JsonResponse({
                    'status': 'error',
                    'message': 'OTP wajib diisi!'
                })

            try:
                user = TbUser.objects.get(gmail=email, email_otp=otp)
            except TbUser.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Harap pastikan email dan OTP anda benar!'
                })
            
            username = user.username
            user.email_otp = ''
            user.password = password
            user.save()
            
            return JsonResponse({
                'status': 'success',
                'message': f'password user {username} berhasil diubah.'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'terjadi kesalahan {e}'
            })
    else:
        return render(request, 'forgotpassword.html')

def session_data_login(request):
    if 'user_id' not in request.session:
        return None
    return {
        'user_id': request.session.get('user_id'),
        'username': request.session.get('username'),
        'gmail': request.session.get('gmail'),
        'profile': request.session.get('profile')
    }

@login_required
def dashboard(request):
    
    session_data_user = session_data_login(request)
    api_count = TbAPI.objects.filter(user_id=request.user.id).count()

    context = {**session_data_user, 
               "namepage": "Dashboard",
               "totalapi": api_count}
    
    return render(request, 'dashboard.html', context)

@login_required
def docpython(request):
    session_data_user = session_data_login(request)

    context = {**session_data_user, 
               "namepage": "Python Documentation"
               }
    
    return render(request, 'documentation/python.html', context)

@login_required
def docphp(request):
    session_data_user = session_data_login(request)

    context = {**session_data_user, 
               "namepage": "PHP Documentation"
               }
    
    return render(request, 'documentation/php.html', context)

@login_required
def docjs(request):
    session_data_user = session_data_login(request)

    context = {**session_data_user, 
               "namepage": "JavaScript Documentation"
               }
    
    return render(request, 'documentation/js.html', context)

@login_required
def tableapiuser(request):
    
    session_data_user = session_data_login(request)

    data = TbAPI.objects.filter(user_id=request.user)

    context = {**session_data_user, 
               "namepage": "Table data",
               "api_data": data}

    return render(request, 'tableapi/tabledataapiuser.html', context)

@login_required
def formnewdatasave(request):
    session_data_user = session_data_login(request)

    if request.method == 'POST':
        title = request.POST.get("title", None)
        file = request.FILES.get("file")
        note = request.POST.get("note", "")
        language = request.POST.get("language", "")
        toxic = request.POST.get("toxic", "")

        if not title or not file or not language or not toxic:
            return JsonResponse({
                "status": "error",
                "message": "Semua field wajib diisi!"
            })
        
        try:
            obj = TbAPI.objects.create(
                user= request.user,
                file = file,
                note = note,
                title = title,
                language = language,
                toxic = toxic
            )

            file_path = obj.file.path
            # user_id = str(request.user.id)
            pdf_id = str(obj.api_key)

            async_task("mywebsite.task.proses_pdf_task", file_path, pdf_id)

            # proses_dan_simpan_ke_qdrant(file_path, pdf_id)
            
            return JsonResponse({
                'status': 'success',
                'message': 'berhasil disimpan',
            })
        except Exception as e:
                print("Error saat menyimpan:", e)
                return JsonResponse({
                'status': 'error',
                'message': "Request gagal!"
            })


    context = {**session_data_user, 
               "namepage": "Form data"}

    return render(request, 'tableapi/formnewdata.html', context)

@login_required
def viewdataapi(request):
    session_data_user = session_data_login(request)

    context = {**session_data_user}

    if request.method == "POST":
        id = request.POST.get("id")
        try:
            data_api = TbAPI.objects.get(id=id)
            if data_api.language == "en":
                bahasa = "English"
            else:
                bahasa = "Indonesia"

            if data_api.toxic == "no":
                toxic = "No"
            else:
                toxic = "Yes"
                
            data = {
                "title": data_api.title,
                "note": data_api.note,
                "api_key": data_api.api_key,
                "file": data_api.file.url,
                "language": bahasa,
                "toxic": toxic
            }
            print("data dikirim:", data)
            return JsonResponse({
                "status": "success", 
                "data": data,
            })
        except Exception as e:
            print("gagal mencari data karena = ", e)
            return JsonResponse({
                'status': 'error',
                'message': "Request gagal!"
            })

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required
def deletecoloumnapi(request):
    session_data_user = session_data_login(request)

    context = {**session_data_user}

    if request.method == 'POST':
        id = request.POST.get("id")

        if id is None:
            return JsonResponse({
                'status': 'error',
                'message': 'ID kolom yang diminta tidak ditemukan!',
            })
        else:
            try: 
                obj = get_object_or_404(TbAPI, id=id)

                user_id = str(obj.user.id)
                pdf_id = str(obj.api_key)

                delete_qdrant_data(pdf_id)

                if obj.file:  # pastikan kolom 'file' ada di model TbAdditional
                    file_path = obj.file.path
                    if os.path.exists(file_path):
                        os.remove(file_path)

                nama_judul = obj.title  # mengambil nama judul
                obj.delete()
                return JsonResponse({
                    "status": "success", 
                    "message": f"data {nama_judul} berhasil dihapus!",
                })
            except Exception as e:
                print(f"error terjadi karena {e}")
                return JsonResponse({
                    "status": "error", 
                    "message": "request gagal!",
                })
        
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required
def logout(request):
    django_logout(request)
    if 'user_id' in request.session:
        del request.session['user_id']
        del request.session['username']
        
    return render(request, 'login.html')

@login_required
def tryapi(request):
    session_data_user = session_data_login(request)

    if request.method == 'POST':
        try:
            api = request.POST.get("api_key")
            data_in_api = TbAPI.objects.get(api_key=api)
            
            return JsonResponse({
                'status': 'success',
                'data': {**session_data_user,
                        'title': data_in_api.title,
                        'api_key': data_in_api.api_key,
                        "namepage": "Try API"}
            })
        
        except Exception as e:
            print("Error gagal dikarenakan = ", e)
            return JsonResponse({
                'status': 'fail',
            })
    else:
        context = {**session_data_user,
                "namepage": "Try API"}

    return render(request, 'tryapi/pagetry.html', context)

@csrf_exempt
def proseschat(request):
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            apikey = body.get('api_key', None)
            question = body.get('message', None)

            if not apikey or not question:
                return JsonResponse({
                    'status': 'fail', 
                    'message': 'API key dan message wajib diisi'
                })

            all_data_in_apikey = TbAPI.objects.get(api_key=apikey)
            bahasa = all_data_in_apikey.language

            jawaban, kutipan3, topk = qdrant_answer(pertanyaan=question, pdf_id=apikey, bahasa_pdf=bahasa)
            print("dari views, kutipan adalah, ", kutipan3)

            return JsonResponse({
                'status': 'success',
                'message': jawaban,
                'lengkap': kutipan3,
                'topk': topk
            })
        
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'fail', 
                'message': 'Format JSON tidak valid'
            })
        
        except Exception as e:
            print("Error gagal dikarenakan = ", e)
            return JsonResponse({
                'status': 'fail',
                'message': 'gagal',
            })

    # return render(request, 'tryapi/pagetry.html', {"namepage": "Try API"})
    return JsonResponse({
        'status': 'fail', 
        'message': 'Format request harus POST'
    })

@login_required
def pagesetting(request):
    if request.method == "POST":
        diupdate = request.POST.get("type")
        current_password = request.POST.get("current_password")

        user = request.user
        user_autentikasi = authenticate(request, username=user.username, password=current_password)
        if not user_autentikasi:
            return JsonResponse({
                "status": "error",
                "message": "Password yang anda inputkan salah"
            })
        
        if diupdate == "username":
            username_baru = request.POST.get("username", "").strip()

            if not username_baru:
                return JsonResponse({
                    "status": "error",
                    "message": "Username tidak boleh kosong!"
                })
            if len(username_baru) > 20:
                return JsonResponse({
                    "status": "error",
                    "message": "Username maksimal 20 karakter!"
                })

            if TbUser.objects.filter(username=username_baru).exclude(pk=user.pk).exists():
                return JsonResponse({
                "status": "error",
                "message": "Username sudah digunakan, mohon input username lain!"
                })
            
            user.username = username_baru
            user.save()

            return JsonResponse({
                "status": "success",
                "message": f"Username berhasil diubah menjadi {username_baru}"
            })
        
        elif diupdate == "gmail":
            email_baru = request.POST.get("gmail", "").strip()

            if not email_baru:
                return JsonResponse({
                    "status": "error",
                    "message": "Email tidak boleh kosong!"
                })
            if len(email_baru) > 255:
                return JsonResponse({
                    "status": "error",
                    "message": "Email maksimal 255 karakter!"
                })
            if "@" not in email_baru:
                return JsonResponse({
                    "status": "error",
                    "message": "Email harus mengandung @gmail atau @company!"
                })

            if TbUser.objects.filter(gmail=email_baru).exclude(pk=user.pk).exists():
                return JsonResponse({
                "status": "error",
                "message": "Email sudah digunakan, mohon input email lain!"
                })
            
            user.gmail = email_baru
            user.save()

            return JsonResponse({
                "status": "success",
                "message": f"Email berhasil diubah menjadi {email_baru}"
            })

        elif diupdate == "gantipassword":
            password_baru = request.POST.get("gantipassword", "").strip()

            if not password_baru:
                return JsonResponse({
                    "status": "error",
                    "message": "Password tidak boleh kosong!"
                })
            if len(password_baru) <= 7:
                return JsonResponse({
                    "status": "error",
                    "message": "Password minimal 8 karakter!"
                })
            if len(password_baru) >= 25:
                return JsonResponse({
                    "status": "error",
                    "message": "Password maximal 25 karakter!"
                })
            if check_password(password_baru, user.password):
                return JsonResponse({
                    "status": "error",
                    "message": "Password baru tidak boleh sama dengan password lama Anda."
                })
            
            user.password = password_baru
            user.save()

            return JsonResponse({
                "status": "success",
                "message": "Password berhasil ganti"
            })
        
        elif diupdate == "photo":
            photo_file = request.FILES.get("photo")

            if not photo_file:
                return JsonResponse({
                    "status": "error",
                    "message": "Harap unggah foto Anda!"
                })

            tipefile = ["image/jpeg", "image/png"]
            if photo_file.content_type not in tipefile:
                return JsonResponse({
                    "status": "error",
                    "message": "File harus berformat JPG, JPEG, atau PNG!"
                })

            max_size = 2 * 1024 * 1024
            if photo_file.size > max_size:
                return JsonResponse({
                    "status": "error",
                    "message": "Ukuran file maksimal 2 MB!"
                })
            
            foto_lama = None
            if user.profile:
                foto_lama = user.profile.path

            user.profile = photo_file
            user.save()

            if foto_lama and os.path.exists(foto_lama) and user.profile.path != foto_lama:
                os.remove(foto_lama)

            return JsonResponse({
                "status": "success", 
                "message": "Foto profil berhasil diperbarui"
            })

    session_data_user = session_data_login(request)

    context = {**session_data_user,
               "namepage": "User Setting"}
    
    return render(request, 'pagesetting.html', context)

@login_required
def pageinfo(request):
    session_data_user = session_data_login(request)

    context = {**session_data_user,
               "namepage": "User Info"}
    
    return render(request, "pageinfo.html", context)

def clear_cache_view(request):
    cache.clear()  # Membersihkan semua data cache
    return HttpResponse("Cache cleared!")

def loginsuperuser(request):
    if request.method == 'POST':
        username = request.POST.get('username', None)
        password = request.POST.get('password', None)

        user = authenticate(request, username=username, password=password)
        if user and user.is_superuser:
            django_login(request, user)
            request.session['user_id'] = str(user.id)
            request.session['username'] = user.username
            request.session['gmail'] = user.gmail
            request.session['profile'] = user.profile.url if user.profile else None

            return JsonResponse({
                'status': 'success',
                'message': "Berhasil login superuser!",
                'user': {
                    'username': user.username,
                }
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': "Hanya untuk superuser!"
            })

    return render(request, 'superuser/loginsuperuser.html')

@login_required
def dashboardsuperuser(request):
    if not request.user.is_superuser:
        return redirect('dashboard')
    
    User = get_user_model()
    session_data_user = session_data_login(request)
    totaluser = User.objects.filter(is_superuser=False).count()

    context = {**session_data_user, 
               "namepage": "Dashboard",
               "totaluser": totaluser}
    
    return render(request, 'superuser/dashboardsuperuser.html', context)

@login_required
def usermanagemessage(request):
    if not request.user.is_superuser:
        return redirect('dashboard')
    
    if request.method == "POST":
        permintaan = request.POST.get("type")

        if permintaan == "gantistatus":
            user_id = request.POST.get("id")
            user = get_object_or_404(TbChat, id=user_id)

            try:
                with transaction.atomic():

                    if user.status == "no":
                        new_status = "finish"
                    else:
                        new_status = "no"

                    user.status = new_status
                    user.save()

                return JsonResponse({
                    "status": "success", 
                    "message": "Status berhasil diganti"
                })

            except Exception as e:
                return JsonResponse({
                    "status": "error", 
                    "message": f"Gagal ganti status: {str(e)}"
                })
            
        if permintaan == "tambahfeedback":
            user_id = request.POST.get("id")
            nama = request.POST.get("name", '')
            questions = request.POST.get("questions", '')
            email = request.POST.get("gmail", None)
            feedback = request.POST.get("feedback", '')
            user = get_object_or_404(TbChat, id=user_id)

            try:
                with transaction.atomic():

                    send_mail(
                        subject='Feedback For Your Question',
                        message=f"""Hi {nama},

                    Thank you for your question:
                    "{questions}"

                    Here is our feedback for you:
                    "{feedback}"

                    Best regards,  
                    Admin
                    """,
                        from_email = settings.EMAIL_HOST_USER,
                        recipient_list = [email],
                        fail_silently=False,
                    )
                    
                    user.status = "finish"
                    user.feedback = feedback
                    user.save()

                return JsonResponse({
                    "status": "success", 
                    "message": "Feedback berhasil ditambahkan dan dikirim!"
                })

            except Exception as e:
                return JsonResponse({
                    "status": "error", 
                    "message": f"Gagal menambahkan feedback: {str(e)}"
                })
    
    session_data_user = session_data_login(request)
    data = TbChat.objects.all()

    context = {**session_data_user, 
        "namepage": "User Manage Message",
        "datauser": data
    }

    return render(request, 'superuser/usermanagemessage.html', context)

@login_required
def usermanagement(request):
    if not request.user.is_superuser:
        return redirect('dashboard')
    
    User = get_user_model()
    session_data_user = session_data_login(request)
    data = User.objects.filter(is_superuser=False).annotate(total_api=Count('tbapi'))

    context = {
        **session_data_user,
        "namepage": "User Management",
        "datauser": data
    }
    
    return render(request, 'superuser/usermanagement.html', context)

def superuserdeletfile(alamatfile):
    if alamatfile and hasattr(alamatfile, "path"):
        alamat = alamatfile.path
        if os.path.exists(alamat):
            os.remove(alamat)
            print(f"File {alamat} deleted.")

@login_required
def deletebysuperuser(request):
    if not request.user.is_superuser:
        return redirect('dashboard')
    
    User = get_user_model()

    if request.method == "POST":
        user_id = request.POST.get("id")
        user = get_object_or_404(User, id=user_id, is_superuser=False)

        try:
            with transaction.atomic():
                apis = TbAPI.objects.filter(user=user)
                for api in apis:
                    delete_qdrant_data(api.api_key)

                fileinapi = TbAPI.objects.filter(user=user)
                for obj in fileinapi:
                    superuserdeletfile(obj.file)
                fileinapi.delete()

                superuserdeletfile(user.profile)

                apis.delete()

                user.delete()

            return JsonResponse({
                "status": "success", 
                "message": "User dan semua data berhasil dihapus."
            })

        except Exception as e:
            return JsonResponse({
                "status": "error", 
                "message": f"Gagal hapus data: {str(e)}"
            })

    return JsonResponse({
        "status": "error", 
        "message": "Invalid request."
    })

@login_required
def resetpasswordsuperuser(request):
    if not request.user.is_superuser:
        return redirect('dashboard')
    
    User = get_user_model()

    if request.method == 'POST':
        user_id = request.POST.get("id")
        user = get_object_or_404(User, id=user_id, is_superuser=False)

        try:
            with transaction.atomic():
                passwordd = str(12345678)
                user.password = passwordd
                user.save()

            return JsonResponse({
                    "status": "success", 
                    "message": "Password berhasil diubah"
                })
        
        except Exception as e:
            return JsonResponse({
                "status": "error", 
                "message": f"Gagal ganti password"
            })
    
    return JsonResponse({
        "status": "error", 
        "message": "Invalid request."
    })
        
