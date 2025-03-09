# Symbolic Link

A **symbolic link (symlink)** is a file that points to another file or directory, essentially acting as a shortcut. It allows you to access a target file or directory from a different location without duplicating the content.

## Key Things to Keep in Mind:
1. **Target Dependency**: If the target of the symlink is deleted or moved, the symlink becomes broken (dangling symlink).
2. **Security Risks**: Symlinks can be exploited to access sensitive files or bypass restrictions (e.g., linking to `/etc/passwd`).
3. **Permissions**: The symlink's permissions don't matter; what matters are the target file's permissions.
4. **Visibility**: It appears as a regular file or directory, but can point to something hidden or critical.
5. **Management**: Always check the target of symlinks to ensure they aren't pointing to sensitive or restricted files.

In short, while symlinks can be useful, they can also pose security risks if not managed carefully.

Let's break down the commands and what happens in each step:

## Step 1: Creating the Symlink
```bash
ln -s /root/root.txt huh.txt
```
- This creates a **symbolic link** named `huh.txt` in the current directory, which points to `/root/root.txt`.
- **Why is this important?**
  `/root/root.txt` is a file that likely contains sensitive information (perhaps used for capturing flags in a Capture The Flag (CTF) challenge or similar). By creating this symlink, you're creating a shortcut to this sensitive file, potentially allowing a user to access it without needing direct access to `/root/root.txt`.

## Step 2: Creating Another Symlink to a PNG File
```bash
ln -s /home/bob/huh.txt huh.png
```
- This creates another **symbolic link** named `huh.png` in the current directory. However, instead of pointing to a critical file, it points to `huh.txt`, which we just created in Step 1.
- **Why does this matter?**
  Now, `huh.png` is a symlink that eventually points to `/root/root.txt`. The target file `/root/root.txt` is potentially sensitive, but the symlink is named `huh.png`, which makes it appear to be a harmless `.png` image.

## Step 3: Running the Script
```bash
sudo CHECK_CONTENT=true /usr/bin/bash /opt/ghost/clean_symlink.sh /home/bob/huh.png
```
- You are running the script `/opt/ghost/clean_symlink.sh` and passing `huh.png` (the symlink you just created) as an argument.
- **Breaking down the script execution:**
  1. **Check for File Type**: The script checks if the provided file is a `.png`. Since `huh.png` ends in `.png`, the script proceeds without error.
  2. **Check if the Argument is a Symlink**: The script checks if `huh.png` is a symlink using `test -L`. Since it is, it continues.
  3. **Inspect Symlink Target**: The script gets the target of the symlink `huh.png` (which is `huh.txt`, pointing to `/root/root.txt`) and checks if it points to sensitive directories (`/etc` or `/root`).
     - **Important**: The symlink target points to `/root/root.txt`, which is in the `/root` directory. Since this is a critical file, the script flags it as potentially dangerous.
  4. **Action on Dangerous Symlink**:
     - The script moves the symlink (`huh.png`) to the quarantine directory (`/var/quarantined`) to prevent potential misuse.
     - It outputs the message:
       ```
       Link found [ /home/bob/huh.png ] , moving it to quarantine
       ```
  5. **Display File Content**: Since the `CHECK_CONTENT=true` flag is set, the script attempts to show the contents of the quarantined file (`huh.png`). However, because `huh.png` is a symlink (not a regular file), the script shows nothing or an error when trying to display the symlink's content.

## **What Happened?**
- The script detected that the symlink `huh.png` pointed to a potentially sensitive file (`/root/root.txt`).
- Since the symlink was deemed dangerous (pointing to `/root`), the script moved it to a quarantine directory (`/var/quarantined`).
- **The content check (`CHECK_CONTENT=true`)** didn't show any contents because the symlink itself doesn't contain readable content—it points to the `huh.txt` file, which, in turn, points to the `/root/root.txt` file.

### **Why This Could Be Useful for a Malicious actor:**
1. **Accessing Critical Files Using Symlinks**:
   A hacker might create a symlink that points to a sensitive file, like `/root/root.txt`, as a way to indirectly access it. In this case, even though the hacker creates a symlink with a harmless name (`huh.png`), it ultimately leads to a sensitive file that can be read, downloaded, or otherwise exploited.

2. **Bypassing Security Measures**:
   If a system is scanning for or filtering access to sensitive files directly, symlinks can be used to bypass such filters. This script attempts to mitigate that risk by detecting symlinks that point to critical files and quarantining them.

3. **Quarantining Suspicious Symlinks**:
   This script can help an administrator isolate suspicious symlinks that may be created to bypass security measures. However, a hacker might attempt to find ways to prevent such symlinks from being detected or manipulate the script's behavior to allow the symlink to remain or move it back to its original location after quarantine.

