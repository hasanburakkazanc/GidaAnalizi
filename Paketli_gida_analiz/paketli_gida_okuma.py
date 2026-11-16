from flask import Flask, request, jsonify
import cv2
import pytesseract
import numpy as np
import re
from difflib import get_close_matches
app = Flask(__name__)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
KATKI_MADDELERI = {
    "sitrik asit": "⚠️ E330 (Sitrik Asit): Mide yanması yapabilir.",
    "msg": "⛔ E621 (MSG): Çin tuzu. Baş ağrısı tetikleyebilir.",
    "monosodyum": "⛔ E621 (MSG): Bağımlılık yapıcı etki riski.",
    "glutamat": "⛔ E621 (MSG): Lezzet artırıcı.",
    "glikoz": "⚠️ Glikoz Şurubu: Kan şekerini aniden yükseltir.",
    "fruktoz": "⚠️ Fruktoz Şurubu: Karaciğer yağlanması riski.",
    "palm": "⛔ Palm Yağı: Damar tıkanıklığı riski yüksektir.",
    "aspartam": "⛔ Aspartam: Tartışmalı yapay tatlandırıcı.",
    "sodyum benzoat": "⚠️ E211: Hiperaktivite tetikleyebilir.",
    "metabisülfit": "⚠️ E223: Astımı olanlar dikkat etmeli.",
    "disodyum": "⚠️ Lezzet Artırıcı: Genelde MSG ile kullanılır.",
    "aroma": "⚠️ Aroma Verici: Yapay katkı içerebilir.",
    "maltodekstrin": "⚠️ Maltodekstrin: Şeker gibi kan şekerini etkiler.",
    "kanola": "⚠️ Kanola Yağı: İşlenmiş bitkisel yağ.",
    "renklendirici": "⚠️ Renklendirici: Yapay gıda boyası.",
    "emülgatör": "⚠️ Emülgatör: Bağırsak sağlığını etkileyebilir."
}
ALERJEN_LISTESI = {
    "YUMURTA": ["yumurta", "egg"], 
    "SOYA": ["soya", "soy", "lecithin", "lesitin"],
    "SUSAM": ["susam", "sesame"], 
    "FISTIK": ["fıstık", "peanut", "yer fıstığı"],
    "SÜT": ["süt", "milk", "whey", "peynir altı", "lactose", "laktoz", "krema", "yoğurt", "peynir"], 
    "GLUTEN": ["gluten", "buğday", "wheat", "un", "flour", "arpa", "barley", "çavdar", "ekmek"],
    "KURUYEMİŞ": ["fındık", "nut", "hazelnut", "ceviz", "badem", "antep", "pistachio"]
}
def ondalik_duzelt(sayi, besin_turu):
    """Ondalık kayıplarını düzelt"""
    if besin_turu == 'seker' and sayi > 30:
        return round(sayi / 10, 1)
    elif besin_turu == 'tuz' and sayi > 5:
        return round(sayi / 10, 1)
    elif besin_turu == 'protein' and sayi > 40:
        return round(sayi / 10, 1)
    elif besin_turu == 'lif' and sayi > 20:
        return round(sayi / 10, 1)
    return sayi
def besin_tablosu_bul(text):
    satirlar = text.split('\n')
    tablo_baslangic = 0
    
    for i, satir in enumerate(satirlar):
        satir_lower = satir.lower()
        if any(x in satir_lower for x in ['besin', 'nutrition', '100g', '100 g', 'per 100', 'porsiyon', 'portion']):
            tablo_baslangic = i
            break
        if 'enerji' in satir_lower and ('kcal' in satir_lower or 'energy' in satir_lower):
            tablo_baslangic = i
            break
    
    return '\n'.join(satirlar[tablo_baslangic:])
def satirdan_sayilari_cikart(satir):
    temiz = satir.replace(',', '.')
    temiz = re.sub(r'[|{}\[\]()!<>~=°]', ' ', temiz)
    
    sayilar = re.findall(r'\d+\.?\d*', temiz)
    
    sonuc = []
    for s in sayilar:
        try:
            val = float(s)
            if val in [100, 1000, 2000, 8400, 15, 0]:
                continue
            if len(s.replace('.', '')) > 3:
                continue
            sonuc.append(val)
        except:
            continue
    return sonuc
