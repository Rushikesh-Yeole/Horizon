import { Button, Input } from '../../components/UI';
import { ArrowRight } from 'lucide-react';

export default function ProfileStep({ formData, setFormData, next }) {
  return (
    <div className="space-y-5">

      <Input
        label="Full Name"
        value={formData.profile.name}
        onChange={e =>
          setFormData({
            ...formData,
            profile: {
              ...formData.profile,
              name: e.target.value
            }
          })
        }
      />

      <Input
        label="Email"
        value={formData.email}
        onChange={e =>
          setFormData({ ...formData, email: e.target.value })
        }
      />

      <Input
        label="Password"
        type="password"
        value={formData.password}
        onChange={e =>
          setFormData({ ...formData, password: e.target.value })
        }
      />

      <Button
        onClick={next}
        className="w-full justify-center"
      >
        Next <ArrowRight className="ml-2 w-4 h-4" />
      </Button>

    </div>
  );
}