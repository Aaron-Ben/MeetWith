interface AttachmentPreviewProps {
  attachments: Array<{ id: string; name: string; url: string; type: string }>;
  onRemove: (id: string) => void;
}

export default function AttachmentPreview({ attachments, onRemove }: AttachmentPreviewProps) {
  if (attachments.length === 0) return null;

  return (
    <div className="attachment-preview-area">
      {attachments.map(attachment => (
        <div key={attachment.id} className="attachment-preview-item">
          <span className="file-preview-icon">📎</span>
          <button
            className="file-preview-remove-btn"
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
