import json

from django.db.models import F
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET

from chats.forms import *


@csrf_exempt
@require_POST
def create_chat(request):
    form = NewChatForm(json.loads(request.body))
    if form.is_valid():
        form.save()
        
        return JsonResponse({
            'msg': 'Чат создан',
        })
    else:
        return JsonResponse({'errors': form.errors}, status=400)


@csrf_exempt
@require_POST
def send_message(request):
    form = SendMessageForm(json.loads(request.body))
    if form.is_valid():
        form.save()
        return JsonResponse({
            'msg': 'Сообщение отправлено'
        })
    else:
        return JsonResponse({'errors': form.errors}, status=400)


@csrf_exempt
@require_GET
def chat_list(request):
    chats = list(Chat.objects.all().values('name', 'tag'))
    count = len(chats)
    iterator = 0
    while iterator < count:
        try:
            Member.objects.get(chat=Chat.objects.get(tag=chats[iterator]['tag']),
                               user=User.objects.get(id=request.GET.get('id')))
        except Member.DoesNotExist:
            chats.pop(iterator)
            count -= 1
            continue
        curr_messages = Message.objects.filter(chat__tag=chats[iterator]['tag'])
        chats[iterator]['indicator'] = len(curr_messages)
        if len(curr_messages) > 0:
            last_mess = curr_messages[0]
            chats[iterator]['lastType'] = last_mess.type
            chats[iterator]['lastMessage'] = last_mess.content or last_mess.url
            chats[iterator]['lastTime'] = last_mess.time.strftime('%H:%M')
        else:
            chats[iterator]['lastType'] = ''
            chats[iterator]['lastMessage'] = ''
            chats[iterator]['lastTime'] = ''
        iterator += 1
    return JsonResponse({'chats': chats})


@csrf_exempt
@require_GET
def one_chat(request):
    try:
        chat = Chat.objects.get(tag=request.GET.get('tag'))
    except Chat.DoesNotExist:
        return HttpResponse('Chat does not exist')
    messages = Message.objects.annotate(whose=F('user__id')).filter(chat=chat).values('id',
                                                                                      'content',
                                                                                      'time',
                                                                                      'type',
                                                                                      'whose')
    for i in range(len(messages)):
        messages[i]['time'] = messages[i]['time'].strftime('%H:%M')
        if messages[i]['type'] != 'text':
            messages[i]['url'] = Message.objects.get(id=messages[i]['id']).url
    return JsonResponse({'messages': list(messages)})


@csrf_exempt
@require_GET
def chat_detail(request):
    chat = Chat.objects.annotate(whose=F('author__id'), channel=F('is_channel')). \
        filter(tag=request.GET.get('tag')). \
        values('whose', 'channel')
    return JsonResponse({'chat': list(chat)})
