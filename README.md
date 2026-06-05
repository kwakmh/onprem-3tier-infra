# onprem-3tier-infra


## 프로젝트 소개
> VirtualBox 기반으로 5대의 Ubuntu Server VM을 구성하여 온프레미스 3-Tier 인프라를  구축하는 프로젝트입니다.
> Load Balancer, App Server 이중화, DB Replication, 백업/복구 자동화까지 구성합니다

---

## 목차
- [프로젝트 목표](#프로젝트-목표)
- [기술 스택](#기술-스택)
- [전체 아키텍처](#전체-아키텍처)
- [서버 구성](#서버-구성)
- [네트워크 구성](#네트워크-구성)
- [App Server 구성](#app-server-구성)
- [로드밸런서 구성](#로드밸런서-구성)
- [DB 연동 구성](#db-연동-구성)
- [DB Replication 구성](#db-replication-구성)
- [DB 백업 및 복구 구성](#db-백업-및-복구-구성)
- [진행 상태](#진행-상태)
- [트러블슈팅](#트러블슈팅)

## 프로젝트 목표

- VirtualBox 기반 온프레미스 3-Tier 인프라 구성
- Load Balancer, App Server, DB Server 역할 분리
- Nginx 기반 로드밸런싱 및 App Server 이중화
- MariaDB Master-Slave Replication 구성
- Bash 스크립트 기반 DB 백업 자동화 및 복구 검증
- 장애 시나리오 구성 및 대응 흐름 검증

---

## 기술 스택

| 분류 | 기술 |
|------|------|
| OS | Ubuntu Server 24.04 LTS |
| Load Balancer | Nginx |
| Application | Python Flask |
| Database | MariaDB |
| 자동화 | Bash Script, Crontab |
| 가상화 | VirtualBox |

---

## 전체 아키텍처

```text
Windows Host (Client)
        |
        | PuTTY SSH (192.168.56.x)
        |
        ↓
lb-server (10.0.0.10)
        |
        | Reverse Proxy / Load Balancing
        |
   ┌────┴────┐
   ↓         ↓
app-server-1  app-server-2
(10.0.0.21)  (10.0.0.22)
        |
        | DB Connection
        ↓
db-master (10.0.0.31)
        |
        | Replication
        ↓
db-slave (10.0.0.32)
```

---

## 서버 구성

| Server | Role | Internal IP | SSH Access IP |
|--------|------|-------------|---------------|
| lb-server | Nginx Load Balancer | 10.0.0.10 | 192.168.56.10 |
| app-server-1 | Flask App Server 1 | 10.0.0.21 | 192.168.56.11 |
| app-server-2 | Flask App Server 2 | 10.0.0.22 | 192.168.56.12 |
| db-master | MariaDB Master | 10.0.0.31 | 192.168.56.13 |
| db-slave | MariaDB Slave | 10.0.0.32 | 192.168.56.14 |

---

## 네트워크 구성

각 VM에는 두 개의 네트워크 인터페이스를 구성했습니다.

| Interface | Network | Purpose |
|-----------|---------|---------|
| enp0s3 | NAT Network (InfraNetwork) | 서버 간 내부 통신 |
| enp0s8 | Host-only Network | Windows에서 PuTTY SSH 접속 |


---

## App Server 구성
3-Tier 구조에서 Application Tier 역할을 수행하기 위해 Flask App Server(app-server-1, app-server-2)를 구성했습니다.

각 App Server는 요청을 받으면 서버 이름, 실행 상태, 응답 시간을 JSON 형식으로 반환합니다
Flask 앱을 systemd 서비스로 등록하여 VM 부팅 시 자동 실행되도록 구성했습니다 

| Endpoint | 설명 |
|----------|------|
| `/` | 서버 이름, 실행 상태, 응답 시간 확인 |
| `/health` | App Server 상태 확인 |
| `/db` | App Server에서 DB-Master 연결 확인 |
| `/visit` | 방문 기록을 DB에 저장 |
| `/record` | DB에 저장된 최근 방문 기록 조회 |
| `/info` | Nginx proxy header 및 요청자 IP 확인 |


- Flask 코드: `app/app.py`
- systemd 서비스 파일: `systemd/flask-app.service`
---

## 로드밸런서 구성
3-Tier 구조에서 lb-server의 Nginx를 Web Tier 및 Load Balancer 역할로 구성했습니다

Nginx는 `10.0.0.10:80`으로 들어온 요청을 `10.0.0.21:5000`, `10.0.0.22:5000`로 분산합니다.

- Nginx 설정 파일: `nginx/flask-lb.conf`

`curl http://10.0.0.10` 요청 시 app-server-1과 app-server-2가 Round Robin 방식으로 번갈아 응답하는 것을 확인했습니다.

app-server-1의 Flask를 중지한 뒤 nginx의 로드밸런서가 장애가 발생한 app-server-1를 제외시키고, app-server-2에만 응답을 보내는 것을 확인했습니다

---
## DB 연동 구성
3-Tier 구조에서 Database Tier 역할을 수행하기 위해 db-master에 MariaDB를 설치하고, 
Flask App Server(app-server-1, app-server-2)에서 DB에 접속할 수 있도록 구성했습니다.

`company_db` 데이터베이스와 `visits` 테이블을 생성하고, App Server에서 DB에 접속할 `app_user` 계정을 생성하였습니다

| 항목 | 값 |
|------|----|
| DB Server | db-master |
| DB IP | 10.0.0.31 |
| Database | company_db |
| Table | visits |
| DB User | app_user |
| 권한 | SELECT, INSERT |

### App Server용 DB 계정 구성


| DB 계정 | 접속 허용 IP | 용도 |
|--------|--------------|------|
| `app_user`@`10.0.0.21` | app-server-1 | App Server 1에서 DB 접속 |
| `app_user`@`10.0.0.22` | app-server-2 | App Server 2에서 DB 접속 |



### 검증 결과


| 테스트 | 설명 |
|--------|------|
| `curl http://10.0.0.10/db` | App Server에서 DB-Master 연결 확인 |
| `curl http://10.0.0.10/visit` | 방문 기록 DB 저장 확인 |
| `curl http://10.0.0.10/record` | DB에 저장된 방문 기록 조회 확인 |

`lb-server → app-server-1/app-server-2 → db-master` 흐름으로 요청이 전달되고,
App Server를 통해 저장된 데이터가 MariaDB의 `visits` 테이블에 기록되는 것을 확인했습니다

---

## DB Replication 구성 
db-master의 변경사항을 db-slave로 복제하기 위해 Master-Slave Replication을 구성했습니다.

db-master는 DB 변경 사항을 binary log에 기록하고, db-slave는 replication 전용 계정으로 db-master에 접속하여 db-master의 binary log를 읽고, db-slave의 relay log에 변경내용을 저장한 뒤 자신의 MariaDB에 반영합니다

| 항목 | 값 |
|---------|------|
| Master DB | db-master |
| Slave DB | db-slave |
| Database | company_db |
| Table | visits | 
| Replication 계정 | repli_user |

### 구성 흐름
1. db-master에 binary log 활성화 설정
2. db-master에 복제 전용 계정 (repli_user) 생성
3. db-master에 초기 데이터 dump 생성 후 db-slave에 복원
4. db-slave에 master 접속 정보, binary log 시작 위치 등록
5. db-slave가 master의 변경 사항을 relay log에 저장하고, 자신의 MariaDB에 반영

### 검증 결과

- db-slave가 db-master의 binary log를 받아, relay log를 통해 자신의 MariaDB에 반영하는 것을 검증함 
  
 `Slave_IO_Running: Yes`
 
`Slave_SQL_Running: Yes`

`Seconds_Behind_Master: 0`

---

## DB 백업 및 복구 구성

db-master의 company_db 데이터베이스의 데이터를 날짜/시간별로 압축하며 crontab으로 자동 백업하고, company_db 데이터베이스의 visits 테이블 손상 시 백업본으로 복구가 가능한지 확인했습니다

| 항목 | 값 |
|------|----|
| 백업 대상 | db-master의 company_db |
| 백업 방식 | mariadb-dump |
| 백업 스크립트 | scripts/db_backup.sh |
| 백업 저장 경로 | /home/moo/backup/db |
| 백업 파일 형식 | backup_YYYYMMDD_HHMMSS.tar.gz |
| 자동 실행 방식 | crontab |

### 백업 흐름 
1. mariadb-dump로 company_db 데이터베이스 덤프
2. tar.gz로 압축하여 날짜/시간별 파일로 저장
3. crontab으로 일정 시간마다 자동 실행 

### 백업 검증
crontab을 통해 일정 시간마다 백업 스크립트를 실행하고, 백업 압축 파일 `backup_YYYYMMDD_HHMMSS.tar.gz` 이 생성되는 것을 확인했습니다.

### 복구 
백업 파일로 실제 데이터 복구가 가능한지 확인하기 위해 `company_db` 데이터베이스의 `visits` 테이블을 삭제한 뒤 복구 테스트를 진행했습니다.

### 복구 테스트 흐름 
1.cron 자동 백업 잠시 중지
2.`DROP TABLE visits;`로 visits 테이블 삭제
3. 백업 파일 `backup_YYYYMMDD_HHMMSS.tar.gz` 압축 해제
4. 압축 해제한 `company_db.sql`을 MariaDB에 입력하여 SQL문 실행
5. 테이블과 데이터 정상 복구 확인 

### 복구 검증
visits 테이블을 DROP으로 삭제한 뒤, 백업 파일로 복구하여 기존 `visits` 테이블과 데이터가 정상 복원되는 것을 확인했습니다.


## 진행 상태

- [x] 5대 Ubuntu Server VM 생성
- [x] 각 VM Hostname 설정
- [x] 서버 간 내부망 고정 IP 설정 (10.0.0.x)
- [x] PuTTY SSH 접속용 Host-only IP 설정 (192.168.56.x)
- [x] 서버 간 내부망 ping 통신 검증
- [x] 외부 인터넷 통신 검증
- [x] DNS 해석 검증
- [x] Flask App Server 구성 (app-server-1, app-server-2)
- [x] Nginx Load Balancer 구성
- [x] 로드밸런싱 및 장애 테스트
- [x] DB-Master MariaDB 구성
- [x] App Server → DB-Master 직접 접속 테스트
- [x] Flask 애플리케이션 DB 연동
- [x] LB → App → DB 요청 흐름 검증
- [x] MariaDB Master-Slave Replication 구성
- [x] DB 백업 자동화 (Bash + Crontab)
- [x] 장애 및 복구 테스트

---

