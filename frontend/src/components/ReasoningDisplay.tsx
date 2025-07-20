interface ReasoningStep {
  text: string;
  icon?: string;
}

interface ReasoningData {
  type: string;
  title: string;
  steps: (string | ReasoningStep)[];
  conclusion: string;
  confidence: 'high' | 'medium' | 'low';
}

interface ReasoningDisplayProps {
  reasoning: ReasoningData;
  className?: string;
}

export default function ReasoningDisplay({ reasoning, className = '' }: ReasoningDisplayProps) {
  const getConfidenceColor = (confidence: string) => {
    switch (confidence) {
      case 'high': return 'text-green-600 dark:text-green-400'
      case 'medium': return 'text-yellow-600 dark:text-yellow-400'
      case 'low': return 'text-orange-600 dark:text-orange-400'
      default: return 'text-green-600 dark:text-green-400'
    }
  }

  const getConfidenceIcon = (confidence: string) => {
    switch (confidence) {
      case 'high': return '🟢'
      case 'medium': return '🟡'
      case 'low': return '🟠'
      default: return '🟢'
    }
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'analysis': return '🔍'
      case 'comparison': return '⚖️'
      case 'recommendation': return '💡'
      default: return '💭'
    }
  }

  return (
    <div className={`bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-slate-800 dark:to-slate-700 rounded-xl p-4 border border-blue-200 dark:border-slate-600 shadow-sm ${className}`}>
      {/* Header */}
      <div className="flex items-start space-x-3 mb-4">
        <div className="w-8 h-8 bg-blue-100 dark:bg-slate-600 rounded-lg flex items-center justify-center flex-shrink-0">
          <span className="text-lg">{getTypeIcon(reasoning.type)}</span>
        </div>
        <div className="flex-1">
          <h3 className="font-semibold text-slate-800 dark:text-slate-200 text-sm">
            {reasoning.title}
          </h3>
          <p className="text-xs text-slate-600 dark:text-slate-400 capitalize">
            {reasoning.type} Process
          </p>
        </div>
      </div>

      {/* Steps */}
      {reasoning.steps && reasoning.steps.length > 0 && (
        <div className="space-y-2 mb-4">
          {reasoning.steps.map((step, index) => {
            const stepText = typeof step === 'string' ? step : step.text;
            const stepIcon = typeof step === 'string' ? '•' : (step.icon || '•');
            
            return (
              <div key={index} className="flex items-start space-x-2">
                <span className="text-blue-500 dark:text-blue-400 font-medium text-xs mt-0.5">
                  {stepIcon}
                </span>
                <span className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">
                  <span className="font-medium">Step {index + 1}:</span> {stepText}
                </span>
              </div>
            );
          })}
        </div>
      )}

      {/* Conclusion */}
      {reasoning.conclusion && (
        <div className="bg-white/50 dark:bg-slate-800/50 rounded-lg p-3 mb-3">
          <div className="flex items-start space-x-2">
            <span className="text-lg">🎯</span>
            <div>
              <span className="font-medium text-slate-800 dark:text-slate-200 text-sm">
                Conclusion:
              </span>
              <p className="text-sm text-slate-700 dark:text-slate-300 mt-1">
                {reasoning.conclusion}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Confidence */}
      <div className="flex items-center space-x-2">
        <span className="text-sm">{getConfidenceIcon(reasoning.confidence)}</span>
        <span className="text-xs font-medium text-slate-600 dark:text-slate-400">
          Confidence:
        </span>
        <span className={`text-xs font-semibold ${getConfidenceColor(reasoning.confidence)}`}>
          {reasoning.confidence.charAt(0).toUpperCase() + reasoning.confidence.slice(1)}
        </span>
      </div>
    </div>
  );
} 