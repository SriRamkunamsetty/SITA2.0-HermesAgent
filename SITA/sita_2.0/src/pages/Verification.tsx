import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Lock, Unlock, Shield, Cpu, Database, Network } from 'lucide-react';
import StarField from '@/components/StarField';
import GridOverlay from '@/components/GridOverlay';
import TypeWriter from '@/components/TypeWriter';
import { cn } from '@/lib/utils';

const verificationSteps = [
  { id: 1, text: 'INITIATING SYSTEM SCAN...', icon: Cpu, duration: 1500 },
  { id: 2, text: 'ANALYZING AGENT CREDENTIALS...', icon: Shield, duration: 1200 },
  { id: 3, text: 'ESTABLISHING NEURAL LINK...', icon: Network, duration: 1800 },
  { id: 4, text: 'SYNCHRONIZING DATABASE ACCESS...', icon: Database, duration: 1000 },
  { id: 5, text: 'CLEARANCE GRANTED', icon: Unlock, duration: 500 },
];

const Verification = () => {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(0);
  const [isComplete, setIsComplete] = useState(false);
  const [showUnlock, setShowUnlock] = useState(false);

  useEffect(() => {
    if (currentStep < verificationSteps.length) {
      const timer = setTimeout(() => {
        setCurrentStep(prev => prev + 1);
      }, verificationSteps[currentStep]?.duration || 1000);
      return () => clearTimeout(timer);
    } else {
      // All steps complete
      setTimeout(() => setShowUnlock(true), 500);
      setTimeout(() => setIsComplete(true), 1500);
      setTimeout(() => navigate('/dashboard'), 3000);
    }
  }, [currentStep, navigate]);

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4 overflow-hidden">
      <StarField />
      <GridOverlay />

      {/* Scanline Effect */}
      <div 
        className="fixed inset-0 pointer-events-none z-10"
        style={{
          background: 'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0, 245, 255, 0.015) 2px, rgba(0, 245, 255, 0.015) 4px)',
        }}
      />

      <div className="relative z-20 text-center">
        {/* Lock Animation */}
        <div className="relative mb-12">
          <div 
            className={cn(
              'w-32 h-32 mx-auto rounded-full flex items-center justify-center transition-all duration-1000',
              isComplete 
                ? 'bg-primary/20 border-2 border-primary shadow-[0_0_60px_hsl(187_100%_48%_/_0.5)]' 
                : 'bg-muted/20 border-2 border-border'
            )}
          >
            {showUnlock ? (
              <Unlock 
                className={cn(
                  'w-16 h-16 transition-all duration-500',
                  isComplete ? 'text-primary animate-pulse' : 'text-primary'
                )}
              />
            ) : (
              <Lock 
                className={cn(
                  'w-16 h-16 text-muted-foreground transition-colors',
                  currentStep > 0 && 'text-primary'
                )}
              />
            )}
          </div>

          {/* Rotating Ring */}
          {!isComplete && (
            <div 
              className="absolute inset-0 w-32 h-32 mx-auto rounded-full border-2 border-transparent animate-spin-slow"
              style={{
                borderTopColor: 'hsl(187 100% 48% / 0.5)',
                borderRightColor: 'hsl(187 100% 48% / 0.3)',
              }}
            />
          )}

          {/* Pulse Rings */}
          {isComplete && (
            <>
              <div className="absolute inset-0 w-32 h-32 mx-auto rounded-full border border-primary/30 animate-ping" />
              <div className="absolute inset-0 w-32 h-32 mx-auto rounded-full border border-primary/20 animate-pulse" />
            </>
          )}
        </div>

        {/* Status Display */}
        <div className="mb-8">
          {isComplete ? (
            <div className="animate-fade-in">
              <h1 className="font-orbitron text-3xl md:text-4xl font-bold text-primary mb-4 text-glow">
                ACCESS GRANTED
              </h1>
              <p className="font-mono text-sm text-muted-foreground">
                WELCOME TO SITA // NEURAL CORE ACTIVE
              </p>
            </div>
          ) : (
            <div className="h-20">
              {currentStep < verificationSteps.length && (
                <div className="animate-fade-in" key={currentStep}>
                  <div className="flex items-center justify-center gap-3 mb-4">
                    {(() => {
                      const Icon = verificationSteps[currentStep].icon;
                      return <Icon className="w-6 h-6 text-primary animate-pulse" />;
                    })()}
                    <TypeWriter 
                      text={verificationSteps[currentStep].text}
                      delay={30}
                      className="font-mono text-sm text-primary"
                    />
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Progress Steps */}
        <div className="flex items-center justify-center gap-2 mb-8">
          {verificationSteps.map((step, index) => (
            <div
              key={step.id}
              className={cn(
                'w-2 h-2 rounded-full transition-all duration-300',
                index < currentStep && 'bg-primary shadow-[0_0_10px_hsl(187_100%_48%_/_0.8)]',
                index === currentStep && 'bg-primary/50 animate-pulse',
                index > currentStep && 'bg-muted'
              )}
            />
          ))}
        </div>

        {/* Data Stream Effect */}
        <div className="font-mono text-xs text-muted-foreground/50 max-w-md mx-auto overflow-hidden h-24">
          {[...Array(8)].map((_, i) => (
            <div 
              key={i}
              className="whitespace-nowrap animate-fade-in"
              style={{ 
                animationDelay: `${i * 200}ms`,
                opacity: Math.max(0.2, 1 - i * 0.1)
              }}
            >
              {currentStep > i % 5 ? 
                `[${Date.now() + i}] :: BLOCK_${Math.random().toString(36).substr(2, 8).toUpperCase()} :: VERIFIED` :
                `[PENDING] :: AWAITING_CLEARANCE_${i}`
              }
            </div>
          ))}
        </div>

        {/* Glitch Effect on Complete */}
        {isComplete && (
          <div className="absolute inset-0 pointer-events-none">
            <div className="absolute inset-0 bg-primary/5 animate-pulse" />
          </div>
        )}
      </div>
    </div>
  );
};

export default Verification;
