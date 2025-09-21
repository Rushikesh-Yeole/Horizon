import React from 'react';
import { motion } from 'framer-motion';
import { clsx } from 'clsx';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  variant?: 'default' | 'glass' | 'liquid';
  hover?: boolean;
  onClick?: () => void;
}

const Card: React.FC<CardProps> = ({
  children,
  className,
  variant = 'default',
  hover = false,
  onClick,
}) => {
  const baseClasses = 'rounded-2xl transition-all duration-300';
  
  const variants = {
    default: 'glass-card',
    glass: 'glass-card glass-card-hover',
    liquid: 'liquid-glass liquid-glass-hover',
  };

  const hoverClasses = hover ? 'cursor-pointer hover:scale-105' : '';

  return (
    <motion.div
      whileHover={hover ? { scale: 1.02 } : {}}
      whileTap={hover ? { scale: 0.98 } : {}}
      className={clsx(
        baseClasses,
        variants[variant],
        hoverClasses,
        className
      )}
      onClick={onClick}
    >
      {children}
    </motion.div>
  );
};

export default Card;

