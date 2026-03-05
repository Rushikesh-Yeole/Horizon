import { Button } from "../../components/UI";

export default function ReviewStep({
  formData,
  handleFinalSubmit,
  back,
  loading
}) {

  const { email, profile } = formData;

  return (
    <div className="space-y-6">

      <div>
        <h2 className="text-lg font-semibold mb-2">
          Final Review
        </h2>
        <p className="text-sm text-gray-500">
          Confirm your digital identity.
        </p>
      </div>

      {/* Summary Card */}
      <div className="bg-gray-50 rounded-xl p-4 space-y-3 text-sm">

        <div>
          <span className="font-semibold">Name:</span> {profile.name}
        </div>

        <div>
          <span className="font-semibold">Email:</span> {email}
        </div>

        <div>
          <span className="font-semibold">Skills:</span>
          <div className="flex flex-wrap gap-2 mt-2">
            {profile.skills.map((skill, index) => (
              <span
                key={index}
                className="px-2 py-1 bg-white border rounded-md text-xs"
              >
                {skill}
              </span>
            ))}
          </div>
        </div>

        {profile.education.length > 0 && (
          <div>
            <span className="font-semibold">Education:</span>
            <ul className="mt-1 space-y-1">
              {profile.education.map((edu, i) => (
                <li key={i}>
                  {edu.degree} — {edu.branch} @ {edu.college}
                </li>
              ))}
            </ul>
          </div>
        )}

        {profile.projects.length > 0 && (
          <div>
            <span className="font-semibold">Projects:</span>
            <ul className="mt-1 space-y-1">
              {profile.projects.map((proj, i) => (
                <li key={i}>
                  {proj.title}
                </li>
              ))}
            </ul>
          </div>
        )}

      </div>

      <div className="flex gap-3 pt-4">
        <Button
          onClick={back}
          variant="secondary"
          className="w-1/2"
        >
          Back
        </Button>

        <Button
          onClick={handleFinalSubmit}
          isLoading={loading}
          className="w-1/2"
        >
          Generate Identity Token
        </Button>
      </div>

    </div>
  );
}