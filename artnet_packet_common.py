import struct

# Note '!' prefix for network (big-endian) ordering! Any multi-byte fields (not arrays) will send with their MSB first, in the 0th index of the array when parsed in C. Unfortunately ArtNet is stupid because they havea few fields not in that order (opcode), which need to be manually flipped before sending
artnet_base_packet_fmt = "!8sH"
artnet_standard_packet_fmt = artnet_base_packet_fmt + "H"


class BaseArtNetPacket(struct.Struct):

    def __init__(self, format_str, opcode):
        self.id = "Art-Net"
        self.opcode = opcode
        super().__init__(format_str)

    def pack(self, *args):
        id_bytes = bytearray(self.id, "utf-8")
        opcode_high_byte = (self.opcode & 0xFF00) >> 8
        opcode_low_byte = (self.opcode & 0xFF)
        return super().pack(id_bytes,
                            (opcode_low_byte << 8) | opcode_high_byte, *args)


class StandardArtNetPacket(BaseArtNetPacket):

    def __init__(self, format_str, opcode):
        self.protocol_version = 14
        super().__init__(format_str, opcode)

    def pack(self, *args):
        return super().pack(self.protocol_version, *args)
