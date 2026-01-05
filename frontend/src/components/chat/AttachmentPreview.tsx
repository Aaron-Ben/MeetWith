import { useTheme } from '@/contexts/ThemeContext';

interface AttachmentPreviewProps {
  attachments: Array<{ id: string; name: string; url: string; type: string }>;
  onRemove: (id: string) => void;
}

export default function AttachmentPreview({ attachments, onRemove }: AttachmentPreviewProps) {
  const { theme } = useTheme();
  if (attachments.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-2 w-full mb-2">
      {attachments.map(attachment => (
        <div
          key={attachment.id}
          className={`rounded-16 px-2.5 py-1 flex items-center text-sm relative ${
            theme === 'dark' ? 'bg-gray-700 text-gray-200' : 'bg-slate-200 text-slate-700'
          }`}
          style={{ borderRadius: '16px' }}
        >
          <span className="file-preview-icon">📎</span>
          <button
            className={`absolute top-[-8px] right-[-8px] bg-transparent border-0 cursor-pointer text-lg leading-none w-5 h-5 flex items-center justify-center rounded-full ${
              theme === 'dark' ? 'text-red-400 hover:bg-red-600 hover:text-white' : 'text-red-500 hover:bg-red-700 hover:text-white'
            }`}
            onClick={() => onRemove(attachment.id)}
            title="移除附件"
          >
            ×
          </button>
        </div>
      ))}
    </div>
  );
}
