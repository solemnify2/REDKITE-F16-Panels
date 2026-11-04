"""Regression checks for the simulator file formats and physical switch positions.

Run: python -m unittest discover -s tests
No serial hardware or simulator installation is required.
"""
from pathlib import Path
import io
import sys
import unittest
from unittest.mock import MagicMock, patch
import xml.etree.ElementTree as ET

TOOLS = Path(__file__).resolve().parents[1] / 'tools'
sys.path.insert(0, str(TOOLS))
import gen_bms_setup_xml as BMS
import gen_dcs_profile as DCS
import dcs_commands
import board


class DumpParserTests(unittest.TestCase):
    def parse(self, lines):
        parser = board.DumpParser()
        for line in lines:
            parser.feed(line)
        return parser

    def test_complete_dump_and_button_128(self):
        parser = self.parse([
            'unrelated boot message',
            '#DX BEGIN device=CONSOLE pid=0x048E entries=2 total=128',
            '#DX 1 127 first', '#DX 128 1 last', '#DX END'])
        self.assertTrue(parser.done)
        self.assertEqual(parser.device, 'CONSOLE')
        self.assertEqual(parser.entries, [(1, 'first', 127), (128, 'last', 1)])

    def test_invalid_dumps_are_rejected(self):
        header = '#DX BEGIN device=CONSOLE pid=0x048E entries=2 total=2'
        cases = {
            'missing row': [header, '#DX 1 1 MPO', '#DX END'],
            'empty': [header, '#DX END'],
            'missing begin': ['#DX END'],
            'row before begin': ['#DX 1 1 MPO'],
            'duplicate begin': [header, header],
            'bad header': ['#DX BEGIN device=CONSOLE'],
            'zero total': [header.replace('entries=2 total=2', 'entries=0 total=0')],
            'overflow header': [header.replace('total=2', 'total=129')],
            'too many entries': [header.replace('entries=2', 'entries=3')],
            'zero dx': [header, '#DX 0 1 MPO'],
            'zero width': [header, '#DX 1 0 MPO'],
            'overflow row': [header, '#DX 129 1 MPO'],
            'width overflow': [header, '#DX 1 3 MPO'],
            'gap': [header, '#DX 2 1 MPO'],
            'overlap': [header, '#DX 1 1 MPO', '#DX 1 1 UHF TEST'],
            'duplicate name': [header, '#DX 1 1 MPO', '#DX 2 1 MPO'],
            'malformed row': [header, '#DX invalid'],
            'wrong total': [header.replace('total=2', 'total=3'),
                            '#DX 1 1 MPO', '#DX 2 1 UHF TEST', '#DX END'],
        }
        for label, lines in cases.items():
            with self.subTest(label=label), self.assertRaises(ValueError):
                self.parse(lines)

    def test_missing_end_remains_incomplete(self):
        parser = self.parse([
            '#DX BEGIN device=AUX pid=0x0487 entries=1 total=1', '#DX 1 1 RF'])
        self.assertFalse(parser.done)

    def test_invalid_serial_dump_prevents_both_generators_from_writing(self):
        for generator in (BMS, DCS):
            with self.subTest(generator=generator.__name__):
                serial = MagicMock()
                port = serial.Serial.return_value.__enter__.return_value
                port.readline.side_effect = [
                    b'#DX BEGIN device=CONSOLE pid=0x048E entries=2 total=2\n',
                    b'#DX 1 1 MPO\n', b'#DX END\n']
                with patch.object(board, '_require_serial', return_value=serial), \
                        patch.object(board, 'find_boards', return_value=[('COM7', 'CONSOLE')]), \
                        patch.object(board, 'next_out') as next_out, \
                        patch.object(sys, 'argv', ['generator']), \
                        self.assertRaisesRegex(SystemExit, 'COM7:'):
                    generator.main()
                next_out.assert_not_called()


