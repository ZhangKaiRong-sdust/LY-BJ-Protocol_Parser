# -*- coding: utf-8 -*-
hex2 = '9700800000AAAAAAAAAAAA9707003840B006090801080132002CE9'
data = bytes.fromhex(hex2)

print('Hex positions:')
for i in range(len(data)):
    print(f'  {i:2d}: {data[i]:02X}')

print()
print('=== Correct parsing ===')
print(f'起始符: {data[0]:02X}')
print(f'TYPE: {data[1]:02X}')
print(f'MAC: {".".join(f"{b:02X}" for b in data[2:8])}')
print(f'ADDR: {".".join(f"{b:02X}" for b in data[8:11])}')
print(f'数据长度: {data[11]:02X} ({data[11]})')
print(f'SEQ: {data[12]:02X}')
print(f'控制域: {data[13]:02X}')
print(f'保留: {data[14]:02X}')
print(f'Fn: {data[15]:02X}{data[16]:02X}')

# Data starts at position 17
du = data[17:-2]
print(f'数据单元 (pos 17 to -2): {" ".join(f"{b:02X}" for b in du)}')
print(f'CS: {data[-2]:02X}')
print(f'结束符: {data[-1]:02X}')

print()
print('=== 数据单元解析 ===')
print(f'1. 硬件模块类型: {du[0]:02X}')
baud = du[1] + (du[2] << 8)
print(f'2. 通信波特率: {baud} bps')
parity_map = {0: '无校验', 1: '偶校验', 2: '奇校验', 0xFF: '不设置'}
print(f'3. 校验方式: {du[3]:02X} ({parity_map.get(du[3], "未知")})')
print(f'4. 数据位: {du[4]:02X}')
print(f'5. 停止位: {du[5]:02X}')
print(f'6. 超时时间: {du[6]:02X} ms')
