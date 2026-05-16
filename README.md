# onprem-3tier-infra

VirtualBox 기반으로 5대의 Ubuntu Server VM을 구성하여 온프레미스 3-Tier 인프라를 실습하는 프로젝트입니다.

이 프로젝트의 목표는 Load Balancer, App Server, DB Server로 구성된 기본적인 서버 인프라 구조를 직접 구축하고, 서버 간 통신, SSH 접속, 로드밸런싱, DB 복제, 백업/복구 과정을 실습하는 것입니다.

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
- 서버 간 내부 통신망 구성
- Windows에서 각 VM으로 SSH 접속 가능한 관리망 구성
- Nginx 기반 로드밸런싱 구성
- Flask App Server 이중화 구성
- MariaDB Master-Slave 복제 구성
- 백업 및 복구 스크립트 작성

---

## 전체 아키텍처

```text
Windows Host
   |
   | PuTTY SSH
   | 192.168.56.x
   |
VirtualBox VMs
   |
   | 10.0.0.x Internal Network
   |
lb-server
   |
   | Nginx Load Balancing
   |
app-server-1     app-server-2
   |
   | DB Connection
   |
db-master  →  db-slave
```

---

## 서버 구성

| Server | Role | Internal IP | SSH Access IP |
|---|---|---:|---:|
| lb-server | Nginx Load Balancer | 10.0.0.10 | 192.168.56.10 |
| app-server-1 | Flask App Server 1 | 10.0.0.21 | 192.168.56.11 |
| app-server-2 | Flask App Server 2 | 10.0.0.22 | 192.168.56.12 |
| db-master | MariaDB Master | 10.0.0.31 | 192.168.56.13 |
| db-slave | MariaDB Slave | 10.0.0.32 | 192.168.56.14 |

---

## 네트워크 구성

각 VM에는 두 개의 네트워크 인터페이스를 구성했습니다.

| Interface | Network | Purpose |
|---|---|---|
| enp0s3 | NAT Network / InfraNetwork | 서버 간 내부 통신 |
| enp0s8 | Host-only Network | Windows에서 PuTTY SSH 접속 |

### 내부 통신용 IP

`10.0.0.x` 대역은 서버 간 통신을 위해 사용합니다.

예를 들어 `lb-server`가 `app-server-1`에 접근할 때는 다음 IP를 사용합니다.

```text
lb-server → app-server-1
10.0.0.10 → 10.0.0.21
```

### SSH 접속용 IP

`192.168.56.x` 대역은 Windows에서 PuTTY를 통해 각 VM에 SSH 접속하기 위한 관리용 IP입니다.

예를 들어 Windows에서 `lb-server`에 접속할 때는 다음 주소를 사용합니다.

```text
Host Name: 192.168.56.10
Port: 22
Connection Type: SSH
```

---

## Netplan 설정 예시

아래는 `lb-server`의 내부망 IP 설정 예시입니다.

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

Host-only IP는 별도 파일로 구성했습니다.

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

### 서버 간 내부 통신 확인

`lb-server`에서 다른 서버로 ping 테스트를 수행했습니다.

```bash
ping -c 3 10.0.0.21
ping -c 3 10.0.0.22
ping -c 3 10.0.0.31
ping -c 3 10.0.0.32
```

검증 결과, 모든 서버 간 통신이 정상적으로 수행되었습니다.

### 외부 인터넷 및 DNS 확인

각 서버에서 외부 IP와 도메인 이름 해석을 확인했습니다.

```bash
ping -c 3 8.8.8.8
ping -c 3 google.com
```

검증 결과, 외부 인터넷 통신과 DNS 해석이 정상적으로 동작했습니다.

---

## 진행 상태

- [x] 5대 Ubuntu Server VM 생성
- [x] Hostname 변경
- [x] 서버 간 통신용 고정 IP 설정
- [x] PuTTY SSH 접속용 Host-only IP 설정
- [x] 서버 간 내부망 통신 검증
- [x] 외부 인터넷 통신 검증
- [x] DNS 해석 검증
- [ ] Flask App Server 구성
- [ ] Nginx Load Balancer 구성
- [ ] MariaDB Master-Slave 복제 구성
- [ ] 백업 및 복구 자동화
- [ ] 장애 테스트 및 복구 검증

---

## 트러블슈팅

### PuTTY SSH 접속 실패

초기에는 VirtualBox NAT Network의 포트포워딩을 사용하여 Windows에서 VM으로 SSH 접속하려고 했습니다.

예상 구조는 다음과 같았습니다.

```text
Windows 127.0.0.1:2210
→ VirtualBox Port Forwarding
→ lb-server 10.0.0.3:22
```

하지만 Windows에서 TCP 2210 포트가 LISTENING 상태로 열리지 않아 PuTTY 접속이 실패했습니다.

확인 결과 VM 내부의 `ssh.service`는 정상 실행 중이었고, 22번 포트도 정상적으로 열려 있었습니다. 따라서 문제는 VM 내부 SSH 서버가 아니라, VirtualBox 포트포워딩 경로가 정상적으로 열리지 않은 것이었습니다.

최종적으로 각 VM에 Host-only Adapter를 추가하고, `192.168.56.x` 대역의 고정 IP를 부여하여 Windows에서 직접 SSH 접속하도록 구성했습니다.

최종 구조는 다음과 같습니다.

```text
Windows PuTTY
→ 192.168.56.x:22
→ VM SSH Server
```

이를 통해 5대 VM 모두 PuTTY SSH 접속에 성공했습니다.

---

## 다음 단계

다음 단계에서는 `app-server-1`, `app-server-2`에 Flask 애플리케이션을 구성하고, `lb-server`의 Nginx를 통해 두 App Server로 요청을 분산시키는 로드밸런싱 구조를 구성할 예정입니다.
