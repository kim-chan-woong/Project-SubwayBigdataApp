from django.shortcuts import render
import phoenixdb
import phoenixdb.cursor
from operator import itemgetter
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# hbase & phoenix table connect
database_url = 'http://192.168.56.100:8765/'

# Create your views here.
def index(request):
    return render(request,'batch/index.html')

# 배치 페이지의 메인
# 전체 통계
def all(request):
    
    conn = phoenixdb.connect(database_url, autocommit=True)
    cursor = conn.cursor()
    query = "select * from ARA"
    cursor.execute(query)
    rows = cursor.fetchall()

    # 가공 결과 json 구조 예시
    # {
    #     'ride': '',
    #     'alight': ''
    # }
    json_data = {}

    json_data['ride'] = format(rows[0][1], ',d')
    json_data['alight'] = format(rows[0][2], ',d')

    return render(request,'batch/all.html', {
                                            'json_data': json_data
                                            })

# 연도별 통계
def yra(request):
    
    conn = phoenixdb.connect(database_url, autocommit=True)
    cursor = conn.cursor()
    query = "select cast(to_number(YEAR) as integer) CAST_YEAR, RIDE_YEAR, ALIGHT_YEAR from YRA order by CAST_YEAR asc"
    cursor.execute(query)
    rows = cursor.fetchall()

    # 가공 결과 json 구조 예시
    # {
    #     '2015': 
    #          {'ride': '', 
    #          'alight': ''
    #          }, 
    #     '2016': {
    #         'ride': '',
    #          'alight': ''
    #          }, 
    #     '2017': {
    #         'ride': '', 
    #         'alight': ''
    #         }, 
    #         ...
    # }
    json_data = {}

    for i in rows:
        json_data[str(i[0])]={}
        json_data[str(i[0])]['ride']=format(i[1], ',d')
        json_data[str(i[0])]['alight']=format(i[2], ',d')

    return render(request,'batch/yra.html', {
                                             'json_data': json_data
                                             })

# 호선별 통계
def lra(request):

    conn = phoenixdb.connect(database_url, autocommit=True)
    cursor = conn.cursor()
    query = "select lra.rank, lra.line_num, lra.ride_line, lc.color from LRA_RIDE as lra inner join LC as lc on lra.line_num = lc.line_num where lra.rank <= 10"
    query2 = "select lra.rank, lra.line_num, lra.alight_line, lc.color from LRA_ALIGHT as lra inner join LC as lc on lra.line_num = lc.line_num where lra.rank <= 10"
    query3 = "select * from ARA"

    # ride(승차)
    cursor.execute(query)
    rows = cursor.fetchall()
    
    # alight(하차)
    cursor.execute(query2)
    rows2 = cursor.fetchall()

    # all_ride(전체 승차), all_alight(전체 하차)
    cursor.execute(query3)
    rows3 = cursor.fetchall()

    # 승, 하차, 호선별 색상 데이터
    # 가공 결과 json 구조 예시
    # {
    #     '-': {'line_num': '전체', 'ride_val or alight_val': '승차 또는 하차 기록'}, 
    #     '1위': {'line_num': '해당 호선', 'ride_val or alight_val': '승차 또는 하차 기록'}, 
    #     '2위': {'line_num': '해당 호선', 'ride_val or alight_val': '승차 또는 하차 기록'}, 
    #     ...
    #     '9위': {'line_num': '해당 호선', 'ride_val or alight_val': '승차 또는 하차 기록'}, 
    #     '10위': {'line_num': '해당 호선', 'ride_val or alight_val': '승차 또는 하차 기록'},  
    # },
    # {
    #     '2호선': 'RGB', 
    #     '1호선': 'RGB', 
    #     '9호선': 'RGB', 
    #     ...
    # }

    json_data_ride = {}
    json_data_alight = {}
    json_data_color = {}

    json_data_ride['-'] = {}
    json_data_ride['-']['line_num'] = '전체'
    json_data_ride['-']['ride_val'] = format(rows3[0][1], ',d')

    json_data_alight['-'] = {}
    json_data_alight['-']['line_num'] = '전체'
    json_data_alight['-']['alight_val'] = format(rows3[0][2], ',d')

    for i in rows:
        json_data_ride[str(i[0])+'위'] = {}
        json_data_ride[str(i[0])+'위']['line_num'] = i[1]
        json_data_ride[str(i[0])+'위']['ride_val'] = format(i[2], ',d')
        if i[1] in json_data_color:
            pass
        else:
            json_data_color[i[1]] = i[3]

    for i in rows2:
        json_data_alight[str(i[0])+'위'] = {}
        json_data_alight[str(i[0])+'위']['line_num'] = i[1]
        json_data_alight[str(i[0])+'위']['alight_val'] = format(i[2], ',d')
        if i[1] in json_data_color:
            pass
        else:
            json_data_color[i[1]] = i[3]

    json_data_color['전체'] = 'black'
    json_data_color['기타 호선합'] = 'silver'

    return render(request,'batch/lra.html', {
                                             'json_data_ride': json_data_ride,
                                             'json_data_alight': json_data_alight,
                                             'json_data_color': json_data_color
                                             })

