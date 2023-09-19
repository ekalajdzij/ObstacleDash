"""
Ugradbeni sistemi 2023
Obstacle Dash
"""
from ili934xnew import ILI9341, color565
from ili9341 import Display, color565
from machine import Pin, SPI, ADC, Timer
from micropython import const
from lib.umqtt.robust import MQTTClient
import network
import os
import glcdfont
import tt14
import tt24
import tt32
import time

# Definisanje pinova tastera
taster1=Pin(0,Pin.IN)
taster2=Pin(1,Pin.IN)
taster3=Pin(2,Pin.IN)
taster4=Pin(3,Pin.IN)

# Definisanje pinova za joystick
X_JOYSTICK = ADC(Pin(26))
Y_JOYSTICK = ADC(Pin(27))
TASTER_JOYSTICK = Pin(22, Pin.IN, Pin.PULL_UP) # 0 pritisnuto

# Dimenzije displeja
SCR_WIDTH =  const(320)
SCR_HEIGHT = const(240)
SCR_ROT = const(0)
CENTER_Y = int(SCR_WIDTH/2)
CENTER_X = int(SCR_HEIGHT/2)

# Podešenja SPI komunikacije sa displejem
TFT_CLK_PIN = const(18)
TFT_MOSI_PIN = const(19)
TFT_MISO_PIN = const(16)
TFT_CS_PIN = const(17)
TFT_RST_PIN = const(20)
TFT_DC_PIN = const(15)

spi = SPI(
    0,
    baudrate=62500000,
    miso=Pin(TFT_MISO_PIN),
    mosi=Pin(TFT_MOSI_PIN),
    sck=Pin(TFT_CLK_PIN))

display = ILI9341(
    spi,
    cs=Pin(TFT_CS_PIN),
    dc=Pin(TFT_DC_PIN),
    rst=Pin(TFT_RST_PIN),
    w=SCR_WIDTH,
    h=SCR_HEIGHT,
    r=SCR_ROT)

display2 = Display(
    spi,
    dc=Pin(TFT_DC_PIN),
    cs=Pin(TFT_CS_PIN),
    rst=Pin(TFT_RST_PIN))

#Boje
WHITE = color565(255, 255, 255)
BLACK = color565(0, 0, 0)
BLUE = color565(0, 0, 255)
YELLOW = color565(255, 255, 0)
RED = color565(255,0,0)
GREEN = color565(0,188,0)
GREY = color565(96,96,96)

# Definisanje varijabli
direction = 0               # 1 2 3 4 (Gore , dole ,lijevo ,desno)
pin=['*','*','*','*']       # pin za multiplayer
pause=False
game_over=False
score=0
obstacle_pos=[0,3,1,4,2]
car_position=2
x_o=0
y_o=0                       # pozicija prepreke
car_position=2              # ima 5 pozicija , krece u sredini
best_score = 0
last_position=car_position
speed=[30,45,54,90]
level=1
request_accepted=False
request_answerd=False
player2_pin=""
multiplayer = False
i=0                         # varijabla za pracenje pozicije traka ceste
multiplayer_score=-1
debounce = 0

# Definisanje tema
TEMASUBZAHTJEV='obstacledash/player2'
TEMAPUBZAHTJEV='obstacledash/player1'
TEMASUBZAHTJEVPRIHVACEN='obstacledash/player2prihvacen'
TEMASUBZAHTJEVODBIJEN='obstacledash/player2odbijen'
TEMAPUBZAHTJEVPRIHVACEN='obstacledash/player1prihvacen'
TEMAPUBZAHTJEVODBIJEN='obstacledash/player1odbijen'
TEMASUBPIN='obstacledash/player2pin'
TEMAPUBPIN='obstacledash/player1pin'
TEMASUBEND='obstacledash/player2end'
TEMAPUBEND='obstacledash/player1end'

# Brisanje displeja 
display.erase()

