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


- Flask 코드: `app/app.py`
- systemd 서비스 파일: `systemd/flask-app.service`
---

## 로드밸런서 구성
3-Tier 구조에서 lb-server의 Nginx를 Web Tier 및 Load Balancer 역할로 구성했습니다

Nginx는 `10.0.0.10:80`으로 들어온 요청을 `10.0.0.21:5000`, `10.0.0.22:5000`로 분산합니다.

- Nginx 설정 파일: `nginx/flask-lb.conf`

`curl http://10.0.0.10` 요청 시 app-server-1과 app-server-2가 Round Robin 방식으로 번갈아 응답하는 것을 확인했습니다.

app-server-1의 flask를 중지한 뒤 nginx의 로드밸런서가 장애가 발생한 app-server-1를 제외시키고, app-server-2에만 응답을 보내는 것을 확인했습니다

---

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
- [ ] MariaDB Master-Slave Replication 구성
- [ ] DB 백업 자동화 (Bash + Crontab)
- [ ] 장애 및 복구 테스트

---

