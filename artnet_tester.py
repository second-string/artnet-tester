import helpers

from artnet_packet_tx import ArtPollPacket, ArtProgIpPacket, ArtCommandPacket, ArtDmxPacket
from artnet_packet_rx import ArtPollReplyPacket, ArtIpProgReplyPacket

if __name__ == "__main__":
    print("Art-Net packet tester")

    sock = helpers.open_connection()

    selected_universes = [0]

    while True:
        print()
        print(
            f"Sending packets to {helpers.dest_ip}:{helpers.dest_port}. Choose an option"
        )
        print(f"Selected universes: {selected_universes}")
        print()
        print("1) Change destination IP or port for test packets")
        print("2) Select universe(s) to send to")
        print()
        print("3) Send ArtPoll")
        print("4) Send ArtIPProg")
        print("5) Send ArtCommand")
        print("6) Send ArtDMX")
        print("7) Send static ArtDMX (full universe of one byte value)")
        print("8) Send cycling RGB ArtDMX (ctrl+c or any key to stop)")
        print("9) Send cycling RGBW ArtDMX (ctrl+c or any key to stop)")
        print("10) Exit")
        print()

        valid_input = False
        num = helpers.prompt_for_number_in_range("Choice: ", range(1, 11))
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
                sock.close()
                sock = helpers.open_connection()
            elif num == 2:
                helpers.dest_port = helpers.prompt_for_number_in_range(
                    "New port: ", range(1, 10000))
        elif num == 2:
            print("Enter space-delimited list of universes (0-32767).")
            selected_universes = helpers.prompt_for_numbers_in_range(
                "Universes: ", range(0, 32768))
            print(f"Selected universes: {selected_universes}")
        elif num == 3:
            packet = ArtPollPacket()
            raw_byte_response = helpers.send_packet(packet, sock, True)
            if not raw_byte_response:
                print("Timed out waiting for response")
            else:
                reply_packet = ArtPollReplyPacket(raw_byte_response)
                reply_packet.print_fields()
        elif num == 4:
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
        elif num == 5:
            command_string = input("Enter the command string: ")
            packet = ArtCommandPacket(command_string)
            helpers.send_packet(packet, sock, False)
        elif num == 6:
            print("Enter DMX data bytes (1-512 bytes, space-delimited).")
            print("Use decimal (e.g. 255) or hex with 0x prefix (e.g. 0xFF).")
            data_bytes = None
            while data_bytes is None:
                raw = input("Data: ").strip()
                tokens = raw.split()
                if len(tokens) < 1 or len(tokens) > 512:
                    print(f"Must enter 1-512 bytes, got {len(tokens)}")
                    continue
                parsed = []
                error = False
                for token in tokens:
                    try:
                        if token.lower().startswith("0x"):
                            val = int(token, 16)
                        else:
                            val = int(token)
                        if val < 0 or val > 255:
                            print(f"Value {token} out of range (0-255)")
                            error = True
                            break
                        parsed.append(val)
                    except ValueError:
                        print(f"Invalid value: {token}")
                        error = True
                        break
                if not error:
                    data_bytes = parsed
            for universe in selected_universes:
                packet = ArtDmxPacket(universe, data_bytes)
                helpers.send_packet(packet, sock, False)
            print(
                f"Sent ArtDMX: universes={selected_universes}, {len(data_bytes)} byte(s)"
            )
        elif num == 7:
            byte_val = helpers.prompt_for_number_in_range(
                "Byte value (0-255): ", range(0, 256))
            data_bytes = [byte_val] * 512
            for universe in selected_universes:
                packet = ArtDmxPacket(universe, data_bytes)
                helpers.send_packet(packet, sock, False)
            print(
                f"Sent ArtDMX: universes={selected_universes}, 512 bytes of {byte_val}"
            )
        elif num == 8:
            print(
                f"Cycling R -> G -> B on universes {selected_universes}. Press any key to stop."
            )
            colors = [("R", 0), ("G", 1), ("B", 2)]
            idx = 0
            try:
                while True:
                    label, offset = colors[idx]
                    data_bytes = [0] * 512
                    for i in range(offset, 510, 3):
                        data_bytes[i] = 128
                    for universe in selected_universes:
                        packet = ArtDmxPacket(universe, data_bytes)
                        helpers.send_packet(packet, sock, False)
                    print(f"Sent {label}=128 to {selected_universes}")
                    if helpers.wait_or_key_pressed(1.0):
                        break
                    idx = (idx + 1) % len(colors)
            except KeyboardInterrupt:
                print()
            print("Stopped RGB cycle")
        elif num == 9:
            print(
                f"Cycling R -> G -> B -> W on universes {selected_universes}. Press any key to stop."
            )
            colors = [("R", 0), ("G", 1), ("B", 2), ("W", 3)]
            idx = 0
            try:
                while True:
                    label, offset = colors[idx]
                    data_bytes = [0] * 512
                    for i in range(offset, 512, 4):
                        data_bytes[i] = 128
                    for universe in selected_universes:
                        packet = ArtDmxPacket(universe, data_bytes)
                        helpers.send_packet(packet, sock, False)
                    print(f"Sent {label}=128 to {selected_universes}")
                    if helpers.wait_or_key_pressed(1.0):
                        break
                    idx = (idx + 1) % len(colors)
            except KeyboardInterrupt:
                print()
            print("Stopped RGBW cycle")
        elif num == 10:
            break
        else:
            print("Not a supported choice")

    sock.close()
