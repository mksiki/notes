Vulnerability: Path Traversal in /download

The issue arises from this part of the code:

```
ticket = request.args.get('ticket')
json_filepath = os.path.join(TICKETS_DIR, ticket)
```
    ticket comes directly from user input (request.args.get('ticket')).
    There is no validation to ensure the filename is within TICKETS_DIR.
    An attacker can manipulate the ticket parameter to access arbitrary files.

Exploitation Example

An attacker could request:

`http://127.0.0.1:5000/download?ticket=../../../../etc/passwd`

Which results in:

`json_filepath = os.path.join("tickets", "../../../../etc/passwd")`

This resolves to /etc/passwd, allowing the attacker to read it.
Impact

    Read arbitrary files:
        /etc/passwd, /etc/shadow (Linux)
        C:\Windows\win.ini (Windows)
    Leak sensitive information:
        Environment variables
        Source code files
        Logs

Fix: Restrict File Paths
1. Validate Input (Allow Only JSON Filenames)

Modify the /download endpoint:

```
import re

@app.route('/download', methods=['GET'])
def download_ticket():
    ticket = request.args.get('ticket')

    if not ticket or not re.match(r'^[a-f0-9\-]+\.json$', ticket):
        return jsonify({"error": "Invalid ticket filename"}), 400

    json_filepath = os.path.join(TICKETS_DIR, ticket)
```
    # Ensure file is inside the intended directory
    if not os.path.exists(json_filepath) or not json_filepath.startswith(os.path.abspath(TICKETS_DIR)):
        return jsonify({"error": "Ticket not found"}), 404

    `return send_file(json_filepath, as_attachment=True, download_name=ticket)`

2. Use safe_join (Flask Secure File Handling)

from werkzeug.utils import safe_join

```
json_filepath = safe_join(TICKETS_DIR, ticket)
if not os.path.exists(json_filepath):
    return jsonify({"error": "Ticket not found"}), 404
```
This prevents attackers from escaping TICKETS_DIR.
Conclusion

Fix it by:

    Validating filenames (only allow UUID-style JSON files).
    Using safe_join to prevent directory traversal.
    Checking file paths to ensure they remain within TICKETS_DIR.
