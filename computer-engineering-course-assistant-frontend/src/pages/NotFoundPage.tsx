import { Link } from "react-router-dom";

export default function NotFoundPage() {
  return (
    <div className="mx-auto max-w-xl rounded-lg border border-warm-border bg-white p-10 text-center">
      <p className="text-sm font-semibold text-terracotta">404</p>
      <h2 className="mt-2 text-2xl font-bold text-charcoal">
        Sayfa bulunamadı
      </h2>
      <Link
        to="/"
        className="mt-5 inline-block text-sm font-semibold text-terracotta hover:text-terracotta-hover"
      >
        Chat ekranına dön
      </Link>
    </div>
  );
}
