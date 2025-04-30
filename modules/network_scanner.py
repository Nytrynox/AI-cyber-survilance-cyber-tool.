#!/usr/bin/env python3
"""
SpecterX Network Scanner Module
-------------------------------
This module provides network scanning functionality for the SpecterX tool,
allowing users to discover active devices on the local network, identify open ports,
and gather basic network information for security analysis.
"""

import os
import csv
import socket
import threading
import ipaddress
import subprocess
import time
import platform
import datetime
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Tuple, Optional, Union, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SpecterX.NetworkScanner")

# Constants
COMMON_PORTS = [21, 22, 23, 25, 53, 80, 443, 445, 3389, 8080, 8443]
LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "network_logs.csv")
TIMEOUT = 0.5  # Socket timeout in seconds
MAX_THREADS = 100  # Max number of concurrent threads

class NetworkScanner:
    """
    Handles network scanning operations including device discovery,
    port scanning, and basic network information gathering.
    """
    
    def __init__(self, timeout: float = TIMEOUT, verbose: bool = False):
        """
        Initialize the NetworkScanner with configurable parameters.
        
        Args:
            timeout: Socket timeout in seconds
            verbose: Whether to print detailed output
        """
        self.timeout = timeout
        self.verbose = verbose
        self.os_type = platform.system().lower()
        self.scan_results = {}
        self._ensure_log_file_exists()
    
    def _ensure_log_file_exists(self) -> None:
        """Ensure log file and directory exist, create if they don't."""
        log_dir = os.path.dirname(LOG_FILE)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        if not os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([
                    'timestamp', 'scan_type', 'ip_address', 'hostname', 
                    'mac_address', 'open_ports', 'latency_ms', 'vendor'
                ])
    
    def _log_result(self, result: Dict[str, Any]) -> None:
        """
        Log scan result to CSV file.
        
        Args:
            result: Dictionary containing scan result data
        """
        timestamp = datetime.datetime.now().isoformat()
        try:
            with open(LOG_FILE, 'a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([
                    timestamp,
                    result.get('scan_type', 'unknown'),
                    result.get('ip_address', ''),
                    result.get('hostname', ''),
                    result.get('mac_address', ''),
                    ';'.join(map(str, result.get('open_ports', []))),
                    result.get('latency_ms', ''),
                    result.get('vendor', '')
                ])
            if self.verbose:
                logger.info(f"Result logged for {result.get('ip_address', 'unknown')}")
        except Exception as e:
            logger.error(f"Failed to log result: {e}")
    
    def get_local_ip(self) -> str:
        """
        Get the local IP address of the machine.
        
        Returns:
            String containing the local IP address
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # doesn't need to be reachable
            s.connect(('10.255.255.255', 1))
            ip = s.getsockname()[0]
        except Exception:
            ip = '127.0.0.1'
        finally:
            s.close()
        return ip
    
    def get_network_range(self, ip: Optional[str] = None) -> str:
        """
        Determine the network range from the local IP.
        
        Args:
            ip: Optional IP address to use instead of local IP
            
        Returns:
            Network CIDR notation (e.g., "192.168.1.0/24")
        """
        if not ip:
            ip = self.get_local_ip()
        
        # Simple method: assume /24 subnet for typical home networks
        ip_parts = ip.split('.')
        return f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.0/24"
    
    def _check_port(self, ip: str, port: int) -> bool:
        """
        Check if a specific port is open on the target IP.
        
        Args:
            ip: IP address to check
            port: Port number to check
            
        Returns:
            True if port is open, False otherwise
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(self.timeout)
        try:
            result = s.connect_ex((ip, port))
            return result == 0
        except:
            return False
        finally:
            s.close()
    
    def scan_ports(self, ip: str, ports: List[int] = None) -> List[int]:
        """
        Scan specified ports on the target IP.
        
        Args:
            ip: IP address to scan
            ports: List of ports to scan (defaults to COMMON_PORTS)
            
        Returns:
            List of open ports
        """
        if ports is None:
            ports = COMMON_PORTS
        
        open_ports = []
        
        with ThreadPoolExecutor(max_workers=min(len(ports), MAX_THREADS)) as executor:
            # Create a map of the port to its future
            future_to_port = {executor.submit(self._check_port, ip, port): port for port in ports}
            
            for future in threading.as_completed(future_to_port):
                port = future_to_port[future]
                try:
                    if future.result():
                        open_ports.append(port)
                except Exception as e:
                    logger.error(f"Error scanning port {port}: {e}")
        
        return sorted(open_ports)
    
    def _ping(self, ip: str) -> Tuple[bool, float]:
        """
        Ping an IP address and return status and latency.
        
        Args:
            ip: IP address to ping
            
        Returns:
            Tuple of (success, latency_ms)
        """
        param = '-n' if self.os_type == 'windows' else '-c'
        count_param = '1'
        timeout_param = '-W' if self.os_type != 'windows' else '-w'
        timeout_value = str(int(self.timeout * 1000)) if self.os_type == 'windows' else str(int(self.timeout))
        
        cmd = ['ping', param, count_param]
        if self.os_type != 'windows':
            cmd.extend([timeout_param, timeout_value])
        cmd.append(ip)
        
        try:
            start_time = time.time()
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output, error = proc.communicate()
            end_time = time.time()
            
            latency = (end_time - start_time) * 1000  # Convert to ms
            
            # Check if ping was successful
            return proc.returncode == 0, latency
        except Exception as e:
            logger.error(f"Ping error for {ip}: {e}")
            return False, 0
    
    def get_mac_address(self, ip: str) -> str:
        """
        Attempt to get the MAC address of a device on the network.
        Uses ARP on most systems.
        
        Args:
            ip: IP address to lookup
            
        Returns:
            MAC address if found, empty string otherwise
        """
        try:
            if self.os_type == 'windows':
                # Windows ARP command
                proc = subprocess.Popen(['arp', '-a', ip], stdout=subprocess.PIPE)
                output = proc.communicate()[0].decode('utf-8')
                for line in output.splitlines():
                    if ip in line:
                        parts = line.split()
                        if len(parts) >= 2:
                            return parts[1].strip()
            else:
                # Linux/Mac ARP command
                proc = subprocess.Popen(['arp', '-n', ip], stdout=subprocess.PIPE)
                output = proc.communicate()[0].decode('utf-8')
                for line in output.splitlines():
                    if ip in line:
                        parts = line.split()
                        if len(parts) >= 3:
                            return parts[2].strip()
        except Exception as e:
            logger.error(f"Error getting MAC address for {ip}: {e}")
        
        return ""
    
    def get_hostname(self, ip: str) -> str:
        """
        Attempt to resolve the hostname for an IP address.
        
        Args:
            ip: IP address to lookup
            
        Returns:
            Hostname if resolved, empty string otherwise
        """
        try:
            hostname, _, _ = socket.gethostbyaddr(ip)
            return hostname
        except:
            return ""
    
    def scan_single_host(self, ip: str, scan_ports: bool = True) -> Dict[str, Any]:
        """
        Perform a comprehensive scan of a single host.
        
        Args:
            ip: IP address to scan
            scan_ports: Whether to scan ports
            
        Returns:
            Dictionary with scan results
        """
        result = {
            'scan_type': 'host',
            'ip_address': ip,
            'hostname': '',
            'mac_address': '',
            'open_ports': [],
            'latency_ms': 0,
            'vendor': ''  # Would require external database
        }
        
        # Check if host is up
        is_up, latency = self._ping(ip)
        if not is_up:
            return result
        
        result['latency_ms'] = round(latency, 2)
        
        # Get hostname
        hostname = self.get_hostname(ip)
        if hostname:
            result['hostname'] = hostname
        
        # Get MAC address
        mac = self.get_mac_address(ip)
        if mac:
            result['mac_address'] = mac
        
        # Scan ports if requested
        if scan_ports:
            result['open_ports'] = self.scan_ports(ip)
        
        # Log the result
        self._log_result(result)
        
        return result
    
    def scan_network(self, network_range: Optional[str] = None, scan_ports: bool = True) -> List[Dict[str, Any]]:
        """
        Scan the entire network range.
        
        Args:
            network_range: Network range in CIDR notation (e.g., "192.168.1.0/24")
            scan_ports: Whether to scan ports on discovered hosts
            
        Returns:
            List of dictionaries with scan results for each alive host
        """
        if not network_range:
            network_range = self.get_network_range()
        
        if self.verbose:
            logger.info(f"Starting network scan on {network_range}")
        
        network = ipaddress.ip_network(network_range)
        host_count = network.num_addresses
        
        if host_count > 1024:
            logger.warning(f"Large network detected ({host_count} hosts). This may take a while.")
        
        results = []
        active_hosts = []
        
        # First pass: find live hosts with ping
        with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            futures = {}
            for ip in network.hosts():
                ip_str = str(ip)
                futures[executor.submit(self._ping, ip_str)] = ip_str
            
            for future in threading.as_completed(futures):
                ip_str = futures[future]
                try:
                    is_up, _ = future.result()
                    if is_up:
                        active_hosts.append(ip_str)
                        if self.verbose:
                            logger.info(f"Host {ip_str} is up")
                except Exception as e:
                    logger.error(f"Error scanning {ip_str}: {e}")
        
        # Second pass: detailed scan of active hosts
        with ThreadPoolExecutor(max_workers=min(len(active_hosts), MAX_THREADS)) as executor:
            futures = {executor.submit(self.scan_single_host, ip, scan_ports): ip for ip in active_hosts}
            
            for future in threading.as_completed(futures):
                ip_str = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                    self.scan_results[ip_str] = result
                except Exception as e:
                    logger.error(f"Error during detailed scan of {ip_str}: {e}")
        
        return results
    
    def get_network_overview(self) -> Dict[str, Any]:
        """
        Get an overview of the network including gateway, subnet, and local interfaces.
        
        Returns:
            Dictionary with network information
        """
        overview = {
            'local_ip': self.get_local_ip(),
            'network_range': self.get_network_range(),
            'gateway': '',
            'interfaces': [],
            'dns_servers': []
        }
        
        # Try to identify gateway
        if self.os_type == 'windows':
            try:
                output = subprocess.check_output('ipconfig', shell=True).decode('utf-8')
                for line in output.splitlines():
                    if 'Default Gateway' in line:
                        parts = line.split(':')
                        if len(parts) > 1:
                            gateway = parts[1].strip()
                            if gateway and gateway != '':
                                overview['gateway'] = gateway
                                break
            except:
                pass
        else:
            # Linux/Mac
            try:
                output = subprocess.check_output('netstat -rn | grep default', shell=True).decode('utf-8')
                parts = output.split()
                if len(parts) > 1:
                    overview['gateway'] = parts[1]
            except:
                pass
        
        # Get DNS servers
        if self.os_type == 'windows':
            try:
                output = subprocess.check_output('ipconfig /all', shell=True).decode('utf-8')
                for line in output.splitlines():
                    if 'DNS Servers' in line:
                        parts = line.split(':')
                        if len(parts) > 1:
                            dns = parts[1].strip()
                            if dns and dns != '':
                                overview['dns_servers'].append(dns)
            except:
                pass
        else:
            # Linux/Mac
            try:
                if os.path.exists('/etc/resolv.conf'):
                    with open('/etc/resolv.conf', 'r') as f:
                        for line in f:
                            if line.startswith('nameserver'):
                                parts = line.split()
                                if len(parts) > 1:
                                    overview['dns_servers'].append(parts[1])
            except:
                pass
        
        # Get network interfaces
        if self.os_type == 'windows':
            try:
                output = subprocess.check_output('ipconfig /all', shell=True).decode('utf-8')
                interface = {}
                for line in output.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    
                    if ':' not in line and interface:
                        overview['interfaces'].append(interface)
                        interface = {}
                    elif 'adapter' in line.lower() and ':' in line:
                        interface = {'name': line.split(':')[0].strip()}
                    elif ':' in line and interface:
                        key, value = line.split(':', 1)
                        key = key.strip().lower().replace(' ', '_')
                        value = value.strip()
                        if value:
                            interface[key] = value
                
                if interface:
                    overview['interfaces'].append(interface)
            except Exception as e:
                logger.error(f"Error getting network interfaces: {e}")
        else:
            # Linux/Mac - simplified
            try:
                if self.os_type == 'darwin':  # macOS
                    cmd = "ifconfig"
                else:  # Linux
                    cmd = "ip addr"
                
                output = subprocess.check_output(cmd, shell=True).decode('utf-8')
                interface = {}
                for line in output.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    
                    if line[0].isalnum() and not line[0].isspace() and interface:
                        overview['interfaces'].append(interface)
                        interface = {'name': line.split(':')[0]}
                    elif line[0].isalnum() and not line[0].isspace():
                        interface = {'name': line.split(':')[0]}
                    elif 'inet ' in line and interface:
                        addr = line.split('inet ')[1].split(' ')[0]
                        interface['ipv4'] = addr
                    elif 'inet6' in line and interface:
                        addr = line.split('inet6 ')[1].split(' ')[0]
                        interface['ipv6'] = addr
                    elif 'ether' in line and interface:
                        addr = line.split('ether ')[1].split(' ')[0]
                        interface['mac'] = addr
                
                if interface:
                    overview['interfaces'].append(interface)
            except Exception as e:
                logger.error(f"Error getting network interfaces: {e}")
        
        return overview
    
    def run_continuous_monitoring(self, interval: int = 300, callback=None) -> None:
        """
        Start continuous network monitoring in a separate thread.
        
        Args:
            interval: Scan interval in seconds
            callback: Optional callback function to call with results
        """
        def monitor_thread():
            while True:
                try:
                    results = self.scan_network()
                    if callback:
                        callback(results)
                    time.sleep(interval)
                except Exception as e:
                    logger.error(f"Error in monitoring thread: {e}")
                    time.sleep(60)  # Shorter interval on error
        
        threading.Thread(target=monitor_thread, daemon=True).start()
        logger.info(f"Started continuous monitoring (interval: {interval}s)")


