from pyspark.sql.session import SparkSession
from pyspark.sql import *

spark = SparkSession.builder.appName('subway').getOrCreate()
path = "hdfs://NNHA/user/source_data/subway*.csv"

####################################################################
# 전체 데이터 통합 및 테이블 저장##########################################

df = spark.read.csv(path, header=True)

rdd_df = df.rdd.zipWithIndex().toDF()
rdd_df = rdd_df.withColumn('use_dt', rdd_df['_1'].getItem("use_dt"))
rdd_df = rdd_df.withColumn('line_num', rdd_df['_1'].getItem("line_num"))
rdd_df = rdd_df.withColumn('sub_sta_nm', rdd_df['_1'].getItem("sub_sta_nm"))
rdd_df = rdd_df.withColumn('ride_pasgr_num', rdd_df['_1'].getItem("ride_pasgr_num"))
rdd_df = rdd_df.withColumn('alight_pasgr_num', rdd_df['_1'].getItem("alight_pasgr_num"))
rdd_df = rdd_df.withColumn('work_dt', rdd_df['_1'].getItem("work_dt"))

df2 = rdd_df.drop("_1").withColumnRenamed("_2", "idx").select("*")

all_df = df2.selectExpr("cast(idx as int) idx", \
                          "use_dt", \
                          "line_num", \
                          "sub_sta_nm", \
                          "cast(ride_pasgr_num as int) ride_pasgr_num ", \
                          "cast(alight_pasgr_num as int) alight_pasgr_num", \
                          "work_dt")

all_df.write \
  .format("org.apache.phoenix.spark") \
  .mode("overwrite") \
  .option("table", "ALL_RESULT") \
  .option("zkUrl", "an01:2181") \
  .save()

# 연산하기 위한 테이블 객체 생성 (데이터 프레임 -> view)
pro_df = df.selectExpr("use_dt", \
                          "line_num", \
                          "sub_sta_nm", \
                          "cast(ride_pasgr_num as int) ride_pasgr_num ", \
                          "cast(alight_pasgr_num as int) alight_pasgr_num", \
                          "work_dt")

pro_df.createOrReplaceTempView("pro_df")

#####################################################################
# 전체 승하차 합계 테이블 저장#############################################

ara = spark.sql("select sum(ride_pasgr_num) as ride_all, sum(alight_pasgr_num) as alight_all from pro_df")

rdd_ara = ara.rdd.zipWithIndex().toDF()
rdd_ara = rdd_ara.withColumn('ride_all', rdd_ara['_1'].getItem("ride_all"))
rdd_ara = rdd_ara.withColumn('alight_all', rdd_ara['_1'].getItem("alight_all"))
ara_df = rdd_ara.drop("_1").withColumnRenamed("_2", "ara_idx").select("*")

ara_result = ara_df.selectExpr("cast(ara_idx as int) ara_idx", \
                                       "ride_all", \
                                       "alight_all")

ara_result.write \
  .format("org.apache.phoenix.spark") \
  .mode("overwrite") \
  .option("table", "ARA") \
  .option("zkUrl", "an01:2181") \
  .save()

#####################################################################
# 연도별 승하차 합계 테이블 저장#############################################

year_df = pro_df.withColumn('year', pro_df.use_dt[0:4])
year_df.createOrReplaceTempView("year_df")
yra = spark.sql("select year, sum(ride_pasgr_num) as ride_year, sum(alight_pasgr_num) as alight_year \
                    from year_df \
                    group by year \
                    order by ride_year desc, alight_year desc")

rdd_yra = yra.rdd.zipWithIndex().toDF()
rdd_yra = rdd_yra.withColumn('year', rdd_yra['_1'].getItem("year"))
rdd_yra = rdd_yra.withColumn('ride_year', rdd_yra['_1'].getItem("ride_year"))
rdd_yra = rdd_yra.withColumn('alight_year', rdd_yra['_1'].getItem("alight_year"))
yra_df = rdd_yra.drop("_1").withColumnRenamed("_2", "yra_idx").select("*")

yra_result = yra_df.selectExpr("cast(yra_idx as int) yra_idx", \
                                      "year", \
                                      "ride_year", \
                                      "alight_year")


