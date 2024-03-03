import datetime
import time

while True:
   timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
   filename = f"/var/log/log_{timestamp}.txt"

   with open(filename, "w") as f:
      f.write(timestamp)

   time.sleep(1)