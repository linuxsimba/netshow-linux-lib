# http://pylint-messages.wikidot.com/all-codes
# attribute defined outside init
# pylint: disable=W0201
# pylint: disable=R0913
# disable unused argument
# pylint: disable=W0613
# disable docstring checking
# pylint: disable=C0111
# disable checking no-self-use
# pylint: disable=R0201
# pylint: disable=W0212
# disable invalid name
# pylint: disable=C0103
# pylint: disable=F0401
# pylint: disable=E0611
# pylint: disable=W0611

import netshow.linux.print_bridge as print_bridge
import netshowlib.linux.bridge as linux_bridge
import mock
from asserts import assert_equals, mod_args_generator
from nose.tools import set_trace
import re


class TestPrintBridgeMember(object):
    def setup(self):
        iface = linux_bridge.BridgeMember('eth22')
        self.piface = print_bridge.PrintBridgeMember(iface)

    @mock.patch('netshow.linux.print_bridge.PrintBridgeMember.cli_header')
    @mock.patch('netshow.linux.print_bridge.PrintBridgeMember.bridgemem_details')
    @mock.patch('netshow.linux.print_bridge.PrintBridgeMember.lldp_details')
    def test_cli_output(self, mock_lldp, mock_details, mock_cli_header):
        mock_cli_header.return_value = 'cli_header'
        mock_details.return_value = 'bridgemem_details'
        mock_lldp.return_value = 'lldp'
        assert_equals(self.piface.cli_output(), 'cli_header\n\nbridgemem_details\n\nlldp\n\n')



    @mock.patch('netshow.linux.print_iface.linux_iface.Iface.is_trunk')
    def test_port_category(self, mock_is_trunk):
        # if trunk
        mock_is_trunk.return_value = True
        assert_equals(self.piface.port_category, 'trunk/l2')
        # if not trunk
        mock_is_trunk.return_value = False
        assert_equals(self.piface.port_category, 'access/l2')

    @mock.patch('netshow.linux.print_bridge.PrintBridgeMember.trunk_summary')
    @mock.patch('netshow.linux.print_bridge.PrintBridgeMember.access_summary')
    @mock.patch('netshow.linux.print_iface.linux_iface.Iface.is_trunk')
    def test_summary(self, mock_is_trunk, mock_access_summary,
                     mock_trunk_summary):
        mock_trunk_summary.return_value = 'trunk summary'
        mock_access_summary.return_value = 'access summary'
        # if trunk
        mock_is_trunk.return_value = True
        assert_equals(self.piface.summary, 'trunk summary')
        # if access
        mock_is_trunk.return_value = False
        assert_equals(self.piface.summary, 'access summary')

    @mock.patch('netshowlib.linux.bridge.os.listdir')
    @mock.patch('netshowlib.linux.common.read_file_oneline')
    @mock.patch('netshowlib.linux.iface.os.path.exists')
    @mock.patch('netshowlib.linux.common.read_symlink')
    def test_bridgemem_details(self, mock_symlink, mock_os_path,
                               mock_oneline, mock_os_listdir):
        mock_subint = mock.MagicMock()
        mock_subint.return_value = ['eth22.11', 'eth22.20',
                                    'eth22.40', 'eth22.30']
        self.piface.iface.get_sub_interfaces = mock_subint
        values22 = {
            '/sys/class/net/br10/brif': ['eth22', 'eth33', 'eth44'],
            '/sys/class/net/br30/brif': ['eth22.30', 'eth1.30', 'eth2'],
            '/sys/class/net/br11/brif': ['eth22.11', 'eth1.11', 'eth4'],
            '/sys/class/net/br40/brif': ['eth22.40', 'eth1.40', 'eth12']
        }
        mock_os_listdir.side_effect = mod_args_generator(values22)
        self.piface.iface.get_sub_interfaces = mock_subint
        # bridgemember is trunk port
        values = {
            '/sys/class/net/eth22/brport': True,
            '/sys/class/net/eth22.11/brport': True,
            '/sys/class/net/eth22.20/brport': False,
            '/sys/class/net/eth22.30/brport': True,
            '/sys/class/net/eth22.40/brport': True,
        }
        values2 = {
            '/sys/class/net/eth22/brport/state': '3',
            '/sys/class/net/eth22/brport/bridge/bridge/root_port': 'aaa',
            '/sys/class/net/eth22/brport/port_id': 'aaa',
            '/sys/class/net/eth22/brport/bridge/bridge/stp_state': '1',
            '/sys/class/net/eth22.11/brport/state': '4',
            '/sys/class/net/eth22.11/brport/bridge/bridge/stp_state': '1',
            '/sys/class/net/eth22.11/brport/bridge/bridge/root_port': 'aaa',
            '/sys/class/net/eth22.11/brport/port_id': '12',
            '/sys/class/net/eth22.30/brport/state': '0',
            '/sys/class/net/eth22.30/brport/bridge/bridge/stp_state': '0',
            '/sys/class/net/eth22.40/brport/bridge/bridge/root_port': 'aaa',
            '/sys/class/net/eth22.40/brport/state': '3',
            '/sys/class/net/eth22.40/brport/port_id': '10',
            '/sys/class/net/eth22.40/brport/bridge/bridge/stp_state': '1'
        }
        values3 = {
            '/sys/class/net/eth22/brport/bridge': 'br10',
            '/sys/class/net/eth22.11/brport/bridge': 'br11',
            '/sys/class/net/eth22.20/brport/bridge': None,
            '/sys/class/net/eth22.30/brport/bridge': 'br30',
            '/sys/class/net/eth22.40/brport/bridge': 'br40'
        }
        mock_symlink.side_effect = mod_args_generator(values3)
        mock_oneline.side_effect = mod_args_generator(values2)
        mock_os_path.side_effect = mod_args_generator(values)
        br10 = linux_bridge.Bridge('br10')
        br11 = linux_bridge.Bridge('br11')
        br30 = linux_bridge.Bridge('br30')
        linux_bridge.BRIDGE_CACHE['br10'] = br10
        linux_bridge.BRIDGE_CACHE['br11'] = br11
        linux_bridge.BRIDGE_CACHE['br30'] = br30
        _output = self.piface.bridgemem_details()
        _outputtable = _output.split('\n')
        assert_equals(_outputtable[0], 'vlans in stp disabled state')
        assert_equals(_outputtable[2], '30')
        assert_equals(_outputtable[4], 'vlans in forwarding state')
        assert_equals(_outputtable[6], 'br10, 40')
        assert_equals(_outputtable[8], 'vlans in blocking state')
        assert_equals(_outputtable[10], '11')


