# Run this to print an INSERT statement with a hashed password for admin.
# Usage: python hash_admin.py your_plain_password
import sys
from werkzeug.security import generate_password_hash
if len(sys.argv) < 2:
    print("Usage: python hash_admin.py <plain_password>")
    sys.exit(1)
plain = sys.argv[1]
h = generate_password_hash(plain)
print("Use this SQL to update seed.sql or insert admin:")
print("INSERT INTO admin (username, password) VALUES ('admin', '%s');" % h)
