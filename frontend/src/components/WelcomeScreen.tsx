import { InputForm } from './InputForm';
import { FileText } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface WelcomeScreenProps {
  handleSubmit: (inputValue: string, model: string) => void;
  onCancel: () => void;
  isLoading: boolean;
  onOpenPodcast: () => void;
}


export const WelcomeScreen: React.FC<WelcomeScreenProps> = ({
  handleSubmit,
  onCancel,
  isLoading,
  onOpenPodcast,
}) => {
  const navigate = useNavigate();

  return (
    <div className="h-full flex flex-col items-center justify-center text-center px-4 flex-1 w-full max-w-3xl mx-auto gap-4 bg-white">
      <div>
        <h1 className="text-5xl md:text-6xl font-semibold text-neutral-900 mb-3">
          Welcome.
        </h1>
        <p className="text-xl md:text-2xl text-neutral-600">
          How can I help you today?
        </p>
      </div>

      {/* 快捷操作按钮 */}
      <div className="flex flex-wrap justify-center gap-3 mt-4">
        <button
          onClick={() => navigate('/ppt')}
          className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
        >
          <FileText className="w-4 h-4" />
          创建PPT
        </button>
      </div>

      <div className="w-full mt-4">
        <InputForm
          onSubmit={handleSubmit}
          isLoading={isLoading}
          onCancel={onCancel}
          hasHistory={false}
          onOpenPodcast={onOpenPodcast}
        />
      </div>
    </div>
  );
};