def besin_degerlerini_bul(text):
    besinler = {
        'enerji': 0, 'seker': 0, 'yag': 0, 
        'tuz': 0, 'protein': 0, 'lif': 0, 'karbonhidrat': 0
    }
    
    tablo_metni = besin_tablosu_bul(text)
    print(f"\n   📊 TABLO BÖLÜMÜ ({len(tablo_metni)} karakter)")
    
    satirlar = tablo_metni.split('\n')
    
    for satir in satirlar:
        satir_lower = satir.lower()
        sayilar = satirdan_sayilari_cikart(satir)
        
        if not sayilar:
            continue
        
        # ENERJİ
        if besinler['enerji'] == 0:
            if any(x in satir_lower for x in ['enerji', 'energy']):
                enerji_adaylari = [s for s in sayilar if 100 <= s <= 700]
                if enerji_adaylari:
                    besinler['enerji'] = max(enerji_adaylari)
                    print(f"   ✅ ENERJİ: {besinler['enerji']}")
        
        # YAĞ
        if besinler['yag'] == 0:
            if any(x in satir_lower for x in ['yağ', 'yag', 'fat']):
                if not any(x in satir_lower for x in ['doymuş', 'doymus', 'saturate', 'bitkisel', 'ayçiçek', 'palm']):
                    yag_adaylari = [s for s in sayilar if 1 <= s <= 50]
                    if yag_adaylari:
                        besinler['yag'] = yag_adaylari[-1]
                        print(f"   ✅ YAĞ: {besinler['yag']}")
        
        # KARBONHİDRAT
        if besinler['karbonhidrat'] == 0:
            if any(x in satir_lower for x in ['karbonhidrat', 'karbon', 'carbohydrate', 'carboh']):
                karb_adaylari = [s for s in sayilar if 5 <= s <= 95]
                if karb_adaylari:
                    besinler['karbonhidrat'] = karb_adaylari[-1]
                    print(f"   ✅ KARBONHİDRAT: {besinler['karbonhidrat']}")
        
        # ŞEKER
        if besinler['seker'] == 0:
            if any(x in satir_lower for x in ['şeker', 'seker', 'sugar']):
                if 'şurubu' not in satir_lower and 'syrup' not in satir_lower:
                    seker_adaylari = [s for s in sayilar if 0.1 <= s <= 60]
                    if seker_adaylari:
                        val = seker_adaylari[-1]
                        besinler['seker'] = ondalik_duzelt(val, 'seker')
                        print(f"   ✅ ŞEKER: {val} → {besinler['seker']}")
        
        # PROTEİN
        if besinler['protein'] == 0:
            if any(x in satir_lower for x in ['protein', 'proteın', 'prote']):
                protein_adaylari = [s for s in sayilar if 0.1 <= s <= 90]
                if protein_adaylari:
                    val = protein_adaylari[-1]
                    besinler['protein'] = ondalik_duzelt(val, 'protein')
                    print(f"   ✅ PROTEİN: {val} → {besinler['protein']}")
        
        # LİF
        if besinler['lif'] == 0:
            if any(x in satir_lower for x in ['lif', 'fibre', 'fiber']):
                lif_adaylari = [s for s in sayilar if 0.1 <= s <= 90]
                if lif_adaylari:
                    val = lif_adaylari[-1]
                    besinler['lif'] = ondalik_duzelt(val, 'lif')
                    print(f"   ✅ LİF: {val} → {besinler['lif']}")
        
        # TUZ
        if besinler['tuz'] == 0:
            if any(x in satir_lower for x in ['tuz', 'salt']):
                if len(satir) < 80:
                    tuz_adaylari = [s for s in sayilar if 0.1 <= s <= 90]
                    if tuz_adaylari:
                        val = tuz_adaylari[-1]
                        besinler['tuz'] = ondalik_duzelt(val, 'tuz')
                        print(f"   ✅ TUZ: {val} → {besinler['tuz']}")
    
    # ===== FALLBACK: Bulunamayan değerler için tahmin =====
    print("\n   📊 FALLBACK KONTROL:")
    
    # Şeker bulunamadıysa, karbonhidratın %10-15'i olarak tahmin et
    if besinler['seker'] == 0 and besinler['karbonhidrat'] > 0:
        besinler['seker'] = round(besinler['karbonhidrat'] * 0.08, 1)  # %8 tahmin
        print(f"   ⚠️ ŞEKER (tahmin): {besinler['seker']} (karbonhidratın %8'i)")
    
    # Protein bulunamadıysa, tipik atıştırmalık değeri ata
    if besinler['protein'] == 0:
        besinler['protein'] = 7.0  # Tipik cips/kraker değeri
        print(f"   ⚠️ PROTEİN (varsayılan): {besinler['protein']}")
    
    return besinler
