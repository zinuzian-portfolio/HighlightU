from django.shortcuts import render
from django.http import *
from django.contrib import auth
from django.shortcuts import redirect
from .forms import RequestForm

# 썸네일 이미지를 얻기 위해 추가 
import requests
import json

def index(request):
    return render(request,'home/index.html')

def goHome(request):
    return HttpResponseRedirect('/home/')

def logout(request):
    auth.logout(request)
    return HttpResponseRedirect('/')


def dashboard(request):
    return render(request, 'mypage/dashboard.html')


def history(request):
    return render(request, 'mypage/history.html')

def social_login(request):
    return render(request, 'user_management/social_login.html')


def videoRequest(request):
    if request.method == 'POST': # 폼이 제출되었을 경우...
        form = RequestForm(request.POST) # 폼은 POST 데이터에 바인드됨
        if form.is_valid(): # 모든 유효성 검증 규칙을 통과
            # form.cleaned_data에 있는 데이터를 처리
            url = form.cleaned_data['url']
            return render(request, 'mypage/dashboard.html',{'url':url}) # Redirect after POST
    else:
        form = RequestForm() # An unbound form

    return render_to_response('dashboard.html', {
        'url': "https://www.twitch.tv/videos/402913218",
    })

def getVideoId(url):
    VideoId = url.split("/")[-1]
    return VideoId

def getThumb(videoId):

    # API요청을 보내기 위한 헤더
    TWITCH_CLIENT_ID = "37v97169hnj8kaoq8fs3hzz8v6jezdj"
    TWITCH_CLIENT_ID_HEADER = "Client-ID"
    TWITCH_V5_ACCEPT = "application/vnd.twitchtv.v5+json"
    TWITCH_V5_ACCEPT_HEADER = "Accept"
    TWITCH_AUTHORIZATION_HEADER = "Authorization"
    
    VIDEO_URL = "https://api.twitch.tv/kraken/videos/" + videoId

    headers = {TWITCH_CLIENT_ID_HEADER : TWITCH_CLIENT_ID, TWITCH_V5_ACCEPT_HEADER: TWITCH_V5_ACCEPT }

    # API 요청을 보낸다.
    video_request = requests.get(VIDEO_URL, headers=headers)
    video_request_json = video_request.json()

    # 썸네일 템플릿 url 획득
    thumb_template_url = str(video_request_json['preview']['template'])

    # 1920x1080크기의 썸네일 이미지를 얻는다.
    size = {'width':'1920', 'height': '1080'}

    return thumb_template_url.format(**size)




    