yra_result.write \
  .format("org.apache.phoenix.spark") \
  .mode("overwrite") \
  .option("table", "YRA") \
  .option("zkUrl", "an01:2181") \
  .save()

#####################################################################
# 호선별 승하차 합계 테이블 따로 저장#############################################

lra_ride = spark.sql("select a.* \
                   from ( \
                          select line_num, sum(ride_pasgr_num) as ride_line, \
                          rank() over (order by sum(ride_pasgr_num) desc) ranking1, \
                          row_number() over (order by sum(ride_pasgr_num) desc) ranking2 \
                          from pro_df \
                          group by line_num) a")

rdd_lra_ride = lra_ride.rdd.zipWithIndex().toDF()
rdd_lra_ride = rdd_lra_ride.withColumn('line_num', rdd_lra_ride['_1'].getItem("line_num"))
rdd_lra_ride = rdd_lra_ride.withColumn('ride_line', rdd_lra_ride['_1'].getItem("ride_line"))
rdd_lra_ride = rdd_lra_ride.withColumn('rank', rdd_lra_ride['_1'].getItem("ranking1"))
lra_ride_df = rdd_lra_ride.drop("_1").withColumnRenamed("_2", "lra_ride_idx").select("*")

lra_ride_result = lra_ride_df.selectExpr("cast(lra_ride_idx as int) lra_ride_idx", \
                                     "line_num", \
                                     "ride_line", \
                                     "cast(rank as int) rank")

lra_ride_result.write \
  .format("org.apache.phoenix.spark") \
  .mode("overwrite") \
  .option("table", "LRA_RIDE") \
  .option("zkUrl", "an01:2181") \
  .save()

------------------------------------------------------------------------------------------------------------------------

lra_alight = spark.sql("select a.* \
                   from ( \
                          select line_num, sum(alight_pasgr_num) as alight_line, \
                          rank() over (order by sum(alight_pasgr_num) desc) ranking1, \
                          row_number() over (order by sum(alight_pasgr_num) desc) ranking2 \
                          from pro_df \
                          group by line_num) a")

rdd_lra_alight = lra_alight.rdd.zipWithIndex().toDF()
rdd_lra_alight = rdd_lra_alight.withColumn('line_num', rdd_lra_alight['_1'].getItem("line_num"))
rdd_lra_alight = rdd_lra_alight.withColumn('alight_line', rdd_lra_alight['_1'].getItem("alight_line"))
rdd_lra_alight = rdd_lra_alight.withColumn('rank', rdd_lra_alight['_1'].getItem("ranking1"))
lra_alight_df = rdd_lra_alight.drop("_1").withColumnRenamed("_2", "lra_alight_idx").select("*")

lra_alight_result = lra_alight_df.selectExpr("cast(lra_alight_idx as int) lra_alight_idx", \
                                     "line_num", \
                                     "alight_line", \
                                     "cast(rank as int) rank")

lra_alight_result.write \
  .format("org.apache.phoenix.spark") \
  .mode("overwrite") \
  .option("table", "LRA_ALIGHT") \
  .option("zkUrl", "an01:2181") \
  .save()

#####################################################################
# 역명별 승하차 합계 테이블 따로 저장#############################################

nra_ride = spark.sql("select a.* \
                     from ( \
                     select sub_sta_nm, sum(ride_pasgr_num) as ride_name, \
                     rank() over (order by sum(ride_pasgr_num) desc) ranking1, \
                     row_number() over (order by sum(ride_pasgr_num) desc) ranking2 \
                     from pro_df \
                     group by sub_sta_nm) a")

rdd_nra_ride = nra_ride.rdd.zipWithIndex().toDF()
rdd_nra_ride = rdd_nra_ride.withColumn('sub_sta_nm', rdd_nra_ride['_1'].getItem("sub_sta_nm"))
rdd_nra_ride = rdd_nra_ride.withColumn('ride_name', rdd_nra_ride['_1'].getItem("ride_name"))
rdd_nra_ride = rdd_nra_ride.withColumn('rank', rdd_nra_ride['_1'].getItem("ranking1"))
nra_ride_df = rdd_nra_ride.drop("_1").withColumnRenamed("_2", "nra_ride_idx").select("*")

