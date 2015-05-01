# pylint: disable=R0902

"""
Module for printout of 'netshow interfaces'
"""

from collections import OrderedDict
from tabulate import tabulate
import netshow.linux.print_bridge as print_bridge
import netshow.linux.print_bond as print_bond
import netshowlib.linux.cache as linux_cache
from netshowlib.linux import iface as linux_iface
import netshow.linux.print_iface as print_iface

from flufl.i18n import initialize

_ = initialize('netshow-linux-lib')


class ShowInterfaces(object):
    """ Class responsible for the 'netshow interfaces' printout for \
        the linux provider
    """
    def __init__(self, **kwargs):
        self._ifacelist = {}
        self.show_mac = kwargs.get('--mac') or kwargs.get('-m')
        self.use_json = kwargs.get('--json') or kwargs.get('-j')
        self.show_all = True
        self.show_mgmt = kwargs.get('mgmt')
        self.show_bridge = kwargs.get('bridge')
        self.show_bond = kwargs.get('bond')
        self.show_bondmem = kwargs.get('bondmem')
        self.show_access = kwargs.get('access')
        self.show_trunk = kwargs.get('trunk')
        self.show_l3 = kwargs.get('l3')
        self.show_l2 = kwargs.get('l2')
        self.show_phy = kwargs.get('phy')
        self.single_iface = kwargs.get('<iface>')
        if kwargs.get('all') or self.single_iface is not None:
            self.show_up = False
        else:
            self.show_up = True
        if self.show_bond or self.show_bondmem \
                or self.show_access or self.show_trunk \
                or self.show_bridge or self.show_mgmt:
            self.show_all = False
        self.oneline = kwargs.get('--oneline') or kwargs.get('-1')
        self.iface_categories = ['bond', 'bondmem',
                                 'bridge', 'trunk', 'access', 'l3',
                                 'l2']
        self._initialize_ifacelist()

    def run(self):
        """
        :return: terminal output or JSON for 'netshow interfaces' for
        the linux provider
        """
        if self.single_iface:
            return self.print_single_iface()
        else:
            return self.print_many_ifaces()

    def print_single_iface(self):
        """
        :return: netshow terminal output or JSON of a single iface
        """
        pass

    def _initialize_ifacelist(self):
        """
        initialize hash of interface lists. so create an empty orderedDict for bridges \
            bonds, trunks, etc
        """
        for i in self.iface_categories:
            self._ifacelist[i] = OrderedDict()
        self._ifacelist['all'] = OrderedDict()
        self._ifacelist['unknown'] = OrderedDict()

    @property
    def ifacelist(self):
        """
        :return: hash of interface categories. each category containing a list of \
            iface pointers to interfaces that belong in that category. For example
           ifacelist['bridge'] points to a list of bridge Ifaces.
        """

        # ifacelist is already populated..
        # to reset set ``self._ifacelist = None``
        if len(self._ifacelist.get('all')) > 0:
            return self._ifacelist

        self._initialize_ifacelist()
        list_of_ports = linux_iface.portname_list()
        feature_cache = linux_cache.Cache()
        feature_cache.run()
        for _portname in list_of_ports:
            _printiface = print_iface.iface(_portname, feature_cache)

            # if iface is a l2 subint bridgemem, then ignore
            if _printiface.iface.is_subint() and \
                    isinstance(_printiface, print_bridge.PrintBridgeMember):
                continue

            self._ifacelist['all'][_portname] = _printiface

            # mutual exclusive bond/bridge/bondmem/bridgemem
            if isinstance(_printiface, print_bridge.PrintBridge):
                self._ifacelist['bridge'][_portname] = _printiface
                self._ifacelist['l2'][_portname] = _printiface
            elif isinstance(_printiface, print_bond.PrintBond):
                self._ifacelist['bond'][_portname] = _printiface
            elif isinstance(_printiface, print_bridge.PrintBridgeMember):
                self._ifacelist['l2'][_portname] = _printiface
            elif isinstance(_printiface, print_bond.PrintBondMember):
                self._ifacelist['bondmem'][_portname] = _printiface
                continue


            # mutual exclusive - l3/trunk/access
            if _printiface.iface.is_l3():
                self._ifacelist['l3'][_portname] = _printiface
            elif _printiface.iface.is_trunk():
                self._ifacelist['trunk'][_portname] = _printiface
            elif _printiface.iface.is_access():
                self._ifacelist['access'][_portname] = _printiface


        return self._ifacelist

    def print_many_ifaces(self):
        """
        :return: the output of 'netshow interfaces' for many interfaces
        """
        _port_type = None
        # determine wants port subtype or just all interfaces
        # for example if user types 'netshow l2' , then 'self.show_l2' will
        # be true, and only l2 ports will be printed
        for i in self.iface_categories:
            dict_name = 'show_' + i
            if self.__dict__[dict_name]:
                _port_type = i
                break
        if not _port_type:
            _port_type = 'all'

        if self.use_json:
            self.print_json_many_ifaces(_port_type)

        return self.print_cli_many_ifaces(_port_type)

    @property
    def summary_header(self):
        """
        :return: summary header for 'netshow interfaces'
        """
        if self.show_mac:
            return ['', _('name'), _('mac'), _('speed'),
                    _('mtu'), _('mode'), _('summary')]
        else:
            return ['', _('name'), _('speed'),
                    _('mtu'), _('mode'), _('summary')]

    def print_json_many_ifaces(self, port_type):
        """
        :return: 'netshow interface' of many interfaces in JSON output
        """
        pass

    def print_cli_many_ifaces(self, port_type):
        """
        :return: 'netshow interface' of many interfaces in terminal output
        """
        _headers = self.summary_header
        _table = []
        for _p_iface in self.ifacelist.get(port_type).values():
            _table.append([_p_iface.linkstate,
                           _p_iface.name,
                           _p_iface.speed,
                           _p_iface.mtu,
                           _p_iface.port_category,
                           _p_iface.summary[0]])

            if len(_p_iface.summary) > 1:
                for i in range(1, len(_p_iface.summary)):
                    _table.append(['', '',
                                   '', '', '', _p_iface.summary[i]])

        return tabulate(_table, _headers)