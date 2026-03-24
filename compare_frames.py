# -*- coding: utf-8 -*-
# 比较两个帧的结构

hex1 = '97FFFFFFFFAAAAAAAAAAAA9702000440B002320050E9'  # 之前成功的帧
hex2 = '9700800000AAAAAAAAAAAA9707003840B006090801080132002CE9'  # 当前的帧

data1 = bytes.fromhex(hex1)
data2 = bytes.fromhex(hex2)

print('=== 之前成功的帧 ===')
print(f'Hex: {hex1}')
print(f'Length: {len(data1)} bytes')
for i, b in enumerate(data1):
    print(f'  {i:2d}: {b:02X}')

print()
print('=== 当前帧 ===')
print(f'Hex: {hex2}')
print(f'Length: {len(data2)} bytes')
for i, b in enumerate(data2):
    print(f'  {i:2d}: {b:02X}')