nra_ride_result = nra_ride_df.selectExpr("cast(nra_ride_idx as int) nra_ride_idx", \
                                     "sub_sta_nm", \
                                     "ride_name", \
                                     "cast(rank as int) rank")

nra_ride_result.write \
  .format("org.apache.phoenix.spark") \
  .mode("overwrite") \
  .option("table", "NRA_RIDE") \
  .option("zkUrl", "an01:2181") \
  .save()

------------------------------------------------------------------------------------------------------------------------------------

nra_alight = spark.sql("select a.* \
                     from ( \
                     select sub_sta_nm, sum(alight_pasgr_num) as alight_name, \
                     rank() over (order by sum(alight_pasgr_num) desc) ranking1, \
                     row_number() over (order by sum(alight_pasgr_num) desc) ranking2 \
                     from pro_df \
                     group by sub_sta_nm) a")

rdd_nra_alight = nra_alight.rdd.zipWithIndex().toDF()
rdd_nra_alight = rdd_nra_alight.withColumn('sub_sta_nm', rdd_nra_alight['_1'].getItem("sub_sta_nm"))
rdd_nra_alight = rdd_nra_alight.withColumn('alight_name', rdd_nra_alight['_1'].getItem("alight_name"))
rdd_nra_alight = rdd_nra_alight.withColumn('rank', rdd_nra_alight['_1'].getItem("ranking1"))
nra_alight_df = rdd_nra_alight.drop("_1").withColumnRenamed("_2", "nra_alight_idx").select("*")

nra_alight_result = nra_alight_df.selectExpr("cast(nra_alight_idx as int) nra_alight_idx", \
                                     "sub_sta_nm", \
                                     "alight_name", \
                                     "cast(rank as int) rank")

nra_alight_result.write \
  .format("org.apache.phoenix.spark") \
  .mode("overwrite") \
  .option("table", "NRA_ALIGHT") \
  .option("zkUrl", "an01:2181") \
  .save()

# 역명, 호선별 승, 하차 순위######################################################

select_line = spark.sql("select distinct(line_num) from pro_df")
list_line = list(select_line.select('line_num').toPandas()['line_num'])
nrl_ride = spark.sql("select '1호선' as line_num, sub_sta_nm, sum(ride_pasgr_num) as ride_line_name, \
                          rank() over (order by sum(ride_pasgr_num) desc) ranking1, \
                          row_number() over (order by sum(ride_pasgr_num) desc) ranking2 \
                          from pro_df \
                          where line_num = '1호선' \
                          group by sub_sta_nm")
for i in list_line:
    if i == '1호선':
        pass
    else:
        nrl_ride_union = spark.sql("select '" + i + "' as line_num, sub_sta_nm, sum(ride_pasgr_num) as ride_line_name, \
                                 rank() over (order by sum(ride_pasgr_num) desc) ranking1, \
                                 row_number() over (order by sum(ride_pasgr_num) desc) ranking2 \
                                 from pro_df \
                                 where line_num = '" + i + "' \
                                 group by sub_sta_nm")
        nrl_ride = nrl_ride.union(nrl_ride_union)

rdd_nrl_ride = nrl_ride.rdd.zipWithIndex().toDF()
rdd_nrl_ride = rdd_nrl_ride.withColumn('line_num', rdd_nrl_ride['_1'].getItem("line_num"))
rdd_nrl_ride = rdd_nrl_ride.withColumn('sub_sta_nm', rdd_nrl_ride['_1'].getItem("sub_sta_nm"))
rdd_nrl_ride = rdd_nrl_ride.withColumn('ride_line_name', rdd_nrl_ride['_1'].getItem("ride_line_name"))
rdd_nrl_ride = rdd_nrl_ride.withColumn('rank', rdd_nrl_ride['_1'].getItem("ranking1"))
nrl_ride_df = rdd_nrl_ride.drop("_1").withColumnRenamed("_2", "nrl_ride_idx").select("*")

