import studyIllustration from "../../assets/study-assistant-illustration.svg";

export default function EmptyChatState() {
  return (
    <div className="flex min-h-64 flex-col items-center justify-center px-6 text-center">
      <h2 className="text-lg font-semibold text-charcoal">Sorularını Sormaya Başla</h2>
      <p className="mt-2 max-w-md text-sm text-warm-gray">
        Seçtiğin dersin materyallerine göre soru sorabilirsin.
      </p>

      <img
        src={studyIllustration}
        alt=""
        className="mt-5 h-auto w-[185px] sm:w-[205px] md:w-[230px]"
      />

      <p className="mt-5 max-w-sm text-sm text-warm-gray">
        Bir ders seçip ilk sorunu yazarak başlayabilirsin.
      </p>
    </div>
  );
}