class BmsProfileTests(unittest.TestCase):
    def test_todo_is_empty_but_real_unknown_callback_still_fails(self):
        mapping = {'MPO': [BMS.bms_callbacks.TODO]}
        dxmap, missing = BMS.build_map([(1, 'MPO', 1)], mapping, {}, 'CONSOLE')
        self.assertEqual(missing, [])
        self.assertEqual(dxmap[1], [BMS.EMPTY] * 4)
        with self.assertRaises(SystemExit):
            BMS.build_map([(1, 'MPO', 1)], {'MPO': ['SimTypo']}, {}, 'CONSOLE')

    def test_todo_is_reported_by_cli(self):
        stderr = io.StringIO()
        with patch.object(board, 'find_boards', return_value=[('COM7', 'CONSOLE')]), \
                patch.object(board, 'query_board', return_value=('CONSOLE', [(1, 'MPO', 1)])), \
                patch.object(board, 'load_catalog', return_value={}), \
                patch.dict(BMS.bms_callbacks.MAPS, {'CONSOLE': {'MPO': [BMS.bms_callbacks.TODO]}}), \
                patch('builtins.open', unittest.mock.mock_open()), \
                patch.object(sys, 'stderr', stderr), \
                patch.object(sys, 'argv', ['generator']):
            self.assertEqual(BMS.main(), 0)
        self.assertIn('TODO', stderr.getvalue())
        self.assertIn('DX 1 MPO', stderr.getvalue())

    def test_profile_hierarchy_and_button_edges(self):
        catalog = {'SimMPO': (115, ''), 'SimEpuOff': (316, ''),
                   'SimEpuOn': (316, ''), 'SimEpuAuto': (317, '')}
        entries = [(1, 'MPO', 1), (57, 'EPU', 2)]
        mapping = {'MPO': ['SimMPO'],
                   'EPU': [('SimEpuOff', 'SimEpuAuto'),
                           ('SimEpuOn', 'SimEpuAuto')]}
        dxmap, missing = BMS.build_map(entries, mapping, catalog, 'CONSOLE')
        self.assertEqual(missing, [])
        for device in ('CONSOLE', 'AUX'):
            with self.subTest(device=device):
                root = ET.fromstring(BMS.render(device, dxmap))
                self.assertEqual([x.tag for x in root], [
                    'detentPosition', 'axis', 'pov', 'dx',
                    'profileDefaultF16', 'profileF15ABCD'])
                self.assertEqual(len(root.findall('axis/AxAssgn')), 8)
                for parent in (root, root.find('profileDefaultF16'),
                               root.find('profileF15ABCD')):
                    self.assertEqual(len(parent.findall('pov')), 1)
                    self.assertEqual(len(parent.findall('dx')), 1)
                    self.assertEqual(len(parent.findall('pov/PovAssgn')), 4)
                    buttons = parent.findall('dx/DxAssgn')
                    self.assertEqual(len(buttons), 128)
                    self.assertTrue(all(len(b.findall('assign/Assgn')) == 4
                                        for b in buttons))
                for path in ('dx', 'profileDefaultF16/dx'):
                    buttons = root.findall(path + '/DxAssgn')
                    self.assertEqual(buttons[0].findtext('assign/Assgn/Callback'),
                                     'SimMPO')
                    for index, callback in ((56, 'SimEpuOff'), (57, 'SimEpuOn')):
                        slots = buttons[index].findall('assign/Assgn')
                        self.assertEqual(slots[0].findtext('Callback'), callback)
                        self.assertEqual(slots[0].findtext('Invoke'), 'Default')
                        self.assertEqual(slots[2].findtext('Callback'), 'SimEpuAuto')
                        self.assertEqual(slots[2].findtext('Invoke'), 'Down')
                        self.assertEqual(slots[2].findtext('SoundID'), '317')
                self.assertTrue(all(x.text == 'SimDoNothing' for x in root.findall(
                    'profileF15ABCD/dx/DxAssgn/assign/Assgn/Callback')))


class DcsSwitchTests(unittest.TestCase):
    def test_cli_explains_how_to_load_each_device_profile(self):
        stderr = io.StringIO()
        with patch.object(board, 'find_boards', return_value=[('COM7', 'CONSOLE')]), \
                patch.object(board, 'query_board', return_value=('CONSOLE', [(1, 'MPO', 1)])), \
                patch.object(DCS, 'load_catalog', return_value=({}, {})), \
                patch('builtins.open', unittest.mock.mock_open()), \
                patch.object(sys, 'stderr', stderr), \
                patch.object(sys, 'argv', ['generator']):
            self.assertEqual(DCS.main(), 0)
        self.assertIn('F16 LEFT CONSOLE', stderr.getvalue())
        self.assertIn('Load Profile...', stderr.getvalue())
        self.assertIn('Save Profile As...', stderr.getvalue())
        self.assertNotIn('Copy-Item', stderr.getvalue())

    @classmethod
    def setUpClass(cls):
        cls.names, _ = DCS.load_catalog()

    def assignments(self, device, entries):
        commands, todo, missing = DCS.collect(entries, dcs_commands.MAPS[device], device)
        self.assertEqual(todo, [])
        self.assertEqual(missing, [])
        return {key: self.names[command] for command, keys in commands.items()
                for key in keys}

    def test_uhf_knob_positions(self):
        keys = self.assignments('CONSOLE', [(16, 'UHF FUNCTION', 4), (20, 'UHF MODE', 3)])
        for dx, position in enumerate(('OFF', 'MAIN', 'BOTH', 'ADF'), 16):
            self.assertEqual(keys['JOY_BTN%d' % dx], 'UHF Function Knob - ' + position)
        for dx, position in enumerate(('MANUAL', 'PRESET', 'GUARD'), 20):
            self.assertEqual(keys['JOY_BTN%d' % dx], 'UHF Mode Knob - ' + position)

    def test_epu_positions_and_center(self):
        keys = self.assignments('CONSOLE', [(57, 'EPU', 2)])
        self.assertEqual(keys['JOY_BTN57'], 'EPU Switch - OFF')
        self.assertEqual(keys['JOY_BTN58'], 'EPU Switch - ON')
        for dx in (57, 58):
            self.assertEqual(keys['JOY_BTN%d_OFF' % dx], 'EPU Switch - NORM')

    def test_cmds_category_switches(self):
        entries = [(32 + i, 'CMDS ' + category, 1)
                   for i, category in enumerate(('O1', 'O2', 'CH', 'FL'))]
        keys = self.assignments('AUX', entries)
        for dx, category in enumerate(('O1', 'O2', 'CH', 'FL'), 32):
            self.assertEqual(keys['JOY_BTN%d' % dx],
                             category + ' Expendable Category Switch - ON')
            self.assertEqual(keys['JOY_BTN%d_OFF' % dx],
                             category + ' Expendable Category Switch - OFF')


if __name__ == '__main__':
    unittest.main()