nrl_ride_result = nrl_ride_df.selectExpr("cast(nrl_ride_idx as int) nrl_ride_idx", \
                                     "line_num", \
                                     "sub_sta_nm", \
                                     "ride_line_name", \
                                     "cast(rank as int) rank")

nrl_ride_result.write \
  .format("org.apache.phoenix.spark") \
  .mode("overwrite") \
  .option("table", "NRL_RIDE") \
  .option("zkUrl", "an01:2181") \
  .save()

nrl_alight = spark.sql("select '1호선' as line_num, sub_sta_nm, sum(alight_pasgr_num) as alight_line_name, \
                          rank() over (order by sum(alight_pasgr_num) desc) ranking1, \
                          row_number() over (order by sum(alight_pasgr_num) desc) ranking2 \
                          from pro_df \
                          where line_num = '1호선' \
                          group by sub_sta_nm")
for i in list_line:
    if i == '1호선':
        pass
    else:
        nrl_alight_union = spark.sql("select '" + i + "' as line_num, sub_sta_nm, sum(alight_pasgr_num) as alight_line_name, \
                                 rank() over (order by sum(alight_pasgr_num) desc) ranking1, \
                                 row_number() over (order by sum(alight_pasgr_num) desc) ranking2 \
                                 from pro_df \
                                 where line_num = '" + i + "' \
                                 group by sub_sta_nm")
        nrl_alight = nrl_alight.union(nrl_alight_union)

rdd_nrl_alight = nrl_alight.rdd.zipWithIndex().toDF()
rdd_nrl_alight = rdd_nrl_alight.withColumn('line_num', rdd_nrl_alight['_1'].getItem("line_num"))
rdd_nrl_alight = rdd_nrl_alight.withColumn('sub_sta_nm', rdd_nrl_alight['_1'].getItem("sub_sta_nm"))
rdd_nrl_alight = rdd_nrl_alight.withColumn('alight_line_name', rdd_nrl_alight['_1'].getItem("alight_line_name"))
rdd_nrl_alight = rdd_nrl_alight.withColumn('rank', rdd_nrl_alight['_1'].getItem("ranking1"))
nrl_alight_df = rdd_nrl_alight.drop("_1").withColumnRenamed("_2", "nrl_alight_idx").select("*")

nrl_alight_result = nrl_alight_df.selectExpr("cast(nrl_alight_idx as int) nrl_alight_idx", \
                                     "line_num", \
                                     "sub_sta_nm", \
                                     "alight_line_name", \
                                     "cast(rank as int) rank")

nrl_alight_result.write \
  .format("org.apache.phoenix.spark") \
  .mode("overwrite") \
  .option("table", "NRL_ALIGHT") \
  .option("zkUrl", "an01:2181") \
  .save()

#####################################################################
# 역명별 소속 라인(python으로 개발)#########################################
import pandas as pd
import glob
import os

# 원본 데이터 통합
path = r'C:/Users/KCW/Desktop/newdata'
file_lit = glob.glob(os.path.join(path, 'subway*'))
all_data = []

for file in file_lit:
    df = pd.read_csv(file)
    all_data.append(df)
    
df = pd.concat(all_data, axis=0, ignore_index=True)

# 가공 후 추가할 json
json_lsn = {}

# 원본 데이터 중 특정 열만 select
df2 = df.loc[:, ['LINE_NUM', 'SUB_STA_NM']]


# json 데이터 생성
for i in df2.values:
    
    if i[1] in json_lsn.keys():
        
        if i[0] in json_lsn[i[1]]:
            pass
        
        else:
            json_lsn[i[1]].append(i[0])
    
    else:
        json_lsn[i[1]] = [i[0]]
        
        
# json to dataframe
# 추가할 데이터 프레임 생성
df3 = pd.DataFrame(columns=['SUB_STA_NM', 'LINE_NUM'])

for i in json_lsn.keys():
    df3 = df3.append({'SUB_STA_NM': i, 'LINE_NUM': ",".join(json_lsn[i])}, ignore_index=True)

# csv 파일 추출
df3.to_csv('C:/Users/KCW/Desktop/subwaylinestanm.csv', encoding='utf-8-sig', index=False)