# 역명별 통계
def nra(request):

    conn = phoenixdb.connect(database_url, autocommit=True)
    cursor = conn.cursor()
    query = "select nra.rank, nra.sub_sta_nm, nra.ride_name, lsn.line_num from NRA_RIDE as nra inner join LSN as lsn on nra.sub_sta_nm = lsn.sub_sta_nm where nra.rank <= 10"
    query2 = "select nra.rank, nra.sub_sta_nm, nra.alight_name, lsn.line_num from NRA_ALIGHT as nra inner join LSN as lsn on nra.sub_sta_nm = lsn.sub_sta_nm where nra.rank <= 10"

    # ride(승차)
    cursor.execute(query)
    rows = cursor.fetchall()

    # alight(하차)
    cursor.execute(query2)
    rows2 = cursor.fetchall()

    # 가공 결과 json 구조 예시
    # {
    #     '1위': {
    #         'sub_sta_nm': '역명', 
    #         'ride_val or alight_val': '승차 또는 하차 기록', 
    #         'line_num': ['소속 호선 또는 호선들']
    #         }, 
    #     '2위': {
    #         'sub_sta_nm': '역명', 
    #         'ride_val or alight_val': '승차 또는 하차 기록', 
    #         'line_num': ['소속 호선 또는 호선들']
    #         }
    #     ...
    # }
    # {
    #     '2호선': 'RGB', 
    #     '1호선': 'RGB', 
    #     '9호선': 'RGB', 
    #     ...
    # }

    json_data_ride = {}
    json_data_alight = {}
    choice_color = []

    for i in rows:
        json_data_ride[str(i[0])+'위'] = {}
        json_data_ride[str(i[0])+'위']['sub_sta_nm'] = i[1]
        json_data_ride[str(i[0])+'위']['ride_val'] = format(i[2], ',d')
        json_data_ride[str(i[0])+'위']['line_num'] = i[3].split(',')

        if ',' in i[3]:
            sp_line = i[3].split(',')
            for j in range(0, len(sp_line)):
                if sp_line[j] in choice_color:
                    pass
                else:
                    choice_color.append(sp_line[j])

        else:
            if i[3] in choice_color:
                pass
            else:
                choice_color.append(i[3])
        
    for i in rows2:
        json_data_alight[str(i[0])+'위'] = {}
        json_data_alight[str(i[0])+'위']['sub_sta_nm'] = i[1]
        json_data_alight[str(i[0])+'위']['alight_val'] = format(i[2], ',d')
        json_data_alight[str(i[0])+'위']['line_num'] = i[3].split(',')

        if ',' in i[3]:
            sp_line = i[3].split(',')
            for j in range(0, len(sp_line)):
                if sp_line[j] in choice_color:
                    pass
                else:
                    choice_color.append(sp_line[j])

        else:
            if i[3] in choice_color:
                pass
            else:
                choice_color.append(i[3])

                
    # 순위내 호선 색상
    select_color = "','".join(choice_color)
    query3 = "select LINE_NUM, COLOR from LC where LINE_NUM IN ('" + select_color + "')"
    cursor.execute(query3)
    rows3 = cursor.fetchall()
    json_data_color = {}

    for i in rows3:
        json_data_color[i[0]] = i[1]

    return render(request,'batch/nra.html', {
                                             'json_data_ride': json_data_ride,
                                             'json_data_alight': json_data_alight,
                                             'json_data_color': json_data_color
                                             })

# 원하는 통계
def selectsubway(request):

    conn = phoenixdb.connect(database_url, autocommit=True)
    cursor = conn.cursor()

    # 호선별 색상
    query = "select LINE_NUM, COLOR from LC"
    cursor.execute(query)
    rows = cursor.fetchall()
    json_data_color = {}

    for i in rows:
        json_data_color[i[0]] = i[1]

    # 전체 역명들
    query2 = "select sub_sta_nm from LSN"
    cursor.execute(query2)
    rows2 = cursor.fetchall()

    # 가공 결과 json 구조 예시
    # {
    #     '2호선': 'RGB', 
    #     '1호선': 'RGB', 
    #     '9호선': 'RGB', 
    #     ...
    # }
    # {
    #     '전체역': ['역명들']
    # }

    json_data_substanm = {}
    json_data_substanm['전체역'] = []

    for i in rows2:
        json_data_substanm['전체역'].append(i[0])

    return render(request,'batch/selectsubway.html', {
                                                    'json_data_color': json_data_color,
                                                    'json_data_substanm': json_data_substanm,
                                                     })

