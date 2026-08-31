import { getErrorMessage } from "../utils/getErrorMessage";

function fakeAxiosError(overrides: {
  response?: { data?: unknown } | undefined;
}) {
  return {
    isAxiosError: true,
    ...overrides,
  };
}

test("backend güvenli message döndürürse onu gösterir", () => {
  const error = fakeAxiosError({
    response: {
      data: {
        error: "LLM_ERROR",
        message: "Yerel dil modeli şu anda yanıt oluşturamadı. Lütfen tekrar deneyin.",
      },
    },
  });

  expect(getErrorMessage(error)).toBe(
    "Yerel dil modeli şu anda yanıt oluşturamadı. Lütfen tekrar deneyin.",
  );
});

test("response içinde teknik bir ek alan olsa bile yalnızca message gösterilir", () => {
  const error = fakeAxiosError({
    response: {
      data: {
        error: "LLM_ERROR",
        message: "Yerel dil modeli şu anda yanıt oluşturamadı. Lütfen tekrar deneyin.",
        // Hypothetical technical field a future backend regression might add.
        stack:
          "Microsoft.ML.OnnxRuntimeGenAI.OnnxRuntimeGenAIException: CUDA error ...",
      },
    },
  });

  const result = getErrorMessage(error);

  expect(result).toBe(
    "Yerel dil modeli şu anda yanıt oluşturamadı. Lütfen tekrar deneyin.",
  );
  expect(result).not.toContain("OnnxRuntimeGenAIException");
  expect(result).not.toContain("CUDA");
});

test("network hatasında (response yok) kullanıcı dostu fallback döner", () => {
  const error = fakeAxiosError({ response: undefined });

  expect(getErrorMessage(error)).toBe(
    "Yerel sunucuya bağlanılamadı. Backend uygulamasının çalıştığından emin olun.",
  );
});

test("ham JS hatasının .stack alanı kullanıcıya yansımaz, yalnızca .message kullanılır", () => {
  const rawError = new Error("Network Error");
  rawError.stack =
    "Error: Network Error\n    at XMLHttpRequest.handleError (axios/lib/adapters/xhr.js:87:14)\n    at fetchData (app.tsx:42:10)";

  const result = getErrorMessage(rawError);

  expect(result).toBe("Network Error");
  expect(result).not.toContain("axios/lib/adapters");
  expect(result).not.toContain("app.tsx");
  expect(result).not.toContain("XMLHttpRequest");
});

test("mesajsız/beklenmeyen bir hata nesnesi ham haliyle basılmaz, fallback döner", () => {
  const weirdError = { some: "unexpected shape", nested: { stack: "..." } };

  const result = getErrorMessage(weirdError, "Beklenmeyen bir hata oluştu.");

  expect(result).toBe("Beklenmeyen bir hata oluştu.");
  expect(result).not.toContain("unexpected shape");
});

test("mesaj hiç yoksa verilen fallback kullanılır", () => {
  const error = fakeAxiosError({ response: { data: {} } });

  expect(getErrorMessage(error, "Özel fallback mesajı.")).toBe(
    "Özel fallback mesajı.",
  );
});
