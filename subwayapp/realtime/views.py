from django.shortcuts import render
import phoenixdb
import phoenixdb.cursor
from operator import itemgetter
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import urllib.request
from urllib.parse import quote
from datetime import *
from dateutil.parser import parse


# hbase & phoenix table connect
database_url = 'http://192.168.56.100:8765/'

# Create your views here.
def realtime(request):
    conn = phoenixdb.connect(database_url, autocommit=True)
    cursor = conn.cursor()

    # 호선별 색상
    query = "select LINE_NUM, COLOR from LC"
    cursor.execute(query)
    rows = cursor.fetchall()
    json_data_color = {}

    for i in rows:
        json_data_color[i[0]] = i[1]

    # 전체 역명 가져오기
    query2 = "select SUB_STA_NM from DIRECTION"
    cursor.execute(query2)
    rows2 = cursor.fetchall()
    json_data_substanm = {}
    json_data_substanm['전체역'] = []

    for i in rows2:
        json_data_substanm['전체역'].append(i[0])

    return render(request,'realtime/realtime.html', {
                                                    'json_data_color': json_data_color,
                                                    'json_data_substanm': json_data_substanm
                                                     })


# 역명 선택시
@csrf_exempt
def selectsubwayAjax_realtime_selectSubstanm(request):
    # ajax
    if request.method == 'POST':

        subway_name = request.POST['name']
        conn = phoenixdb.connect(database_url, autocommit=True)
        cursor = conn.cursor()

        # 선택한 역명의 도착지 방면 리스트
        query = "select DIRECTION_VAL from DIRECTION where SUB_STA_NM = '" + subway_name + "'"
        cursor.execute(query)
        rows = cursor.fetchall()
        direction_list = {}
        direction_list['list'] = rows[0][0].split(',')

        return JsonResponse(direction_list)

