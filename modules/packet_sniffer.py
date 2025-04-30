#!/usr/bin/env python3
"""
SpecterX Packet Sniffer Module
------------------------------
This module handles network packet capturing and analysis for the SpecterX tool.
It can capture packets on specified interfaces, analyze protocols, and log network traffic.
"""

import os
import csv
import time
import socket
import struct
import threading
import logging
from datetime import datetime
from scapy.all import sniff, IP, TCP, UDP, DNS, ARP, ICMP, Ether
from scapy.layers.http import HTTP, HTTPRequest
import pandas as pd
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SpecterX.PacketSniffer")

class PacketSniffer:
    """
    Class for capturing and analyzing network packets.
    """
    def __init__(self, interface=None, output_file="../logs/network_logs.csv"):
        """
        Initialize the packet sniffer.
        
        Args:
            interface (str): Network interface to sniff on (None for auto-selection)
            output_file (str): Path to output CSV log file
        """
        self.interface = interface
        self.output_file = output_file
        self.running = False
        self.capture_thread = None
        self.packet_count = 0
        self.protocol_stats = {
            'TCP': 0, 'UDP': 0, 'ICMP': 0, 'DNS': 0, 
            'HTTP': 0, 'HTTPS': 0, 'ARP': 0, 'Other': 0
        }
        self.connections = {}
        self.captured_packets = []
        
        # Ensure log directory exists
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
        
        # Initialize CSV file with headers if it doesn't exist
        if not os.path.exists(self.output_file):
            with open(self.output_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'Timestamp', 'Source IP', 'Source Port', 'Destination IP', 
                    'Destination Port', 'Protocol', 'Length', 'Info'
                ])

    def start_capture(self, packet_count=0, timeout=None):
        """
        Start packet capture in a separate thread.
        
        Args:
            packet_count (int): Number of packets to capture (0 for unlimited)
            timeout (int): Timeout in seconds (None for no timeout)
        """
        if self.running:
            logger.warning("Packet capture already running")
            return False
        
        self.running = True
        self.packet_count = 0
        self.protocol_stats = {
            'TCP': 0, 'UDP': 0, 'ICMP': 0, 'DNS': 0, 
            'HTTP': 0, 'HTTPS': 0, 'ARP': 0, 'Other': 0
        }
        self.captured_packets = []
        
        logger.info(f"Starting packet capture on interface {self.interface or 'auto'}")
        
        self.capture_thread = threading.Thread(
            target=self._capture_packets,
            args=(packet_count, timeout),
            daemon=True
        )
        self.capture_thread.start()
        return True

    def stop_capture(self):
        """Stop the packet capture."""
        if not self.running:
            logger.warning("No packet capture is running")
            return False
        
        self.running = False
        if self.capture_thread:
            self.capture_thread.join(timeout=2.0)
            
        logger.info(f"Packet capture stopped. Captured {self.packet_count} packets")
        return True

    def _capture_packets(self, packet_count=0, timeout=None):
        """
        Internal method to capture packets using scapy.
        
        Args:
            packet_count (int): Number of packets to capture (0 for unlimited)
            timeout (int): Timeout in seconds (None for no timeout)
        """
        try:
            sniff(
                iface=self.interface,
                prn=self._process_packet,
                count=packet_count if packet_count > 0 else None,
                timeout=timeout,
                store=False,
                stop_filter=lambda x: not self.running
            )
        except Exception as e:
            logger.error(f"Error during packet capture: {e}")
            self.running = False

    def _process_packet(self, packet):
        """
        Process a captured packet and log it.
        
        Args:
            packet: Scapy packet object
        """
        if not self.running:
            return True
        
        self.packet_count += 1
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        
        # Default values
        src_ip = "N/A"
        dst_ip = "N/A"
        src_port = "N/A"
        dst_port = "N/A"
        protocol = "Unknown"
        length = len(packet)
        info = ""
        
        # Extract Ethernet information
        if Ether in packet:
            src_mac = packet[Ether].src
            dst_mac = packet[Ether].dst
            info += f"MAC: {src_mac} -> {dst_mac} "
        
        # Process IP packets
        if IP in packet:
            src_ip = packet[IP].src
            dst_ip = packet[IP].dst
            
            # TCP packet
            if TCP in packet:
                protocol = "TCP"
                src_port = packet[TCP].sport
                dst_port = packet[TCP].dport
                flags = packet[TCP].flags
                seq = packet[TCP].seq
                info += f"Flags: {flags}, Seq: {seq} "
                
                # Identify HTTP/HTTPS
                if src_port == 80 or dst_port == 80:
                    protocol = "HTTP"
                    self.protocol_stats['HTTP'] += 1
                elif src_port == 443 or dst_port == 443:
                    protocol = "HTTPS"
                    self.protocol_stats['HTTPS'] += 1
                else:
                    self.protocol_stats['TCP'] += 1
                    
                # Parse HTTP requests
                if HTTPRequest in packet:
                    http_layer = packet[HTTPRequest]
                    http_method = http_layer.Method.decode() if hasattr(http_layer, 'Method') else "N/A"
                    http_path = http_layer.Path.decode() if hasattr(http_layer, 'Path') else "N/A"
                    http_host = http_layer.Host.decode() if hasattr(http_layer, 'Host') else "N/A"
                    info += f"HTTP: {http_method} {http_host}{http_path} "
            
            # UDP packet
            elif UDP in packet:
                protocol = "UDP"
                src_port = packet[UDP].sport
                dst_port = packet[UDP].dport
                self.protocol_stats['UDP'] += 1
                
                # DNS packets
                if DNS in packet:
                    protocol = "DNS"
                    self.protocol_stats['DNS'] += 1
                    qname = packet[DNS].qd.qname.decode() if packet[DNS].qd else "N/A"
                    info += f"Query: {qname} "
            
            # ICMP packet
            elif ICMP in packet:
                protocol = "ICMP"
                icmp_type = packet[ICMP].type
                icmp_code = packet[ICMP].code
                info += f"Type: {icmp_type}, Code: {icmp_code} "
                self.protocol_stats['ICMP'] += 1
        
        # ARP packet
        elif ARP in packet:
            protocol = "ARP"
            src_ip = packet[ARP].psrc
            dst_ip = packet[ARP].pdst
            info += f"Operation: {packet[ARP].op}, " \
                    f"Hardware: {packet[ARP].hwsrc} -> {packet[ARP].hwdst} "
            self.protocol_stats['ARP'] += 1
        
        # Other packet types
        else:
            self.protocol_stats['Other'] += 1
        
        # Track connections
        if src_ip != "N/A" and dst_ip != "N/A":
            conn_key = f"{src_ip}:{src_port}-{dst_ip}:{dst_port}"
            if conn_key not in self.connections:
                self.connections[conn_key] = {
                    'count': 1,
                    'first_seen': timestamp,
                    'last_seen': timestamp,
                    'bytes': length
                }
            else:
                self.connections[conn_key]['count'] += 1
                self.connections[conn_key]['last_seen'] = timestamp
                self.connections[conn_key]['bytes'] += length
        
        # Store packet info
        packet_info = {
            'Timestamp': timestamp,
            'Source IP': src_ip,
            'Source Port': src_port,
            'Destination IP': dst_ip,
            'Destination Port': dst_port,
            'Protocol': protocol,
            'Length': length,
            'Info': info
        }
        
        self.captured_packets.append(packet_info)
        
        # Log to CSV
        self._log_packet(packet_info)
        
        return True
    
    def _log_packet(self, packet_info):
        """
        Log packet information to CSV file.
        
        Args:
            packet_info (dict): Packet information dictionary
        """
        try:
            with open(self.output_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    packet_info['Timestamp'],
                    packet_info['Source IP'],
                    packet_info['Source Port'],
                    packet_info['Destination IP'],
                    packet_info['Destination Port'],
                    packet_info['Protocol'],
                    packet_info['Length'],
                    packet_info['Info']
                ])
        except Exception as e:
            logger.error(f"Error logging packet to CSV: {e}")
    
    def get_stats(self):
        """
        Get packet capture statistics.
        
        Returns:
            dict: Dictionary with packet statistics
        """
        return {
            'packet_count': self.packet_count,
            'protocol_stats': self.protocol_stats,
            'connection_count': len(self.connections),
            'is_running': self.running
        }
    
    def get_protocol_distribution(self):
        """
        Get protocol distribution as a dictionary.
        
        Returns:
            dict: Protocol distribution
        """
        return self.protocol_stats
    
    def get_top_connections(self, limit=10):
        """
        Get top connections by packet count.
        
        Args:
            limit (int): Number of connections to return
            
        Returns:
            list: List of top connections
        """
        sorted_connections = sorted(
            self.connections.items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )
        
        top_conns = []
        for i, (conn, data) in enumerate(sorted_connections[:limit]):
            src, dst = conn.split('-')
            top_conns.append({
                'rank': i + 1,
                'source': src,
                'destination': dst,
                'packets': data['count'],
                'bytes': data['bytes'],
                'first_seen': data['first_seen'],
                'last_seen': data['last_seen']
            })
        
        return top_conns
    
    def export_to_json(self, filename):
        """
        Export packet data to JSON file.
        
        Args:
            filename (str): Path to output JSON file
            
        Returns:
            bool: Success status
        """
        try:
            with open(filename, 'w') as f:
                json.dump({
                    'stats': self.get_stats(),
                    'connections': self.connections,
                    'packets': self.captured_packets[:1000]  # Limit to 1000 packets
                }, f, indent=2)
            logger.info(f"Exported packet data to {filename}")
            return True
        except Exception as e:
            logger.error(f"Error exporting to JSON: {e}")
            return False
    
    def analyze_traffic(self):
        """
        Analyze captured traffic and return insights.
        
        Returns:
            dict: Traffic analysis results
        """
        if not self.captured_packets:
            return {"error": "No packets captured"}
        
        # Convert to pandas for analysis
        try:
            df = pd.DataFrame(self.captured_packets)
            
            # Traffic by protocol
            protocol_counts = df['Protocol'].value_counts().to_dict()
            
            # Top source IPs
            top_sources = df['Source IP'].value_counts().head(5).to_dict()
            
            # Top destination IPs
            top_destinations = df['Destination IP'].value_counts().head(5).to_dict()
            
            # Traffic volume over time (10 second intervals)
            df['Timestamp'] = pd.to_datetime(df['Timestamp'])
            df.set_index('Timestamp', inplace=True)
            traffic_over_time = df.resample('10S').size().to_dict()
            
            # Average packet size by protocol
            avg_size_by_protocol = df.groupby('Protocol')['Length'].mean().to_dict()
            
            return {
                'protocol_distribution': protocol_counts,
                'top_source_ips': top_sources,
                'top_destination_ips': top_destinations,
                'traffic_over_time': {str(k): v for k, v in traffic_over_time.items()},
                'avg_packet_size': avg_size_by_protocol
            }
            
        except Exception as e:
            logger.error(f"Error analyzing traffic: {e}")
            return {"error": f"Analysis failed: {str(e)}"}

    @staticmethod
    def get_available_interfaces():
        """
        Get list of available network interfaces.
        
        Returns:
            list: List of interface names
        """
        from scapy.arch import get_if_list
        try:
            return get_if_list()
        except Exception as e:
            logger.error(f"Error getting interfaces: {e}")
            return []
    
    @staticmethod
    def decode_packet(packet_bytes):
        """
        Decode raw packet bytes.
        
        Args:
            packet_bytes (bytes): Raw packet data
            
        Returns:
            dict: Decoded packet information
        """
        try:
            # Basic Ethernet header decoding
            eth_length = 14
            eth_header = packet_bytes[:eth_length]
            eth = struct.unpack('!6s6sH', eth_header)
            eth_protocol = socket.ntohs(eth[2])
            
            # Parse IP packets
            if eth_protocol == 8:  # IP
                ip_header = packet_bytes[eth_length:20+eth_length]
                iph = struct.unpack('!BBHHHBBH4s4s', ip_header)
                
                version_ihl = iph[0]
                version = version_ihl >> 4
                ihl = version_ihl & 0xF
                iph_length = ihl * 4
                
                ttl = iph[5]
                protocol = iph[6]
                s_addr = socket.inet_ntoa(iph[8])
                d_addr = socket.inet_ntoa(iph[9])
                
                return {
                    'version': version,
                    'header_length': iph_length,
                    'ttl': ttl,
                    'protocol': protocol,
                    'source_ip': s_addr,
                    'dest_ip': d_addr
                }
            
            return {'error': 'Not an IP packet'}
            
        except Exception as e:
            logger.error(f"Error decoding packet: {e}")
            return {'error': str(e)}


