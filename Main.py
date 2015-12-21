# Script for PiTar UI
import Menu as MenuClass

#create list of modes
Menu = MenuClass.menu()
   
Volume = MenuClass.volume(50) #setup volume control
Looper = MenuClass.looper() #attach 8 loopers
Tremolo = MenuClass.tremolo() #attach 8 loopers

#attach modes to Menu
Menu.attachMode(Volume)
Menu.attachMode(Looper)
Menu.attachMode(Tremolo)
Menu.displayUpdate()

##read buttons
while True:
    Menu.readLCD()