lsn_path = "hdfs://NNHA/user/source_data/linestanm_subway.csv"
lsn_df = spark.read.csv(lsn_path, header=True)

rdd_lsn = lsn_df.rdd.zipWithIndex().toDF()
rdd_lsn = rdd_lsn.withColumn('sub_sta_nm', rdd_lsn['_1'].getItem("sub_sta_nm"))
rdd_lsn = rdd_lsn.withColumn('line_num', rdd_lsn['_1'].getItem("line_num"))

lsn_df2 = rdd_lsn.drop("_1").withColumnRenamed("_2", "lsn_idx").select("*")

lsn_result = lsn_df2.selectExpr("cast(lsn_idx as int) lsn_idx", \
                          "sub_sta_nm", \
                          "line_num")

lsn_result.write \
  .format("org.apache.phoenix.spark") \
  .mode("overwrite") \
  .option("table", "LSN") \
  .option("zkUrl", "an01:2181") \
  .save()

#####################################################################
# 호선별 색상##########################################################
lc_path = "hdfs://NNHA/user/source_data/linecolor_subway.csv"
lc_df = spark.read.csv(lc_path, header=True)

rdd_lc = lc_df.rdd.zipWithIndex().toDF()
rdd_lc = rdd_lc.withColumn('line_num', rdd_lc['_1'].getItem("line_num"))
rdd_lc = rdd_lc.withColumn('color', rdd_lc['_1'].getItem("color"))

lc_df2 = rdd_lc.drop("_1").withColumnRenamed("_2", "lc_idx").select("*")

lc_result = lc_df2.selectExpr("cast(lc_idx as int) lc_idx", \
                          "line_num", \
                          "color")

lc_result.write \
  .format("org.apache.phoenix.spark") \
  .mode("overwrite") \
  .option("table", "LC") \
  .option("zkUrl", "an01:2181") \
  .save()
#####################################################################
# 역명, 중복 호선 통합 전처리#########################################################
import pandas as pd
import glob
import os
from tqdm import trange, notebook

path = r'C:/Users/KCW/Desktop/newdata'
file_lit = glob.glob(os.path.join(path, 'subway*'))
all_data = []

for file in file_lit:
    df = pd.read_csv(file)
    all_data.append(df)
    
df = pd.concat(all_data, axis=0, ignore_index=True)

val = df['SUB_STA_NM'].values
cnt = len(val)

for i in notebook.tqdm(range(0, cnt)):
    
    if '(' in val[i]:
        
        if val[i].split('(')[0] in val:
            df.loc[df.SUB_STA_NM == val[i].split('(')[0], 'SUB_STA_NM'] = val[i]
        
        else:
            pass
    
    else:
        pass
    
df = df.astype({'USE_DT': 'str'})
df2 = df.loc[df.SUB_STA_NM.str.contains('청량리'), 'SUB_STA_NM'] = '청량리'

val = df['LINE_NUM'].values
cnt = len(val)

list_one = ['경부선', '경인선', '장항선']
list_two = ['일산선']
list_three = ['과천선', '안산선']
list_four = ['경의선', '중앙선']
list_five = ['공항철도 1호선']
list_six = ['수인선', '분당선']

for i in notebook.tqdm(range(0, cnt)):
    if val[i] in list_one:
        df.loc[df.LINE_NUM == val[i], 'LINE_NUM'] = '1호선'
    elif val[i] in list_two:
        df.loc[df.LINE_NUM == val[i], 'LINE_NUM'] = '3호선'
    elif val[i] in list_three:
        df.loc[df.LINE_NUM == val[i], 'LINE_NUM'] = '4호선'
    elif val[i] in list_four:
        df.loc[df.LINE_NUM == val[i], 'LINE_NUM'] = '경의중앙선'
    elif val[i] in list_five:
        df.loc[df.LINE_NUM == val[i], 'LINE_NUM'] = '공항철도선'
    elif val[i] in list_six:
        df.loc[df.LINE_NUM == val[i], 'LINE_NUM'] = '수인분당선'
    else:
        pass

