import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export const Card = ({ children, className }) => (
  <div className={twMerge("bg-white border border-neutral-200/90 rounded-2xl p-7 sm:p-8 transition-all hover:border-neutral-900/80 hover:shadow-sm", className)}>
    {children}
  </div>
);

export const Button = ({ children, onClick, variant = "primary", isLoading, className, ...props }) => {
  const base = "inline-flex items-center justify-center px-5 py-3 rounded-full font-semibold text-sm sm:text-base transition-all duration-150 disabled:opacity-50 disabled:cursor-not-allowed select-none";
  const styles = {
    primary: "bg-neutral-950 text-white hover:bg-neutral-800 active:bg-black shadow-sm",
    secondary: "bg-neutral-100 text-neutral-900 hover:bg-neutral-200 active:bg-neutral-300",
    outline: "border border-neutral-300 text-neutral-900 hover:border-neutral-950 hover:bg-neutral-50 bg-white"
  };

  return (
    <button onClick={onClick} disabled={isLoading} className={twMerge(clsx(base, styles[variant]), className)} {...props}>
      {isLoading ? "Processing..." : children}
    </button>
  );
};

export const Input = ({ label, ...props }) => (
  <div className="mb-5">
    <label className="block text-xs font-semibold text-neutral-600 uppercase tracking-wider mb-2">{label}</label>
    <input 
      className="w-full bg-transparent border-b border-neutral-200 py-2.5 text-base sm:text-lg text-neutral-900 focus:outline-none focus:border-neutral-950 transition-colors placeholder-neutral-400"
      {...props} 
    />
  </div>
);