# print() is required for py3 not py2. so need to disable C0325
# pylint: disable=C0325

"""
Usage:
    netshow neighbors [--json | -j ]
    netshow system [--json | -j ]
    netshow interface [all] [ -m | --mac ] [ --oneline | -1 | -j | --json ]
    netshow [interface] [ access | bridge | bond | bondmem | mgmt | l2 | l3 | trunk | <iface> ] [all] [--mac | -m ] [--oneline | -1  | --json | -j]
    netshow (--version | -v)

Help:
    * default is to show intefaces only in the UP state.
    interface                 summary info of all interfaces
    interface access          summary of physical ports with l2 or l3 config
    interface bond            summary of bonds
    interface bondmem         summary of bond members
    interface bridge          summary of ports with bridge members
    interface trunk           summary of trunk interfaces
    interface mgmt            summary of mgmt ports
    interface l3              summary of ports with an IP.
    interface l2              summary of access, trunk and bridge interfaces
    interface <interface>     list summary of a single interface
    system                    system information
    neighbors                 physical device neighbor information

Options:
    all        show all ports include those are down or admin down
    --mac      show inteface MAC in output
    --version  netshow software version
    --oneline  output each entry on one line
    -1         alias for --oneline
    --json     print output in json
"""

from docopt import docopt, printable_usage
from netshow.linux._version import get_version
from netshow.linux.show_interfaces import ShowInterfaces
from netshow.linux.show_neighbors import ShowNeighbors
from netshow.linux.show_system import ShowSystem


def _interface_related(results):
    """ give user ability to issue `show bridge` and other
    interface related commands without the interface keyword
    """

    if results.get('trunk') or \
            results.get('access') or \
            results.get('l3') or \
            results.get('l2') or \
            results.get('phy') or \
            results.get('bridge') or \
            results.get('bond') or \
            results.get('bondmem') or \
            results.get('bridgemem') or \
            results.get('mgmt') or \
            results.get('interface'):
        return True
    return False


def run():
    """ run linux netshow version """
    _results = docopt(__doc__)
    if _interface_related(_results):
        _showint = ShowInterfaces(**_results)
        print(_showint.run())
    elif _results.get('system'):
        _showsys = ShowSystem(**_results)
        print(_showsys.run())
    elif _results.get('neighbors'):
        _shownei = ShowNeighbors(**_results)
        print(_shownei.run())
    elif _results.get('--version') or _results.get('-v'):
        print(get_version())
    else:
        print(printable_usage(__doc__))