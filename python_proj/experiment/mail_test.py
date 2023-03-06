import perceval
from perceval.backends.core.mbox import MBox
import os
import json

import logging
logging.basicConfig(level=logging.DEBUG)

mbox_uri = "https://mail-archives.apache.org/mod_mbox/httpd-dev/"
mbox_dir = 'archives'
repo = MBox(uri=mbox_uri, dirpath=mbox_dir)
with open(os.path.abspath("./data/mail_test.json"), "w+", encoding="utf-8") as output_file:
    for message in repo.fetch():
        output_file.write(json.dumps(message))
        print(message['data']['Subject'])


# from perceval.backends.core.pipermail import Pipermail
# mbox_uri = "https://mail-archives.apache.org/mod_mbox/httpd-dev/"
# path = os.path.abspath("./archives")
# pm = Pipermail(mbox_uri, dirpath=path)
# out_path = os.path.abspath("./data/mail_test.json")
# with open(out_path, "w+", encoding="utf-8") as output_file:
#     for message in pm.fetch():
#         output_file.write(json.dumps(message))
#         print(message['data']['Subject'])





# This works though:
# curl -X GET https://lists.apache.org/api/mbox.lua?list=dev@httpd.apache.org&date=2016-06
