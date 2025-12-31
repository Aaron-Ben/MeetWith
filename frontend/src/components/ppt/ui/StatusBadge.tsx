import React from 'react';
import { cn } from '@/utils/ppt';

type PageStatus = 'DRAFT' | 'DESCRIPTION_GENERATED' | 'GENERATING' | 'COMPLETED' | 'FAILED';
type TaskStatus = 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED';

interface StatusBadgeProps {
  status: PageStatus | TaskStatus | string;
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, className }) => {
  const getStatusConfig = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return {
          label: '已完成',
          bgColor: 'bg-green-100',
          textColor: 'text-green-700',
        };
      case 'GENERATING':
      case 'RUNNING':
      case 'PENDING':
        return {
          label: '生成中',
          bgColor: 'bg-blue-100',
          textColor: 'text-blue-700',
        };
      case 'FAILED':
        return {
          label: '失败',
          bgColor: 'bg-red-100',
          textColor: 'text-red-700',
        };
      case 'DESCRIPTION_GENERATED':
        return {
          label: '已生成描述',
          bgColor: 'bg-purple-100',
          textColor: 'text-purple-700',
        };
      case 'DRAFT':
      default:
        return {
          label: '草稿',
          bgColor: 'bg-gray-100',
          textColor: 'text-gray-700',
        };
    }
  };

  const config = getStatusConfig(status);

  return (
    <span
      className={cn(
        'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
        config.bgColor,
        config.textColor,
        className
      )}
    >
      {config.label}
    </span>
  );
};