def main():
    """Main function for running the scanner standalone."""
    import argparse
    
    parser = argparse.ArgumentParser(description='SpecterX Network Scanner')
    parser.add_argument('--range', help='Network range to scan (CIDR notation)')
    parser.add_argument('--timeout', type=float, default=TIMEOUT, help='Timeout for connections')
    parser.add_argument('--ports', action='store_true', help='Enable port scanning')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
    args = parser.parse_args()
    
    scanner = NetworkScanner(timeout=args.timeout, verbose=args.verbose)
    
    print(f"[+] SpecterX Network Scanner")
    print(f"[+] Local IP: {scanner.get_local_ip()}")
    
    net_range = args.range if args.range else scanner.get_network_range()
    print(f"[+] Scanning network: {net_range}")
    
    results = scanner.scan_network(net_range, scan_ports=args.ports)
    
    print(f"[+] Found {len(results)} active hosts")
    for host in results:
        print(f"\n[+] Host: {host['ip_address']}")
        if host['hostname']:
            print(f"    Hostname: {host['hostname']}")
        if host['mac_address']:
            print(f"    MAC: {host['mac_address']}")
        print(f"    Latency: {host['latency_ms']}ms")
        if args.ports and host['open_ports']:
            print(f"    Open ports: {', '.join(map(str, host['open_ports']))}")
    
    print(f"\n[+] Results saved to: {LOG_FILE}")


if __name__ == "__main__":
    main()