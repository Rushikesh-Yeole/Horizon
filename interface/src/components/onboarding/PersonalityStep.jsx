import { useEffect } from "react";
import { Button } from "../../components/UI";

export default function PersonalityStep({
  questions,
  formData,
  setFormData,
  next,
  back
}) {

  // ✅ Initialize answers safely
  useEffect(() => {
    if (
      questions.length > 0 &&
      (!formData.personality_answers ||
        formData.personality_answers.length !== questions.length)
    ) {
      const initializedAnswers = questions.map((q) => ({
        type: q.type,
        score: 3, // default neutral
      }));

      setFormData((prev) => ({
        ...prev,
        personality_answers: initializedAnswers,
      }));
    }
  }, [questions]);

  const handleAnswerChange = (index, type, score) => {
    const updated = [...formData.personality_answers];

    updated[index] = { type, score };

    setFormData((prev) => ({
      ...prev,
      personality_answers: updated,
    }));
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold mb-2">
          Personality Calibration
        </h2>
        <p className="text-sm text-gray-500">
          Choose how strongly you agree.
        </p>
      </div>

      {questions.length === 0 ? (
        <p className="text-sm text-gray-400">
          Loading questions...
        </p>
      ) : (
        questions.map((q, index) => {
          const selectedScore =
            formData.personality_answers?.[index]?.score ?? 3;

          return (
            <div key={index} className="space-y-3">
              <p className="text-sm font-medium">
                {q.question}
              </p>

              <div className="flex justify-between gap-2">
                {[1, 2, 3, 4, 5].map((value) => (
                  <button
                    key={value}
                    type="button"
                    onClick={() =>
                      handleAnswerChange(index, q.type, value)
                    }
                    className={`flex-1 py-2 rounded-lg border text-sm font-medium transition
                      ${
                        selectedScore === value
                          ? "bg-blue-600 text-white border-blue-600"
                          : "bg-white text-gray-700 border-gray-300 hover:bg-gray-100"
                      }
                    `}
                  >
                    {value}
                  </button>
                ))}
              </div>

              <div className="flex justify-between text-xs text-gray-400">
                <span>Strongly Disagree</span>
                <span>Strongly Agree</span>
              </div>
            </div>
          );
        })
      )}

      <div className="flex gap-3 pt-4">
        <Button
          onClick={back}
          variant="secondary"
          className="w-1/2"
        >
          Back
        </Button>

        <Button
          onClick={next}
          className="w-1/2"
        >
          Review
        </Button>
      </div>
    </div>
  );
}