class TestPrintBridge(object):
    def setup(self):
        iface = linux_bridge.Bridge('br0')
        self.piface = print_bridge.PrintBridge(iface)

    @mock.patch('netshow.linux.print_iface.linux_iface.Iface.is_l3')
    def test_port_category(self, mock_is_l3):
        # if l3
        mock_is_l3.return_value = True
        assert_equals(self.piface.port_category, 'bridge/l3')
        # if l3 is not true
        mock_is_l3.return_value = False
        assert_equals(self.piface.port_category, 'bridge/l2')

    @mock.patch('netshowlib.linux.bridge.Bridge._memberlist_str')
    def test_vlan_id(self, mock_bridgemems):
        # tagged ports
        mock_bridgemems.return_value = ['eth1.100', 'eth2.100', 'eth3', 'eth4']
        assert_equals(self.piface.vlan_id(), '100')
        # untagged ports
        mock_bridgemems.return_value = ['eth1', 'eth12', 'eth13']
        assert_equals(self.piface.vlan_id(), 'untagged')
        # no ports
        mock_bridgemems.return_value = ['']
        assert_equals(self.piface.vlan_id(), 'untagged')

    @mock.patch('netshowlib.linux.bridge.os.listdir')
    def test_tagged_ifaces(self, mock_listdirs):
        # if list of tagged ports exists
        bridgemems = ['bond0.100', 'bond1.100', 'eth9.100', 'eth10.100']
        mock_listdirs.return_value = bridgemems
        assert_equals(self.piface.tagged_ifaces().split(),
                      ['tagged:', 'bond0-1,eth9-10'])
        # if list of tagged ports does not exist
        bridgemems = ['bond0', 'bond1', 'eth9', 'eth10']
        mock_listdirs.return_value = bridgemems
        assert_equals(self.piface.tagged_ifaces(), '')

    @mock.patch('netshowlib.linux.bridge.os.listdir')
    def test_untagged_ifaces(self, mock_listdirs):
        # list of untagged ports exists
        bridgemems = ['bond0', 'bond1', 'eth9', 'eth10']
        mock_listdirs.return_value = bridgemems
        assert_equals(self.piface.untagged_ifaces().split(),
                      ['untagged:', 'bond0-1,eth9-10'])
        # list has no untagged ports
        bridgemems = ['bond0.100', 'bond1.100']
        mock_listdirs.return_value = bridgemems
        assert_equals(self.piface.untagged_ifaces(), '')

    @mock.patch('netshow.linux.print_bridge.PrintBridge.stp_summary')
    @mock.patch('netshow.linux.print_bridge.PrintBridge.untagged_ifaces')
    @mock.patch('netshow.linux.print_bridge.PrintBridge.tagged_ifaces')
    @mock.patch('netshow.linux.print_bridge.PrintBridge.vlan_id')
    def test_summary(self, mock_vlan_id, mock_tagged, mock_untagged,
                     mock_stp_summary):
        manager = mock.MagicMock()
        manager.attach_mock(mock_stp_summary, 'stp_summary')
        manager.attach_mock(mock_vlan_id, 'vlan_id')
        manager.attach_mock(mock_tagged, 'tagged_ifaces')
        manager.attach_mock(mock_untagged, 'untagged_ifaces')
        self.piface.summary
        expected_calls = [mock.call.untagged_ifaces(),
                          mock.call.tagged_ifaces(),
                          mock.call.vlan_id(),
                          mock.call.stp_summary()]
        assert_equals(manager.method_calls, expected_calls)

    @mock.patch('netshowlib.linux.common.read_file_oneline')
    @mock.patch('netshowlib.linux.bridge.os.listdir')
    @mock.patch('netshowlib.linux.bridge.Bridge.read_from_sys')
    @mock.patch('netshowlib.linux.bridge.KernelStpBridge.is_root')
    def test_stp_summary(self, mock_is_root, mock_read_from_sys,
                         mock_listdir, mock_oneline):
        # if stp is disabled
        mock_read_from_sys.return_value = '0'
        assert_equals(self.piface.stp_summary().split(), ['stp:', 'disabled'])
        # if stp is root
        values = {
            'bridge/stp_state': '1',
            'bridge/root_id': '4000.fe54007e7eeb',
            'bridge/bridge_id': '4000.fe54007e7eeb'}
        mock_read_from_sys.side_effect = mod_args_generator(values)
        mock_is_root.return_value = True
        assert_equals(self.piface.stp_summary().split(), ['stp:', 'rootswitch(16384)'])
        # if stp is not root
        values = {
            'bridge/stp_state': '1',
            'bridge/root_id': '4000.fe54007e7eeb',
            'bridge/bridge_id': '8000.fe54007e7111'}
        values2 = {
            '/sys/class/net/eth1/brport/state': '3',
            '/sys/class/net/eth1/brport/bridge/bridge/root_port': '1',
            '/sys/class/net/eth1/brport/port_id': '1',
            '/sys/class/net/eth2/brport/state': '0',
            '/sys/class/net/eth2/brport/bridge/bridge/stp_state': '1',
            '/sys/class/net/eth2/brport/bridge/bridge/root_port': '1',
            '/sys/class/net/eth2/brport/port_id': '2',
        }
        mock_oneline.side_effect = mod_args_generator(values2)
        mock_read_from_sys.side_effect = mod_args_generator(values)
        mock_is_root.return_value = False
        mock_listdir.return_value = ['eth1', 'eth2']
        assert_equals(self.piface.stp_summary().split(),
                      ['stp:', 'eth1(root)', '16384(root_priority)'])

    @mock.patch('netshowlib.linux.bridge.KernelStpBridge.is_root')
    @mock.patch('netshowlib.linux.common.read_file_oneline')
    @mock.patch('netshowlib.linux.bridge.os.listdir')
    @mock.patch('netshowlib.linux.bridge.Bridge.read_from_sys')
    def test_stp_details(self, mock_read_sys, mock_listdir,
                         mock_file_oneline, mock_is_root):
        mock_is_root.return_value = False
        mock_listdir.return_value = ['eth1', 'eth2']
        values1 = {
            'bridge/stp_state': '1',
            'bridge/root_id': '4000.fe54007e7eeb',
            'bridge/bridge_id': '8000.fe54007e7111'}
        values2 = {
            '/sys/class/net/eth1/brport/state': '3',
            '/sys/class/net/eth1/brport/bridge/bridge/root_port': '1',
            '/sys/class/net/eth1/brport/port_id': '1',
            '/sys/class/net/eth2/brport/state': '0',
            '/sys/class/net/eth2/brport/bridge/bridge/stp_state': '1',
            '/sys/class/net/eth2/brport/bridge/bridge/root_port': '1',
            '/sys/class/net/eth2/brport/port_id': '2',
        }
        mock_read_sys.side_effect = mod_args_generator(values1)
        mock_file_oneline.side_effect = mod_args_generator(values2)
        _output = self.piface.stp_details()
        _outputtable = _output.split('\n')
        assert_equals(re.split(r'\s{2,}', _outputtable[2]),
                      ['stp_mode:', '802.1d / per bridge instance'])
        assert_equals(_outputtable[3].split(),
                      ['root_port:', 'eth1'])
        assert_equals(_outputtable[4].split(),
                      ['root_priority:', '16384'])
        assert_equals(_outputtable[5].split(), ['bridge_priority:', '32768'])
        assert_equals(_outputtable[6].split(), ['802.1q_tag:', 'untagged'])

    @mock.patch('netshowlib.linux.bridge.Bridge.read_from_sys')
    def test_no_stp_details(self, mock_read_from_sys):
        mock_read_from_sys.return_value = '0'
        _output = self.piface.no_stp_details()
        _outputtable = _output.split('\n')
        assert_equals(_outputtable[2].split(),
                      ['stp_mode:', 'disabled'])
        assert_equals(_outputtable[3].split(),
                      ['802.1q_tag:', 'untagged'])

    @mock.patch('netshowlib.linux.bridge.Bridge.read_from_sys')
    @mock.patch('netshow.linux.print_bridge.PrintBridge.cli_header')
    @mock.patch('netshow.linux.print_bridge.PrintBridge.ip_details')
    @mock.patch('netshow.linux.print_bridge.PrintBridge.stp_details')
    @mock.patch('netshow.linux.print_bridge.PrintBridge.no_stp_details')
    @mock.patch('netshow.linux.print_bridge.PrintBridge.ports_in_fwd_state')
    @mock.patch('netshow.linux.print_bridge.PrintBridge.ports_in_blocking_state')
    def test_cli_output(self, mock_block_state, mock_fwd_state,
                        mock_no_stp_details, mock_stp_details, mock_ip_details,
                        mock_cli_header, mock_read_from_sys):
        manager = mock.MagicMock()
        manager.attach_mock(mock_fwd_state, 'ports_in_fwd_state')
        manager.attach_mock(mock_block_state, 'ports_in_blocking_state')
        manager.attach_mock(mock_no_stp_details, 'no_stp_details')
        manager.attach_mock(mock_stp_details, 'stp_details')
        manager.attach_mock(mock_ip_details, 'ip_details')
        manager.attach_mock(mock_cli_header, 'cli_header')
        self.piface.cli_output()
        # stp enabled
        expected_calls = [mock.call.cli_header(),
                          mock.call.ip_details(),
                          mock.call.stp_details(),
                          mock.call.ports_in_fwd_state(),
                          mock.call.ports_in_blocking_state()]
        assert_equals(manager.method_calls, expected_calls)
        # stp disabled
        manager.reset_mock()
        mock_read_from_sys.return_value = '0'
        self.piface.cli_output()
        expected_calls = [mock.call.cli_header(),
                          mock.call.ip_details(),
                          mock.call.no_stp_details()]
        assert_equals(manager.method_calls, expected_calls)

    @mock.patch('netshowlib.linux.bridge.KernelStpBridge.is_root')
    @mock.patch('netshowlib.linux.common.read_file_oneline')
    @mock.patch('netshowlib.linux.bridge.os.listdir')
    @mock.patch('netshowlib.linux.bridge.Bridge.read_from_sys')
    def test_ports_in_fwd_state(self, mock_read_sys, mock_listdir,
                                mock_oneline,
                                mock_is_root):
        values1 = {
            'bridge/stp_state': '1',
            'bridge/root_id': '4000.fe54007e7eeb',
            'bridge/bridge_id': '8000.fe54007e7111'}
        values2 = {
            '/sys/class/net/eth1/brport/state': '3',
            '/sys/class/net/eth1/brport/bridge/bridge/root_port': '1',
            '/sys/class/net/eth1/brport/port_id': '1',
            '/sys/class/net/eth2/brport/state': '3',
            '/sys/class/net/eth2/brport/bridge/bridge/stp_state': '1',
            '/sys/class/net/eth2/brport/bridge/bridge/root_port': '1',
            '/sys/class/net/eth2/brport/port_id': '2',
        }
        mock_oneline.side_effect = mod_args_generator(values2)
        mock_read_sys.side_effect = mod_args_generator(values1)
        mock_is_root.return_value = True
        mock_listdir.return_value = ['eth1', 'eth2']
        _output = self.piface.ports_in_fwd_state()
        _outputtable = _output.split('\n')
        assert_equals(_outputtable[0], 'ports_in_fwding_state')
        assert_equals(_outputtable[2], 'eth1-2')
        # if no ports are forwarding
        values2 = {
            '/sys/class/net/eth1/brport/state': '1',
            '/sys/class/net/eth1/brport/bridge/bridge/root_port': '1',
            '/sys/class/net/eth1/brport/port_id': '1',
            '/sys/class/net/eth2/brport/state': '1',
            '/sys/class/net/eth2/brport/bridge/bridge/stp_state': '1',
            '/sys/class/net/eth2/brport/bridge/bridge/root_port': '1',
            '/sys/class/net/eth2/brport/port_id': '2',
        }
        mock_oneline.side_effect = mod_args_generator(values2)
        assert_equals(self.piface.ports_in_fwd_state(), '')

    @mock.patch('netshowlib.linux.bridge.KernelStpBridge.is_root')
    @mock.patch('netshowlib.linux.common.read_file_oneline')
    @mock.patch('netshowlib.linux.bridge.os.listdir')
    @mock.patch('netshowlib.linux.bridge.Bridge.read_from_sys')
    def test_ports_in_blocking_state(self, mock_read_sys, mock_listdir,
                                     mock_oneline,
                                     mock_is_root):
        values1 = {
            'bridge/stp_state': '1',
            'bridge/root_id': '4000.fe54007e7eeb',
            'bridge/bridge_id': '8000.fe54007e7111'}
        values2 = {
            '/sys/class/net/eth1/brport/state': '4',
            '/sys/class/net/eth1/brport/bridge/bridge/root_port': '1',
            '/sys/class/net/eth1/brport/port_id': '1',
            '/sys/class/net/eth2/brport/state': '4',
            '/sys/class/net/eth2/brport/bridge/bridge/stp_state': '1',
            '/sys/class/net/eth2/brport/bridge/bridge/root_port': '1',
            '/sys/class/net/eth2/brport/port_id': '2',
        }
        mock_oneline.side_effect = mod_args_generator(values2)
        mock_read_sys.side_effect = mod_args_generator(values1)
        mock_is_root.return_value = True
        mock_listdir.return_value = ['eth1', 'eth2']
        _output = self.piface.ports_in_blocking_state()
        _outputtable = _output.split('\n')
        assert_equals(_outputtable[0], 'ports_in_blocking_state')
        assert_equals(_outputtable[2], 'eth1-2')
        # if no ports are forwarding
        values2 = {
            '/sys/class/net/eth1/brport/state': '1',
            '/sys/class/net/eth1/brport/bridge/bridge/root_port': '1',
            '/sys/class/net/eth1/brport/port_id': '1',
            '/sys/class/net/eth2/brport/state': '1',
            '/sys/class/net/eth2/brport/bridge/bridge/stp_state': '1',
            '/sys/class/net/eth2/brport/bridge/bridge/root_port': '1',
            '/sys/class/net/eth2/brport/port_id': '2',
        }
        mock_oneline.side_effect = mod_args_generator(values2)
        assert_equals(self.piface.ports_in_blocking_state(), '')
