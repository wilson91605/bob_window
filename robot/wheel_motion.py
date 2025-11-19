# -*- coding: utf-8 -*-
"""
用法：
    from wheel_motion import WheelMotion

    robot = Dynamixel("COM6", 115200)
    robot.open()

    wm = WheelMotion(robot, motion_table_path="wheel.csv",
                     wheel_ids=(11,12,13,14),
                     dir_cal={11:+1,12:+1,13:+1,14:+1})
    wm.move("右橫移", 160, duration=0.8)   # 跑 0.8 秒後自動煞停
    wm.move("直走", 120)                   # 持續動
    wm.stop()
"""

from __future__ import annotations
import time
from pathlib import Path
from typing import Dict, Iterable, Tuple


DirectionMap = Dict[int, int]  # servoId -> {-1,0,+1}

class WheelMotion:
    def __init__(
        self,
        robot,
        motion_table_path: str,
        wheel_ids: Iterable[int] = (11, 12, 13, 14),
        dir_cal: Dict[int, int] | None = None,
        encoding: str = "utf-8",
    ):
        """
        robot: 需具備 setVelocity(servoId=int, velocity=int) 的物件
        motion_table_path: 走路方式表 CSV 路徑（動作名 + 4 行 "id,方向"）
        wheel_ids: 四個輪子的 servo ID 順序
        dir_cal: 方向校正（接線顛倒時改為 -1），預設全 +1
        """
        self.robot = robot
        self.wheel_ids = tuple(wheel_ids)
        self.dir_cal = {sid: 1 for sid in self.wheel_ids}
        if dir_cal:
            self.dir_cal.update({int(k): (1 if v >= 0 else -1) for k, v in dir_cal.items()})

        self.encoding = encoding
        self.table_path = Path(motion_table_path)
        self._table: Dict[str, DirectionMap] = {}
        self.reload()

    # ---------------- Public API ----------------

    def reload(self) -> None:
        """重新載入走路方式表。"""
        self._table = self._load_motion_table(self.table_path, self.encoding)

    def move(self, action: str, speed: int, duration: float | None = None) -> None:
        """
        讓四輪依照指定動作移動。
        action: 走路方式名稱（中文/英文，需存在於 CSV 表中）
        speed: 速度（正數整數；方向由表決定）
        duration: 若給值（秒），在時間到會自動 stop()
        """
        if not action:
            return
        action_key = self._norm_action(action)
        mapping = self._table.get(action_key)
        if mapping is None:
            raise ValueError(f"走路方式 '{action}' 不在走路方式表（鍵名以空白移除後比對）")

        spd = int(speed)
        for sid in self.wheel_ids:
            sign = int(mapping.get(sid, 0))
            cal = self.dir_cal.get(sid, 1)
            self.robot.setVelocity(servoId=int(sid), velocity=spd * sign * cal)

        if duration and duration > 0:
            time.sleep(float(duration))
            self.stop()
    def enable (self) -> None:
        for sid in self.wheel_ids:
            try:
                self.robot.enableTorque(servoId=int(sid), enable = 1)
            except:
                pass

    def disable (self) -> None:
        for sid in self.wheel_ids:
            try:
                self.robot.enableTorque(servoId=int(sid), enable = 0)
            except:
                pass

    def stop(self) -> None:
        """四輪全停。"""
        for sid in self.wheel_ids:
            self.robot.setVelocity(servoId=int(sid), velocity=0)

    def set_calibration(self, sid: int, sign: int) -> None:
        """動態調整單輪方向校正（+1/-1）。"""
        if sid not in self.dir_cal:
            raise ValueError(f"未知的輪子 ID: {sid}")
        self.dir_cal[sid] = 1 if sign >= 0 else -1

    # ---------------- Internal helpers ----------------

    @staticmethod
    def _norm_action(name: str) -> str:
        # 移除所有空白做比對，大小寫不敏感
        return "".join(str(name).split()).lower()

    @staticmethod
    def _dir_to_sign(token: str) -> int:
        t = (token or "").strip().lower()
        if t in ("正", "+", "pos", "1", "+1"):
            return +1
        if t in ("負", "-", "neg", "-1"):
            return -1
        return 0

    def _load_motion_table(self, path: Path, encoding: str) -> Dict[str, DirectionMap]:
        """
        解析格式：
            動作名稱
            11,正
            12,負
            13,正
            14,負
            （下一個動作名稱 ...）
        回傳 dict：{ norm_action -> {sid: sign, ...} }
        """
        if not path.exists():
            raise FileNotFoundError(path)
        table: Dict[str, DirectionMap] = {}
        current_name: str | None = None

        with path.open("r", encoding=encoding) as f:
            for raw in f:
                line = raw.strip()
                if not line:
                    continue
                if "," not in line:
                    # 動作標題行
                    current_name = self._norm_action(line)
                    if current_name in table:
                        # 同名動作覆寫
                        pass
                    table[current_name] = {}
                    continue

                if current_name is None:
                    raise ValueError(f"表格格式錯誤：在沒有動作標題時遇到資料列：{line}")

                # 解析 "id,方向"
                try:
                    sid_str, dir_str = [x.strip() for x in line.split(",", 1)]
                    sid = int(sid_str)
                except Exception:
                    raise ValueError(f"行格式錯誤：{line}")

                table[current_name][sid] = self._dir_to_sign(dir_str)

        # 補齊缺漏的輪子（預設 0，不動）
        for name, mapping in table.items():
            for sid in self.wheel_ids:
                mapping.setdefault(sid, 0)
        return table
