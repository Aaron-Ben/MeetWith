import React from 'react';
import { cn } from '@/utils/ppt';

interface ProgressBarProps {
  progress: number;
  total: number;
  className?: string;
  label?: string;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  progress,
  total,
  className,
  label,
}) => {
  const percentage = total > 0 ? (progress / total) * 100 : 0;

  return (
    <div className={cn('w-full', className)}>
      {(label || total > 0) && (
        <div className="flex justify-between items-center mb-1">
          {label && <span className="text-sm text-gray-600">{label}</span>}
          {total > 0 && (
            <span className="text-sm text-gray-600">
              {progress} / {total}
            </span>
          )}
        </div>
      )}
      <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
        <div
          className="bg-blue-500 h-2 rounded-full transition-all duration-300 ease-out"
          style={{ width: `${Math.min(percentage, 100)}%` }}
        />
      </div>
    </div>
  );
};