year_val = ['2015','2016','2017','2018','2019','2020']
cnt = len(year_val)

for i in notebook.tqdm(range(0, cnt)):
    df_result = df.loc[df.USE_DT.str.contains(year_val[i])]
    df_result.to_csv('C:/Users/KCW/Desktop/newdata5/subway' + year_val[i] + 't.csv', encoding='utf-8-sig', index=False)
######################################################################
# 호선별 역 개수#########################################################

lct_path = "hdfs://NNHA/user/source_data/linecount_subway.csv"
lct_df = spark.read.csv(lct_path, header=True)

rdd_lct = lct_df.rdd.zipWithIndex().toDF()
rdd_lct = rdd_lct.withColumn('line_num', rdd_lct['_1'].getItem("line_num"))
rdd_lct = rdd_lct.withColumn('line_cnt', rdd_lct['_1'].getItem("line_cnt"))

lct_df2 = rdd_lct.drop("_1").withColumnRenamed("_2", "lct_idx").select("*")

lct_result = lct_df2.selectExpr("cast(lct_idx as int) lct_idx", \
                          "cast(line_num as string) line_num ", \
                          "cast(line_cnt as int) line_cnt")

lct_result.write \
  .format("org.apache.phoenix.spark") \
  .mode("overwrite") \
  .option("table", "LCT") \
  .option("zkUrl", "an01:2181") \
  .save()

#########################################################################
# 역명별 도착지 구분#########################################################

import urllib.request
from urllib.parse import quote
import json
import pandas as pd

# 실시간 지하철 도착 정보 일괄
url = "http://swopenAPI.seoul.go.kr/api/subway/537868565164696433344d52436f69/json/realtimeStationArrival/ALL"
response=urllib.request.urlopen(url)
json_str=response.read().decode("utf-8")
json_object=json.loads(json_str)

# 역명별 도착지 방면 중복, 급행 가공
json_data = {}

for i in json_object['realtimeArrivalList']:
    
    # 이미 들어간 역명일 때
    if i['statnNm'] in json_data.keys():
        
        # (급행) 여부
        if '(' in i['trainLineNm']:            
            if i['trainLineNm'].split(' (')[0] in json_data[i['statnNm']]:
                pass            
            else:
                json_data[i['statnNm']].append(i['trainLineNm'].split(' (')[0])        
        else:
            if i['trainLineNm'] in json_data[i['statnNm']]:
                pass
            else:
                json_data[i['statnNm']].append(i['trainLineNm'])
                
    # 최초 역명 append 시    
    else:
        json_data[i['statnNm']] = []
        if '(' in i['trainLineNm']:
            json_data[i['statnNm']].append(i['trainLineNm'].split(' (')[0])
        else:
            json_data[i['statnNm']].append(i['trainLineNm'])
            
# json to dataframe
df = pd.DataFrame(columns=['SUB_STA_NM', 'DIRECTION_VAL'])

for i in json_data.keys():
    df = df.append({'SUB_STA_NM': i, 'DIRECTION_VAL': ",".join(json_data[i])}, ignore_index=True)
    
df.to_csv('C:/Users/KCW/Desktop/direction_subway.csv', encoding='utf-8-sig', index=False)

direction_path = "hdfs://NNHA/user/source_data/direction_subway.csv"
direction_df = spark.read.csv(direction_path, header=True)

rdd_direction = direction_df.rdd.zipWithIndex().toDF()
rdd_direction = rdd_direction.withColumn('sub_sta_nm', rdd_direction['_1'].getItem("sub_sta_nm"))
rdd_direction = rdd_direction.withColumn('direction_val', rdd_direction['_1'].getItem("direction_val"))

direction_df2 = rdd_direction.drop("_1").withColumnRenamed("_2", "direction_idx").select("*")

direction_result = direction_df2.selectExpr("cast(direction_idx as int) direction_idx", \
                          "sub_sta_nm", \
                          "direction_val")

direction_result.write \
  .format("org.apache.phoenix.spark") \
  .mode("overwrite") \
  .option("table", "DIRECTION") \
  .option("zkUrl", "an01:2181") \
  .save()

#########################################################################