# Povezivanje na WiFi mrežu
wlan=network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect("Ugradbeni", "USlaboratorija220")

while not wlan.isconnected():
    print("Waiting to connect:")
    time.sleep(1)
    
print(wlan.ifconfig())

#Funkcija koja se poziva kada dobijemo poruku na subscribanu temu
def sub(t,p):
    global request_answerd, request_accepted, player2_pin,multiplayer_score
    print("Message arrived: ",t," value: ",p)
    if t==b'obstacledash/player2':
        recivedRequestScreen()
    elif t==b'obstacledash/player2prihvacen':
        request_accepted=True
        request_answerd=True
    elif t==b'obstacledash/player2odbijen':
        request_accepted=False
        request_answerd=True
    elif t==b'obstacledash/player2pin':
        player2_pin=p
    elif t==b'obstacledash/player2end':    
        multiplayer_score = int(p)
    
# Povezivanje na na MQTT broker
mqtt_conn=MQTTClient(client_id='player1fjgkfldk',server='broker.hivemq.com',user="",password="",port=1883)
mqtt_conn.set_callback(sub)
mqtt_conn.connect()

# Pretplaćivanje na teme
mqtt_conn.subscribe(TEMASUBZAHTJEV)
mqtt_conn.subscribe(TEMASUBZAHTJEVPRIHVACEN)
mqtt_conn.subscribe(TEMASUBZAHTJEVODBIJEN)
mqtt_conn.subscribe(TEMASUBPIN)
mqtt_conn.subscribe(TEMASUBEND)
print('Connected to {0} MQTT broker'.format('broker.hivemq.com'))


#Dizajnovi ekrana

# Dizajn pocetnog ekrana
def makeHomeScreenDesign():
    display.erase()
    display.set_color(WHITE,BLACK)
    display.fill_rectangle(0,0,SCR_HEIGHT,SCR_WIDTH,BLACK)
    display.fill_rectangle(0,0,SCR_WIDTH,110,BLUE)
    display2.draw_rectangle(10,120,220,SCR_HEIGHT-50,BLUE)
    display.set_font(tt32)
    display.set_color(WHITE,BLUE)
    display.set_pos(20,50)
    display.print('Obstacle Dash')
    display.set_color(WHITE,BLACK)
    display.set_pos(35,160)
    display.print('Singleplayer')
    display.set_color(WHITE,BLACK)
    display.set_pos(35,220)
    display.print('Multiplayer')

# Dizajn ekrana tokom igre
def makeGameScreenDesign():
    display.erase()
    display.fill_rectangle(0,0,SCR_HEIGHT,SCR_WIDTH,GREY)
    display.set_color(WHITE,BLACK)
    display.set_font(tt32)
    display2.draw_vline(0, 0, 319, GREEN)
    display2.draw_vline(1, 0, 319, GREEN)
    display2.draw_vline(2, 0, 319, GREEN)
    display2.draw_vline(3, 0, 319, GREEN)
    display2.draw_vline(236, 0, 319, GREEN)
    display2.draw_vline(237, 0, 319, GREEN)
    display2.draw_vline(238, 0, 319, GREEN)
    display2.draw_vline(239, 0, 319, GREEN)

# Dizajn ekrana koji se prikaze nakon zavrsetka igre u singleplayer-u    
def makeGameOverScreenDesign():
    display.erase()
    display.set_color(WHITE,BLACK)
    display.fill_rectangle(0,0,SCR_HEIGHT,SCR_WIDTH,WHITE)
    display.fill_rectangle(0,0,SCR_HEIGHT,180,RED)
    display2.draw_rectangle(10,190,SCR_HEIGHT-20,SCR_WIDTH-200,RED)
    display.set_color(WHITE,RED)
    display.set_font(tt32)
    display.set_pos(40,30)
    display.print('GAME OVER')
    display.set_font(tt24)
    display.set_pos(40,90)
    display.print('Score: ')
    display.set_pos(40,140)
    display.print('Best score: ')
    display.set_color(RED,WHITE)
    display.set_pos(35,220)
    display.print('Play again')
    display.set_pos(35,260)
    display.print('Exit')

