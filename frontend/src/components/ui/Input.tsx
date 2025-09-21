import React, { forwardRef } from 'react';
import { motion } from 'framer-motion';
import { clsx } from 'clsx';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  icon?: React.ReactNode;
  variant?: 'default' | 'glass';
}

const Input = forwardRef<HTMLInputElement, InputProps>(({
  label,
  error,
  icon,
  variant = 'default',
  className,
  ...props
}, ref) => {
  const baseClasses = 'w-full px-4 py-3 rounded-xl text-white placeholder-white/50 focus:outline-none transition-all duration-300';
  
  const variants = {
    default: 'bg-white/5 border border-white/20 focus:border-blue-400 focus:bg-white/10 text-white',
    glass: 'liquid-glass focus:border-blue-400 focus:from-white/15 focus:to-white/10 text-white',
  };

  return (
    <div className="space-y-2">
      {label && (
        <label className="block text-sm font-medium text-white/90">
          {label}
        </label>
      )}
      
      <div className="relative">
        {icon && (
          <div className="absolute left-3 top-1/2 transform -translate-y-1/2 text-white/50">
            {icon}
          </div>
        )}
        
        <motion.input
          ref={ref}
          className={clsx(
            baseClasses,
            variants[variant],
            icon && 'pl-10',
            error && 'border-red-400 focus:border-red-400',
            className
          )}
          whileFocus={{ scale: 1.02 }}
          {...(props as any)}
        />
      </div>
      
      {error && (
        <motion.p
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-red-400 text-sm"
        >
          {error}
        </motion.p>
      )}
    </div>
  );
});

Input.displayName = 'Input';

export default Input;
