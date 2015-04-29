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

from collections import OrderedDict
from asserts import assert_equals
import netshow.linux.show_interfaces as showint
import netshowlib.linux.bond as linux_bond
import netshow.linux.print_bridge as print_bridge
import netshow.linux.print_bond as print_bond
import netshow.linux.print_iface as print_iface
from nose.tools import set_trace
import mock


class TestShowInterfaces(object):

    def setup(self):
        results = {'l2': True}
        self.showint = showint.ShowInterfaces(**results)

    @mock.patch('netshow.linux.show_interfaces.linux_iface.portname_list')
    @mock.patch('netshow.linux.show_interfaces.linux_cache.Cache')
    @mock.patch('netshow.linux.show_interfaces.linux_print_iface.PrintIface.is_bridgemem')
    def test_ifacelist_l2_subints(self, mock_bridgemem_test,
                                  mock_cache, mock_portname_list):
        # make sure L2 subints don't get into the list
        mock_bridgemem_test.return_value = True
        mock_portname_list.return_value = ['eth1.1', 'eth2.1']
        assert_equals(self.showint.ifacelist.get('all'), OrderedDict())


    @mock.patch('netshow.linux.show_interfaces.linux_print_iface.PrintIface.is_bridge')
    @mock.patch('netshow.linux.show_interfaces.linux_cache.Cache')
    @mock.patch('netshow.linux.show_interfaces.linux_iface.portname_list')
    def test_ifacelist_is_bridge(self, mock_portname_list,
                                 mock_cache, mock_is_bridge):
        # test to see if bridge is probably placed
        mock_is_bridge.return_value = True
        mock_portname_list.return_value = ['br0']
        assert_equals(isinstance(
            self.showint.ifacelist.get('all').get('br0'),
            print_bridge.PrintBridge), True)
        assert_equals(
            self.showint.ifacelist.get('bridge').get('br0'),
            self.showint.ifacelist.get('l2').get('br0'))
        assert_equals(
            self.showint.ifacelist.get('bridge').get('br0'),
            self.showint.ifacelist.get('all').get('br0'))

    @mock.patch('netshow.linux.show_interfaces.print_bond.PrintBond.is_l3')
    @mock.patch('netshow.linux.show_interfaces.linux_print_iface.PrintIface.is_bond')
    @mock.patch('netshow.linux.show_interfaces.linux_cache.Cache')
    @mock.patch('netshow.linux.show_interfaces.linux_iface.portname_list')
    def test_ifacelist_is_bond_l3(self, mock_portname_list,
                                  mock_cache, mock_is_bond, mock_is_l3):
        # test to see if bridge is probably placed
        mock_is_bond.return_value = True
        mock_is_l3.return_value = True
        mock_portname_list.return_value = ['bond0']
        assert_equals(isinstance(
            self.showint.ifacelist.get('all').get('bond0'),
            print_bond.PrintBond), True)
        assert_equals(
            self.showint.ifacelist.get('bond').get('bond0'),
            self.showint.ifacelist.get('l3').get('bond0'))
        assert_equals(
            self.showint.ifacelist.get('bond').get('bond0'),
            self.showint.ifacelist.get('all').get('bond0'))


    @mock.patch('netshow.linux.show_interfaces.print_bridge.PrintBridgeMember.is_l3')
    @mock.patch('netshow.linux.show_interfaces.print_bridge.PrintBridgeMember.is_trunk')
    @mock.patch('netshow.linux.show_interfaces.linux_print_iface.PrintIface.is_bridgemem')
    @mock.patch('netshow.linux.show_interfaces.linux_cache.Cache')
    @mock.patch('netshow.linux.show_interfaces.linux_iface.portname_list')

    def test_ifacelist_is_bridgemem_trunk(self, mock_portname_list,
                                          mock_cache, mock_is_bridgemem,
                                          mock_is_trunk, mock_is_l3):
        mock_is_l3.return_value = False
        mock_is_trunk.return_value = True
        mock_is_bridgemem.return_value = True
        mock_portname_list.return_value = ['eth1']
        assert_equals(isinstance(
            self.showint.ifacelist.get('all').get('eth1'),
            print_bridge.PrintBridgeMember), True)
        assert_equals(
            self.showint.ifacelist.get('trunk').get('eth1'),
            self.showint.ifacelist.get('all').get('eth1'))




    @mock.patch('netshow.linux.show_interfaces.ShowInterfaces.print_single_iface')
    @mock.patch('netshow.linux.show_interfaces.ShowInterfaces.print_many_ifaces')
    def test_run_single_iface(self, mock_many, mock_single):
        # single interface config
        self.showint.single_iface = True
        self.showint.run()
        assert_equals(mock_single.call_count, 1)

    @mock.patch('netshow.linux.show_interfaces.ShowInterfaces.print_single_iface')
    @mock.patch('netshow.linux.show_interfaces.ShowInterfaces.print_many_ifaces')
    def test_run_many_iface(self, mock_many, mock_single):
        # single interface config
        self.showint.single_iface = False
        self.showint.run()
        assert_equals(mock_many.call_count, 1)
        assert_equals(mock_single.call_count, 0)

    @mock.patch('netshow.linux.show_interfaces.ShowInterfaces.print_json_many_ifaces')
    @mock.patch('netshow.linux.show_interfaces.ShowInterfaces.print_cli_many_ifaces')
    def test_many_ifaces_cli_output(self, mock_cli_ifaces, mock_json_ifaces):
        # if json is false get cli output
        self.showint.print_many_ifaces()
        mock_cli_ifaces.assert_called_with('l2')

    @mock.patch('netshow.linux.show_interfaces.ShowInterfaces.print_json_many_ifaces')
    @mock.patch('netshow.linux.show_interfaces.ShowInterfaces.print_cli_many_ifaces')
    def test_many_ifaces_json_output(self, mock_cli_ifaces, mock_json_ifaces):
        # if json is false get cli output
        self.showint.use_json = True
        self.showint.print_many_ifaces()
        mock_json_ifaces.assert_called_with('l2')

    @mock.patch('netshow.linux.show_interfaces.linux_iface.portname_list')
    @mock.patch('netshow.linux.print_iface.PrintIface.is_trunk')
    def test_many_cli_ifaces(self, mock_is_trunk, mock_portlist):
        mock_portlist.return_value = ['eth1', 'eth2']
        mock_is_trunk.return_value = True
        _table = self.showint.print_cli_many_ifaces('l2')