# Dizajn ekrana pri slanju zahtjeva za multiplayer  
def makeSentRequestScreenDesign():
    display.erase()
    display.set_color(WHITE,BLACK)
    display.fill_rectangle(0,0,SCR_HEIGHT,SCR_WIDTH,BLUE)
    display.set_font(tt32)
    display.set_color(WHITE,BLUE)
    display.set_pos(20,50)
    display.print('Request sent')
    display.set_pos(20,150)
    display.print('Waiting for other player to accept ...')

# Dizajn ekrana pri primaju zahtjeva za multipalyer igru    
def makeRecivedRequestScreenDesign():
    display.erase()
    display.set_color(WHITE,BLACK)
    display.fill_rectangle(0,0,SCR_WIDTH,SCR_HEIGHT,BLACK)
    display.fill_rectangle(0,0,SCR_WIDTH,110,BLUE)
    display2.draw_rectangle(10,120,220,SCR_HEIGHT-50,BLUE)
    display.set_font(tt32)
    display.set_color(WHITE,BLUE)
    display.set_pos(20,40)
    display.print('Player 2 sent you a request')
    display.set_color(WHITE,BLACK)
    display.set_pos(35,145)
    display.print('Accept')
    display.set_pos(35,195)
    display.print('Decline')

# Dizajn ekrana za ukucavanje pin-a    
def makePinScreenDesign():
    display.erase()
    display.set_color(WHITE,BLACK)
    display.fill_rectangle(0,0,SCR_HEIGHT,SCR_WIDTH,BLACK)
    display.fill_rectangle(0,0,SCR_HEIGHT,110,BLUE)
    display.set_font(tt32)
    display.set_color(WHITE,BLUE)
    display.set_pos(20,50)
    display.print('Insert your pin:')
    display.set_color(WHITE,BLACK)
   
    display.set_pos(52,153)
    display2.draw_rectangle(40,150,35,35,BLUE)
    display.set_pos(92,153)
    display2.draw_rectangle(80,150,35,35,BLUE)
    display.set_pos(132,153)
    display2.draw_rectangle(120,150,35,35,BLUE)
    display.set_pos(172,153)
    display2.draw_rectangle(160,150,35,35,BLUE)

# Dizajn ekrana koji se prikaze nakon zavrsetka igre u multiplayer-u 
def makeMultiplayerResultScreenDesign():
    display.erase()
    display.set_color(WHITE,BLACK)
    display.fill_rectangle(0,0,SCR_HEIGHT,SCR_WIDTH,RED)
    display.set_color(WHITE,RED)
    display.set_font(tt32)

# Dizajn ekrana koji se prikaze igracu koji prvi zavrsi igru u multiplayer-u
def waitingForOtherPlyerScreenDesign():
    display.erase()
    display.set_color(WHITE,BLACK)
    display.fill_rectangle(0,0,SCR_HEIGHT,SCR_WIDTH,BLUE)
    display.set_font(tt32)
    display.set_color(WHITE,BLUE)
    display.set_pos(20,100)
    display.print('Waiting for other player to finish')

# Funkcija za pracenje pozicije joystick-a
def joystickDirections():
    global direction
    x_value = X_JOYSTICK.read_u16()
    y_value = Y_JOYSTICK.read_u16()
    if(y_value<2000):
        direction=1         # smjer joysticka je gore
    elif(y_value>50000):
        direction=2         # smjer joysticka je goredole
    if(x_value<2000):
        direction=3         # smjer joysticka je gore lijevo      
    elif(x_value>50000):
        direction=4         # smjer joysticka je gore desno

