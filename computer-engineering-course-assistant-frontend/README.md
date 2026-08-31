# Bilgisayar Mühendisliği Ders Asistanı – Frontend

React + TypeScript + Vite tabanlı Local RAG frontend.

## Tech Stack

- React
- TypeScript
- Vite
- Tailwind CSS
- React Router
- Axios
- React Markdown
- Lucide React
- Vitest + Testing Library

## Backend

Frontend varsayılan olarak şu local backend’e bağlanır:

```text
http://localhost:8000
```

Backend ayrı terminalde çalışıyor olmalıdır:

```powershell
uvicorn app.main:app --reload
```

## Kurulum

Node.js 20.19+ veya 22.12+ önerilir.

```powershell
npm install
```

`.env` oluştur:

```powershell
Copy-Item .env.example .env
```

## Çalıştırma

```powershell
npm run dev
```

Varsayılan adres:

```text
http://localhost:5173
```

## Test

```powershell
npm test
```

## Build

```powershell
npm run build
```

## Sayfalar

```text
/           Chat
/courses    Dersler
/documents  Kaynaklar
/about      Hakkında
```

## Ana Kullanım Akışı

```text
Ders oluştur
   ↓
PDF yükle
   ↓
Chat ekranında ders seç
   ↓
Soru sor
   ↓
Backend RAG yanıtı al
   ↓
Cevap + kaynakları görüntüle
```

## API Contract

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

### Chat

```text
POST /api/chat
```

## Not

Frontend tarafında chunking, embedding, cosine similarity veya LLM inference
yapılmaz. Tüm RAG işlemleri backend tarafındadır.