# 원하는 통계 페이지 선택 후 검색 결과
@csrf_exempt
def selectsubwayAjax_batch(request):
    # ajax
    if request.method == 'POST':

        conn = phoenixdb.connect(database_url, autocommit=True)
        cursor = conn.cursor()
        subway_name = request.POST['name']
        query =  """SELECT lsn.sub_sta_nm, lsn.line_num, nr.rank, nr.ride_name, na.rank, na.alight_name
                  FROM LSN AS lsn
                  LEFT JOIN
                  (NRA_RIDE AS nr
                  INNER JOIN NRA_ALIGHT AS na
                  ON nr.sub_sta_nm = na.sub_sta_nm)
                  ON na.sub_sta_nm = lsn.sub_sta_nm
                  where lsn.sub_sta_nm = '""" + subway_name + "'"

        cursor.execute(query)
        rows = cursor.fetchall()

        # 가공 결과 json 구조 예시
        # {
        #     'sub_sta_nm': '선택한 역명', 
        #     'line_num': ['선택한 역이 소속된 호선 또는 호선들'], 
        #     'value': {
        #         '전체': {
        #             'cnt': '전체 호선의 역 개수', 
        #             'ride_rank': '전체 역들 중 선택한 역의 승차 순위', 
        #             'ride_value': '전체 역 기준 선택한 역의 승차 기록', 
        #             'alight_rank': '전체 역들 중 선택한 역의 하차 순위', 
        #             'alight_value': '전체 역 기준 선택한 역의 하차 기록'
        #                 }, 
        #         '소속 호선': {
        #             'cnt': '선택한 역명이 소속된 호선의 역 개수', 
        #             'ride_rank': '선택한 역명이 소속된 호선 기준 승차 순위', 
        #             'ride_value': '선택한 역명이 소속된 호선 기준 승차 기록', 
        #             'alight_rank': '선택한 역명이 소속된 호선 기준 하차 순위', 
        #             'alight_value': '선택한 역명이 소속된 호선 기준 하차 기록'
        #                  }, 
        #         '소속 호선': {
        #             'cnt': '선택한 역명이 소속된 호선의 역 개수', 
        #             'ride_rank': '선택한 역명이 소속된 호선 기준 승차 순위', 
        #             'ride_value': '선택한 역명이 소속된 호선 기준 승차 기록', 
        #             'alight_rank': '선택한 역명이 소속된 호선 기준 하차 순위', 
        #             'alight_value': '선택한 역명이 소속된 호선 기준 하차 기록'
        #                 }, 
        #     }
        # }
        json_data = {}

        json_data['sub_sta_nm'] = rows[0][0]
        json_data['line_num'] = rows[0][1].split(',')
        json_data['value'] = {}
        json_data['value']['전체'] = {}
        json_data['value']['전체']['cnt'] = '519'
        json_data['value']['전체']['ride_rank'] = str(rows[0][2])
        json_data['value']['전체']['ride_value'] = format(rows[0][3], ',d') + '건'
        json_data['value']['전체']['alight_rank'] = str(rows[0][4])
        json_data['value']['전체']['alight_value'] = format(rows[0][5], ',d') + '건'

        query2 = """SELECT lct.line_num, lct.line_cnt, nrl_ride.rank, nrl_ride.ride_line_name, nrl_alight.rank, nrl_alight.alight_line_name 
                  FROM LCT as lct 
                  LEFT JOIN 
                  (NRL_RIDE as nrl_ride 
                  INNER JOIN NRL_ALIGHT as nrl_alight 
                  ON nrl_ride.line_num = nrl_alight.line_num)  
                  ON nrl_ride.line_num = lct.line_num 
                  where nrl_ride.sub_sta_nm = '""" + subway_name + "' and nrl_alight.sub_sta_nm = '" + subway_name + "'"

        cursor.execute(query2)
        rows2 = cursor.fetchall()

        for i in range(0, len(rows2)):
            json_data['value'][rows2[i][0]] = {}
            json_data['value'][rows2[i][0]]['cnt'] = str(rows2[i][1])
            json_data['value'][rows2[i][0]]['ride_rank'] = str(rows2[i][2])
            json_data['value'][rows2[i][0]]['ride_value'] = format(rows2[i][3], ',d') + '건'
            json_data['value'][rows2[i][0]]['alight_rank'] = str(rows2[i][4])
            json_data['value'][rows2[i][0]]['alight_value'] = format(rows2[i][5], ',d') + '건'

        return JsonResponse(json_data)