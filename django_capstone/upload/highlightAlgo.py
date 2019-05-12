from dashboard.models import MergedVideo
from django.core.files import File
from .face_detection import face_detection
from .chatAnalyze import ChatAnalyze
from .video_util import *
from django.conf import settings
import subprocess
import os
import re
from .video_util import cropVideo


class Error(Exception):
    pass


class AlgorithmError(Error):

    def __init__(self, expression, message):
        self.expression = expression
        self.message = message


def getTwitchChat(videoID, savePath):

    chatLogPath = os.path.join(savePath, videoID + ".txt")
    if os.path.isfile(chatLogPath):
        print("Chatlog already exists ! ")
        return chatLogPath

    # getTwitchChat("406987059","/home/moyak/") 이런식으로 사용
    #
    # tcd 를 사용하기 위해 셋팅이 필요
    #
    # python 3.7 이상으로 tcd를 설치(이전 버전에서는 동작하지 않음)
    # git clone https://github.com/PetterKraabol/Twitch-Chat-Downloader
    # cd Twtich-Chat-Downloader
    # python3 setup.py build
    # sudo python3 setup.py install
    #
    # chat log를 원하는 포멧으로 저장하기 위해 설정 수정
    #
    # ~/.config/tcd/setting.json
    # 파일에서
    # "capstone": {
    #    "comments": {
    #       "format": "{timestamp[relative]} {message[body]}",
    #       "ignore_new_messages": false,
    #       "timestamp": {
    #           "relative": "%X"
    #        }
    #   },
    #   "output": {
    #       "format": "{id}.txt",
    #       "timestamp": {
    #           "absolute": "%x"
    #       }
    #   }
    # },
    #
    # 추가.

    ############################# for Windows #############################
    #if savePath[-1] != '\\':
    #    savePath = savePath + '\\'
    #
    #proc = ["tcd",
    #        "-v", videoID,
    #        "--output", savePath,
    #        "--format", "capstone",
    #        ]
    ############################# for Windows #############################


    ############################# for Linux #############################
    if savePath[-1] != '/':
        savePath = savePath + '/'
    proc = ["sudo", "tcd",
            "-v", videoID,
            "--output", savePath,
            "--format", "capstone",
            ]
    ############################# for Linux #############################
    try:
        subprocess.check_call(proc)
        print("twitch chat download finish!")
        print("this file downloaded in ", savePath)

        return chatLogPath

    except subprocess.CalledProcessError as e:
        print("Twitch chat download failed: ", e)
        return None

    return None


def makeCandidatesByChatlog(chatlog, numOfHighlights):

    cummulative_sec = 5

    labeldwords = ['pog', 'poggers', 'pogchamp', 'holy', 'shit', 'wow', 'ez', 'clip', 'nice',
                   'omg', 'wut', 'gee', 'god', 'dirty', 'way', 'moly', 'wtf', 'fuck', 'crazy', 'omfg', 'kappa', 'trihard', '4head', 'cmonbruh', 'lul', 'haha', 'sourpls', 'feelsbadman', 'feelsgoodman', 'gachigasm',  'monkas', 'pepehands', 'destructroid', 'jebaited'
                   ]

    f = open(chatlog, 'rt', encoding='UTF8')

    # Download nltk
    chat_analyzer = ChatAnalyze(f, labeldwords)
    score = chat_analyzer.Preprocessing()
    result = chat_analyzer.Scoring(score)
    sectioned_result = chat_analyzer.Sectioned_Scoring(result, cummulative_sec)
    sorted_list = sorted(sectioned_result.items(),
                         key=lambda t: t[1], reverse=True)[:numOfHighlights]
    print(sorted_list)
    sorted_list = dict(sorted([(second(t), v) for t, v in sorted_list]))
    print(sorted_list)

    return sorted_list


def makeCandidatesByEmotion(videopath, original_candidate, x, y, w, h, numOfHighlights):
    cand = face_detection(videopath, original_candidate, x, y, w, h)
    return cand


def second(timestamp):
    arr = re.split("[:]", timestamp)
    if len(arr) != 3:
        print("check time string :"+timestamp)
    else:
        return int(arr[0])*3600 + int(arr[1])*60 + int(arr[2])
    return -1


def getTimeSection(candidates, videoLen, delay):
    # make raw candidate list (must be sorted by key)
    candidates = list(candidates.keys())

    # if picked points are too close
    deleteList = []
    for i in range(len(candidates) - 1):
        if i in deleteList:
            continue
        else:
            j = 1
            while i+j < len(candidates) and candidates[i+j] - candidates[i] < delay:
                deleteList.append(i + j)
                j += 1

    print(deleteList)
    print(candidates)

    for i in deleteList:
        candidates[i] = -1

    candidates = [[i-delay, i+delay] for i in candidates if i != -1]

    # post-processing
    for i in range(len(candidates)):
        if candidates[i][0] < 0:
            candidates[i][0] = 0
        if candidates[i][1] > videoLen:
            candidates[i][1] = videoLen

    return candidates


def makeHighlight(highlight_request, user_instance, video_object):

    numOfHighlights = 10
    multiplier = 4
    #
    # Chat Download
    #
    chat_save_path = os.path.join(settings.MEDIA_ROOT, highlight_request.path)
    print("The downloaded chat will be stored at --> " + chat_save_path)
    chatlog = getTwitchChat(str(video_object.videoNumber), chat_save_path)

    # If TCD fails, there will be no highlight
    if chatlog is None:
        print("Fail to create chatlog !!!")
        raise AlgorithmError

    #
    # Make Highlights
    #
    if video_object.face == True:



        temp_cand = makeCandidatesByChatlog(chatlog=chatlog, numOfHighlights=numOfHighlights*multiplier)
        # TODO videopath should be input
        cand = makeCandidatesByEmotion(original_candidate=temp_cand, numOfHighlights=numOfHighlights )

        # Get video path and resized frame info
        videopath = video_object.videoFileURL
        x = video_object.rect_x
        y = video_object.rect_y
        width = video_object.rect_width
        height = video_object.rect_.height



    else:

        cand = makeCandidatesByChatlog(chatlog=chatlog, numOfHighlights=numOfHighlights)

    video_length = get_video_length(clip=highlight_request.videoFile.path)

    sections = getTimeSection(
        candidates=cand, videoLen=video_length, delay=int(video_object.delay))

    print(sections)

    highlights = split_video(video_path=highlight_request.videoFile.path,
                             save_path=highlight_request.path,
                             video_id=video_object.videoNumber,
                             split_times=sections)


    #
    # Register them on DB
    #
    for highlight in highlights:
        with open(highlight, 'rb') as file:
            highlight_obj = MergedVideo.objects.create(
                owner=user_instance,
                videoNumber=video_object.videoNumber,
                date=video_object.date,
                path=highlight_request.path,
                video=None,
            )

            # Link DB and files
            highlight_obj.video.save(highlight_request.title + ".mp4", File(file))