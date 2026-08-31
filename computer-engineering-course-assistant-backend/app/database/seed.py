from __future__ import annotations

from app.database import repositories
from app.database.db import transaction


DEFAULT_COURSES: list[tuple[str, str]] = [
    (
        "Programlamaya Giriş",
        "Temel programlama kavramları, değişkenler, kontrol yapıları, döngüler ve "
        "fonksiyonlara ait ders materyalleri.",
    ),
    (
        "Nesne Yönelimli Programlama",
        "Sınıflar, nesneler, kalıtım, çok biçimlilik ve kapsülleme konularına ait "
        "ders materyalleri.",
    ),
    (
        "Veri Yapıları ve Algoritmalar",
        "Diziler, bağlı listeler, ağaçlar, graflar ve temel algoritma tasarımı "
        "konularına ait ders materyalleri.",
    ),
    (
        "Algoritma Analizi",
        "Zaman ve uzay karmaşıklığı, asimptotik analiz ve algoritma karşılaştırma "
        "yöntemlerine ait ders materyalleri.",
    ),
    (
        "Bilgisayar Organizasyonu ve Mimarisi",
        "İşlemci mimarisi, bellek hiyerarşisi, veri yolu ve donanım-yazılım "
        "etkileşimine ait ders materyalleri.",
    ),
    (
        "İşletim Sistemleri",
        "İşletim sistemleri, süreç yönetimi, bellek yönetimi, dosya sistemleri ve "
        "eşzamanlılık konularına ait ders materyalleri.",
    ),
    (
        "Veritabanı Yönetim Sistemleri",
        "İlişkisel veritabanı tasarımı, SQL, normalizasyon ve işlem yönetimi "
        "konularına ait ders materyalleri.",
    ),
    (
        "Bilgisayar Ağları",
        "Ağ mimarileri, TCP/IP, yönlendirme, protokoller ve ağ güvenliği "
        "konularına ait ders materyalleri.",
    ),
    (
        "Yazılım Mühendisliği",
        "Yazılım geliştirme süreçleri, gereksinim analizi, tasarım desenleri ve "
        "proje yönetimine ait ders materyalleri.",
    ),
    (
        "Web Programlama",
        "İstemci ve sunucu taraflı web teknolojileri, HTTP protokolü ve modern "
        "web çatıları konularına ait ders materyalleri.",
    ),
    (
        "Mobil Uygulama Geliştirme",
        "Android ve iOS platformlarında uygulama geliştirme, arayüz tasarımı ve "
        "mobil mimarilere ait ders materyalleri.",
    ),
    (
        "Yapay Zeka",
        "Arama algoritmaları, bilgi temsili, uzman sistemler ve akıllı ajanlara "
        "ait ders materyalleri.",
    ),
    (
        "Makine Öğrenmesi",
        "Denetimli ve denetimsiz öğrenme, model eğitimi ve değerlendirme "
        "yöntemlerine ait ders materyalleri.",
    ),
    (
        "Veri Madenciliği",
        "Büyük veri kümelerinden örüntü çıkarımı, kümeleme ve sınıflandırma "
        "tekniklerine ait ders materyalleri.",
    ),
    (
        "Görüntü İşleme",
        "Dijital görüntü temelleri, filtreleme, kenar tespiti ve görüntü "
        "segmentasyonuna ait ders materyalleri.",
    ),
    (
        "Siber Güvenlik",
        "Ağ güvenliği, kriptografi, saldırı türleri ve savunma mekanizmalarına "
        "ait ders materyalleri.",
    ),
    (
        "Gömülü Sistemler",
        "Mikrodenetleyiciler, gerçek zamanlı işletim sistemleri ve donanım "
        "programlamaya ait ders materyalleri.",
    ),
    (
        "Mikroişlemciler",
        "İşlemci mimarisi, komut kümeleri, adresleme modları ve assembly "
        "programlamaya ait ders materyalleri.",
    ),
    (
        "Otomata Teorisi ve Biçimsel Diller",
        "Sonlu otomatlar, bağlamsız gramerler, Turing makineleri ve "
        "hesaplanabilirlik konularına ait ders materyalleri.",
    ),
    (
        "Derleyiciler",
        "Sözdizimsel ve anlamsal analiz, ara kod üretimi ve derleyici "
        "optimizasyonuna ait ders materyalleri.",
    ),
    (
        "Paralel ve Dağıtık Sistemler",
        "Paralel programlama modelleri, dağıtık sistem mimarileri ve "
        "senkronizasyon konularına ait ders materyalleri.",
    ),
    (
        "Bulut Bilişim",
        "Bulut hizmet modelleri, sanallaştırma, ölçeklenebilirlik ve konteyner "
        "teknolojilerine ait ders materyalleri.",
    ),
    (
        "İnsan-Bilgisayar Etkileşimi",
        "Kullanıcı arayüzü tasarımı, kullanılabilirlik ilkeleri ve etkileşim "
        "değerlendirmesine ait ders materyalleri.",
    ),
    (
        "DevOps ve Yazılım Dağıtımı",
        "Sürekli entegrasyon, sürekli dağıtım, otomasyon ve altyapı yönetimine "
        "ait ders materyalleri.",
    ),
    (
        "Bilgisayar Grafikleri",
        "2B/3B modelleme, render teknikleri, dönüşümler ve grafik donanımına ait "
        "ders materyalleri.",
    ),
]


def seed_default_courses() -> None:
    """Bootstrap DEFAULT_COURSES, but only into a genuinely empty courses
    table -- i.e. only on the very first startup, before any real usage.

    This app now supports full user-managed course CRUD (create/rename/
    delete), so seeding must never "top up" or resurrect defaults once the
    table has any row in it: if it did, a course the user deleted (default
    or not) would silently reappear on the next restart, which defeats
    dynamic course management. Once a single course exists -- seeded or
    user-created -- this is a permanent no-op for the lifetime of that
    database.
    """
    with transaction() as conn:
        if repositories.count_courses(conn) > 0:
            return
        repositories.seed_courses(conn, DEFAULT_COURSES)
