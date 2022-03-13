import time
from selenium import webdriver
import os, sys


videoFileName = "list_url_video.txt"

viewCountFileName = "luong_xem.txt"

videoFile = open(videoFileName)
listVideo = videoFile.readlines()

saveViewFile = open(viewCountFileName, "r")
viewCount = int(saveViewFile.read())
saveViewFile.close()	

def cls():
	os.system("cls")

cls()
def background():
    hehe="""
    ╔═════════════════════════════════════════════════════════╗
    ║                                                         ║
    ║                      Trần xuân Lợi                      ║
    ║                                                         ║
    ║ Copy nhớ ghi nguồn                                      ║
    ║ Zalo: 0387640248                            Editor: Lợi ║
    ╚═════════════════════════════════════════════════════════╝         
    >>>>>>>>>>>>>>>>>>>>>> Tools View YTB <<<<<<<<<<<<<<<<<<<<<\n\n   """

    for haha in hehe:
        sys.stdout.write(haha)
        sys.stdout.flush()
        time.sleep(0.005)
def key_dung():
    key_dg="    Key đúng, vui lòng đợi...."
    for kkk in key_dg:
        sys.stdout.write(kkk)
        sys.stdout.flush()
        time.sleep(0.003)

logo="    -----------------------------------------------------------"
background()
key=input(" Nhập key: ")
if key=="Lu TV" or "daukute":
    print(logo)
    key_dung()
    time.sleep(3)
    cls()
else:
    print(logo)
    print("    Key sai, không làm mà đòi có ăn :))")
    time.sleep(3)
    quit()
background()
print(" -----------------------------------------------------------")
print("    Nhập sai bấm (Ctrl+c+Enter) để nhập lại")
print(logo)
print("    Nếu nhập sai định dạng tools lỗi (chỉ nhập số)")

so_tab=input("    Nhập số tab: ")
NUMBER_OF_WINDOW = int(so_tab)

NUMBER_OF_VIDEO = len(listVideo)

delay_xem=input("    Nhập thời gian xem (giây): ")
time.sleep(1)
print("    Tools Start...")
time.sleep(3)
cls()
LOOP_TIME = int(delay_xem)

print("  WINDOW: " + str(NUMBER_OF_WINDOW))
print("  VIDEO: " + str(NUMBER_OF_VIDEO))

videoIndex = 0
windowIndex = 0
windowCount = 1

browser = webdriver.Chrome()
browser.get(listVideo[videoIndex])
time.sleep(2)
play_video = "#movie_player > div.ytp-cued-thumbnail-overlay > button"
e = browser.find_element_by_css_selector(play_video)
cls()
e.click()
time.sleep(1)

while True:
    videoIndex = (videoIndex + 1) % int(NUMBER_OF_VIDEO)
    windowIndex = (windowIndex + 1) % int(NUMBER_OF_WINDOW)
    print(str(windowIndex) + " : " + str(videoIndex))
    url = listVideo[videoIndex].strip();

    if windowCount < NUMBER_OF_WINDOW:
        windowCount = windowCount + 1;
        browser.execute_script("window.open('"+url+"')")
    else:
        browser.switch_to.window(browser.window_handles[windowIndex])
        time.sleep(0.5)
        browser.get(url)

    viewCount = viewCount+1    
    
    saveViewFile = open(viewCountFileName, "w")
    saveViewFile.write(str(viewCount))
    saveViewFile.close()

    time.sleep(LOOP_TIME)
