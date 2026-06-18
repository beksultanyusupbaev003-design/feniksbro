import os
import json
import zipfile
import requests
from playwright.sync_api import sync_playwright

# === SOZLAMALAR ===
LOGIN = os.environ['FENIKS_LOGIN']
PAROL = os.environ['FENIKS_PAROL']
TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
TELEGRAM_CHAT_ID = os.environ['TELEGRAM_CHAT_ID']
SANA = os.environ['SANA']  # DD.MM.YYYY
MASHINA = os.environ['MASHINA']  # ISUZU 890

BASE_URL = "https://feniks.traceapp.uz"

# Feniks mahsulot nomi → ZOLOTO_N1 mahsulot nomi moslashtirish
MAHSULOT_MAP = {
    "SARBAST LITE": {
        "ПЭТ": "Sarbast Lite PET 1,5L",
        "алюм": "Sarbast Lite CAN 0,45L",
        "бут. 0.5": "Sarbast Lite RGB 0,5L",
    },
    "SARBAST ORIGINAL": {
        "ПЭТ": "Sarbast Original PET 1,5L",
        "алюм": "Sarbast Original CAN 0,45L",
        "бут. 0.5": "Sarbast Original RGB 0,5L",
        "Unfiltered": "Sarbast Original Unfiltered CAN 0,45L",
    },
    "SARBAST SPECIAL": {
        "ПЭТ": "Sarbast Special PET 1,5L",
        "алюм": "Sarbast Special CAN 0,45L",
        "бут. 0.5": "Sarbast Special RGB 0,5L",
    },
    "TUBORG GREEN": {
        "алюм": "Tuborg Green CAN 0,45L",
        "бут. 0.5": "Tuborg Green RGB 0,5L",
    },
    "TUBORG LITE": {
        "алюм": "Tuborg Lite CAN 0,45L",
        "бут. 0.5": "Tuborg Lite RGB 0,5L",
    },
    "ZATECKY GUS SVETLY": {
        "алюм": "Zatecky Gus Svetliy CAN 0,45L",
        "бут": "Zatecky Gus Svetliy RGB 0,47L",
    },
    "ZATECKY GUS EXPORT": {
        "алюм": "Zatecky Gus Exportniy CAN 0,45L",
        "бут": "Zatecky Gus Exportniy RGB 0,47L",
    },
    "ZATECKY GUS KREPK": {
        "алюм": "Zatecky Gus Krepkiy CAN 0,45L",
    },
    "ZATECKY GUS NEFILT": {
        "алюм": "Zatecky Gus Nefiltrovaniy CAN 0,45L",
    },
    "CARLSBERG": {
        "алюм": "Carlsberg Pilsner CAN 0,45L",
        "бут": "Carlsberg Pilsner RGB 0,45L",
    },
    "KRONENBOURG": {
        "алюм": "Kronenbourg Blanc CAN 0,45L",
        "бут": "Kronenbourg Blanc RGB 0,43L",
    },
}

def mahsulot_nomi_aniqlash(feniks_nom):
    """Feniks mahsulot nomidan ZOLOTO_N1 nomini aniqlaydi"""
    nom = feniks_nom.upper()
    
    for kalit, variantlar in MAHSULOT_MAP.items():
        if kalit in nom:
            for tip, zoloto_nom in variantlar.items():
                if tip.upper() in nom or tip in feniks_nom:
                    return zoloto_nom
            # Birinchi variantni qaytarish
            return list(variantlar.values())[0]
    
    return feniks_nom  # Topilmasa original nom

def telegram_yuborish(xabar):
    """Telegram'ga xabar yuborish"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": xabar,
        "parse_mode": "HTML"
    })

def telegram_fayl_yuborish(fayl_yoli, caption=""):
    """Telegram'ga fayl yuborish"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument"
    with open(fayl_yoli, 'rb') as f:
        requests.post(url, data={
            "chat_id": TELEGRAM_CHAT_ID,
            "caption": caption
        }, files={"document": f})

