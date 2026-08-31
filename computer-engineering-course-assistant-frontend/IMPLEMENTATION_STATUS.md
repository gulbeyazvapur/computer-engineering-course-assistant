# Frontend Implementation Status

## Tamamlanan Modüller

- React/Vite/TypeScript proje iskeleti
- Tailwind CSS
- React Router
- Header / Sidebar / Layout
- Chat ekranı
- Ders seçimi
- Chat input
- Markdown AI cevabı
- Kaynak gösterimi
- Ders listeleme ve oluşturma
- Doküman listeleme ve filtreleme
- PDF upload
- Hakkında sayfası
- Axios servis katmanı
- TypeScript API modelleri
- Loading / success / error durumları
- Responsive yapı
- Unit test dosyaları

## Backend Contract

Frontend aşağıdaki mevcut backend endpointleri ile eşleştirilmiştir:

```text
GET  /api/courses
POST /api/courses
GET  /api/documents
POST /api/documents
POST /api/chat
```

## Kalan Lokal Doğrulama

- `npm install`
- `npm test`
- `npm run build`
- `npm run dev`
- Gerçek FastAPI backend ile CORS/API smoke test
- Foundry Local hazırlandıktan sonra PDF ingestion + gerçek chat
