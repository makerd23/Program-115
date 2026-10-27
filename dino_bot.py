"""Use a mouse-selected screen point to detect obstacles and jump."""

from __future__ import annotations

import argparse
import time
from statistics import median
from typing import Protocol


class Screenshot(Protocol):
    width: int
    height: int

    def getpixel(self, xy: tuple[int, int]) -> tuple[int, ...]: ...


def build_background(frames: list[Screenshot]) -> list[tuple[int, int, int]]:
    """Build a per-pixel background using the median of several frames."""
    if not frames:
        raise ValueError("至少需要一張背景畫面")

    width, height = frames[0].width, frames[0].height
    if any(frame.width != width or frame.height != height for frame in frames):
        raise ValueError("背景畫面尺寸不一致")

    return [
        tuple(
            int(median(frame.getpixel((x, y))[channel] for frame in frames))
            for channel in range(3)
        )
        for y in range(height)
        for x in range(width)
    ]


def count_changed_pixels(
    current: Screenshot,
    background: list[tuple[int, int, int]],
    *,
    threshold: int = 55,
    target_colors: tuple[tuple[int, int, int], ...] = (
        (83, 83, 83),
        (172, 172, 172),
    ),
    color_tolerance: int = 20,
) -> int:
    """Detect obstacle pixels while compensating for whole-scene day/night color shifts."""
    if len(background) != current.width * current.height:
        raise ValueError("背景取樣範圍尺寸不符")
    if threshold <= 0:
        raise ValueError("顏色變化門檻必須大於 0")
    if color_tolerance < 0:
        raise ValueError("目標顏色容差不可小於 0")

    pixels = [
        current.getpixel((x, y))[:3]
        for y in range(current.height)
        for x in range(current.width)
    ]
    # Chrome changes most pixels together when the game switches between day and night.
    # Remove that common shift before counting local obstacle changes.
    scene_shift = tuple(
        median(pixels[index][channel] - background[index][channel]
               for index in range(len(background)))
        for channel in range(3)
    )

    target_color_matches = [
        any(
            max(abs(pixel[channel] - color[channel]) for channel in range(3))
            <= color_tolerance
            for color in target_colors
        )
        for pixel in pixels
    ]
    target_color_is_local = sum(target_color_matches) <= len(pixels) // 2

    changed = 0
    for index, pixel in enumerate(pixels):
        baseline = background[index]
        shift_adjusted_change = max(
            abs(pixel[channel] - scene_shift[channel] - baseline[channel])
            for channel in range(3)
        )
        if shift_adjusted_change >= threshold or (
            target_color_is_local and target_color_matches[index]
        ):
            changed += 1
    return changed


class ObstacleTrigger:
    def __init__(self, *, minimum_changed_pixels: int = 3, clear_frames: int = 3):
        if minimum_changed_pixels <= 0 or clear_frames <= 0:
            raise ValueError("偵測像素數與重置影格數必須大於 0")
        self.minimum_changed_pixels = minimum_changed_pixels
        self.clear_frames = clear_frames
        self.armed = True
        self.clear_count = 0

    def update(self, changed_pixels: int) -> bool:
        if changed_pixels >= self.minimum_changed_pixels:
            self.clear_count = 0
            if self.armed:
                self.armed = False
                return True
            return False

        if not self.armed:
            self.clear_count += 1
            if self.clear_count >= self.clear_frames:
                self.armed = True
        return False


def sensor_region(
    x: int,
    y: int,
    *,
    lookahead: int = 60,
    radius: int = 5,
) -> tuple[int, int, int, int]:
    """Place the sensor ahead of the selected collision point."""
    if lookahead < 0 or radius < 0:
        raise ValueError("提前距離與取樣半徑不可小於 0")
    return (x + lookahead - radius, y - radius, radius * 2 + 1, radius * 2 + 1)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="以滑鼠指定位置提前偵測障礙並跳躍。")
    parser.add_argument(
        "--lookahead",
        type=int,
        default=60,
        help="相對滑鼠位置向右提前偵測的像素數（預設：60）",
    )
    parser.add_argument(
        "--radius",
        type=int,
        default=5,
        help="取樣區域半徑（預設：5，區域為 11x11）",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.lookahead < 0 or args.radius < 0:
        raise SystemExit("--lookahead 與 --radius 不可小於 0")

    try:
        import pyautogui
    except ImportError as exc:
        raise SystemExit(
            "找不到 pyautogui。請在 iem_python 環境執行："
            " conda install -c conda-forge pyautogui"
        ) from exc

    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0

    print("先點一下恐龍遊戲，讓 Chrome 取得焦點。")
    print("將滑鼠放在你原本希望觸發跳躍的位置（例如 450, 644）。")
    print(f"偵測器會在該位置右側 {args.lookahead} 像素處偵測。")
    print("5 秒後固定位置並取樣背景；倒數期間不要移動滑鼠。")
    time.sleep(5)

    x, y = pyautogui.position()
    radius = args.radius
    screen_width, screen_height = pyautogui.size()
    region = sensor_region(x, y, lookahead=args.lookahead, radius=radius)
    if (
        region[0] < 0
        or region[1] < 0
        or region[0] + region[2] > screen_width
        or region[1] + region[3] > screen_height
    ):
        raise SystemExit("取樣點太靠近螢幕邊緣，請重新執行並將滑鼠移到畫面內側")

    sensor_x = x + args.lookahead
    print(f"跳躍參考座標：({x}, {y})；偵測座標：({sensor_x}, {y})")
    print(f"取樣區域：{region}")
    print("正在記錄背景，請保持遊戲畫面與滑鼠不動...")
    frames = []
    for _ in range(9):
        frames.append(pyautogui.screenshot(region=region))
        time.sleep(0.03)
    background = build_background(frames)
    trigger = ObstacleTrigger()

    print("背景已記錄。開始偵測；每個障礙只會觸發一次。")
    pyautogui.press("space")

    last_report = 0.0
    try:
        while True:
            pyautogui.failSafeCheck()
            current = pyautogui.screenshot(region=region)
            changed_pixels = count_changed_pixels(current, background)
            if trigger.update(changed_pixels):
                pyautogui.press("space")
                print(
                    f"\n偵測到障礙：座標 ({sensor_x}, {y}) 附近有 "
                    f"{changed_pixels} 個變化像素，已跳躍。"
                )

            now = time.monotonic()
            if now - last_report >= 0.5:
                center_rgb = current.getpixel((radius, radius))
                print(
                    f"\r偵測點 ({sensor_x}, {y})｜中心 RGB {center_rgb}｜"
                    f"變化像素 {changed_pixels}    ",
                    end="",
                    flush=True,
                )
                last_report = now
            time.sleep(0.005)
    except KeyboardInterrupt:
        print("\n已停止自動跳躍。")
    except pyautogui.FailSafeException:
        print("\n已將滑鼠移至左上角，停止自動跳躍。")


if __name__ == "__main__":
    main()