# Funkcija koja ispisuje ukucani pin na ekran
def ispisi():
    display.set_pos(51,153)
    display.print(str(pin[0]))
   
    display.set_pos(91,153)
    display.print(str(pin[1]))
   
    display.set_pos(131,153)
    display.print(str(pin[2]))
   
    display.set_pos(171,153)
    display.print(str(pin[3]))

# Funkcija koja se pozove klikom na taster 1
def t1(p):
    # debouncing dodan da ne bi doslo do citanja istog pritiska tastera vise puta
    global pin , debounce                   
    if time.ticks_diff( time.ticks_ms(),debounce)>=500 :
        for i in range (0,4):
            if pin[i]=='*':
                pin[i]=1
                break
        debounce = time.ticks_ms()
        ispisi()

# Funkcija koja se pozove klikom na taster 2 
def t2(p):
    # debouncing dodan da ne bi doslo do citanja istog pritiska tastera vise puta
    global pin, debounce
    if time.ticks_diff( time.ticks_ms(),debounce)>=500 :
        for i in range (0,4):
            if pin[i]=='*':
                pin[i]=2
                break
        debounce = time.ticks_ms()
        ispisi()

# Funkcija koja se pozove klikom na taster 3 
def t3(p):
    # debouncing dodan da ne bi doslo do citanja istog pritiska tastera vise puta
    global pin, debounce
    if time.ticks_diff( time.ticks_ms(),debounce)>=500 :
        for i in range (0,4):
            if pin[i]=='*':
                pin[i]=3
                break
        debounce = time.ticks_ms()
        ispisi()

# Funkcija koja se pozove klikom na taster 4  
def t4(p):
    # debouncing dodan da ne bi doslo do citanja istog pritiska tastera vise puta
    global pin, debounce
    if time.ticks_diff( time.ticks_ms(),debounce)>=500 :
        for i in range (0,4):
            if pin[i]=='*':
                pin[i]=4
                break
        debounce = time.ticks_ms()
        ispisi()

# Crtanje traka na cesti
def drawLines():
    global i  # pozicija od koje pocinjemo crtati trake
    xevi=[47,48,95,96,143,144,191,192]  # Pozicije gdje svaka traka pocinje
    for x in xevi:
        display2.draw_vline(x, 0, 319, GREY)   # Brisanje starih traka
        coords = [[x,0],[x, 0+i], [x, 40+i],  [x, 80+i],  [x, 120+i],[x, 160+i], [x, 200+i], [x, 240+i]]
        # Uslovi ukoliko su trake na pocetku il na kraju ekrana do pola prikazane
        if i==0 or i==10 or i==20:
            display2.draw_vline(x, 279+i, 20, WHITE)
        elif i==30:
            display2.draw_vline(x, 0, 10, WHITE)
            display2.draw_vline(x, 309, 10, WHITE)
        display2.draw_vlines(coords, WHITE)   # Crtanje novih traka
    if i==0:
        i=10
    elif i==10:
        i=20
    elif i==20:
        i=30
    elif i==30:
        i=0

# Cranje auta
def drawCar():
    drawLines()      # Crtanje traka na cesti
    global direction, car_position, last_position
    joystickDirections()
    if(direction==3 and car_position!=0):
        car_position-=1  # pomjeranje joysticka lijevo
        direction=0
    elif(direction==4 and car_position!=4):
        car_position+=1  # pomjeranje joysticka desno
        direction=0
    if(car_position!=last_position):  # Auto se crta samo ako je promjenjena pozicija ( da se ne crta duplo na istoj poziciji)
        display.fill_rectangle(last_position*48+3, 320-48, 42, 48,GREY)
        last_position=car_position
    display2.draw_car(car_position)  # Poziv funkcije koju smo dodali u biblioteku

# Ispis rezultata na ekran
def printScore(s):
    display.set_pos(7,7)
    display.set_color(RED,GREY)
    display.print(str(s))
    display.set_color(BLUE, GREY)

