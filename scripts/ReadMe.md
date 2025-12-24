1. kickstart 파일 위치 
- fedora42 및 alma10 : "/var/lib/libvirt/kickstarts/"

2. disk path: KVM Thin Pool Provisioning 사용함 
- 작업 절차 
1) 신규 Disk 추가@VMWare Workstation  -> 접속 후 lsblk 
2) 해당 Disk Partitioning -> fdisk OR parted [Opt, but recommended, 디스크 통으로 사용해도 되지만 파티셔닝 권장
```
# lsblk  출력 중 
sdb                             8:16   0   50G  0 disk 
└─sdb1                          8:17   0   50G  0 part

# fdisk -l /dev/sdb 출력 중 
Device     Boot Start       End   Sectors Size Id Type
/dev/sdb1        2048 104857599 104855552  50G 8e Linux LVM
```
2) Thin Pool 생성-> Sequentially [pvcreate , vgcreate, lvcreate]
``` 

# pvcreate for dedicated partition (It's OK for whole disk)
pvcreate /dev/sdb1

# vgcreate for thin pool(=logical volume)
vgcreate SOME_VG_NAME /dev/sdb1

# lvcreate for Thin Pool 
lvcreate -l 100%FREE -T myKVMvg/myKVMpool
  
Thin pool volume with chunk size 64.00 KiB can address at most <15.88 TiB of data.
  Logical volume "myKVMpool" created.
```

# lvs
```
  LV        VG      Attr       LSize   Pool Origin Data%  Meta%  Move Log Cpy%Sync Convert
  myKVMpool myKVMvg twi-a-tz--  49.89g             0.00   10.44                           
  root      rl      -wi-ao---- <26.00g                                                    
  swap      rl      -wi-ao----   3.00g    
```

3) Virtual Volume (vv) 생성 -> Thin Pool(TP)의 총 용량을 적절히 나눠 쓰는 가상 볼륨(초과 않도록 유의)

# lvcreate -V <SOME_CAPA_FOR_VV_WITH_UNIT> -T myKVMvg/myKVMpool -n <SOME_NAME_FOR_VV>

```
[root@node1]$lvcreate -V 10G -T myKVMvg/myKVMpool -n appvm
  Logical volume "appvm" created.
[root@node1]$lvcreate -V 10G -T myKVMvg/myKVMpool -n webvm
  Logical volume "webvm" created.
[root@node1]$lvcreate -V 10G -T myKVMvg/myKVMpool -n dbvm
  Logical volume "dbvm" created.
[root@node1]$lvcreate -V 15G -T myKVMvg/myKVMpool -n monvm
  Logical volume "monvm" created.
[root@node1]$lvs
  LV        VG      Attr       LSize   Pool      Origin Data%  Meta%  Move Log Cpy%Sync Convert
  appvm     myKVMvg Vwi-a-tz--  10.00g myKVMpool        0.00                                   
  dbvm      myKVMvg Vwi-a-tz--  10.00g myKVMpool        0.00                                   
  monvm     myKVMvg Vwi-a-tz--  15.00g myKVMpool        0.00                                   
  myKVMpool myKVMvg twi-aotz--  49.89g                  0.00   10.47                           
  webvm     myKVMvg Vwi-a-tz--  10.00g myKVMpool        0.00                                   
  root      rl      -wi-ao---- <26.00g                                                         
  swap      rl      -wi-ao----   3.00g 
```

3. RUN  virt-install script (or manually)
