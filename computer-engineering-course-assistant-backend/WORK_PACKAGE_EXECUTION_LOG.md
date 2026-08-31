# Backend İş Paketleri – Uygulama Günlüğü

İş paketleri WP-BE-01 → WP-BE-21 sırasıyla ele alınmıştır.

## Sıralı Sonuç

1. **WP-BE-01 – Backend Proje Kurulumu:** FastAPI proje iskeleti ve bağımlılık dosyaları oluşturuldu.
2. **WP-BE-02 – Konfigürasyon:** `.env`, CORS ve merkezi ayarlar eklendi.
3. **WP-BE-03 – SQLite:** `courses`, `documents`, `document_chunks` şemaları ve repository katmanı oluşturuldu.
4. **WP-BE-04 – Ders API:** `GET/POST /api/courses` geliştirildi.
5. **WP-BE-05 – Upload:** Multipart PDF upload ve dosya doğrulama geliştirildi.
6. **WP-BE-06 – PDF Parsing:** PyPDF ile text extraction geliştirildi.
7. **WP-BE-07 – Chunking:** Text normalization ve paragraf tabanlı chunking geliştirildi.
8. **WP-BE-08 – Embedding:** Foundry Local `get_embedding_client()` entegrasyonu kodlandı.
9. **WP-BE-09 – Ingestion:** PDF → text → chunk → embedding → SQLite transaction akışı tamamlandı.
10. **WP-BE-10 – Doküman API:** `GET /api/documents` ve ders filtresi tamamlandı.
11. **WP-BE-11 – Query Retrieval:** Query embedding ve yalnız seçilen derste retrieval tamamlandı.
12. **WP-BE-12 – Similarity:** NumPy cosine similarity ve Top-K sıralama tamamlandı.
13. **WP-BE-13 – Prompt:** Context-grounded, bilgi uydurmamayı isteyen system prompt tamamlandı.
14. **WP-BE-14 – Local LLM:** Foundry Local `get_chat_client()` + `complete_chat()` entegrasyonu kodlandı.
15. **WP-BE-15 – RAG:** Retrieval → context → prompt → LLM orchestration tamamlandı.
16. **WP-BE-16 – Chat API:** `POST /api/chat` tamamlandı.
17. **WP-BE-17 – Sources:** Retrieval sonucundan gerçek doküman kaynakları response'a eklendi.
18. **WP-BE-18 – Hatalar/Logging:** Kontrollü `AppError` response'ları ve logging eklendi.
19. **WP-BE-19 – Offline/Performance:** Model reuse, önceden model cacheleme script'i ve embedding tekrar hesaplamama yaklaşımı eklendi.
20. **WP-BE-20 – Test:** Chunking, similarity, course, retrieval ve RAG testleri yazıldı.
21. **WP-BE-21 – Cleanup/Docs:** README, requirements, `.env.example` ve uygulama durum dokümanları tamamlandı.

## Otomatik Test Sonucu

```text
12 passed
```

Ayrıca FastAPI smoke testinde:

```text
GET /health       → 200 {"status":"ok"}
GET /api/courses  → 200 []
```

doğrulandı.

## Gerçek Windows/Foundry Local Ortamında Kalan Doğrulama

Kod güncel Microsoft Foundry Local Python SDK yüzeyine göre yazılmıştır; ancak bu
çalışma ortamında Foundry Local runtime/model dosyaları bulunmadığından aşağıdaki
maddeler kullanıcının Windows bilgisayarında doğrulanmalıdır:

- `qwen3-embedding-0.6b` modelini cache/load etme.
- `phi-3.5-mini` alias'ını katalogda doğrulama; mevcut değilse bir küçük chat modeli seçme.
- Gerçek PDF üzerinde embedding oluşturma.
- Gerçek `/api/chat` inference.
- Modeller cache'lendikten sonra internet kapalı uçtan uca test.
