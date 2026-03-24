# -*- coding: utf-8 -*-
"""
背夹通信协议解析工具 - 核心解析模块
Protocol: Q/GDW XXXXX-2022 附录D

已按当前工作区中的协议文档和样例帧整理出如下基础帧结构：

    97H | TYPE(4) | MAC(6) | 97H | L(2) | SEQ | C | Fn(2) | DATA | CS | E9H

- TYPE: 4 字节设备功能位图
- MAC: 6 字节背夹蓝牙 MAC，文档说明传输时低字节在前
- L:   数据域长度，2 字节，小端
- Fn:  低字节 F0，高字节 F1
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple


FRAME_START = 0x97
FRAME_SPLIT = 0x97
FRAME_END = 0xE9
MIN_FRAME_LEN = 20


TYPE_BIT_LAYOUT = {
    0: {
        7: "超高频RFID",
        6: "北斗模块",
    },
    1: {
        7: "RS485",
    },
    3: {
        6: "热点",
        5: "SIM卡",
        4: "扫描",
        3: "高频RFID",
        2: "激光红外",
        1: "普通红外",
        0: "计量通信认证模块",
    },
}

F0_MAP = {
    0x01: "查询通用参数",
    0x0F: "在线升级",
    0x20: "超高频RFID",
    0xB0: "背夹",
    0xC0: "北斗模块",
}

F1_QUERY_GENERAL_MAP = {
    0x02: "设备状态",
}

F1_BACKCLIP_MAP = {
    0x01: "获取背夹信息",
    0x02: "设置背夹不交互自动关闭时间",
    0x03: "获取模块电源状态",
    0x04: "模块电源开启关闭",
    0x05: "获取模块通讯参数",
    0x06: "设置模块通讯参数",
    0x07: "模块数据转发",
    0x08: "设置开机后高级功能启动状态",
    0x09: "获取开机后高级功能启动状态",
    0x19: "获取蓝牙PIN码",
    0x20: "获取业务状态与设备指纹",
    0x21: "SM4协商开始",
    0x22: "SM4协商结束",
    0x23: "SM4密钥下发",
    0x30: "SIM卡通信参数设置",
    0x31: "SIM卡通信参数读取",
    0x32: "查询SIM卡连接状态",
    0x33: "配置热点参数",
    0x34: "获取热点参数",
    0x35: "设置热点启动关闭",
    0x36: "获取热点状态",
    0x37: "设置充电宝功能启动关闭",
    0x38: "设置移动硬盘功能启动关闭",
}

MODULE_TYPE_MAP = {
    0x09: "RS485",
    0x17: "高频RFID",
    0x18: "激光红外",
    0x19: "普通红外",
    0x20: "计量通信认证模块",
    0x21: "超高频RFID",
    0x22: "扫描",
    0x23: "定位模块",
    0x24: "SIM卡",
    0xFF: "无效",
}

FORWARD_DATA_TYPE_MAP = {
    0x01: "非报文格式的数据",
    0x02: "计量通信认证模块报文",
    0x03: "645报文",
    0x04: "698报文",
    0x05: "1376.1报文",
    0x06: "电子封印数据",
}

BACKCLIP_ERROR_MAP = {
    0x01: "设置参数失败",
    0x02: "模块开启失败",
    0x03: "模块关闭失败",
    0x04: "模块写入失败",
    0x05: "模块读取失败",
    0x06: "硬件模块与数据类型不匹配",
    0x07: "接收数据超时",
    0x08: "APN卡参数未设置",
    0x09: "未连接主站",
    0x0A: "网络注册失败",
    0x0B: "热点密码长度小于8位",
    0xF1: "失败",
    0xFA: "参数非法",
    0xFB: "通信超时",
    0xFC: "数据格式不正确",
    0xFD: "无此功能",
}


def parse_hex_string(hex_str: str) -> bytes:
    """解析十六进制字符串，自动过滤空白和分隔符。"""
    cleaned = re.sub(r"[^0-9A-Fa-f]", "", hex_str.strip())
    if not cleaned:
        raise ValueError("请输入十六进制报文")
    if len(cleaned) % 2 != 0:
        raise ValueError("十六进制字符串长度必须为偶数")
    return bytes.fromhex(cleaned)


def bytes_to_hex(data: bytes, sep: str = " ") -> str:
    return sep.join(f"{b:02X}" for b in data)


def little_endian_u16(data: bytes) -> int:
    return int.from_bytes(data, "little")


def bcd_to_int(value: int) -> int:
    high = (value >> 4) & 0x0F
    low = value & 0x0F
    if high > 9 or low > 9:
        return value
    return high * 10 + low


def decode_type(type_bytes: bytes) -> Dict[str, Any]:
    features: List[str] = []
    for byte_index, bit_map in TYPE_BIT_LAYOUT.items():
        if byte_index >= len(type_bytes):
            continue
        current = type_bytes[byte_index]
        for bit, name in sorted(bit_map.items(), reverse=True):
            if current & (1 << bit):
                features.append(name)
    return {
        "raw": bytes_to_hex(type_bytes),
        "raw_compact": type_bytes.hex().upper(),
        "features": features,
        "display": "、".join(features) if features else "无",
    }


def decode_control(control_byte: int) -> Dict[str, Any]:
    direction = (control_byte >> 7) & 0x01
    prm = (control_byte >> 6) & 0x01
    error = (control_byte >> 5) & 0x01
    encrypted = (control_byte >> 4) & 0x01

    if direction == 0 and prm == 1:
        frame_kind = "主站请求"
    elif direction == 1 and prm == 0 and error == 0:
        frame_kind = "从站正常应答"
    elif direction == 1 and prm == 0 and error == 1:
        frame_kind = "从站异常应答"
    elif direction == 1 and prm == 1:
        frame_kind = "从站主动上报"
    elif direction == 0 and prm == 0:
        frame_kind = "主站应答"
    else:
        frame_kind = "未知"

    return {
        "raw": f"{control_byte:02X}H",
        "direction": "背夹发送" if direction else "终端发送",
        "prm": "主设备" if prm else "从设备",
        "error": bool(error),
        "encrypted": bool(encrypted),
        "reserved_low_nibble": control_byte & 0x0F,
        "frame_kind": frame_kind,
        "is_request": direction == 0 and prm == 1,
        "is_response": direction == 1 and prm == 0,
        "is_normal_response": direction == 1 and prm == 0 and error == 0,
        "is_error_response": direction == 1 and prm == 0 and error == 1,
    }


def get_fn_name(f0: int, f1: int) -> str:
    f0_name = F0_MAP.get(f0, f"未知F0(0x{f0:02X})")
    if f0 == 0x01:
        return f"{f0_name} / {F1_QUERY_GENERAL_MAP.get(f1, f'未知F1(0x{f1:02X})')}"
    if f0 == 0xB0:
        return f"{f0_name} / {F1_BACKCLIP_MAP.get(f1, f'未知F1(0x{f1:02X})')}"
    return f0_name


def module_type_name(module_type: int) -> str:
    return MODULE_TYPE_MAP.get(module_type, f"未知(0x{module_type:02X})")


def error_name(error_code: int) -> str:
    return BACKCLIP_ERROR_MAP.get(error_code, f"未知错误(0x{error_code:02X})")


def append_kv_block(lines: List[str], title: str, rows: List[Tuple[str, Any]]) -> None:
    lines.append(title)
    if not rows:
        lines.append("  (空)")
        return

    for label, value in rows:
        lines.append(f"  {label}\t: {value}")


def parse_device_status(data: bytes) -> Dict[str, Any]:
    if len(data) != 7:
        return {
            "raw": bytes_to_hex(data),
            "error": f"设备状态数据长度应为7字节，实际{len(data)}字节",
        }

    voltage = f"{bcd_to_int(data[0]):02d}.{bcd_to_int(data[1]):02d} V"
    percentage = f"{bcd_to_int(data[2])}%"
    return {
        "电池电压": voltage,
        "电量百分比": percentage,
        "预留": bytes_to_hex(data[3:7]),
    }


def parse_backclip_info(data: bytes) -> Dict[str, Any]:
    if len(data) < 60:
        return {
            "raw": bytes_to_hex(data),
            "error": f"获取背夹信息数据长度不足，至少60字节，实际{len(data)}字节",
        }

    result: Dict[str, Any] = {}
    pos = 0

    device_model = data[pos:pos + 12].decode("ascii", errors="replace").strip("\x00 ").strip()
    result["设备型号"] = device_model
    pos += 12

    device_id = bytes_to_hex(data[pos:pos + 6], "")
    result["设备ID号"] = device_id
    pos += 6

    result["硬件版本号"] = f"{bcd_to_int(data[pos]):02d}.{bcd_to_int(data[pos + 1]):02d}"
    pos += 2

    result["硬件版本日期"] = f"20{bcd_to_int(data[pos]):02d}-{bcd_to_int(data[pos + 1]):02d}-{bcd_to_int(data[pos + 2]):02d}"
    pos += 3

    result["软件版本号"] = ".".join(f"{bcd_to_int(b):02d}" for b in data[pos:pos + 4])
    pos += 4

    result["软件版本日期"] = f"20{bcd_to_int(data[pos]):02d}-{bcd_to_int(data[pos + 1]):02d}-{bcd_to_int(data[pos + 2]):02d}"
    pos += 3

    result["电池容量"] = "".join(f"{bcd_to_int(b):02d}" for b in data[pos:pos + 4]) + " mAh"
    pos += 4

    module_flags = data[pos:pos + 4]
    decoded_module_flags = decode_type(module_flags)
    result["支持的硬件模块信息"] = decoded_module_flags["raw"]
    result["支持的硬件模块"] = decoded_module_flags["display"]
    pos += 4

    result["背夹不交互自动关闭时间"] = f"{little_endian_u16(data[pos:pos + 2])} 分钟"
    pos += 2

    result["厂商编码"] = bytes_to_hex(data[pos:pos + 24], "")
    pos += 24

    if pos < len(data):
        name_len = data[pos]
        pos += 1
        if pos + name_len <= len(data):
            vendor_name_bytes = data[pos:pos + name_len]
            try:
                result["厂家名称"] = vendor_name_bytes.decode("gbk")
            except UnicodeDecodeError:
                result["厂家名称"] = bytes_to_hex(vendor_name_bytes)
        else:
            result["厂家名称"] = f"长度异常(N={name_len})"

    return result


def parse_auto_off_time(data: bytes) -> Dict[str, Any]:
    if len(data) != 2:
        return {"raw": bytes_to_hex(data), "error": f"自动关闭时间应为2字节，实际{len(data)}字节"}
    return {"背夹不交互自动关闭时间": f"{little_endian_u16(data)} 分钟"}


def parse_module_power_status(data: bytes) -> Dict[str, Any]:
    if len(data) == 1:
        module_type = data[0]
        return {"硬件模块类型": f"{module_type:02X}H ({module_type_name(module_type)})"}
    if len(data) == 2:
        module_type = data[0]
        power_status = data[1]
        return {
            "硬件模块类型": f"{module_type:02X}H ({module_type_name(module_type)})",
            "电源状态": "开" if power_status == 0x01 else "关",
        }
    return {"raw": bytes_to_hex(data), "error": f"模块电源状态数据长度非法: {len(data)}"}


def parse_module_power_control(data: bytes) -> Dict[str, Any]:
    if len(data) != 2:
        return {"raw": bytes_to_hex(data), "error": f"模块电源控制数据应为2字节，实际{len(data)}字节"}
    module_type = data[0]
    command = data[1]
    return {
        "硬件模块类型": f"{module_type:02X}H ({module_type_name(module_type)})",
        "控制命令": "打开" if command == 0x01 else "关闭",
    }


def parse_comm_params(data: bytes) -> Dict[str, Any]:
    if len(data) != 8:
        return {
            "error": "数据非法",
            "当前报文数据区长度": f"{len(data)} 字节",
            "协议要求长度": "8 字节",
            "raw": bytes_to_hex(data),
        }

    module_type = data[0]
    baud_raw = little_endian_u16(data[1:3])
    parity = data[3]
    data_bits = data[4]
    stop_bits = data[5]
    timeout = little_endian_u16(data[6:8])

    baudrate = baud_raw * 300 if baud_raw <= 9 else baud_raw
    parity_map = {0x00: "无校验", 0x01: "偶校验", 0x02: "奇校验", 0xFF: "保持不变"}
    stop_bits_map = {
        0x00: "无停止位",
        0x01: "1个停止位",
        0x02: "2个停止位",
        0x03: "1.5个停止位",
        0xFF: "保持不变",
    }

    result = {
        "硬件模块类型": f"{module_type:02X}H ({module_type_name(module_type)})",
        "通信波特率原始值": f"{baud_raw}",
        "通信波特率": f"{baudrate} bps",
        "校验方式": parity_map.get(parity, f"未知(0x{parity:02X})"),
        "数据位": "保持不变" if data_bits == 0xFF else f"{data_bits} 位",
        "停止位": stop_bits_map.get(stop_bits, f"未知(0x{stop_bits:02X})"),
        "超时时间": f"{timeout} ms",
    }
    return result


def parse_data_forward_request(data: bytes) -> Dict[str, Any]:
    if len(data) < 4:
        return {"raw": bytes_to_hex(data), "error": f"模块数据转发请求数据长度不足，至少4字节，实际{len(data)}字节"}

    module_type = data[0]
    data_type = data[1]
    payload_len = little_endian_u16(data[2:4])
    payload = data[4:]
    result = {
        "硬件模块类型": f"{module_type:02X}H ({module_type_name(module_type)})",
        "转发数据类型": f"{data_type:02X}H ({FORWARD_DATA_TYPE_MAP.get(data_type, '未知类型')})",
        "转发数据长度": payload_len,
        "转发数据": bytes_to_hex(payload),
    }
    if payload_len != len(payload):
        result["说明"] = f"声明长度={payload_len}，实际长度={len(payload)}"
    return result


def parse_data_forward_response(data: bytes) -> Dict[str, Any]:
    if len(data) < 4:
        return {"raw": bytes_to_hex(data), "error": f"模块数据转发响应数据长度不足，至少4字节，实际{len(data)}字节"}

    module_type = data[0]
    data_type = data[1]
    payload_len = little_endian_u16(data[2:4])
    payload = data[4:]
    result = {
        "硬件模块类型": f"{module_type:02X}H ({module_type_name(module_type)})",
        "响应数据类型": f"{data_type:02X}H ({FORWARD_DATA_TYPE_MAP.get(data_type, '未知类型')})",
        "响应数据长度": payload_len,
        "硬件模块响应数据": bytes_to_hex(payload),
    }
    if payload_len != len(payload):
        result["说明"] = f"声明长度={payload_len}，实际长度={len(payload)}"
    return result


def parse_error_payload(f0: int, f1: int, data: bytes) -> Dict[str, Any]:
    if not data:
        return {"说明": "异常应答但无错误数据"}

    if f0 == 0x01 and f1 == 0x02 and len(data) == 1:
        return {"错误代码": f"{data[0]:02X}H ({error_name(data[0])})"}

    if f0 == 0xB0 and f1 == 0x01 and len(data) == 1:
        return {"错误代码": f"{data[0]:02X}H ({error_name(data[0])})"}

    if f0 == 0xB0 and f1 == 0x02 and len(data) == 1:
        return {"错误代码": f"{data[0]:02X}H ({error_name(data[0])})"}

    if f0 == 0xB0 and f1 in (0x03, 0x04, 0x05, 0x06) and len(data) == 2:
        module_type = data[0]
        error_code = data[1]
        return {
            "硬件模块类型": f"{module_type:02X}H ({module_type_name(module_type)})",
            "错误代码": f"{error_code:02X}H ({error_name(error_code)})",
        }

    if f0 == 0xB0 and f1 == 0x07 and len(data) >= 4:
        module_type = data[0]
        error_code = data[1]
        error_len = little_endian_u16(data[2:4])
        error_payload = data[4:]
        result = {
            "硬件模块类型": f"{module_type:02X}H ({module_type_name(module_type)})",
            "错误代码": f"{error_code:02X}H ({error_name(error_code)})",
            "错误响应数据长度": error_len,
            "硬件模块错误响应数据": bytes_to_hex(error_payload),
        }
        if error_len != len(error_payload):
            result["说明"] = f"声明长度={error_len}，实际长度={len(error_payload)}"
        return result

    return {
        "错误数据原文": bytes_to_hex(data),
        "说明": "未匹配到该功能码的异常应答结构",
    }


def parse_data_unit(f0: int, f1: int, data: bytes, control: Dict[str, Any]) -> Dict[str, Any]:
    if control["is_error_response"]:
        return parse_error_payload(f0, f1, data)

    if not data:
        if control["is_normal_response"]:
            return {"说明": "该报文为从站正常应答帧，无数据单元"}
        if control["is_request"]:
            return {"说明": "该报文为主站请求帧，无数据单元"}
        return {"说明": "无数据单元"}

    if f0 == 0x01 and f1 == 0x02:
        return parse_device_status(data)

    if f0 == 0xB0 and f1 == 0x01:
        return parse_backclip_info(data)

    if f0 == 0xB0 and f1 == 0x02:
        return parse_auto_off_time(data)

    if f0 == 0xB0 and f1 == 0x03:
        return parse_module_power_status(data)

    if f0 == 0xB0 and f1 == 0x04:
        return parse_module_power_control(data)

    if f0 == 0xB0 and f1 in (0x05, 0x06):
        return parse_comm_params(data)

    if f0 == 0xB0 and f1 == 0x07:
        if control["is_request"]:
            return parse_data_forward_request(data)
        if control["is_response"]:
            return parse_data_forward_response(data)

    return {"raw": bytes_to_hex(data)}


def parse_frame(data: bytes) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """解析背夹协议帧。"""
    if len(data) < MIN_FRAME_LEN:
        return None, f"数据太短: 至少需要{MIN_FRAME_LEN}字节，实际{len(data)}字节"

    if data[0] != FRAME_START:
        return None, f"起始符错误: 期望97H，实际{data[0]:02X}H"

    if data[11] != FRAME_SPLIT:
        return None, f"帧头分隔符错误: 期望97H，实际{data[11]:02X}H"

    if data[-1] != FRAME_END:
        return None, f"结束符错误: 期望E9H，实际{data[-1]:02X}H"

    type_bytes = data[1:5]
    mac_bytes = data[5:11]
    length_bytes = data[12:14]
    data_len = little_endian_u16(length_bytes)
    seq = data[14]
    control_byte = data[15]
    f0 = data[16]
    f1 = data[17]
    payload = data[18:-2]
    cs_received = data[-2]
    cs_calculated = sum(data[:-2]) & 0xFF

    warnings: List[str] = []
    if data_len != len(payload):
        warnings.append(f"L字段={data_len}，实际数据域长度={len(payload)}")
    if cs_received != cs_calculated:
        warnings.append(f"CS校验失败: 接收{cs_received:02X}H，计算{cs_calculated:02X}H")

    type_info = decode_type(type_bytes)
    control = decode_control(control_byte)
    data_unit_parsed = parse_data_unit(f0, f1, payload, control)

    result: Dict[str, Any] = {
        "frame_start": f"{data[0]:02X}H",
        "device_type_raw": type_info["raw"],
        "device_type_compact": type_info["raw_compact"],
        "device_type_features": type_info["features"],
        "device_type_display": type_info["display"],
        "mac_raw_order": bytes_to_hex(mac_bytes),
        "mac_display": ":".join(f"{b:02X}" for b in reversed(mac_bytes)),
        "frame_split": f"{data[11]:02X}H",
        "length_raw": bytes_to_hex(length_bytes),
        "data_len": data_len,
        "seq": seq,
        "control": control,
        "f0": f0,
        "f1": f1,
        "fn_name": get_fn_name(f0, f1),
        "fn_raw": f"{f0:02X}{f1:02X}H",
        "data_unit_raw": bytes_to_hex(payload),
        "data_unit": payload,
        "data_unit_parsed": data_unit_parsed,
        "cs": {
            "received": f"{cs_received:02X}H",
            "calculated": f"{cs_calculated:02X}H",
            "valid": cs_received == cs_calculated,
        },
        "end": f"{data[-1]:02X}H",
        "warnings": warnings,
        "is_error_response": control["is_error_response"],
    }
    return result, None


def format_result_text(result: Dict[str, Any]) -> str:
    """格式化输出解析结果。"""
    control = result["control"]
    lines: List[str] = []

    lines.append("=" * 72)
    lines.append(" 背夹通信协议报文解析结果")
    lines.append("=" * 72)

    lines.append("")
    append_kv_block(
        lines,
        "【帧头】",
        [
            ("起始符", result["frame_start"]),
            ("设备功能 TYPE", f"{result['device_type_raw']} ({result['device_type_display']})"),
            ("MAC(原始传输序)", result["mac_raw_order"]),
            ("MAC(常规显示)", result["mac_display"]),
            ("帧头分隔符", result["frame_split"]),
            ("数据域长度 L", f"{result['data_len']} 字节 ({result['length_raw']}, 小端)"),
            ("帧序号 SEQ", f"{result['seq']:02X}H ({result['seq']})"),
        ],
    )

    lines.append("")
    append_kv_block(
        lines,
        "【控制码】",
        [
            ("C", control["raw"]),
            ("帧类型", control["frame_kind"]),
            ("发送方向", control["direction"]),
            ("主从角色", control["prm"]),
            ("异常应答", "是" if control["error"] else "否"),
            ("是否加密", "是" if control["encrypted"] else "否"),
            ("保留位(D3-D0)", f"0x{control['reserved_low_nibble']:X}"),
        ],
    )

    lines.append("")
    append_kv_block(
        lines,
        "【功能码】",
        [
            ("Fn", result["fn_raw"]),
            ("功能定义", result["fn_name"]),
        ],
    )

    lines.append("")
    data_rows: List[Tuple[str, Any]] = [
        ("原始数据", result["data_unit_raw"] or "(空)"),
        ("实际长度", f"{len(result['data_unit'])} 字节"),
    ]

    parsed = result.get("data_unit_parsed", {})
    if parsed:
        for key, value in parsed.items():
            data_rows.append((key, value))
    append_kv_block(lines, "【数据单元】", data_rows)

    lines.append("")
    append_kv_block(
        lines,
        "【帧尾】",
        [
            (
                "校验CS",
                f"{result['cs']['received']} (计算: {result['cs']['calculated']}) "
                f"{'OK' if result['cs']['valid'] else 'FAIL'}",
            ),
            ("结束符", result["end"]),
        ],
    )

    warnings = result.get("warnings") or []
    if warnings:
        lines.append("")
        lines.append("【注意】")
        for item in warnings:
            lines.append(f"  - {item}")

    lines.append("")
    lines.append("=" * 72)
    return "\n".join(lines)


if __name__ == "__main__":
    sample_frames = [
        "97FFFFFFFFAAAAAAAAAAAA9700000340B0011AE9",
        "97FFFFFFFFAAAAAAAAAAAA9702000440B002320050E9",
        "9700800000AAAAAAAAAAAA9707003840B006090801080132002CE9",
    ]

    for hex_str in sample_frames:
        print(f"输入: {hex_str}\n")
        frame, error = parse_frame(bytes.fromhex(hex_str))
        if error:
            print(f"错误: {error}")
        else:
            print(format_result_text(frame))
        print()
