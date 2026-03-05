import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export const Card = ({ children, className }) => (
  <div className={twMerge("glass-panel rounded-2xl p-6 transition-all hover:shadow-md", className)}>
    {children}
  </div>
);

export const Button = ({ children, onClick, variant = "primary", isLoading }) => {
  const base = "px-6 py-3 rounded-full font-medium text-sm transition-all active:scale-95 disabled:opacity-50";
  const styles = {
    primary: "bg-black text-white hover:bg-gray-800 shadow-lg shadow-black/10",
    secondary: "bg-gray-100 text-gray-900 hover:bg-gray-200",
    outline: "border border-gray-200 text-gray-600 hover:border-black hover:text-black"
  };

  return (
    <button onClick={onClick} disabled={isLoading} className={clsx(base, styles[variant])}>
      {isLoading ? "Processing..." : children}
    </button>
  );
};

export const Input = ({ label, ...props }) => (
  <div className="mb-4">
    <label className="block text-xs font-semibold text-secondary uppercase tracking-wider mb-2">{label}</label>
    <input 
      className="w-full bg-transparent border-b border-gray-200 py-2 text-lg focus:outline-none focus:border-black transition-colors placeholder-gray-300"
      {...props} 
    />
  </div>
);