"""Checks for the unified bridge's BMS shutdown handling.

Run: python -m unittest discover -s tests
No serial hardware, no simulator and no pyserial installation is required —
`serial` is stubbed before the import.
"""
from pathlib import Path
import sys
import unittest
from unittest.mock import MagicMock, patch

for name in ('serial', 'serial.tools', 'serial.tools.list_ports'):
    sys.modules.setdefault(name, MagicMock())

TOOLS = Path(__file__).resolve().parents[1] / 'tools'
sys.path.insert(0, str(TOOLS))
import bridge


class WaitForBmsGoneTests(unittest.TestCase):
    """After run_bms returns, the wait must always end — and end for the right reason."""

    def run_wait(self, exists, flag, timeout=15.0):
        """`exists` / `flag` are the successive answers each probe gives."""
        exists_calls = list(exists)
        flag_calls = list(flag)
        slept = []
        with patch.object(bridge, 'shm_exists', side_effect=exists_calls), \
                patch.object(bridge, 'exit_flag_set', side_effect=flag_calls), \
                patch.object(bridge.time, 'sleep', slept.append), \
                patch('builtins.print'):
            bridge.wait_for_bms_gone(timeout)
        return slept

    def test_returns_once_the_section_is_gone(self):
        slept = self.run_wait(exists=[True, True, False], flag=[True, True])
        self.assertEqual(slept, [0.5, 0.5])

    def test_a_restarted_bms_ends_the_wait_instead_of_hanging(self):
        # The name is back because a NEW session created it; its IsExitGame is clear.
        slept = self.run_wait(exists=[True, True], flag=[True, False])
        self.assertEqual(slept, [0.5])

    def test_a_section_that_never_goes_away_times_out(self):
        # Another BMS tool holds a handle, so the name outlives BMS forever.
        with patch.object(bridge, 'shm_exists', return_value=True), \
                patch.object(bridge, 'exit_flag_set', return_value=True), \
                patch.object(bridge.time, 'sleep'), \
                patch('builtins.print'):
            bridge.wait_for_bms_gone(timeout=0.3)   # returns rather than looping forever

    def test_exit_flag_is_read_without_keeping_the_section(self):
        view = MagicMock()
        view.open.return_value = True
        view.flag.return_value = True
        with patch.object(bridge, 'ShmView', return_value=view):
            self.assertTrue(bridge.exit_flag_set())
        view.close.assert_called_once()
        view.flag.assert_called_once_with(bridge.OFF_IV_IS_EXIT_GAME)

    def test_a_missing_intellivibe_section_reads_as_not_exiting(self):
        view = MagicMock()
        view.open.return_value = False
        with patch.object(bridge, 'ShmView', return_value=view):
            self.assertFalse(bridge.exit_flag_set())
        view.flag.assert_not_called()


class ShmViewTests(unittest.TestCase):
    def test_opening_a_missing_section_never_creates_one(self):
        name = 'RedkiteSectionThatDoesNotExist'
        self.assertFalse(bridge.shm_exists(name))
        view = bridge.ShmView(name, 64)
        self.assertFalse(view.open())
        # mmap(-1, tagname=...) would have created it here; OpenFileMapping must not.
        self.assertFalse(bridge.shm_exists(name))
        view.close()

    def test_close_releases_the_name(self):
        import mmap
        name = 'RedkiteSectionLifetimeTest'
        creator = mmap.mmap(-1, 64, tagname=name)
        try:
            view = bridge.ShmView(name, 64)
            self.assertTrue(view.open())
            self.assertTrue(bridge.shm_exists(name))
            creator.close()                      # the "simulator" exits
            # Our own handle still keeps the name findable — this is exactly what
            # made the old bridge unable to notice BMS going away.
            self.assertTrue(bridge.shm_exists(name))
            view.close()
            self.assertFalse(bridge.shm_exists(name))
        finally:
            try:
                creator.close()
            except Exception:
                pass


if __name__ == '__main__':
    unittest.main()
