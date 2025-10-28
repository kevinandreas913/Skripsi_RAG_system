"""
URL configuration for andreasproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from mywebsite.views import *
from django.conf.urls import include
from django.contrib.auth.views import LoginView
from mywebsite.views import clear_cache_view

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', landingpage, name='landingpage'),
    path('clearcache/', clear_cache_view, name='clear_cache'),
    path('dashboard/', dashboard, name='dashboard'),
    path('deletecoloumnapi/', deletecoloumnapi, name='deletecoloumnapi'),
    path('docpython', docpython, name='docpython'),
    path('docphp', docphp, name='docphp'),
    path('docjs', docjs, name='docjs'),
    path('forgotpassword/', forgotpassword, name='forgotpassword'),
    path('formnewdatasave/', formnewdatasave, name='formnewdatasave'),
    path('kritiksaran/', kritiksaran, name='kritiksaran'),
    path('login/', login, name='login'),
    path('logout/', logout, name='logout'),
    path('pageinfo/', pageinfo, name='pageinfo'),
    path('pagesetting/', pagesetting, name='pagesetting'),
    path('proseschat/', proseschat, name='proseschat'),
    path('replacepassword', replacepassword, name='replacepassword'),
    path('signup/', signup, name='signup'),
    path('tableapiuser/', tableapiuser, name='tableapiuser'),
    path('tryapi/', tryapi, name='tryapi'),
    path('viewdataapi/', viewdataapi, name='viewdataapi'),

    path('loginsuperuser/', loginsuperuser, name='loginsuperuser'),
    path('dashboardsuperuser/', dashboardsuperuser, name='dashboardsuperuser'),
    path('usermanagement/', usermanagement, name='usermanagement'),
    path('deletebysuperuser/', deletebysuperuser, name='deletebysuperuser'),
    path('usermanagemessage/', usermanagemessage, name='usermanagemessage'),
    path('resetpasswordsuperuser', resetpasswordsuperuser, name='resetpasswordsuperuser')
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


