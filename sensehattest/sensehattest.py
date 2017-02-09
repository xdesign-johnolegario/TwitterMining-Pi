#from sense_hat import SenseHat
from time import sleep
import threading

flash = False

def do_flash():
    global flash
    while True:
        if flash:
            print("start flashing")
            sleep(5)
            print("stop flashing")
            flash = False

t1 = threading.Thread(target=do_flash)
t1.start()



#sense = SenseHat()
#sense.show_message('hERMES!')

def do_flash_asynchronously():
    global flash
    flash = True

for i in range(0, 100):
    if i % 10 == 0:
         do_flash_asynchronously()
    print(i)
    sleep(1)

t1.join()
