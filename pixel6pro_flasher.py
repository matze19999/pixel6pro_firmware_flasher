while True:
    try:
        import os
        import sys
        import json
        import time
        import requests
        import zipfile
        import shutil
        import re
        import subprocess
        import warnings
        from adb_shell.adb_device import AdbDeviceUsb
        import adb_shell.exceptions
        from adb_shell.auth.sign_pythonrsa import PythonRSASigner
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
        from selenium.common.exceptions import NoSuchElementException
        break
    except Exception as e:
        print(e)
        os.system('pip3 install --upgrade selenium adb-shell[usb]')

telegram_bottoken = ''


warnings.filterwarnings("ignore", category=DeprecationWarning)

def download(filename, url):
    with open(filename, 'wb') as f:
        response = requests.get(url, stream=True)
        total = response.headers.get('content-length')

        if total is None:
            f.write(response.content)
        else:
            downloaded = 0
            total = int(total)
            for data in response.iter_content(chunk_size=max(int(total/1000), 1024*1024)):
                downloaded += len(data)
                f.write(data)
                done = int(50*downloaded/total)
                sys.stdout.write('\r[{}{}]'.format('█' * done, '.' * (50-done)))
                sys.stdout.flush()
    sys.stdout.write('\n')

if not os.access(os.getcwd(), mode=os.W_OK):
    print("In das aktuelle Verzeichnis kann nicht geschrieben werden! Beende Programm...")
    exit(1)

workdir = f'{os.getcwd()}\\workdir'

jsondata = {}
jsondata['counter'] = []

try:
    with open('data.json') as infile:
        oldcounter = int(json.load(infile)['counter'][0]['lastcounter'])
except FileNotFoundError:
    oldcounter = 0

print('Initialisiere Chrome Browser')
options = webdriver.ChromeOptions()
options.add_argument('disable-features=InfiniteSessionRestore')
options.add_argument('--disable-dev-shm-usage')
prefs={'profile.managed_default_content_settings.images': 2, 'disk-cache-size': 4096 }
options.add_experimental_option('prefs', prefs)
options.add_experimental_option('excludeSwitches', ['enable-logging'])
options.add_argument('--headless')
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')
options.page_load_strategy = 'none'
caps = DesiredCapabilities().CHROME
caps["pageLoadStrategy"] = 'none'

try:
    driver = webdriver.Chrome(desired_capabilities=caps, options=options)
except FileNotFoundError:
    print("Chromedriver ist nicht installiert! Lade die passende Version für deine Chrome Version herunter und verschiebe sie nach C:\\Windows\\\n\nhttps://chromedriver.chromium.org/downloads")

print("Öffne Google Pixel Firmware Download Seite")
driver.get("https://developers.google.com/android/images")
time.sleep(3)
try:
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '/html/body/devsite-snackbar/div/div/button'))).click()
except NoSuchElementException:
    print("Seite konnte nicht geladen werden. Bitte überprüfe deine Internetverbindung!")
    exit(1)

WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#gc-wrapper > main > devsite-content > article > div.devsite-article-body.clearfix > p:nth-child(9) > devsite-wall-acknowledgement > a'))).click()
time.sleep(5)

print("Prüfe ob neue Firmware vorhanden ist")
counter = 50
while True:
    try:
        driver.find_element_by_xpath(f'/html/body/section/section/main/devsite-content/article/div[3]/div[2]/table/tbody/tr[{counter}]/td[1]')
        break
    except NoSuchElementException:
        counter -= 1
        continue

while counter > 0:
    versiontext = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, f'/html/body/section/section/main/devsite-content/article/div[3]/div[2]/table/tbody/tr[{counter}]/td[1]'))).text.replace(' ', '')
    if 'Verizon' in versiontext or 'AT&T' in versiontext or 'Google Fi' in versiontext or 'carrier' in versiontext:
        counter -= 1
        continue
    else:
        break


if counter != oldcounter:
    # Send telegram notification
    print(f'Neue Firmware gefunden!  {versiontext}')
    requests.get(f'https://api.telegram.org/bot{telegram_bottoken}/sendMessage?chat_id=8166546&text=Neues Update verfügbar für GP6P!%0A%0AVersion:%0A{versiontext}')
    # Set new counter in json file
    jsondata['counter'].append({
        'lastcounter': f'{counter}'
    })
else:
    exit(0)

print('Downloade Firmware')
downloadurl = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, f'/html/body/section/section/main/devsite-content/article/div[3]/div[2]/table/tbody/tr[{counter}]/td[3]/a'))).get_attribute('href')
download(f'{versiontext}.zip', downloadurl)

print(f'Extrahiere {versiontext}.zip')
with zipfile.ZipFile(f'{versiontext}.zip', 'r') as zip_ref:
    zip_ref.extractall(workdir)
