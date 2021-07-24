# Subway-Bigdata-Web   
   
# RESULT    aa
* 문의 사항에 정성껏 답변주신 서울 열린데이터 광장 직원분들께 큰 감사의 인사를 드립니다.   
   
## 실행   
<img width="80%" src="https://user-images.githubusercontent.com/66659846/126601495-ef7f13c4-a26c-455b-bbf7-8a32f213ef7f.gif"/>   
    
### 배치 계층:   
   
1. 서울 열린데이터 광장 사이트의 연도별 지하철 승하차 인원 통계 파일(.CSV)을 다운로드 받습니다.  
   
2. 다운로드 받은 파일들을 HDFS에 저장합니다. (원본 데이터 유지)   
   
3. PYSPARK를 통해 원본 데이터를 가공 후 각각의 목적에 맞는 데이터로 변환 후 DB 테이블 형태로 저장합니다. (PYSPARK 코드 첨부)   

4. 가공된 데이터는 PHEONIX를 통해 HBASE에 실제 저장됩니다. / NoSQL(Hbase)을 SQL 구문을 활용하여 접근 하기 위해 Phoenix와 연동   
   
5. 적재된 데이터를 조건 SELECT, JOIN 등을 통해 웹상에 표현합니다.   
   
### 실시간 계층:   
   
1. 서울 열린데이터 광장으로부터 API 키를 발급 받아 실시간 지하철 위치 정보를 불러옵니다.   
   
2. 사용자의 선택 조건에 따라 결과가 산출됩니다.   
   
3. 데이터 포맷은 JSON 형식이며, 데이터 흐름 간 가공, 동작 등은 코드 내 주석으로 설명되어 있습니다.   
   
## PROCESS   
![Screenshot_263](https://user-images.githubusercontent.com/66659846/126603190-d7bb0de4-8b10-41d2-ad7e-c9cb80366ced.png)  
   
## SERVERS & JPS   
* VM 가상 서버 6대 / MobaXterm 활용 원격 작업 + local Django 서버를 통해 구성 
![Screenshot_276](https://user-images.githubusercontent.com/66659846/126731080-e0b140b0-010f-4a80-9f13-6974e1450b64.png)   
![Screenshot_277](https://user-images.githubusercontent.com/66659846/126731082-da703a19-909e-4725-bdf0-292d39686eeb.png)   
      
## SAVE HDFS & HBASE & PHOENIX   
### 192.168.56.100:9870(hdfs), 16010(hbase), 8765(phoenix)   
   
### 데이터 hdfs 저장 (hdfs://NNHA/user/source_data)   
- direction_subway.csv: 역명별 도착지 방면 선택지   
- linecolor_subway.csv: 호선별 색상 / RGB   
- linecount_subway.csv: 호선별 역 개수   
- linestanm_subway.csv: 역명별 소속 호선   
- subway2015t ~ 2020t.csv: 연도별 승, 하차 기록 통계  
   
### hbase & phoenix 저장   
- phoenix를 통해 SQL구문으로 연동된 hbase NoSQL에 저장 / view는 phoenix 테이블 / pyspark 활용 데이터 가공 및 적재   
- CATALOG ~ STATS: phoenix 설치 시 생성되는 SYSTEM 테이블   
- ALL_RESULT: 모든 승, 하차 기록 테이블   
- ARA: 모든 승, 하차 기록 합계 테이블   
- DIRECTION: 역명별 도착지 방면 선택지 테이블   
- LC: 호선별 색상 / RGB 테이블   
- LCT: 호선별 역 개수 테이블   
- LRA_RIDE ~ ALIGHT: 호선별 승, 하차 기록 합계 테이블   
- LSN: 역명별 소속 호선 테이블   
- NRA_RIDE ~ ALIGHT: 역명별 승, 하차 기록 합계 테이블   
- NRL_RIDE ~ ALIGHT: 역명 + 호선별 승, 하차 기록 합계 테이블   
- YRA: 연도별 승, 하차 기록 합계 테이블   
![Screenshot_280](https://user-images.githubusercontent.com/66659846/126732024-c5e3da4b-b0e8-47b8-aefa-54ee6d95692e.png)   
![Screenshot_281](https://user-images.githubusercontent.com/66659846/126732021-944f7f4d-c779-481d-8caf-e68d99116f4a.png)   