def analiz_et(text):
    text_lower = text.lower()
    katki_raporu = []
    bulunan_alerjenler = set()
    kelimeler_ham = text_lower.split()
    
    print("\n--- İÇERİK ANALİZİ ---")
    
    for ana, altlar in ALERJEN_LISTESI.items():
        for alt in altlar:
            if alt in text_lower: 
                bulunan_alerjenler.add(ana)
                print(f"   🚨 ALERJEN: {ana}")
                break
    
    for k_madde, aciklama in KATKI_MADDELERI.items():
        if k_madde in text_lower:
            if aciklama not in katki_raporu:
                katki_raporu.append(aciklama)
                print(f"   🧪 KATKI: {k_madde}")
        else:
            matches = get_close_matches(k_madde, kelimeler_ham, n=1, cutoff=0.85)
            if matches and aciklama not in katki_raporu:
                katki_raporu.append(aciklama)
    print("\n--- BESİN DEĞERLERİ ANALİZİ ---")
    besinler = besin_degerlerini_bul(text)
    # ===== YENİ PUANLAMA SİSTEMİ =====
    puan = 70  # Başlangıç
    
    # Enerji
    if besinler['enerji'] > 400: puan -= 15
    elif besinler['enerji'] > 300: puan -= 10
    elif besinler['enerji'] > 200: puan -= 5
    
    # Yağ
    if besinler['yag'] > 25: puan -= 20
    elif besinler['yag'] > 15: puan -= 15
    elif besinler['yag'] > 10: puan -= 10
    
    # Şeker
    if besinler['seker'] > 15: puan -= 25
    elif besinler['seker'] > 10: puan -= 20
    elif besinler['seker'] > 5: puan -= 10
    
    # Tuz
    if besinler['tuz'] > 2: puan -= 25
    elif besinler['tuz'] > 1.5: puan -= 20
    elif besinler['tuz'] > 1: puan -= 10
    
    # Karbonhidrat
    if besinler['karbonhidrat'] > 70: puan -= 15
    elif besinler['karbonhidrat'] > 50: puan -= 10
    
    # Alerjen ve katkı cezası
    puan -= len(bulunan_alerjenler) * 2
    puan -= len(katki_raporu) * 3
    
    # Protein (pozitif)
    if besinler['protein'] > 15: puan += 20
    elif besinler['protein'] > 10: puan += 15
    elif besinler['protein'] > 5: puan += 10
    
    # Lif (pozitif)
    if besinler['lif'] > 8: puan += 20
    elif besinler['lif'] > 5: puan += 15
    elif besinler['lif'] > 3: puan += 10
    
    puan = max(0, min(100, int(puan)))
    # ===== PUANLAMA SONU =====
    
    print(f"\n--- SONUÇ ---")
    print(f"   Besinler: {besinler}")
    print(f"   Alerjen: {len(bulunan_alerjenler)}, Katkı: {len(katki_raporu)}")
    print(f"   Puan: {puan}")
    
    return {
        "alerjenler": list(bulunan_alerjenler),
        "katki_maddeleri": katki_raporu,
        "besin_degerleri": besinler,
        "saglik_puani": puan,
        "renk": "Kirmizi" if puan < 40 else "Sari" if puan < 70 else "Yesil"
    }
def ultra_tarama(img_path):
    img = cv2.imread(img_path)
    if img is None: return ""
    
    img = cv2.resize(img, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_LINEAR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    
    config = r'--oem 3 --psm 6'
    text = pytesseract.image_to_string(enhanced, lang='tur+eng', config=config)
    
    return text
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files: 
        return jsonify({"error": "Dosya yok"}), 400
    
    file = request.files['file']
    file.save("gecici.jpg")
    
    text = ultra_tarama("gecici.jpg")
    
    print("\n" + "="*60)
    print("📄 OCR ÇIKTISI:")
    print("="*60)
    print(text)
    print("="*60)
    
    if not text.strip():
        return jsonify({
            "error": "Metin okunamadı",
            "alerjenler": [], "katki_maddeleri": [],
            "besin_degerleri": {}, "saglik_puani": 0, "renk": "Kirmizi"
        })
    
    return jsonify(analiz_et(text))
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"})
if __name__ == '__main__':
    print("\n🍎 GIDA ANALİZ v6 (Fallback'li)")
    app.run(host='0.0.0.0', port=5000, debug=False)
