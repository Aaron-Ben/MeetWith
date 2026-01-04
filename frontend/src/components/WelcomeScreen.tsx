import { InputForm } from './InputForm';

interface WelcomeScreenProps {
  handleSubmit: (inputValue: string, model: string) => void;
  onCancel: () => void;
  isLoading: boolean;
}


export const WelcomeScreen: React.FC<WelcomeScreenProps> = ({
  handleSubmit,
  onCancel,
  isLoading,
}) => {
  return (
    <div className="h-full flex flex-col items-center justify-center text-center px-4 flex-1 w-full max-w-3xl mx-auto gap-4 bg-white">
      <div>
        <p className="text-xl md:text-2xl text-neutral-600">
          How can I help you today?
        </p>
      </div>

      <div className="w-full mt-4">
        <InputForm
          onSubmit={handleSubmit}
          isLoading={isLoading}
          onCancel={onCancel}
          hasHistory={false}
        />
      </div>
    </div>
  );
};
