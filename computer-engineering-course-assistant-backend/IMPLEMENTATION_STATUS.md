# Backend İş Paketleri – Uygulama Durumu

| Paket | Durum | Teknik Çıktı |
|---|---|---|
| WP-BE-01 | Tamamlandı | FastAPI skeleton, requirements, klasörler |
| WP-BE-02 | Tamamlandı | Config, CORS, environment ayarları |
| WP-BE-03 | Tamamlandı | SQLite schema, DB init, repository katmanı |
| WP-BE-04 | Tamamlandı | GET/POST `/api/courses` |
| WP-BE-05 | Tamamlandı | Multipart PDF upload ve validasyon |
| WP-BE-06 | Tamamlandı | PyPDF text extraction |
| WP-BE-07 | Tamamlandı | Normalization + 1–3 paragraf chunking |
| WP-BE-08 | Kodlandı | Foundry Local embedding client entegrasyonu |
| WP-BE-09 | Tamamlandı | Transactional ingestion pipeline |
| WP-BE-10 | Tamamlandı | GET `/api/documents`, course filter |
| WP-BE-11 | Tamamlandı | Query embedding + course scoped retrieval |
| WP-BE-12 | Tamamlandı | NumPy cosine similarity + Top-K |
| WP-BE-13 | Tamamlandı | Grounded system/context prompt |
| WP-BE-14 | Kodlandı | Foundry Local chat client entegrasyonu |
| WP-BE-15 | Tamamlandı | RAG orchestration |
| WP-BE-16 | Tamamlandı | POST `/api/chat` |
| WP-BE-17 | Tamamlandı | Retrieval tabanlı source response |
| WP-BE-18 | Tamamlandı | AppError handler + logging |
| WP-BE-19 | Kodlandı | Model reuse, cached embeddings, preload script |
| WP-BE-20 | Tamamlandı | Unit/RAG tests; Foundry çağrıları mock |
| WP-BE-21 | Tamamlandı | README, requirements, cleanup |

## Donanım Üzerinde Doğrulanması Gerekenler

Aşağıdaki maddeler kodlandı ancak bu çalışma ortamında Microsoft Foundry Local
runtime/model dosyaları bulunmadığı için gerçek cihaz üzerinde doğrulanmalıdır:

1. `qwen3-embedding-0.6b` modelinin cihaz kataloğunda bulunması ve yüklenmesi.
2. `phi-3.5-mini` alias'ının cihaz kataloğunda bulunması; yoksa mevcut küçük chat modeliyle değiştirilmesi.
3. Gerçek PDF ingestion sırasında embedding üretimi.
4. Gerçek `/api/chat` çağrısında local LLM yanıtı.
5. Modeller cache'lendikten sonra internet kapalıyken uçtan uca test.

Bu doğrulama için `scripts/prepare_models.py` ve Swagger `/docs` kullanılabilir.