src_files = os.listdir(workdir)
for filename in src_files:
    if os.path.isdir(f'{workdir}\\{filename}'):
        if 'raven' in filename:
            firmwarefolder = filename
            break
src_files = os.listdir(f'{workdir}\\{firmwarefolder}')
for filename in src_files:
    shutil.move(f'{workdir}\\{firmwarefolder}\\{filename}', f'{workdir}\\{filename}')

print('Entferne unnötige Dateien')
os.rmdir(f'{workdir}\\{firmwarefolder}')
os.remove(f'{versiontext}.zip')


print('Öffne Google Plattform Tools Seite')
driver.get('https://developer.android.com/studio/releases/platform-tools')
time.sleep(3)
WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '/html/body/devsite-snackbar/div/div/button'))).click()
WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#gc-wrapper > main > devsite-content > article > div.devsite-article-body.clearfix > ul:nth-child(7) > li:nth-child(1) > button'))).click()
WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#agree_dac-download-windows-dialog-id'))).click()
url = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#agree-button__dac-download-windows-dialog-id'))).get_attribute('href')

print('Downloade Google Plattform Tools...')
download('platformtools.zip', url)
driver.close()
print('Extrahiere platformtools.zip...')
with zipfile.ZipFile('platformtools.zip', 'r') as zip_ref:
    zip_ref.extractall(workdir)
src_files = os.listdir(f'{workdir}\\platform-tools/')

print('Entferne unnötige Dateien')
shutil.copytree(f'{workdir}\\platform-tools', f'{workdir}', dirs_exist_ok=True)
shutil.rmtree(f'{workdir}\\platform-tools', ignore_errors=True)
os.remove('platformtools.zip')

print('Extrahiere Pixel 6 Pro Boot.img')
src_files = os.listdir(f'{workdir}')
for filename in src_files:
    if 'image-raven-' in filename:
        with zipfile.ZipFile(f'{workdir}\\{filename}', 'r') as zip_ref:
            zip_ref.extract('boot.img', path=workdir)
        break

print(f'\n\nBitte patche die boot.img im Magisk Manger und kopiere die gepatchte magisk.img zurück nach {workdir}\n\nEnter drücken zum Fortsetzen...')

while not 'magiskname' in locals():
    input()
    src_files = os.listdir(f'{workdir}')
    for filename in src_files:
        if 'magisk' in filename:
            magiskname = filename

    if not 'magiskname' in locals():
        print('\n\nMagisk.img wurde nicht gefunden. Bitte versuche es erneut. Enter drücken zum Fortsetzen...')


print('Patche flash-all.bat Datei')
with open(f'{workdir}\\flash-all.bat', 'r+') as f:
    text = f.read()
    text = re.sub('-w', '--disable-verity --disable-verification --skip-reboot', text)
    f.seek(0)
    f.write(text)
    f.truncate()

print('Lade ADB Keys')
adbkey = f'{os.getenv("USERPROFILE")}\\.android\\adbkey'
with open(adbkey) as f:
    priv = f.read()
with open(adbkey + '.pub') as f:
     pub = f.read()
signer = PythonRSASigner(pub, priv)

while True:
    try:
        print("Verbinde per ADB mit Pixel 6 Pro")
        device = AdbDeviceUsb()
        device.connect(rsa_keys=[signer], auth_timeout_s=10)
        device.close()
        time.sleep(2)
        print("Starte GP6P in Bootloader Modus")
        text = subprocess.Popen(f'adb reboot bootloader')
        print(text)
        time.sleep(5)
        subprocess.Popen(f'adb kill-server')
        break
    except adb_shell.exceptions.UsbDeviceNotFoundError:
        print('\n\nGP6P mit aktiviertem USB Debugging wurde nicht gefunden!\nVerbinde dein Telefon und drücke Enter.')
        input()
        continue

time.sleep(15)

print('Starte Firmware Flash')
process = subprocess.Popen(f'{workdir}\\flash-all.bat', stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
while process.stdout.readable():
    line = process.stdout.readline()
    if not line:
        break
    try:
        print(line.decode('utf-8').strip())
    except:
        ...

print('\n\nStarte in den Bootloader Modus')
subprocess.Popen(f'fastboot reboot bootloader')
time.sleep(5)


print('Flashe Magisk-modifizierte Boot.img')
src_files = os.listdir(f'{workdir}')
for filename in src_files:
    if 'magisk' in filename:
        subprocess.Popen(f'fastboot flash boot {workdir}\\{filename}', stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        print('Starte GP6P neu')
        subprocess.Popen(f'fastboot reboot')
        break

print('Flash Vorgang beendet!')
