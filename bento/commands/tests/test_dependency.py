from bento.compat.api.moves \
    import \
        unittest

from bento.commands.dependency \
    import \
        CommandScheduler

class TestCommandScheduler(unittest.TestCase):
    def test_simple(self):
        scheduler = CommandScheduler()
        scheduler.set_before("task2", "task1")
        scheduler.set_after("task2", "task3")
        scheduler.set_after("task2", "task4")
        scheduler.set_before("task4", "task3")

        tasks = scheduler.order("task4")
        self.assertEqual(tasks, ["task1", "task2", "task3"])

    def test_cycle(self):
        scheduler = CommandScheduler()
        scheduler.set_before("task2", "task1")
        scheduler.set_before("task1", "task2")

        self.assertRaises(ValueError, lambda: scheduler.order("task1"))
