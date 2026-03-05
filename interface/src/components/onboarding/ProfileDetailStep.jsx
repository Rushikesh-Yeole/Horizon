import { useRef } from "react";
import { Button, Input } from "../../components/UI";
import API from "../../services/api";

export default function ProfileDetailsStep({
  formData,
  setFormData,
  next,
  back
}) {
  const fileRef = useRef();

  // -------- Resume Upload --------
  const handleResumeUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const data = new FormData();
    data.append("resume", file);

    try {
      const res = await API.post("/users/me/resume", data, {
        headers: { "Content-Type": "multipart/form-data" }
      });

      const parsed = res.data.resume;

      setFormData({
        ...formData,
        profile: {
          ...formData.profile,
          name: parsed.name || formData.profile.name,
          skills: parsed.skills || [],
          education: parsed.education || [],
          projects: parsed.projects || []
        }
      });

    } catch (err) {
      console.error("Resume parsing failed:", err);
    }
  };

  // -------- Education Handlers --------
  const addEducation = () => {
    setFormData({
      ...formData,
      profile: {
        ...formData.profile,
        education: [
          ...formData.profile.education,
          { degree: "", branch: "", college: "" }
        ]
      }
    });
  };

  const updateEducation = (index, field, value) => {
    const updated = [...formData.profile.education];
    updated[index][field] = value;

    setFormData({
      ...formData,
      profile: {
        ...formData.profile,
        education: updated
      }
    });
  };

  // -------- Project Handlers --------
  const addProject = () => {
    setFormData({
      ...formData,
      profile: {
        ...formData.profile,
        projects: [
          ...formData.profile.projects,
          { title: "", desc: "" }
        ]
      }
    });
  };

  const updateProject = (index, field, value) => {
    const updated = [...formData.profile.projects];
    updated[index][field] = value;

    setFormData({
      ...formData,
      profile: {
        ...formData.profile,
        projects: updated
      }
    });
  };

  return (
    <div className="space-y-6">

      {/* Resume Upload */}
      <div>
        <p className="text-xs font-semibold uppercase tracking-wider mb-2">
          Upload Resume (Auto-Fill)
        </p>
        <input
          type="file"
          accept=".pdf"
          ref={fileRef}
          onChange={handleResumeUpload}
        />
      </div>

      {/* Skills */}
      <Input
        label="Skills (comma separated)"
        value={formData.profile.skills.join(",")}
        onChange={e =>
          setFormData({
            ...formData,
            profile: {
              ...formData.profile,
              skills: e.target.value
                .split(",")
                .map(s => s.trim())
                .filter(Boolean)
            }
          })
        }
      />

      {/* Education Section */}
      <div>
        <div className="flex justify-between items-center mb-2">
          <p className="text-xs font-semibold uppercase tracking-wider">
            Education
          </p>
          <Button onClick={addEducation} variant="secondary">
            Add
          </Button>
        </div>

        {formData.profile.education.map((edu, index) => (
          <div key={index} className="space-y-2 mb-4">
            <Input
              placeholder="Degree"
              value={edu.degree}
              onChange={e => updateEducation(index, "degree", e.target.value)}
            />
            <Input
              placeholder="Branch"
              value={edu.branch}
              onChange={e => updateEducation(index, "branch", e.target.value)}
            />
            <Input
              placeholder="College"
              value={edu.college}
              onChange={e => updateEducation(index, "college", e.target.value)}
            />
          </div>
        ))}
      </div>

      {/* Projects Section */}
      <div>
        <div className="flex justify-between items-center mb-2">
          <p className="text-xs font-semibold uppercase tracking-wider">
            Projects
          </p>
          <Button onClick={addProject} variant="secondary">
            Add
          </Button>
        </div>

        {formData.profile.projects.map((proj, index) => (
          <div key={index} className="space-y-2 mb-4">
            <Input
              placeholder="Project Title"
              value={proj.title}
              onChange={e => updateProject(index, "title", e.target.value)}
            />
            <textarea
              className="w-full bg-gray-50 rounded-lg border-0 p-3 text-sm focus:ring-1 focus:ring-black"
              placeholder="Project Description"
              value={proj.desc}
              onChange={e => updateProject(index, "desc", e.target.value)}
            />
          </div>
        ))}
      </div>

      {/* Navigation */}
      <div className="flex gap-3">
        <Button onClick={back} className="w-1/2" variant="secondary">
          Back
        </Button>

    <Button
      onClick={() => {
        if (formData.profile.skills.length === 0) {
          alert("Please add at least one skill or upload a resume.");
          return;
        }
        next();
      }}
    >
  Continue
</Button>
      </div>

    </div>
  );
}