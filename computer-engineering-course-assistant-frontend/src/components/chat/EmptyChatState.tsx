import studyIllustration from "../../assets/study-assistant-illustration.svg";

export default function EmptyChatState() {
  return (
    <div className="flex min-h-64 flex-col items-center justify-center px-6 text-center">
      <h2 className="text-lg font-semibold text-charcoal">Ders Asistanı</h2>
      <p className="mt-2 max-w-md text-sm text-warm-gray">
        Yüklediğiniz ders materyalleri üzerinden soru sorun.
      </p>

      <img
        src={studyIllustration}
        alt=""
        className="mt-5 h-auto w-[185px] sm:w-[205px] md:w-[230px]"
      />

      <p className="mt-5 text-sm font-medium text-charcoal">Henüz sohbet başlamadı.</p>
      <p className="mt-2 max-w-sm text-sm text-warm-gray">
        Bir ders seçip ilk sorunuzu yazarak başlayabilirsiniz.
      </p>
    </div>
  );
}
