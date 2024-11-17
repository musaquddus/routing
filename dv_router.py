"""
Your awesome Distance Vector router for CS 168

Based on skeleton code by:
  MurphyMc, zhangwen0411, lab352
"""

import sim.api as api
from cs168.dv import (
    RoutePacket,
    Table,
    TableEntry,
    DVRouterBase,
    Ports,
    FOREVER,
    INFINITY,
)


class DVRouter(DVRouterBase):

    # A route should time out after this interval
    ROUTE_TTL = 15

    # -----------------------------------------------
    # At most one of these should ever be on at once
    SPLIT_HORIZON = False
    POISON_REVERSE = False
    # -----------------------------------------------

    # Determines if you send poison for expired routes
    POISON_EXPIRED = False

    # Determines if you send updates when a link comes up
    SEND_ON_LINK_UP = False

    # Determines if you send poison when a link goes down
    POISON_ON_LINK_DOWN = False

    def __init__(self):
        """
        Called when the instance is initialized.
        DO NOT remove any existing code from this method.
        However, feel free to add to it for memory purposes in the final stage!
        """
        assert not (
            self.SPLIT_HORIZON and self.POISON_REVERSE
        ), "Split horizon and poison reverse can't both be on"

        self.start_timer()  # Starts signaling the timer at correct rate.

        # Contains all current ports and their latencies.
        # See the write-up for documentation.
        self.ports = Ports()

        # This is the table that contains all current routes
        self.table = Table()
        self.history = {}
        self.table.owner = self

    def add_static_route(self, host, port):
        """
        Adds a static route to this router's table.

        Called automatically by the framework whenever a host is connected
        to this router.

        :param host: the host.
        :param port: the port that the host is attached to.
        :returns: nothing.
        """
        # `port` should have been added to `peer_tables` by `handle_link_up`
        # when the link came up.
        assert port in self.ports.get_all_ports(), "Link should be up, but is not."
        latency = self.ports.get_latency(port)
        self.table[host] = TableEntry(dst=host, port= port, expire_time=FOREVER, latency=latency)

    def handle_data_packet(self, packet, in_port):
        """
        Called when a data packet arrives at this router.

        You may want to forward the packet, drop the packet, etc. here.

        :param packet: the packet that arrived.
        :param in_port: the port from which the packet arrived.
        :return: nothing.
        """
        # TODO: fill this in!
        if not self.table.get(packet.dst):
            return
        tbl_ent = self.table.get(packet.dst)
        if tbl_ent.latency >= INFINITY:
            return
        if tbl_ent.port == in_port:
            return
        self.send(packet, tbl_ent.port, flood=False)

    def send_routes(self, force=False, single_port=None):
        """
        Send route advertisements for all routes in the table.

        :param force: if True, advertises ALL routes in the table;
                      otherwise, advertises only those routes that have
                      changed since the last advertisement.
               single_port: if not None, sends updates only to that port; to
                            be used in conjunction with handle_link_up.
        :return: nothing.
        """
        all_ports = list(self.ports.get_underlying_dict().keys())
        for p in all_ports:
            for host, entry in self.table.items():
                if (host, p) in self.history.keys():
                    old = self.history[(host, p)]

                if self.SPLIT_HORIZON:
                    if p != entry.port:
                        self.send_route(p, host, entry.latency)
                elif self.POISON_REVERSE:
                    if p == entry.port:
                        self.send_route(p, host, INFINITY)
                    else: 
                        self.send_route(p, host, entry.latency)
                else:
                    self.send_route(p, host, entry.latency)
                

    def expire_routes(self):
        """
        Clears out expired routes from table.
        accordingly.
        """
        # TODO: fill this in!
        for host in list(self.table.keys()):
            tbl_ent = self.table[host]
            if tbl_ent.expire_time == FOREVER:
                return
            else:
                if api.current_time() > tbl_ent.expire_time:
                    if self.POISON_EXPIRED:
                        self.table[host] = TableEntry(dst=host, port = self.table[host].port, latency=INFINITY, expire_time=self.ROUTE_TTL)
                    else:
                        del self.table[host]

    def handle_route_advertisement(self, route_dst, route_latency, port):
        """
        Called when the router receives a route advertisement from a neighbor.

        :param route_dst: the destination of the advertised route.
        :param route_latency: latency from the neighbor to the destination.
        :param port: the port that the advertisement arrived on.
        :return: nothing.
        """
        # TODO: fill this in!
        new_exp = api.current_time() + self.ROUTE_TTL
        new_latency = self.ports.get_latency(port) + route_latency
        new_route = TableEntry(dst=route_dst, port = port, latency=new_latency,expire_time=new_exp)
        curr_route = self.table.get(route_dst)
        if route_latency >= INFINITY and curr_route.port == port:
            poisoned = TableEntry(dst = route_dst, port = port, latency=INFINITY, expire_time=curr_route.expire_time)
            self.table[route_dst] = poisoned
            self.send_routes(force=False)
            return
        if not curr_route or new_latency < curr_route.latency or curr_route.port == port:
            self.table[route_dst] = new_route

    def handle_link_up(self, port, latency):
        """
        Called by the framework when a link attached to this router goes up.

        :param port: the port that the link is attached to.
        :param latency: the link latency.
        :returns: nothing.
        """
        self.ports.add_port(port, latency)

        # TODO: fill in the rest!

    def handle_link_down(self, port):
        """
        Called by the framework when a link attached to this router goes down.

        :param port: the port number used by the link.
        :returns: nothing.
        """
        self.ports.remove_port(port)

        # TODO: fill this in!

    # Feel free to add any helper methods!
