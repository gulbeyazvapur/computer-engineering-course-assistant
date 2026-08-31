# Bilgisayar Mühendisliği Ders Asistanı – Backend

Microsoft Foundry Local kullanarak tamamen yerel çalışan RAG tabanlı ders asistanının FastAPI backend'i.

## Mimari

```text
PDF → Text → Chunk → Embedding → SQLite
                              ↓
Question → Query Embedding → Cosine Similarity → Top-K
                                             ↓
                                   Context + Prompt
                                             ↓
                                   Foundry Local LLM
                                             ↓
                                    Answer + Sources
```

## Gereksinimler

- Python 3.11+
- Microsoft Foundry Local tarafından desteklenen ortam
- Windows için Foundry Local WinML paketi önerilir

## Kurulum

### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-windows.txt
```

### macOS / Linux

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Microsoft'un güncel Foundry Local dokümantasyonunda Windows için
`foundry-local-sdk-winml`, diğer platformlar için `foundry-local-sdk`
önerilmektedir.

## Environment

```bash
copy .env.example .env
```

Uygulama proje kökündeki `.env` dosyasını otomatik yükler.
`.env.example`, desteklenen ayarların örneğidir. `.env` oluşturmasanız da
varsayılan değerlerle uygulama çalışabilir.

## Modelleri Önceden Hazırlama

İlk kullanımda model ağırlıkları indirilebilir. İnternetsiz demo öncesinde:

```bash
python scripts/prepare_models.py
```

çalıştırın.

Modeller cache'lendikten sonra:

```text
AUTO_DOWNLOAD_MODELS=false
```

kullanarak uygulamanın eksik model için ağ indirmesi denemesini engelleyebilirsiniz.

Varsayılan embedding modeli:

```text
qwen3-embedding-0.6b
```

Varsayılan chat modeli:

```text
qwen3-4b
```

`phi-3.5-mini` ve `qwen3.5-2b-text` cihazda denendi; ikisi de "Deadlock nedir?"
gibi temel işletim sistemleri kavramlarında teknik hatalar / uydurma bilgi
üretti. `qwen3-4b` (Qwen3 ailesinin 4B yoğun modeli) öncelikli aday olarak
seçildi çünkü:

- Model kapasitesi `qwen3.5-2b-text`'in iki katı; teknik/gerçek bilgi
  doğruluğunda parametre sayısının büyümesi, bağlam uzunluğundan çok daha
  belirleyici — halüsinasyon sorununu doğrudan hedefliyor.
  `qwen3.5-2b-text`'in çok daha uzun bağlam penceresi (262144) bu projede
  kullanılmıyor; RAG akışı zaten yalnızca Top-K (varsayılan 3) chunk
  gönderiyor, dolayısıyla `qwen3-4b`'nin 40960 token'lık bağlamı fazlasıyla
  yeterli.
- Aynı Microsoft/Qwen3 ailesi, `apache-2.0` lisanslı, `reasoning` +
  `tool-calling` destekli — `complete_streaming_chat()` kod yolu ve
  `<think>` etiketi temizleme mantığı değişmeden çalışıyor.
- CUDA GPU varyantı 2.6 GB; test edilen cihazdaki RTX 5050 Laptop GPU'nun
  7.7 GB VRAM'ine rahatça sığıyor. Buna karşın cihazda ölçülen boş sistem
  RAM'i (2.7 GB / 15.6 GB) düşüktü — model yüklerken diğer ağır
  uygulamaları kapatmanız önerilir.
- Sonuç: daha yavaş ilk yükleme ve biraz daha yüksek VRAM kullanımı
  pahasına, ders asistanı için kritik olan "doğru ve halüsinasyonsuz teknik
  cevap" önceliğini karşılıyor.

Model cihazda henüz cache'li değilse önce indirin:

```powershell
foundry model download qwen3-4b
```

Eğer alias cihazınızdaki katalogda yoksa `.env`/environment üzerinden mevcut
model alias'ını kullanın.

## Backend'i Çalıştırma

Proje kökünde:

```bash
uvicorn app.main:app --reload
```

Adres:

```text
http://localhost:8000
```

Swagger:

```text
http://localhost:8000/docs
```

Health:

```text
GET http://localhost:8000/health
```

## API

### Dersler

```text
GET  /api/courses
POST /api/courses
```

### Dokümanlar

```text
GET  /api/documents
POST /api/documents
```

Upload `multipart/form-data`:

```text
courseId=<integer>
file=<pdf>
```

### Chat

```text
POST /api/chat
```

Request:

```json
{
  "question": "Deadlock nedir?",
  "courseId": 1
}
```

Response:

```json
{
  "answer": "...",
  "sources": [
    {
      "documentName": "Deadlock.pdf",
      "chunkIndex": 2
    }
  ]
}
```

## Testler

Foundry Local gerçek model çağrıları testlerde mock'lanmıştır; bu nedenle temel
unit testler model indirmeden çalıştırılabilir.

```bash
python -m pytest -q
```

## Offline Çalışma

Soru-cevap akışı localdir:

```text
React localhost
→ FastAPI localhost
→ SQLite
→ Foundry Local
```

Model dosyaları önceden cihazda cache'lendikten sonra chat akışı internet
bağlantısı gerektirmez.

## İlk Sürüm Kapsam Dışı

- Login / JWT
- PostgreSQL
- Cloud LLM API
- Azure deployment
- OCR
- FAISS / Pinecone / Qdrant
- Conversation memory
- Multi-user session
