# -*- coding: utf-8 -*-
# 检查之前的成功帧结构
hex1 = '97FFFFFFFFAAAAAAAAAAAA9702000440B002320050E9'
data1 = bytes.fromhex(hex1)

print('=== 之前成功帧 ===')
for i in range(len(data1)):
    print(f'  {i:2d}: {data1[i]:02X}')

print()
print(f'Fn (pos 16-17): {data1[16]:02X}{data1[17]:02X}')
print(f'Data (pos 18 to -2): {data1[18:-2].hex()}')

print()

# 当前帧
hex2 = '9700800000AAAAAAAAAAAA9707003840B006090801080132002CE9'
data2 = bytes.fromhex(hex2)

print('=== 当前帧 ===')
for i in range(len(data2)):
    print(f'  {i:2d}: {data2[i]:02X}')

print()
# 尝试不同的位置
print(f'Fn (pos 15-16): {data2[15]:02X}{data2[16]:02X}')
print(f'Fn (pos 16-17): {data2[16]:02X}{data2[17]:02X}')
print(f'Data (pos 17 to -2): {data2[17:-2].hex()}')
print(f'Data (pos 18 to -2): {data2[18:-2].hex()}')
