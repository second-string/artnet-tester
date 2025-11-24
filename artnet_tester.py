import helpers

from artnet_packet_tx import ArtPollPacket, ArtProgIpPacket, ArtCommandPacket
from artnet_packet_rx import ArtPollReplyPacket, ArtIpProgReplyPacket

if __name__ == "__main__":
    print("Art-Net packet tester")

    sock = helpers.open_connection()

    while True:
        print()
        print(
            f"Sending packets to {helpers.dest_ip}:{helpers.dest_port}. Choose an option"
        )
        print("1) Change destination IP or port for test packets")
        print("2) Send ArtPoll")
        print("3) Send ArtIPProg")
        print("4) Send ArtCommand")
        print("9) Exit")
        print()

        valid_input = False
        num = helpers.prompt_for_number_in_range("Choice: ",
                                                 list(range(1, 5)) + [9])
        if num == 1:
            print()
            print("Set destination IP or port?")
            print("1) IP address")
            print("2) Port")
            print()

            num = helpers.prompt_for_number_in_range("Choice: ", [1, 2])
            if num == 1:
                ip = helpers.prompt_for_ip("New IP: ")
                helpers.dest_ip = str(ip)
            elif num == 2:
                helpers.dest_port = helpers.prompt_for_number_in_range(
                    "New port: ", range(1, 10000))
        elif num == 2:
            packet = ArtPollPacket()
            raw_byte_response = helpers.send_packet(packet, sock, True)
            if not raw_byte_response:
                print("Timed out waiting for response")
            else:
                reply_packet = ArtPollReplyPacket(raw_byte_response)
                reply_packet.print_fields()
        elif num == 3:
            print()
            print("Select the field to program")
            print("1) Set IP address")
            print("2) Set default gateway")
            print("3) Set subnet mask")
            print("4) Set port")
            print("5) Set DHCP or static IP")
            print("6) No changes, read existing config")
            print()

            num = helpers.prompt_for_number_in_range("Choice: ", range(1, 7))
            packet = ArtProgIpPacket()
            if num == 1:
                ip = helpers.prompt_for_ip("New IP: ")
                packet.set_new_ip(ip)
            elif num == 2:
                gateway = helpers.prompt_for_ip("New default gateway: ")
                packet.set_new_gateway(gateway)
            elif num == 3:
                subnet = helpers.prompt_for_ip("New subnet mask: ")
                packet.set_new_subnet_mask(subnet)
            elif num == 4:
                port = helpers.prompt_for_number("New port: ")
                pass
            elif num == 5:
                ip_mode = helpers.prompt_for_string_in_range(
                    "DHCP or static? (dhcp/static): ", ["dhcp", "static"])
                dhcp_en = False
                if ip_mode.lower() == "dhcp":
                    dhcp_en = True
                elif ip_mode.lower() == "static":
                    dhcp_en = False
                packet.set_dhcp(dhcp_en)
            elif num == 6:
                # do nothing, packet is already set up with command == 0 for reading back current config
                pass
            else:
                print("Not a supported choice")

            raw_byte_response = helpers.send_packet(packet, sock, True)
            if not raw_byte_response:
                print("Timed out waiting for response")
            else:
                reply_packet = ArtIpProgReplyPacket(raw_byte_response)
                reply_packet.print_fields()
        elif num == 4:
            command_string = input("Enter the command string: ")
            packet = ArtCommandPacket(command_string)
            helpers.send_packet(packet, sock, False)
        elif num == 9:
            break
        else:
            print("Not a supported choice")

    sock.close()
