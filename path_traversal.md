# Path Traversal Vulnerability

Path traversal (also called directory traversal) is a web security vulnerability that allows an attacker to access arbitrary files and directories outside the intended scope by manipulating file paths in user input. This can lead to sensitive file disclosure, source code access, and even remote code execution in some cases.
How Path Traversal Works

A web application may improperly handle user-supplied file paths when retrieving files. If the application does not properly validate input, an attacker can use ../ (dot-dot-slash) sequences to traverse directories and access restricted files.
Example Vulnerable Code (PHP)

```
<?php
$file = $_GET['file'];
include("uploads/" . $file);
?>

```
An attacker could request:

`http://example.com/index.php?file=../../../../../etc/passwd`

This allows reading of /etc/passwd (on Linux), potentially exposing system user accounts.
Common Exploits

1. Reading Sensitive System Files

On Linux/macOS:

http://example.com/page?file=../../../../etc/passwd
http://example.com/page?file=../../../../etc/hosts
http://example.com/page?file=../../../../root/.ssh/id_rsa

On Windows:

http://example.com/page?file=../../../../windows/win.ini
http://example.com/page?file=../../../../windows/system32/drivers/etc/hosts

2. Reading Web Application Source Code

Attackers can read PHP source files or config files:

`http://example.com/page?file=../../../../var/www/html/config.php`

This may expose database credentials.
3. Log Poisoning for Code Execution

    Inject PHP code into a log file using HTTP headers:

`curl -A "<?php system('id'); ?>" http://example.com`

Then include the log file:

    http://example.com/page?file=../../../../var/log/apache2/access.log

    This can lead to remote code execution (RCE).

Mitigation & Prevention
1. Validate & Sanitize Input

    Restrict input to expected filenames.
    Reject ../ sequences and null bytes (%00).

2. Use an Allowlist for File Access

    Instead of direct file input, use a predefined list:

```
$allowed_files = ["about.html", "contact.html"];
    if (!in_array($_GET['file'], $allowed_files)) {
        die("Invalid file!");
    }

```
3. Use Secure File Access Functions

    Use absolute paths instead of relative ones.
    Example in PHP:

```
    $file = realpath("uploads/" . $_GET['file']);
    if (strpos($file, realpath("uploads/")) !== 0) {
        die("Access denied!");
    }

```
4. Configure Web Server Security

    Disable open_basedir in PHP to restrict file access.
    Set proper permissions (chmod 640) on sensitive files.
    Use a Web Application Firewall (WAF) to block directory traversal attempts.

Conclusion

Path traversal vulnerabilities allow attackers to access files outside the intended directory, potentially exposing sensitive information or leading to RCE. Proper input validation, whitelisting, and secure file access methods are necessary to prevent this attack.
