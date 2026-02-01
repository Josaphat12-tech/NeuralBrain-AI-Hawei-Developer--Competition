
import socket
import sys

host = "db.odtsblamvtqjlrxtwntr.supabase.co"
ports = [5432, 6543]

print(f"Diagnosing IPv6 connection to {host}...")

try:
    # getaddrinfo with AF_INET6
    info = socket.getaddrinfo(host, None, socket.AF_INET6)
    ipv6 = info[0][4][0]
    print(f"IPv6 Address: {ipv6}")
    
    for port in ports:
        print(f"\nTesting port {port} on IPv6...")
        try:
            # Create IPv6 socket
            sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((ipv6, port, 0, 0))
            if result == 0:
                print(f"✅ Port {port} is OPEN (Success)")
            else:
                print(f"❌ Port {port} is CLOSED or BLOCKED (Error code: {result})")
            sock.close()
        except Exception as e:
             print(f"❌ Error checking port {port}: {e}")

except Exception as e:
    print(f"IPv6 Resolution failed: {e}")
