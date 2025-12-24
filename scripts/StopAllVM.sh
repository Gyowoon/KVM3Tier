#!/bin/bash
# ============================================================================
# File: StartAStopAllVM.sh
# Description: 모든 VM 중지 스크립트
# Version: 1.0    
# Prerequisites:    
# ============================================================================

for vm in $(virsh list --all | awk 'NR>2 {print $2}'); do
    echo "Stopping VM: $vm"
    virsh shutdown "$vm"
done