# 선택한 역명의 도착지 방면 클릭 시
@csrf_exempt
def selectsubwayAjax_realtime_selectAll(request):
    # ajax
    if request.method == 'POST':

        subway_name = request.POST['name']
        direction_val = request.POST['direction_val']

        select = subway_name
        substanm = quote(select)

        # api 키 호출
        url = "http://swopenAPI.seoul.go.kr/api/subway/537868565164696433344d52436f69/json/realtimeStationArrival/0/50/" + substanm
        response=urllib.request.urlopen(url)
        json_str=response.read().decode("utf8")
        json_object=json.loads(json_str)

        json_val = json_object['realtimeArrivalList']
        result_val = {}

        # 역명 구분 호출 결과 중 표현할 값 추출
        for i in range(0, len(json_val)):

            result_val[json_val[i]['btrainNo']] = {}
            result_val[json_val[i]['btrainNo']]['trainLineNm'] = json_val[i]['trainLineNm']
            result_val[json_val[i]['btrainNo']]['updnLine'] = json_val[i]['updnLine']
            result_val[json_val[i]['btrainNo']]['subwayHeading'] = json_val[i]['subwayHeading']
            result_val[json_val[i]['btrainNo']]['btrainSttus'] = json_val[i]['btrainSttus']
            result_val[json_val[i]['btrainNo']]['barvlDt'] = json_val[i]['barvlDt']
            result_val[json_val[i]['btrainNo']]['arvlMsg3'] = json_val[i]['arvlMsg3']
            result_val[json_val[i]['btrainNo']]['arvlCd'] = json_val[i]['arvlCd']
            result_val[json_val[i]['btrainNo']]['recptnDt'] = json_val[i]['recptnDt'].split(' ')[1]

        # 최종 표현을 위한 가공
        json_data_result = {}

        # 도착지 방면을 인자로 해당 결과를 추가
        for i in result_val:
            if direction_val in result_val[i]['trainLineNm']:
                json_data_result[i] = {}
                json_data_result[i] = result_val[i]
            else:
                pass

        # 해당 결과가 없을 시 바로 넘김
        if len(json_data_result) == 0:
            pass

        # 해당 결과 존재 시 가공 후 넘김
        else:
            # 결과가 1건이라면 sort 없이 바로 넘김
            if len(json_data_result) == 1:
                pass

            # 결과가 2건 이상이라면 sort 후 넘김
            else:
                # 해당 결과의 개수를 2건으로 맞춤 / 도착 예정 시간이 가장 빠른 순, 이번 열차, 다음 열차
                # 후 프론트에서 도착 예정 시간 정수형(barvlDt2)를 기준으로 이번열차와 다음 열차를 구분하여 표현 
                json_list = []

                for i in json_data_result:
                    json_list.append([i, json_data_result[i]])

                reset_list = sorted(json_list, key=(lambda x: int(x[1]['barvlDt'])))

                while True:
                    if len(reset_list) == 2:
                        break
                    else:
                        reset_list.pop()
            
                sort_json = {}

                for i in reset_list:
                    sort_json[i[0]] = i[1]

                json_data_result = sort_json

            # 도착지 방면 문자열에 (급행)이 있으면 같은 방면이라도 다르게 추출되어 결합 후 btrainSttus값을 변경(일반 / 급행)
            for i in json_data_result:

                if '(급행)' in json_data_result[i]['trainLineNm']:
                    json_data_result[i]['trainLineNm'] = json_data_result[i]['trainLineNm'].split(' (')[0]
    
                else:
                    if json_data_result[i]['btrainSttus'] == None:
                        json_data_result[i]['btrainSttus'] = '일반'
                    else:
                        pass

                # arvlCd 코드에 따라 현재 상태 변경
                if json_data_result[i]['arvlCd'] == '0':
                    json_data_result[i]['arvlCd'] = '진입'
        
                elif json_data_result[i]['arvlCd'] == '1':
                    json_data_result[i]['arvlCd'] = '도착'
        
                elif json_data_result[i]['arvlCd'] == '2':
                    json_data_result[i]['arvlCd'] = '출발'
        
                elif json_data_result[i]['arvlCd'] == '3':
                    json_data_result[i]['arvlCd'] = '전역출발'
        
                elif json_data_result[i]['arvlCd'] == '4':
                    json_data_result[i]['arvlCd'] = '전역진입'
        
                elif json_data_result[i]['arvlCd'] == '5':
                    json_data_result[i]['arvlCd'] = '전역도착'
    
                elif json_data_result[i]['arvlCd'] == '99':
                    json_data_result[i]['arvlCd'] = '운행중'
    
                else:
                    pass

            # api 키 호출 값 중 예상 도착 시간(barvlDt)에서 현재 시간 - 실제 데이터 발생시간을 빼주어 차이를 줄이기 위함
            for i in json_data_result:

                if json_data_result[i]['barvlDt'] == '0':
                    json_data_result[i]['barvlDt2'] = 0
                    json_data_result[i]['barvlDt'] = '-'
                    json_data_result[i]['recptnDt'] = json_data_result[i]['recptnDt'].split(':')
                    json_data_result[i]['recptnDt'] = json_data_result[i]['recptnDt'][0] + '시 ' + json_data_result[i]['recptnDt'][1] + '분 ' + str(round(float(json_data_result[i]['recptnDt'][2]))) + '초'

                else:
                    json_data_result[i]['barvlDt2'] = int(json_data_result[i]['barvlDt'])
                    json_data_result[i]['barvlDt'] = int(json_data_result[i]['barvlDt']) - (datetime.now() - parse(json_data_result[i]['recptnDt'])).seconds
                    m, s = divmod(json_data_result[i]['barvlDt'], 60)
    
                    json_data_result[i]['recptnDt'] = json_data_result[i]['recptnDt'].split(':')
                    json_data_result[i]['recptnDt'] = json_data_result[i]['recptnDt'][0] + '시 ' + json_data_result[i]['recptnDt'][1] + '분 ' + str(round(float(json_data_result[i]['recptnDt'][2]))) + '초'
    
                    if m == 0:
                        json_data_result[i]['barvlDt'] = str(s) + '초 후 도착 예정'
            
                    else:
                        json_data_result[i]['barvlDt'] = str(m) + '분 ' + str(s) + '초 후 도착 예정'
                        
        return JsonResponse(json_data_result)