# Crtanje prepreke
def drawObstacle(p):
    global score
    printScore(score)      # ispis trenutnog scora
    global x_o,y_o,obstacle_pos, car_position,game_over,level,speed
    
    if obstacle_pos[x_o]==car_position and y_o+50>272:     # Kraj igre ako je sudar
        game_over=True
        return
    display.fill_rectangle(obstacle_pos[x_o]*48+4,y_o,40,50, WHITE)   #Crtanje nove prepreke
    if(y_o>=speed[level-1]):
        display.fill_rectangle(obstacle_pos[x_o]*48+4,y_o-speed[level-1],40,speed[level-1],GREY)   # brisanje stare prepreke
       
    y_o+=speed[level-1]
    # mjenjanje levela u zavisnosti od scora
    if(y_o+50>320):
        x_o+=1
        if(x_o==5):
            x_o=0
        y_o=0
        score+=1
        if score>15:
            level=4
        elif score>10:
            level=3    
        elif score>5:
            level=2
        display.fill_rectangle(obstacle_pos[x_o-1]*48+4,270,40,50, GREY)    # brisanje prepreke ako je dosla do kraja
    drawCar()       # crtanje auta
    if obstacle_pos[x_o]==car_position and y_o+50>272:
        game_over=True

# Pocetni ekran
def homeScreen():
    global direction                                        # pozicija joysticka  
    makeHomeScreenDesign()
    single_player = True
    direction=0
    display2.draw_rectangle(25,150,180,45,RED)              # okvir oko opcije singleplayer
    while True:
        mqtt_conn.check_msg()
        joystickDirections()
        if(direction== 1 and single_player==False):         # joystick - gore
            single_player=True
            display2.draw_rectangle(25,210,180,45,BLACK)    # brisanje okvira oko opcije multiplayer
            display2.draw_rectangle(25,150,180,45,RED)      # crtanje okvira oko opcije singleplayer
        elif(direction==2 and single_player==True):         # jojstick - dole
            single_player=False
            display2.draw_rectangle(25,150,180,45,BLACK)    # brisanje okvira oko opcije singleplayer
            display2.draw_rectangle(25,210,180,45,RED)      # crtanje okvira oko opcije multiplayer
        if TASTER_JOYSTICK.value()==0:                      # klik na taster za biranje opcije
            break
        time.sleep(0.2)
    
    if single_player==True:                                 # ako je odabrana opcija singleplayer otvara se ekran za igranje
        while True:
            if TASTER_JOYSTICK.value()==1:
                break
        gameScreen()
    else:                                                   # ako je odabrana opcija multiplayer salje se zahtjev drugom igracu
        sentRequestScreen()                              

# Ekran igre
def gameScreen():
    global game_over,multiplayer
    makeGameScreenDesign()
    game_over=False
    while True:                             # da osiguramo da je otpusten taster prije kretanja igre
        if TASTER_JOYSTICK.value()==1 :
            break
    drawing_timer=Timer(period=300,mode=Timer.PERIODIC,callback=drawObstacle)  # timer za crtanje prepreka , auta i linija na cesti
    pause=False
    while True:
        if game_over:                                   # ako game over onda iskljucujemo timer i prekidamo igru
            drawing_timer.deinit()
            break
        if TASTER_JOYSTICK.value()==0 :                 # ako je kliknuto na taster pauzira se igra (iskljucujemo timer) i cekamo ponovni klik
            drawing_timer.deinit()
            while True:
                if TASTER_JOYSTICK.value()==1 :
                    break
            while True:
                if TASTER_JOYSTICK.value()==0 :         # kraj pauze nakon drugog klika
                    drawing_timer.init(period=300,mode=Timer.PERIODIC,callback=drawObstacle)
                    while True:
                        if TASTER_JOYSTICK.value()==1 :
                            break
                    break
    if multiplayer:                                     # ako je igrac igrao u multipalyeru
        multiplayerResultScreen()
    else:                                               # ako je igrac igrao u singleplayeru
        gameOverScreen()

