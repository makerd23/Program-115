import unittest

from dino_bot import (
    ObstacleTrigger,
    build_background,
    count_changed_pixels,
    sensor_region,
)


class FakeScreenshot:
    def __init__(self, width: int, height: int, color: tuple[int, int, int]):
        self.width = width
        self.height = height
        self.color = color
        self.pixels: dict[tuple[int, int], tuple[int, int, int]] = {}

    def getpixel(self, xy: tuple[int, int]) -> tuple[int, int, int]:
        return self.pixels.get(xy, self.color)


class BackgroundDetectionTests(unittest.TestCase):
    def test_builds_median_background_from_frames(self) -> None:
        first = FakeScreenshot(2, 1, (255, 255, 255))
        second = FakeScreenshot(2, 1, (255, 255, 255))
        third = FakeScreenshot(2, 1, (255, 255, 255))
        first.pixels[(0, 0)] = (20, 20, 20)
        second.pixels[(0, 0)] = (20, 20, 20)

        self.assertEqual(
            build_background([first, second, third]),
            [(20, 20, 20), (255, 255, 255)],
        )

    def test_detects_obstacle_against_background(self) -> None:
        background_frame = FakeScreenshot(5, 5, (255, 255, 255))
        background = build_background([background_frame] * 3)
        current = FakeScreenshot(5, 5, (255, 255, 255))
        current.pixels[(1, 1)] = (83, 83, 83)
        current.pixels[(2, 1)] = (83, 83, 83)
        current.pixels[(3, 1)] = (83, 83, 83)

        self.assertEqual(count_changed_pixels(current, background), 3)

    def test_does_not_detect_unchanged_background(self) -> None:
        frame = FakeScreenshot(5, 5, (255, 255, 255))
        background = build_background([frame] * 3)

        self.assertEqual(count_changed_pixels(frame, background), 0)

    def test_tolerates_small_color_variation(self) -> None:
        background_frame = FakeScreenshot(5, 5, (255, 255, 255))
        background = build_background([background_frame] * 3)
        current = FakeScreenshot(5, 5, (255, 255, 255))
        current.pixels[(1, 1)] = (220, 220, 220)

        self.assertEqual(count_changed_pixels(current, background), 0)

    def test_detects_night_mode_obstacle_color_172(self) -> None:
        frame = FakeScreenshot(5, 5, (83, 83, 83))
        background = build_background([frame] * 3)
        current = FakeScreenshot(5, 5, (83, 83, 83))
        for x in range(1, 4):
            current.pixels[(x, 2)] = (172, 172, 172)

        self.assertEqual(count_changed_pixels(current, background), 3)

    def test_ignores_uniform_day_night_color_shift(self) -> None:
        day = FakeScreenshot(5, 5, (83, 83, 83))
        background = build_background([day] * 3)
        night = FakeScreenshot(5, 5, (172, 172, 172))

        self.assertEqual(count_changed_pixels(night, background), 0)

    def test_rejects_mismatched_background_size(self) -> None:
        frame = FakeScreenshot(5, 5, (255, 255, 255))

        with self.assertRaises(ValueError):
            count_changed_pixels(frame, [(255, 255, 255)])


class ObstacleTriggerTests(unittest.TestCase):
    def test_triggers_once_per_obstacle_then_rearms_after_clear(self) -> None:
        trigger = ObstacleTrigger(minimum_changed_pixels=3, clear_frames=2)

        self.assertTrue(trigger.update(4))
        self.assertFalse(trigger.update(4))
        self.assertFalse(trigger.update(0))
        self.assertFalse(trigger.update(0))
        self.assertTrue(trigger.update(4))

    def test_does_not_retrigger_while_obstacle_remains_in_sample(self) -> None:
        trigger = ObstacleTrigger(minimum_changed_pixels=3, clear_frames=3)

        self.assertTrue(trigger.update(6))
        for _ in range(10):
            self.assertFalse(trigger.update(6))


class SensorRegionTests(unittest.TestCase):
    def test_sensor_is_ahead_of_selected_jump_point(self) -> None:
        self.assertEqual(
            sensor_region(450, 644),
            (505, 639, 11, 11),
        )

    def test_lookahead_and_radius_can_be_adjusted(self) -> None:
        self.assertEqual(
            sensor_region(450, 644, lookahead=160, radius=3),
            (607, 641, 7, 7),
        )


if __name__ == "__main__":
    unittest.main()
