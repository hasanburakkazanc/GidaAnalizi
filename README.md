# 🍎 Paketli Gıda Analizi / Packaged Food Analyzer

Paketli gıda ambalajlarının fotoğraflarını **OpenCV** ile ön işlemden geçirip **Tesseract OCR** ile okuyan, içindeki katkı maddelerini, alerjenleri ve besin değerlerini analiz ederek 0–100 arası sağlık puanı hesaplayan **Flask REST API** projesi.

*(A Flask REST API that preprocesses packaged food label images with OpenCV, extracts text using Tesseract OCR, detects additives/allergens and nutrition facts, and calculates a 0–100 health score.)*

---

## ✨ Özellikler / Features
- **Görüntü Ön İşleme (`ultra_tarama`):** Yeniden boyutlandırma, gri tonlama ve CLAHE kontrast artırma.
- **OCR (Türkçe + İngilizce):** `pytesseract` (`lang='tur+eng'`) ile ambalaj üzerindeki içerik ve besin tablosu metnini çıkarma.
- **Katkı Maddesi & Alerjen Tespiti:** E-kodları / riskli bileşenler (`E330`, `E621 / MSG`, `Palm Yağı`, `Aspartam`, `Glikoz Şurubu` vb.) ve yaygın alerjenler (`Gluten`, `Süt`, `Yumurta`, `Soya`, `Fıstık`, `Susam`, `Kuruyemiş`) için bulanık eşleştirme (`difflib.get_close_matches`) destekli tarama.
- **Besin Değerleri & Sağlık Puanı:** Enerji, şeker, yağ, tuz, karbonhidrat, protein ve lif değerlerini ayıklayarak 0–100 arası puan + renk kodu (`Yesil`, `Sari`, `Kirmizi`) üretme.

---

## 📁 Proje Yapısı / Structure
```text
GidaAnalizi/
├── Paketli_gida_analiz/
│   ├── paketli_gida_okuma.py   # Flask API + OpenCV/Tesseract analiz motoru
│   ├── foto_cips.jpg           # Örnek test görseli (cips)
│   └── foto_cikolata.jpg       # Örnek test görseli (çikolata)
├── requirements.txt
└── README.md
```

---

## 🚀 Kurulum & Çalıştırma / Setup & Run

> **Ön koşul / Prerequisite:** Sisteminizde [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) (`tur` ve `eng` dil paketleriyle) kurulu olmalıdır.

```bash
git clone https://github.com/hasanburakkazanc/GidaAnalizi.git
cd GidaAnalizi
pip install -r requirements.txt
python Paketli_gida_analiz/paketli_gida_okuma.py
```

### API Endpoint'leri
- `GET /health` → Servis durum kontrolü (`{"status": "ok"}`)
- `POST /upload` → `file` form-data alanı ile etiket görseli gönderir ve JSON analiz sonucu döner.
