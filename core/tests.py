import os
import subprocess

# print(os.path.exists("smt.php"))
# subprocess.call("php smt.php 0 600", shell=True)
# with open("testfile.txt") as f:
#     contents = f.readlines()
#     print(contents)
result = '<?xml version="1.0" encoding="utf-8"?><response><pg_status>ok</pg_status><pg_payment_id>642486831</pg_payment_id><pg_redirect_url>https://customer.paybox.money/pay.html?customer=d088814c6cd15dc9e074dfdff96f97a7</pg_redirect_url><pg_redirect_url_type>need data</pg_redirect_url_type><pg_salt>O8KuZ5s0ZZ8HsGAH</pg_salt><pg_sig>6833ed23dbb009b8d4716a36c8b0579c</pg_sig></response>'
sg = ""
for i in range(10, result.__sizeof__()):
    if result[i] == 'l' and result[i + 1] == '>':
        print('gfdsgdfg')
        i += 2
        while result[i] != '<':
            sg += result[i]
            i += 1
        break
print(sg)