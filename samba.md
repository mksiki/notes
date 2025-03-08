Samba is an open-source implementation of the SMB (Server Message Block) protocol, allowing file and printer sharing between Unix/Linux and Windows systems. It enables interoperability by letting Linux act as a Windows file server or domain controller.

### **Ports Used by Samba:**
- **TCP/UDP 137** (NetBIOS Name Service)
- **TCP/UDP 138** (NetBIOS Datagram Service)
- **TCP/UDP 139** (NetBIOS Session Service)
- **TCP/UDP 445** (Direct SMB over TCP, used in modern implementations)

### **Why is Samba Important for Hackers?**
- **Misconfigurations** can expose shared files, allowing unauthorized access.
- **Null session vulnerabilities** can reveal usernames, shares, and even system information.
- **Exploitable versions** can be targeted using tools like `EternalBlue` (MS17-010).
- **Privilege escalation** can be achieved by exploiting writable shares or weak permissions.
- **Lateral movement** is possible within a network if credentials are obtained.

### **Common Tools Used for Attacks:**
- `nmap` (`smb-enum-shares`, `smb-os-discovery`)
- `smbclient` (for interacting with shares)
- `enum4linux` (for enumeration)
- `Metasploit` (for exploitation)
- `CrackMapExec` (for brute-forcing and lateral movement)

