import unittest

from workout_tracking import (
    calculate_progression,
    canonical_exercise_key,
    canonical_muscle_group,
)


class WorkoutTrackingTests(unittest.TestCase):
    def test_normalizes_muscle_groups(self):
        self.assertEqual(canonical_muscle_group("Грудь"), "chest")
        self.assertEqual(canonical_muscle_group("Спина"), "back")
        self.assertEqual(canonical_muscle_group("Плечи"), "shoulders")
        self.assertEqual(canonical_muscle_group("Трицепс"), "arms")
        self.assertEqual(canonical_muscle_group("Legs"), "legs")
        self.assertEqual(canonical_muscle_group("Core"), "core")

    def test_prefers_stable_sys_id(self):
        self.assertEqual(
            canonical_exercise_key("Bench_Press", "Жим лёжа"),
            "bench_press",
        )

    def test_increases_after_all_sets_reach_top_of_range(self):
        result = calculate_progression(
            working_sets=[
                {"completed": True, "set_type": "working", "reps": 12, "weight_kg": 60},
                {"completed": True, "set_type": "working", "reps": 12, "weight_kg": 60},
                {"completed": True, "set_type": "working", "reps": 13, "weight_kg": 60},
            ]
        )
        self.assertEqual(result["decision"], "increase")
        self.assertEqual(result["next_weight"], 62.5)
        self.assertEqual(result["failed_streak"], 0)

    def test_holds_after_first_failed_session_and_decreases_after_second(self):
        sets = [
            {"completed": True, "set_type": "working", "reps": 6, "weight_kg": 60},
            {"completed": True, "set_type": "working", "reps": 7, "weight_kg": 60},
            {"completed": True, "set_type": "working", "reps": 8, "weight_kg": 60},
        ]
        first = calculate_progression(working_sets=sets, previous_streak=0)
        self.assertEqual(first["decision"], "hold_after_first_failure")
        self.assertEqual(first["next_weight"], 60)
        self.assertEqual(first["failed_streak"], 1)

        second = calculate_progression(working_sets=sets, previous_streak=1)
        self.assertEqual(second["decision"], "decrease")
        self.assertEqual(second["next_weight"], 57.5)
        self.assertEqual(second["failed_streak"], 0)

    def test_warmups_do_not_affect_progression(self):
        result = calculate_progression(
            working_sets=[
                {"completed": True, "set_type": "warmup", "reps": 20, "weight_kg": 20},
                {"completed": True, "set_type": "working", "reps": 12, "weight_kg": 60},
                {"completed": True, "set_type": "working", "reps": 12, "weight_kg": 60},
            ]
        )
        self.assertEqual(result["decision"], "increase")
        self.assertEqual(result["next_weight"], 62.5)

    def test_bodyweight_exercise_does_not_add_external_weight(self):
        result = calculate_progression(
            working_sets=[
                {"completed": True, "set_type": "working", "reps": 12, "weight_kg": 0},
                {"completed": True, "set_type": "working", "reps": 12, "weight_kg": 0},
            ]
        )
        self.assertEqual(result["decision"], "bodyweight")
        self.assertEqual(result["next_weight"], 0)

    def test_incomplete_sets_are_ignored(self):
        result = calculate_progression(
            working_sets=[
                {"completed": False, "set_type": "working", "reps": 12, "weight_kg": 60},
            ]
        )
        self.assertEqual(result["decision"], "no_sets")
        self.assertIsNone(result["next_weight"])


if __name__ == "__main__":
    unittest.main()