def main():
    """Main function for standalone execution."""
    print("SpecterX Packet Sniffer")
    print("----------------------")
    
    # Get available interfaces
    interfaces = PacketSniffer.get_available_interfaces()
    print(f"Available interfaces: {', '.join(interfaces)}")
    
    # Select interface
    if interfaces:
        interface = interfaces[0]  # Default to first interface
        print(f"Using interface: {interface}")
    else:
        interface = None
        print("No interfaces found, using auto-detection")
    
    # Create sniffer
    sniffer = PacketSniffer(interface=interface)
    
    try:
        # Start packet capture
        print("Starting packet capture... Press Ctrl+C to stop")
        sniffer.start_capture()
        
        # Show live stats
        while sniffer.running:
            time.sleep(5)
            stats = sniffer.get_stats()
            print(f"\rPackets: {stats['packet_count']} | " +
                  f"TCP: {stats['protocol_stats']['TCP']} | " +
                  f"UDP: {stats['protocol_stats']['UDP']} | " +
                  f"HTTP: {stats['protocol_stats']['HTTP']} | " +
                  f"DNS: {stats['protocol_stats']['DNS']}", end="")
    
    except KeyboardInterrupt:
        print("\nStopping packet capture...")
    
    finally:
        # Stop capture and display results
        sniffer.stop_capture()
        stats = sniffer.get_stats()
        print("\n\nCapture Summary:")
        print(f"Total Packets: {stats['packet_count']}")
        print(f"Protocol Distribution: {stats['protocol_stats']}")
        print(f"Unique Connections: {stats['connection_count']}")
        
        top_conns = sniffer.get_top_connections(5)
        if top_conns:
            print("\nTop Connections:")
            for conn in top_conns:
                print(f"  {conn['source']} -> {conn['destination']}: {conn['packets']} packets")
        
        print(f"\nPacket log saved to: {sniffer.output_file}")


if __name__ == "__main__":
    main()