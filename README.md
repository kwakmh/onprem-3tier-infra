# onprem-3tier-infra

> VirtualBox 기반으로 5대의 Ubuntu Server VM을 구성하여 온프레미스 3-Tier 인프라를 직접 구축하는 프로젝트입니다.
> Load Balancer, App Server 이중화, DB Replication, 백업/복구 자동화까지 직접 구현하며 인프라 운영 전반을 실습합니다.

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
| SSH 접속 | PuTTY |

---

## 목차

- [프로젝트 목표](#프로젝트-목표)
- [전체 아키텍처](#전체-아키텍처)
- [서버 구성](#서버-구성)
- [네트워크 구성](#네트워크-구성)
- [네트워크 검증](#네트워크-검증)
- [진행 상태](#진행-상태)
- [트러블슈팅](#트러블슈팅)

---

## 프로젝트 목표

- VirtualBox 기반 온프레미스 3-Tier 인프라 구성
- Load Balancer, App Server, DB Server 역할 분리
- Nginx 기반 로드밸런싱 및 App Server 이중화
- MariaDB Master-Slave Replication 구성
- Bash 스크립트 기반 DB 백업 자동화 및 복구 검증
- 장애 시나리오 구성 및 대응 흐름 검증

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
        | Nginx Load Balancing
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

### 내부 통신 (enp0s3)

`10.0.0.x` 대역은 서버 간 통신에 사용합니다.

```text
lb-server → app-server-1
10.0.0.10 → 10.0.0.21
```

### SSH 관리 접속 (enp0s8)

`192.168.56.x` 대역은 Windows PuTTY를 통한 SSH 관리 접속에 사용합니다.

```text
Host Name: 192.168.56.10
Port: 22
Connection Type: SSH
```

### Netplan 설정 예시 (lb-server 기준)

내부망 설정:

```yaml
network:
  version: 2
  ethernets:
    enp0s3:
      addresses:
        - 10.0.0.10/24
      routes:
        - to: default
          via: 10.0.0.1
      nameservers:
        addresses:
          - 8.8.8.8
```

Host-only 설정:

```yaml
network:
  version: 2
  ethernets:
    enp0s8:
      addresses:
        - 192.168.56.10/24
      optional: true
```

---

## 네트워크 검증

### 서버 간 내부 통신

lb-server에서 나머지 서버로 ping 테스트를 수행했습니다.

```bash
ping -c 3 10.0.0.21  # app-server-1
ping -c 3 10.0.0.22  # app-server-2
ping -c 3 10.0.0.31  # db-master
ping -c 3 10.0.0.32  # db-slave
```

모든 서버 간 통신 정상 확인 (0% packet loss)

### 외부 인터넷 및 DNS 확인

```bash
ping -c 3 8.8.8.8     # 외부 IP 통신
ping -c 3 google.com  # DNS 해석
```

외부 인터넷 통신 및 DNS 해석 정상 확인

---

## 진행 상태

- [x] 5대 Ubuntu Server VM 생성
- [x] 각 VM Hostname 설정
- [x] 서버 간 내부망 고정 IP 설정 (10.0.0.x)
- [x] PuTTY SSH 접속용 Host-only IP 설정 (192.168.56.x)
- [x] 서버 간 내부망 ping 통신 검증
- [x] 외부 인터넷 통신 검증
- [x] DNS 해석 검증
- [ ] Flask App Server 구성 (app-server-1, app-server-2)
- [ ] Nginx Load Balancer 구성
- [ ] 로드밸런싱 및 장애 테스트
- [ ] MariaDB Master-Slave Replication 구성
- [ ] DB 백업 자동화 (Bash + Crontab)
- [ ] 장애 및 복구 테스트

---

## 트러블슈팅

### PuTTY SSH 접속 실패 (포트포워딩 방식)

**문제 상황**

초기에 VirtualBox NAT Network 포트포워딩으로 Windows에서 VM SSH 접속을 시도했습니다.

```text
Windows 127.0.0.1:2210
→ VirtualBox Port Forwarding
→ lb-server 10.0.0.3:22
```

**원인 파악**

VM 내부의 `ssh.service`는 정상 실행 중이었고 22번 포트도 열려 있었습니다.
`Test-NetConnection` 명령어로 확인한 결과 Windows에서 2210 포트가 LISTENING 상태로 열리지 않았습니다.
VirtualBox 포트포워딩 경로 자체가 정상적으로 동작하지 않았습니다.

**해결 방법**

각 VM에 Host-only Adapter를 추가하고 `192.168.56.x` 대역 고정 IP를 부여했습니다.

```text
Windows PuTTY
→ 192.168.56.x:22
→ VM SSH Server
```

5대 VM 모두 PuTTY SSH 접속 성공했습니다.

---

## 다음 단계

app-server-1, app-server-2에 Flask 앱을 구성하고, lb-server의 Nginx를 통해 두 서버로 트래픽을 분산하는 로드밸런싱 구조를 구성할 예정입니다.
