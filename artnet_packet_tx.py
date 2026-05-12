import struct
from ipaddress import ip_address, IPv4Address

from artnet_packet_common import artnet_standard_packet_fmt, StandardArtNetPacket

artnet_poll_packet_fmt = artnet_standard_packet_fmt + "2B4H"
artnet_ipprog_packet_fmt = artnet_standard_packet_fmt + "4B2IHI"
artnet_command_packet_partial_fmt = artnet_standard_packet_fmt + "HH"  # partial format because # of trailing string format specifier depends on length of command string passed into constructor
artnet_dmx_packet_fmt = artnet_standard_packet_fmt + "BBBBH512s"


class ArtPollPacket(StandardArtNetPacket):

    def __init__(self):
        format_str = artnet_poll_packet_fmt

        self.flags = 0
        self.lowest_diagnostic_priority = 0
        self.target_port_range_top = 0
        self.target_port_range_bottom = 0
        self.esta_mfgr = 0
        self.oem = 0

        super().__init__(format_str, 0x2000)

    def pack(self):
        return super().pack(self.flags, self.lowest_diagnostic_priority,
                            self.target_port_range_top,
                            self.target_port_range_bottom, self.esta_mfgr,
                            self.oem)


class ArtProgIpPacket(StandardArtNetPacket):

    def __init__(self):
        format_str = artnet_ipprog_packet_fmt

        self.filler1 = 0
        self.filler2 = 0
        self.command = 0
        self.filler4 = 0
        self.new_ip = IPv4Address("0.0.0.0")
        self.new_subnet_mask = IPv4Address("0.0.0.0")
        self.new_port = 0
        self.new_default_gateway = IPv4Address("0.0.0.0")

        super().__init__(format_str, 0xF800)

    def pack(self):
        # we store them as IPv4Adress objects, convert to ints
        ip_int = int(self.new_ip)
        gateway_int = int(self.new_default_gateway)
        subnet_int = int(self.new_subnet_mask)
        return super().pack(self.filler1, self.filler2, self.command,
                            self.filler4, ip_int, subnet_int, self.new_port,
                            gateway_int)

    def set_dhcp(self, dhcp_enabled):
        self.command = self.command | ((1 << 7) | dhcp_enabled << 6)

    def set_new_ip(self, new_ip):
        self.command = self.command | (1 << 7) | (1 << 2)
        self.new_ip = new_ip

    def set_new_subnet_mask(self, new_subnet_mask):
        self.command = self.command | (1 << 7) | (1 << 1)
        self.new_subnet_mask = new_subnet_mask

    def set_new_gateway(self, new_gateway):
        self.command = self.command | (1 << 7) | (1 << 4)
        self.new_default_gateway = new_gateway

    def set_new_port(self, new_port):
        self.command = self.command | (1 << 7) | (1 << 0)
        self.new_port = new_port


class ArtCommandPacket(StandardArtNetPacket):

    def __init__(self, command_string):
        self.esta_mfgr = 0xFFFF  # spec says artcommand always txs with 0xFFFF ESTA
        self.command_string = command_string
        self.length = len(command_string) + 1  # include null term in length

        format_str = artnet_command_packet_partial_fmt + str(self.length) + "s"

        super().__init__(format_str, 0x2400)

    def pack(self):
        return super().pack(self.esta_mfgr, self.length,
                            bytes(self.command_string, "utf-8"))


class ArtDmxPacket(StandardArtNetPacket):

    def __init__(self, universe, data_bytes):
        # universe is a 15-bit value: low 8 bits -> sub_uni, high 7 bits -> net
        self.sequence = 0  # 0 disables sequence checking
        self.physical = 0
        self.sub_uni = universe & 0xFF
        self.net = (universe >> 8) & 0x7F
        # length must be even and between 2-512
        length = max(2, len(data_bytes))
        if length % 2 != 0:
            length += 1
        self.length = length
        padded = list(data_bytes) + [0] * (512 - len(data_bytes))
        self.data = bytes(padded)

        super().__init__(artnet_dmx_packet_fmt, 0x5000)

    def pack(self):
        return super().pack(self.sequence, self.physical, self.sub_uni,
                            self.net, self.length, self.data)
