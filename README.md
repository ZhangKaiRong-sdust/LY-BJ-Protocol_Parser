# LY-BJ-Protocol Parser

背夹通信协议解析工具，基于 `Q/GDW XXXXX-2022` 附录 D，对手机背夹协议报文进行解析，并提供简单的 Tkinter 图形界面。

## 当前内容

- `protocol_parser.py`
  - 协议核心解析模块
  - 提供 `parse_hex_string()`、`parse_frame()`、`format_result_text()` 接口
- `bj_protocol_parser_gui.py`
  - Tkinter 图形界面
  - 支持粘贴十六进制报文并显示解析结果
- `bj_protocol_parser.docx`
  - 协议参考文档
- 其他 `compare_*.py`、`parse_*.py`、`analyze_*.py`
  - 当前用于样例分析和协议比对

## 已支持的解析范围

- 基础帧结构解析
- `F0=0x01, F1=0x02` 设备状态
- `F0=0xB0`
  - `F1=0x01` 获取背夹信息
  - `F1=0x02` 设置背夹不交互自动关闭时间
  - `F1=0x03` 获取模块电源状态
  - `F1=0x04` 模块电源开启关闭
  - `F1=0x05` 获取模块通讯参数
  - `F1=0x06` 设置模块通讯参数
  - `F1=0x07` 模块数据转发

## 帧结构

当前代码按以下样例帧结构解析：

```text
97H | TYPE(4) | MAC(6) | 97H | L(2) | SEQ | C | Fn(2) | DATA | CS | E9H
```

说明：

- `TYPE` 为 4 字节设备功能位图
- `MAC` 为 6 字节背夹蓝牙 MAC
- `L` 为 2 字节小端数据域长度
- `Fn` 为 2 字节功能码
- `CS` 为从首字节到数据域末尾的模 256 累加和

## 运行方式

### 启动 GUI

```bash
python bj_protocol_parser_gui.py
```

### 命令行中直接调用解析器

```python
from protocol_parser import parse_frame, format_result_text

hex_str = "97FFFFFFFFAAAAAAAAAAAA9700000340B0011AE9"
result, error = parse_frame(bytes.fromhex(hex_str))

if error:
    print(error)
else:
    print(format_result_text(result))
```

## 长度校验说明

部分功能码按协议严格校验数据区长度。

例如 `B006` 按文档 D.32 要求必须为 8 字节数据单元；若实际长度不符，解析结果会返回：

- `数据非法`
- 当前报文数据区长度
- 协议要求长度

## 后续可扩展方向

- 补齐更多 `F0/F1` 功能码解析
- 增强异常应答解析
- GUI 增加字段化展示、样例库和导出功能
- 增加测试用例
