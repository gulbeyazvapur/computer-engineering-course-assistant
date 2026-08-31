# Bilgisayar Mühendisliği Ders Asistanı

Bilgisayar Mühendisliği Ders Asistanı, yüklenen ders materyalleri üzerinden çalışan yerel bir **RAG (Retrieval-Augmented Generation)** uygulamasıdır.

Kullanıcı bir ders seçerek PDF kaynakları üzerinden doğal dilde soru sorabilir. Sistem, soruyla ilgili doküman bölümlerini semantic retrieval ile bulur ve yerel dil modeline bağlam olarak göndererek kaynak odaklı yanıt üretir.

Yapay zekâ işlemleri **Microsoft Foundry Local** ile cihaz üzerinde gerçekleştirilir.

## Özellikler

- Ders ve PDF kaynak yönetimi
- Çoklu PDF yükleme
- PDF metin çıkarma ve chunking
- Embedding tabanlı semantic search
- Ders bazlı RAG ve kaynak izolasyonu
- Kaynak dosya gösterimi
- Yerel LLM kullanımı
- GPU model swapping
- Kaynakta bilgi bulunmadığında fallback
- Model tekrarları ve prompt sızıntılarına karşı çıktı kontrolleri

Sistem; kavram açıklama, karşılaştırma, algoritma açıklama ve teknik süreç analizi gibi farklı soru türlerini destekleyecek şekilde geliştirilmiştir.

Örnek:

```text
Process ve thread arasındaki farkları kaynak paylaşımı
ve yürütme açısından karşılaştır.
```

```text
Deadlock oluşması için gerekli dört Coffman koşulunu
açıklayarak her birinin neden gerekli olduğunu belirt.
```

## Kullanılan Teknolojiler

### Backend
Python, FastAPI, SQLite, Microsoft Foundry Local, PyPDF, Pytest

### Frontend
React, TypeScript, Vite, React Router, Axios, Vitest

### Yapay Zeka
- Chat modeli: `phi-4-mini`
- Embedding modeli: `qwen3-embedding-0.6b`

## RAG Akışı

```text
PDF → Metin Çıkarma → Chunking → Embedding
                                ↓
Kullanıcı Sorusu → Semantic Retrieval → Yerel LLM → Yanıt
```

Dokümanlar heading-aware ve paragraph-aware şekilde maksimum **1000 karakterlik** chunk'lara ayrılır.

## Bilinen Sınırlamalar

Kaynakta bulunmayan ancak ders konusuyla ilişkili bazı sorularda yerel model kendi genel bilgisinden cevap üretebilir. Bu nedenle kritik bilgiler gerektiğinde orijinal ders materyali üzerinden doğrulanmalıdır.

## Geliştirici

**Gülbeyaz Vapur**  
Bilgisayar Mühendisliği
