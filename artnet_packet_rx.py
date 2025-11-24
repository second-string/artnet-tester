import struct
from ipaddress import ip_address, IPv4Address

from helpers import bswap16, bswap32, uint32_to_big_endian_bytes
from artnet_packet_common import BaseArtNetPacket, StandardArtNetPacket, artnet_base_packet_fmt, artnet_standard_packet_fmt

artnet_poll_reply_packet_fmt = artnet_base_packet_fmt + "I 2H 2B H 2B H 18s 64s 64s H 5I 13B I 2B I 7B 2H 11B"
artnet_ipprog_reply_packet_fmt = artnet_standard_packet_fmt + "3I H 2B I H"


class ArtPollReplyPacket(BaseArtNetPacket):

    def __init__(self, raw_bytes):
        format_str = artnet_poll_reply_packet_fmt

        super().__init__(format_str, 0x2100)

        unpacked_data = None
        try:
            unpacked_data = super().unpack(raw_bytes)
        except struct.error as e:
            print(
                f"Error unpacking struct, number of bytes in buffer ({len(raw_bytes)}) does not match expected unpack length ({self.size}!"
            )

        # All of our struct subclasses have a big endian format string, so anything the artnet spec says is little endian in the packet (LSB first, i.e. port), must be flipped from what we parse it as here
        if (unpacked_data):
            # idx 0 and 1 are artnet header and opcode
            self.ip_addr = unpacked_data[2]
            self.port_number = bswap16(
                unpacked_data[3])  # port is low byte first
            self.vers_info = unpacked_data[4]
            self.net_switch = unpacked_data[5]
            self.sub_switch = unpacked_data[6]
            self.oem = unpacked_data[7]
            self.ubea_version = unpacked_data[8]
            self.status_1 = unpacked_data[9]
            self.esta_mfgr = bswap16(unpacked_data[10])
            self.port_name = unpacked_data[11].rstrip(b'\x00').decode("utf-8")
            self.long_name = unpacked_data[12].rstrip(b'\x00').decode("utf-8")
            self.node_report = unpacked_data[13].rstrip(b'\x00').decode(
                "utf-8")
            self.num_ports = unpacked_data[14]
            self.port_types = unpacked_data[15]
            self.good_input = unpacked_data[16]
            self.good_output = unpacked_data[17]
            self.sw_in = unpacked_data[18]
            self.sw_out = unpacked_data[19]
            self.acn_priority = unpacked_data[20]
            self.sw_macro = unpacked_data[21]
            self.sw_remote = unpacked_data[22]
            self.padding_1 = (unpacked_data[23] << 16) | (
                unpacked_data[24] << 8) | (unpacked_data[25])
            self.style = unpacked_data[26]
            self.mac = ":".join(
                str(b)[2:] for b in [
                    hex(unpacked_data[27]),
                    hex(unpacked_data[28]),
                    hex(unpacked_data[29]),
                    hex(unpacked_data[30]),
                    hex(unpacked_data[31]),
                    hex(unpacked_data[32])
                ])
            self.bind_ip = unpacked_data[33]
            self.bind_index = unpacked_data[34]
            self.status_2 = unpacked_data[35]
            self.good_output_B = unpacked_data[36]
            self.status_3 = unpacked_data[37]
            self.default_response_uid = ":".join(
                str(b)[2:] for b in [
                    hex(unpacked_data[38]),
                    hex(unpacked_data[39]),
                    hex(unpacked_data[40]),
                    hex(unpacked_data[41]),
                    hex(unpacked_data[42]),
                    hex(unpacked_data[43])
                ])
            self.user = unpacked_data[44]
            self.refresh_rate = unpacked_data[45]
        else:
            print("Returning empty ArtPollReplyPacket")

    def print_fields(self):
        print("ArtNetPollReply packet:")
        print(f'{"IP addr:":<20} {IPv4Address(self.ip_addr)}')
        print(f'{"Port:":<20} {self.port_number}')
        print(f'{"FW version:":<20} {self.vers_info:#04x}')
        print(f'{"ArtNet Net:":<20} {self.net_switch}')
        print(f'{"ArtNet Switch:":<20} {self.sub_switch}')
        print(f'{"OEM code:":<20} {hex(self.oem)}')
        print(f'{"UBEA version:":<20} {self.ubea_version}')
        print(f'{"Status 1:":<20} {hex(self.status_1)}')
        print(f'{"ESTA manufacturer:":<20} {hex(self.esta_mfgr)}')
        print(f'{"Port name:":<20} {self.port_name}')
        print(f'{"Long name:":<20} {self.long_name}')
        print(f'{"Node report:":<20} {self.node_report}')
        print(f'{"# ports:":<20} {self.num_ports}')
        print(
            f'{"Port types:":<20} {["0x%02X" % b for b in uint32_to_big_endian_bytes(self.port_types)]}'
        )
        print(
            f'{"Good input:":<20} {["0x%02X" % b for b in uint32_to_big_endian_bytes(self.good_input)]}'
        )
        print(
            f'{"Good output:":<20} {["0x%02X" % b for b in uint32_to_big_endian_bytes(self.good_output)]}'
        )
        print(
            f'{"Switch input:":<20} {["0x%02X" % b for b in uint32_to_big_endian_bytes(self.sw_in)]}'
        )
        print(
            f'{"Switch output:":<20} {["0x%02X" % b for b in uint32_to_big_endian_bytes(self.sw_out)]}'
        )
        print(f'{"sACN priority:":<20} {self.acn_priority}')
        print(f'{"Switch macro:":<20} {self.sw_macro}')
        print(f'{"Switch remote:":<20} {self.sw_remote}')
        print(f'{"Style:":<20} {self.style}')
        print(f'{"MAC address:":<20} {self.mac}')
        print(f'{"Bind IP:":<20} {IPv4Address(self.bind_ip)}')
        print(f'{"Bind index:":<20} {self.bind_index}')
        print(f'{"Status 2:":<20} {hex(self.status_2)}')
        print(
            f'{"Good output B:":<20} {["0x%02X" % b for b in uint32_to_big_endian_bytes(self.good_output_B)]}'
        )
        print(f'{"Status 3:":<20} {hex(self.status_3)}')
        print(f'{"Response UID:":<20} {self.default_response_uid}')
        print(f'{"User bytes:":<20} {self.user:#04x}')
        print(f'{"Refresh rate:":<20} {self.refresh_rate}')