def main():
    print(f"Boshlanmoqda: {MASHINA} | {SANA}")
    
    os.makedirs("output", exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # === 1. LOGIN ===
        print("Login qilinmoqda...")
        page.goto(f"{BASE_URL}/Account/Login")
        page.wait_for_load_state("networkidle")
        
        # Login formani to'ldirish - DevExtreme
        page.wait_for_timeout(3000)
        
        # Barcha inputlarni topish
        all_inputs = page.query_selector_all('input')
        text_inputs = []
        pass_inputs = []
        for inp in all_inputs:
            try:
                t = inp.get_attribute('type') or 'text'
                if t == 'password':
                    pass_inputs.append(inp)
                elif t in ['text', 'email', ''] and inp.is_visible():
                    text_inputs.append(inp)
            except:
                pass
        
        if text_inputs:
            text_inputs[0].click()
            page.wait_for_timeout(300)
            text_inputs[0].fill(LOGIN)
        
        if pass_inputs:
            pass_inputs[0].click()
            page.wait_for_timeout(300)
            pass_inputs[0].fill(PAROL)
        
        page.wait_for_timeout(500)
        page.keyboard.press('Enter')
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(3000)
        print("Login muvaffaqiyatli!")
        
        # === 2. ОТГРУЗКА sahifasiga o'tish ===
        print("Отгрузка sahifasiga o'tilmoqda...")
        page.goto(f"{BASE_URL}/Shipment")
        page.wait_for_load_state("networkidle")
        
        # === 3. SANA FILTRI ===
        print(f"Sana filtri qo'yilmoqda: {SANA}")
        # Sana input maydonini topib to'ldirish
        sana_inputs = page.query_selector_all('input[type="text"]')
        for inp in sana_inputs:
            placeholder = inp.get_attribute('placeholder') or ''
            if 'дата' in placeholder.lower() or 'сана' in placeholder.lower() or 'date' in placeholder.lower():
                inp.fill(SANA)
                break
        
        # Sana ustunidagi filter inputga yozish
        page.wait_for_timeout(1000)
        
        # === 4. MASHINA FILTRI ===
        print(f"Mashina filtri: {MASHINA}")
        page.wait_for_timeout(500)
        
        # === 5. OTGRUZKA QATORINI TOPISH VA OCHISH ===
        print("Otgruzka qatori izlanmoqda...")
        page.wait_for_timeout(2000)
        
        # Saytdan API orqali ma'lumot olish
        # Avval cookie'larni olamiz
        cookies = page.context.cookies()
        cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
        
        headers = {
            "Cookie": cookie_str,
            "Content-Type": "application/json",
            "X-Requested-With": "XMLHttpRequest"
        }
        
        # Otgruzka ro'yxatini API orqali olish
        print("API orqali otgruzka ro'yxati olinmoqda...")
        
        # Sana formatini o'zgartirish DD.MM.YYYY → YYYY-MM-DD
        sana_parts = SANA.split('.')
        sana_api = f"{sana_parts[2]}-{sana_parts[1]}-{sana_parts[0]}"
        
        # Shipment ro'yxatini olish
        response = requests.get(
            f"{BASE_URL}/api/Shipment",
            headers=headers,
            params={
                "dateFrom": sana_api,
                "dateTo": sana_api,
                "transport": MASHINA
            }
        )
        
        print(f"API javob: {response.status_code}")
        
        mahsulotlar = {}  # {mahsulot_nomi: [kodlar]}
        
        if response.status_code == 200:
            data = response.json()
            print(f"Topildi: {len(data)} ta otgruzka")
            
            for otgruzka in data:
                otgruzka_id = otgruzka.get('id')
                transport = otgruzka.get('transport', '')
                
                if MASHINA.upper() not in transport.upper():
                    continue
                
                # Otgruzka detallari
                detail_response = requests.get(
                    f"{BASE_URL}/api/Shipment/{otgruzka_id}",
                    headers=headers
                )
                
                if detail_response.status_code != 200:
                    continue
                    
                detail = detail_response.json()
                
                # Mahsulotlarni aylanib chiqish
                items = detail.get('items', detail.get('products', []))
                
                for item in items:
                    mahsulot_nom_feniks = item.get('productName', item.get('name', ''))
                    zoloto_nom = mahsulot_nomi_aniqlash(mahsulot_nom_feniks)
                    
                    kodlar = item.get('codes', item.get('marks', []))
                    
                    if zoloto_nom not in mahsulotlar:
                        mahsulotlar[zoloto_nom] = []
                    
                    for kod in kodlar:
                        kod_qiymati = kod if isinstance(kod, str) else kod.get('code', '')
                        if kod_qiymati:
                            mahsulotlar[zoloto_nom].append(kod_qiymati)
        
        else:
            # API ishlamasa Playwright orqali olish
            print("API ishlamadi, Playwright orqali olinmoqda...")
            mahsulotlar = playwright_orqali_olish(page, SANA, MASHINA)
        
        browser.close()
        
        # === 6. TXT FAYLLAR YARATISH ===
        if not mahsulotlar:
            telegram_yuborish(f"⚠️ {SANA} | {MASHINA}\nKodlar topilmadi!")
            return
        
        print(f"Jami {len(mahsulotlar)} ta mahsulot topildi")
        
        zip_fayl = f"output/markerovka_{MASHINA.replace(' ', '_')}_{SANA.replace('.', '_')}.zip"
        
        with zipfile.ZipFile(zip_fayl, 'w') as zf:
            for mahsulot, kodlar in mahsulotlar.items():
                if not kodlar:
                    continue
                txt_content = "\n".join(kodlar)
                fayl_nom = f"{mahsulot}.txt"
                zf.writestr(fayl_nom, txt_content)
                print(f"  ✅ {mahsulot}: {len(kodlar)} kod")
        
        # === 7. TELEGRAM YUBORISH ===
        xulosa = f"✅ <b>{MASHINA}</b> | {SANA}\n\n"
        jami_kodlar = 0
        for mahsulot, kodlar in mahsulotlar.items():
            if kodlar:
                xulosa += f"📦 {mahsulot}: {len(kodlar)} ta kod\n"
                jami_kodlar += len(kodlar)
        xulosa += f"\n<b>Jami: {jami_kodlar} ta kod</b>"
        
        telegram_yuborish(xulosa)
        telegram_fayl_yuborish(zip_fayl, f"📁 {MASHINA} | {SANA} — ZIP")
        
        print("Tayyor! ZIP Telegram'ga yuborildi.")


def playwright_orqali_olish(page, sana, mashina):
    """Playwright orqali sahifadan kodlarni o'qish"""
    mahsulotlar = {}
    
    try:
        # Sana filtrini qo'yish
        page.wait_for_timeout(2000)
        
        # Sana input topish
        date_inputs = page.query_selector_all('input')
        for inp in date_inputs:
            try:
                val = inp.input_value()
                if '.' in str(val) and len(str(val)) > 5:
                    inp.triple_click()
                    inp.type(sana)
                    break
            except:
                pass
        
        page.wait_for_timeout(2000)
        
        # Birinchi qatorni ochish (✏️ tugma)
        edit_buttons = page.query_selector_all('button.k-grid-edit-command, a.k-grid-edit-command, button[title="Edit"], .k-i-edit')
        if edit_buttons:
            edit_buttons[0].click()
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(2000)
        
        # Mahsulot qatorlarini topish
        rows = page.query_selector_all('tr.k-master-row, tr[role="row"]')
        
        for row in rows:
            # Expand tugma
            expand = row.query_selector('.k-i-expand, .k-i-arrow-e')
            if expand:
                expand.click()
                page.wait_for_timeout(1000)
        
        # Kodlarni o'qish
        detail_rows = page.query_selector_all('tr.k-detail-row')
        for detail in detail_rows:
            cells = detail.query_selector_all('td')
            for cell in cells:
                text = cell.inner_text().strip()
                if len(text) > 20 and text.startswith('01'):
                    # Bu markerovka kodi
                    mahsulot_nom = "Noma'lum mahsulot"
                    if mahsulot_nom not in mahsulotlar:
                        mahsulotlar[mahsulot_nom] = []
                    mahsulotlar[mahsulot_nom].append(text)
    
    except Exception as e:
        print(f"Xato: {e}")
    
    return mahsulotlar


if __name__ == "__main__":
    main()