# Ekran nakon zavrsetka igre u singleplayeru   
def gameOverScreen():
    global score, game_over, x_o, y_o, obstacle_pos, last_position, car_position, level, speed, best_score

    makeGameOverScreenDesign()
    display.set_color(WHITE,RED)
    display.set_pos(170,90)
    display.print(str(score))
   
    if score > best_score:
        best_score = score
   
    display.set_pos(170,140)
    display.print(str(best_score)) 
    display2.draw_rectangle(25,210,180,45,RED)
    score=0
    play_again=True
    while True:
        joystickDirections()
        if(direction== 1 and play_again==False):            # joystick - gore
            play_again=True
            display2.draw_rectangle(25,250,180,45,WHITE)    # brisanje okvira oko opcije play again
            display2.draw_rectangle(25,210,180,45,RED)      # crtanje okvira oko opcije exit
        elif(direction==2 and play_again==True):            # joystick - dole
            play_again=False
            display2.draw_rectangle(25,210,180,45,WHITE)    # brisanje okvira oko opcije exit
            display2.draw_rectangle(25,250,180,45,RED)      # crtanje okvira oko opcije play again
        if TASTER_JOYSTICK.value()==0:                      # klik na taster za biranje opcije
            while True:
                if TASTER_JOYSTICK.value()==1:
                    break
            break
        time.sleep(0.2)
    x_o=0
    y_o=0
    car_positionition=2
    last_position=car_position
    level=1
    game_over=False
    if play_again:              # Ponovna igra
        gameScreen()
    else:                       # Vracanje u homeScreen
        homeScreen()

# Ekran koji se prikaze kada igrac posalje zahtjev za multiplayer igru    
def sentRequestScreen():
    global request_accepted, request_answerd
    makeSentRequestScreenDesign()
    message="Zahtjev za igru"
    mqtt_conn.publish(TEMAPUBZAHTJEV,message)    # slanje poruke na temu na koju je drugi igrac subscribed
    while True:
        mqtt_conn.check_msg()                    # cekanje odgovora od drugog igraca (da li je prihvatio ili odbio zahtjev)
        if request_answerd:
            break
        time.sleep(0.1)
    # prikazivanje sljedeceg ekrana u zavisnosti od odgovora drugog igraca
    if request_accepted:
        request_accepted = False
        request_answerd = False
        pinScreen()
    else:
        request_accepted = False
        request_answerd = False
        homeScreen()

# Ekran koji se prikaze ako nam stigne zahtjev za igru
def recivedRequestScreen():
    global direction, request_accepted
    makeRecivedRequestScreenDesign()
    direction = 1                                   # pozicija joysticka            
    display2.draw_rectangle(25,190,180,45,BLACK)
    display2.draw_rectangle(25,140,180,45,RED)      # crtanje okvira oko opcije prihvati zahtjev
    while True:
        joystickDirections()
        if(direction== 1 and request_accepted==False):      # joystick - gore
            request_accepted=True
            display2.draw_rectangle(25,190,180,45,BLACK)    # brisanje okvira oko opcije odbij zahtjev
            display2.draw_rectangle(25,140,180,45,RED)      # crtanje okvira oko opcije prihvati zahtjev
        elif(direction==2 and request_accepted==True):      # joystick - dole
            request_accepted=False
            display2.draw_rectangle(25,140,180,45,BLACK)    # brisanje okvira oko opcije izbrisi zahtjev
            display2.draw_rectangle(25,190,180,45,RED)      # crtanje okvira oko opcije odbij zahtjev
        if TASTER_JOYSTICK.value()==0:                      # klik na taster za biranje opcije
            while True:
                if TASTER_JOYSTICK.value()==1:
                    break
            break
        time.sleep(0.2)

    # u zavisnosti od odabrane opcije (prihvati/odbij) salje se poruka na odgovarajucu temu na koju je drugi igrac subscribed
    if request_accepted:             
        message="Zahtjev prihvacen"
        mqtt_conn.publish(TEMAPUBZAHTJEVPRIHVACEN,message)
        request_accepted = False
        pinScreen()
    else:
        message="Zahtjev odbijen"
        mqtt_conn.publish(TEMAPUBZAHTJEVODBIJEN,message)
        homeScreen()