class ArtIpProgReplyPacket(StandardArtNetPacket):

    def __init__(self, raw_bytes):
        format_str = artnet_ipprog_reply_packet_fmt

        super().__init__(format_str, 0xF900)

        unpacked_data = None
        try:
            unpacked_data = super().unpack(raw_bytes)
        except struct.error as e:
            print(
                f"Error unpacking struct, number of bytes in buffer ({len(raw_bytes)}) does not match expected unpack length ({self.size}!"
            )

        # All of our struct subclasses have a big endian format string, so anything the artnet spec says is little endian in the packet (LSB first, i.e. port), must be flipped from what we parse it as here
        if (unpacked_data):
            # idx 0, 1, 2 are artnet header, opcode, & protocol version
            # self.filler = unpacked_data[3]
            self.ip_addr = unpacked_data[4]
            self.subnet_mask = unpacked_data[5]
            self.port = unpacked_data[6]
            self.status = unpacked_data[7]
            # self.filler = unpacked_data[8]
            self.gateway = unpacked_data[9]
            # self.filler = unpacked_data[10]
        else:
            print("Returning empty ArtPollReplyPacket")

    def print_fields(self):
        print("ArtNetIPProgReply packet:")
        print(f'{"DHCP enabled":<15} {self.status >> 6}')
        print(f'{"IP addr":<15} {IPv4Address(self.ip_addr)}')
        print(f'{"Subnet mask":<15} {IPv4Address(self.subnet_mask)}')
        print(f'{"Port":<15} {self.port}')
        print(f'{"Gateway":<15} {IPv4Address(self.gateway)}')
        print(f'{"Status":<15} {hex(self.status)}')
