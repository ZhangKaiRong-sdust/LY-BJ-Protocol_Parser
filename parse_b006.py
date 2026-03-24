# -*- coding: utf-8 -*-
hex_str = '9700800000AAAAAAAAAAAA9707003840B006090801080132002CE9'
data = bytes.fromhex(hex_str)
print('Hex:', ' '.join(f'{b:02X}' for b in data))
print('Bytes:', len(data))
print()

# Frame structure
print('=== 帧结构 ===')
print(f'起始符: {data[0]:02X}')
print(f'TYPE: {data[1]:02X}')
print(f'MAC: {".".join(f"{b:02X}" for b in data[2:8])}')
print(f'ADDR: {".".join(f"{b:02X}" for b in data[8:11])}')

# Data length (little endian)
ll = data[11] + (data[12] << 8)
print(f'数据长度: {ll} ({data[11]:02X}{data[12]:02X})')
print(f'SEQ: {data[13]:02X}')
print(f'控制域: {data[14]:02X}')
print(f'保留: {data[15]:02X}')
print(f'Fn: {data[16]:02X}{data[17]:02X}')
print()

du = data[18:-2]
print('=== 数据单元 ===')
print(f'原始: {" ".join(f"{b:02X}" for b in du)}')
print(f'长度: {len(du)} bytes')
print()

print('=== 字段解析 (表D.24 设置模块通讯参数) ===')
# 1. 硬件模块类型: 1 byte
print(f'1. 硬件模块类型: {du[0]:02X}')

# 2. 通信波特率: 2 bytes (little endian)
baud = du[1] + (du[2] << 8)
print(f'2. 通信波特率: {du[1]:02X}{du[2]:02X} = {baud} bps')

# 3. 校验方式: 1 byte
parity = du[3]
parity_map = {0: '无校验', 1: '偶校验', 2: '奇校验'}
print(f'3. 校验方式: {du[3]:02X} ({parity_map.get(parity, "未知")})')

# 4. 数据位: 1 byte
data_bits = du[4]
print(f'4. 数据位: {du[4]:02X} 位')

# 5. 停止位: 1 byte
stop_bits = du[5]
print(f'5. 停止位: {du[5]:02X} 位')

# 6. 超时时间: 2 bytes (little endian)
timeout = du[6] + (du[7] << 8) if len(du) >= 8 else du[6]
print(f'6. 超时时间: {du[6]:02X} = {du[6]} ms')

print()
print(f'CS: {data[-2]:02X}')
print(f'结束符: {data[-1]:02X}')
