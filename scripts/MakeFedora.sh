#!/bin/bash
# ============================================================================
# File: MakeFedora.sh
# Description: Fedora42 생성 스크립트
# Version: 1.0 , 정상 동작 검증 완료, 부팅 이후 RAM 용량 축소 진행 (필요 시)
# Prerequisites: Kickstart 파일 준비, LVM Thin Pool 생성 후 vm이름으로 Thin Volume 생성 필요
# ============================================================================

# 에러 발생 시 즉시 중단
set -euo pipefail  
# -e: 명령어 실패 시 스크립트 종료
# -u: 정의되지 않은 변수 사용 시 오류 발생
# -o pipefail: 파이프라인에서 명령어 실패 시 전체 실패 처리

# 설정 변수
KICKSTART_FILE="/var/lib/libvirt/kickstarts/fedora42-minimal.ks"
FEDORA_URL="https://ftp.kaist.ac.kr/fedora/linux/releases/42/Server/x86_64/os/"
BRIDGE="br0"
VG_NAME="myKVMvg"
RAM=4096
VCPUS=2
DISK_SIZE="10G"

# VM 정의
declare -A VMS=(
    [webvm]="web"
    [appvm]="app"
    [dbvm]="db"
)

# 색상 출력 함수 (선택사항)
log_info() {
    echo "[INFO] $1"
}

log_success() {
    echo "[SUCCESS] $1"
}

log_warn() {
    echo "[WARN] $1"
}

log_error() {
    echo "[ERROR] $1"
}

# 함수: Kickstart 파일 존재 여부 확인
check_kickstart() {
    if [ ! -f "$KICKSTART_FILE" ]; then
        log_error "Kickstart 파일을 찾을 수 없습니다: $KICKSTART_FILE"
        exit 1
    fi
    log_info "Kickstart 파일 확인 완료: $KICKSTART_FILE"
}

# 함수: LVM Thin Volume 존재 여부 확인
check_lvm_volume() {
    local vm_name=$1
    local lv_path="/dev/${VG_NAME}/${vm_name}"
    
    if ! lvs "${lv_path}" &>/dev/null; then
        log_error "LVM Volume이 존재하지 않습니다: $lv_path"
        return 1
    fi
    log_info "LVM Volume 확인: $lv_path"
    return 0
}

# 함수: VM 정의 존재 여부 확인 (Idempotency 핵심)
vm_exists() {
    local vm_name=$1
    if virsh list --all --name | grep -q "^${vm_name}$"; then
        return 0
    fi
    return 1
}

# 함수: VM 생성
create_vm() {
    local vm_name=$1
    local role=$2
    local disk_path="/dev/${VG_NAME}/${vm_name}"
    
    log_info "VM 생성 시작: $vm_name (Role: $role)"
    
    virt-install \
      --name "$vm_name" \
      --memory "$RAM" \
      --vcpus "$VCPUS" \
      --disk "path=${disk_path},device=disk,format=raw" \
      --location "$FEDORA_URL" \
      --initrd-inject="$KICKSTART_FILE" \
      --extra-args="inst.ks=file:/fedora42-minimal.ks console=ttyS0" \
      --network "bridge=$BRIDGE" \
      --graphics none \
      --console "pty,target_type=serial" \
      --os-variant fedora42 \
      --noautoconsole \
      --wait -1
    
    log_success "VM 생성 완료: $vm_name"
}

# 함수: 모든 VM 생성 또는 스킵
create_all_vms() {
    for vm_name in "${!VMS[@]}"; do
        local role="${VMS[$vm_name]}"
        
        # 1. LVM Volume 존재 확인
        if ! check_lvm_volume "$vm_name"; then
            log_warn "LVM Volume이 없어서 $vm_name을 생성할 수 없습니다. 먼저 LVM을 생성하세요."
            continue
            # exit 1  # 필요시 스크립트 종료, 지금은 건너뛰기
        fi
        
        # 2. VM이 이미 존재하는지 확인 (Idempotency)
        if vm_exists "$vm_name"; then
            log_warn "VM이 이미 존재합니다. 건너뜁니다: $vm_name"
            continue
        fi
        
        # 3. VM 생성
        create_vm "$vm_name" "$role"
    done
}

# 메인 로직
main() {
    log_info "=========================================="
    log_info "Fedora 42 VM 자동 생성 스크립트 시작"
    log_info "=========================================="
    
    # 사전 확인
    check_kickstart
    
    # VM 생성
    create_all_vms
    
    log_info "=========================================="
    log_success "모든 VM 생성 작업 완료!"
    log_info "=========================================="
    
    # 최종 상태 출력
    log_info "생성된 VM 목록:"
    virsh list --all
}

# 스크립트 실행
main "$@"
