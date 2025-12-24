#!/bin/bash
# ============================================================================
# File: StartAllVM.sh
# Description: 모든 VM 시작 스크립트
# Version: 1.0    
# Prerequisites:    
# ============================================================================

for vm in $(virsh list --all | awk 'NR>2 {print $2}'); do
    echo "Starting VM: $vm"
    virsh start "$vm"
done