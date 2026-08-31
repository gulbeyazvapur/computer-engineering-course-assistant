# Frontend İş Paketleri – Uygulama Günlüğü

İş paketleri WP-FE-01 → WP-FE-25 sırasıyla uygulanmıştır.

| Paket | Durum | Teknik Çıktı |
|---|---|---|
| WP-FE-01 | Tamamlandı | React + TypeScript + Vite proje iskeleti |
| WP-FE-02 | Tamamlandı | Tailwind CSS v4 + temel stil altyapısı |
| WP-FE-03 | Tamamlandı | React Router, 4 ana route + 404 |
| WP-FE-04 | Tamamlandı | AppLayout, Header, Sidebar |
| WP-FE-05 | Tamamlandı | Course, Document, Chat ve API TypeScript modelleri |
| WP-FE-06 | Tamamlandı | Axios API client + `.env` base URL |
| WP-FE-07 | Tamamlandı | `GET /api/courses` entegrasyonu + `useCourses` |
| WP-FE-08 | Tamamlandı | Ana ChatPage yapısı |
| WP-FE-09 | Tamamlandı | CourseSelector |
| WP-FE-10 | Tamamlandı | ChatInput, boş soru ve Enter validasyonu |
| WP-FE-11 | Tamamlandı | `POST /api/chat` entegrasyonu |
| WP-FE-12 | Tamamlandı | ChatMessage + React Markdown |
| WP-FE-13 | Tamamlandı | SourceList + doküman deduplication |
| WP-FE-14 | Tamamlandı | Chat loading/error + duplicate submit engeli |
| WP-FE-15 | Tamamlandı | CoursesPage + CourseCard |
| WP-FE-16 | Tamamlandı | `POST /api/courses` + CreateCourseForm |
| WP-FE-17 | Tamamlandı | DocumentsPage + list/card |
| WP-FE-18 | Tamamlandı | PDF upload + multipart FormData |
| WP-FE-19 | Tamamlandı | Derse göre document filter |
| WP-FE-20 | Tamamlandı | AboutPage + Local RAG açıklaması |
| WP-FE-21 | Tamamlandı | Responsive desktop/tablet/mobile düzeni |
| WP-FE-22 | Tamamlandı | Button, Alert, Loader + UX standardizasyonu |
| WP-FE-23 | Kodlandı | Vitest + Testing Library testleri |
| WP-FE-24 | Hazır | Gerçek backend contract’ına göre servisler |
| WP-FE-25 | Tamamlandı | README, env, build/test scriptleri |

## Gerçek Bilgisayarda Doğrulanacaklar

Bu teslimde `node_modules` bulunmaz. Kullanıcının bilgisayarında:

```powershell
npm install
npm test
npm run build
npm run dev
```

komutları çalıştırılmalıdır.

Backend `http://localhost:8000` üzerinde açıkken gerçek uçtan uca test:

1. Ders oluşturma
2. PDF yükleme
3. Doküman listeleme
4. Chat’te ders seçme
5. Soru gönderme
6. Answer + Sources render
7. Backend kapalıyken bağlantı hatası