# Ekran za kucanje pina        
def pinScreen():
    global player2_pin,multiplayer, pin , debounce
    makePinScreenDesign()
    debounce = time.ticks_ms()
    # deklarisanje prekida
    taster1.irq(trigger=Pin.IRQ_FALLING,handler=t1)
    taster2.irq(trigger=Pin.IRQ_FALLING,handler=t2)
    taster3.irq(trigger=Pin.IRQ_FALLING,handler=t3)
    taster4.irq(trigger=Pin.IRQ_FALLING,handler=t4)
    display.set_font(tt24)
    ispisi()
    while True:
        mqtt_conn.check_msg()
        if pin[3]!='*':   # cekanje dok se ne ukucaju sve 4 cifre
            break
   
    display.set_font(tt14)
    display.set_pos(44,280)
    
    # iskljucivanje prekida
    taster1.irq(handler=None)
    taster2.irq(handler=None)
    taster3.irq(handler=None)
    taster4.irq(handler=None)
    
    display.set_font(tt14)
    display.set_pos(44,280)
    display.print('Press button to confirm') #
    
    my_pin=pin[0]*1000+pin[1]*100+pin[2]*10+pin[3]
    pin=['*','*','*','*']
    while True:
        mqtt_conn.check_msg()                           # primanje poruke o pinu drugog igraca
        if TASTER_JOYSTICK.value()==0:
            print(print("b'"+str(my_pin)+"'"))
            while True:
                if TASTER_JOYSTICK.value()==1:
                    break
            message=str(my_pin)                         # slanje pina drugom igracu klikom na joystick
            mqtt_conn.publish(TEMAPUBPIN,message)
            break
    
    while True: 
        mqtt_conn.check_msg()                           # primanje poruke o pinu drugog igraca
        if player2_pin!="":
            print(player2_pin)
            break

    pinCheck = "b'{}'".format(my_pin) 
    if str(player2_pin) in pinCheck:                    # provjera da li se poklapaju pinovi
        multiplayer = True
        player2_pin=""
        gameScreen()
    else:
        homeScreen()

# Ekran koji se prikazuje nakon zavrsetka igre u multiplayeru 
def multiplayerResultScreen():
    global score,multiplayer_score,multiplayer
    message=str(score)
    mqtt_conn.publish(TEMAPUBEND,message)   # slanje rezultata drugom igracu
    waitingForOtherPlyerScreenDesign()

    while True:
        mqtt_conn.check_msg()               # cekanje poruke o rezultatu drugog igraca
        if multiplayer_score!=-1:
            break
    
    makeMultiplayerResultScreenDesign()
    display.set_pos(40,30)
    # u zavisnosti od rezultata prikazuje se odgovarajuci tekst
    if score < multiplayer_score:
        display.print('YOU LOST')
    elif score > multiplayer_score:
        display.print('WINNER')
    else:
        display.print('TIE')
    display.set_font(tt24)
    display.set_pos(40,80)
    display.print('Your score: '+str(score))
    display.set_pos(40,130)
    display.print('Opponent: '+str(multiplayer_score))
    display.set_pos(40,200)
    display.print('Press button to exit')
    multiplayer_score = -1
    score = 0
    multiplayer = False
    while True:
        if TASTER_JOYSTICK.value()==0:          # klik na joystick za vracanje u homeScreen
            while True:
                if TASTER_JOYSTICK.value()==1:
                    break
            break
        time.sleep(0.2)
    homeScreen()
        
homeScreen()