import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, ArrowRight, Check, User, Phone, FileText, Shield } from 'lucide-react';
import StarField from '@/components/StarField';
import GridOverlay from '@/components/GridOverlay';
import GlassPanel from '@/components/GlassPanel';
import NeonButton from '@/components/NeonButton';
import StatusIndicator from '@/components/StatusIndicator';
import { cn } from '@/lib/utils';

const steps = [
  { id: 1, label: 'IDENTITY', icon: User },
  { id: 2, label: 'CONTACT', icon: Phone },
  { id: 3, label: 'PURPOSE', icon: FileText },
  { id: 4, label: 'ETHICS', icon: Shield },
];

const AccessGate = () => {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    reason: '',
    pledgeAccepted: false,
  });

  const handleInputChange = (field: string, value: string | boolean) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const isStepValid = () => {
    switch (currentStep) {
      case 1:
        return formData.name.length > 2 && formData.email.includes('@');
      case 2:
        return formData.phone.length >= 10;
      case 3:
        return formData.reason.length > 20;
      case 4:
        return formData.pledgeAccepted;
      default:
        return false;
    }
  };

  const handleNext = () => {
    if (currentStep < 4) {
      setCurrentStep(prev => prev + 1);
    } else {
      navigate('/verification');
    }
  };

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(prev => prev - 1);
    } else {
      navigate('/');
    }
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <StarField />
      <GridOverlay />

      <div className="w-full max-w-lg relative z-10">
        {/* Header */}
        <div className="text-center mb-8">
          <StatusIndicator status="processing" label="AGENT PROFILING" className="justify-center mb-4" />
          <h1 className="font-orbitron text-2xl md:text-3xl font-bold mb-2">
            ACCESS <span className="text-primary">GATE</span>
          </h1>
          <p className="font-mono text-sm text-muted-foreground">
            SECURITY CHECKPOINT // VERIFICATION REQUIRED
          </p>
        </div>

        {/* Progress Indicator */}
        <div className="flex items-center justify-between mb-8 px-4">
          {steps.map((step, index) => {
            const Icon = step.icon;
            const isCompleted = currentStep > step.id;
            const isCurrent = currentStep === step.id;
            
            return (
              <div key={step.id} className="flex items-center">
                <div className="flex flex-col items-center">
                  <div 
                    className={cn(
                      'w-10 h-10 rounded-lg flex items-center justify-center transition-all duration-300',
                      isCompleted && 'bg-primary text-primary-foreground',
                      isCurrent && 'bg-primary/20 border border-primary text-primary',
                      !isCompleted && !isCurrent && 'bg-muted/30 border border-border text-muted-foreground'
                    )}
                  >
                    {isCompleted ? <Check className="w-5 h-5" /> : <Icon className="w-5 h-5" />}
                  </div>
                  <span className={cn(
                    'font-mono text-[10px] mt-2 tracking-wider',
                    isCurrent ? 'text-primary' : 'text-muted-foreground'
                  )}>
                    {step.label}
                  </span>
                </div>
                {index < steps.length - 1 && (
                  <div 
                    className={cn(
                      'w-12 h-px mx-2',
                      currentStep > step.id ? 'bg-primary' : 'bg-border'
                    )}
                  />
                )}
              </div>
            );
          })}
        </div>

        {/* Form Panel */}
        <GlassPanel className="p-8" corners>
          {/* Step 1: Identity */}
          {currentStep === 1 && (
            <div className="space-y-6 animate-fade-in">
              <div className="text-center mb-6">
                <h2 className="font-orbitron text-lg font-semibold text-primary mb-2">
                  IDENTITY CONFIRMATION
                </h2>
                <p className="font-mono text-xs text-muted-foreground">
                  AUTHENTICATE VIA EXTERNAL PROVIDER
                </p>
              </div>

              <button 
                className="w-full p-4 rounded-lg border border-border bg-muted/20 hover:bg-muted/40 hover:border-primary/30 transition-all duration-300 flex items-center justify-center gap-3"
                onClick={() => handleInputChange('name', 'Agent User')}
              >
                <svg className="w-5 h-5" viewBox="0 0 24 24">
                  <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                  <path fill="currentColor" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                  <path fill="currentColor" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                  <path fill="currentColor" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                </svg>
                <span className="font-mono text-sm">Continue with Google</span>
              </button>

              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-border"></div>
                </div>
                <div className="relative flex justify-center">
                  <span className="bg-card px-4 font-mono text-xs text-muted-foreground">
                    OR ENTER MANUALLY
                  </span>
                </div>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="font-mono text-xs text-muted-foreground uppercase tracking-wider block mb-2">
                    Agent Designation
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => handleInputChange('name', e.target.value)}
                    placeholder="Enter your name"
                    className="w-full p-3 bg-muted/30 border border-border rounded-lg font-mono text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary/50 transition-all placeholder:text-muted-foreground/50"
                  />
                </div>
                <div>
                  <label className="font-mono text-xs text-muted-foreground uppercase tracking-wider block mb-2">
                    Secure Communication Channel
                  </label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => handleInputChange('email', e.target.value)}
                    placeholder="Enter your email"
                    className="w-full p-3 bg-muted/30 border border-border rounded-lg font-mono text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary/50 transition-all placeholder:text-muted-foreground/50"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Step 2: Contact */}
          {currentStep === 2 && (
            <div className="space-y-6 animate-fade-in">
              <div className="text-center mb-6">
                <h2 className="font-orbitron text-lg font-semibold text-primary mb-2">
                  SECONDARY VERIFICATION
                </h2>
                <p className="font-mono text-xs text-muted-foreground">
                  PROVIDE SECURE CONTACT ENDPOINT
                </p>
              </div>

              <div>
                <label className="font-mono text-xs text-muted-foreground uppercase tracking-wider block mb-2">
                  Mobile Terminal ID
                </label>
                <input
                  type="tel"
                  value={formData.phone}
                  onChange={(e) => handleInputChange('phone', e.target.value)}
                  placeholder="+1 (555) 000-0000"
                  className="w-full p-3 bg-muted/30 border border-border rounded-lg font-mono text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary/50 transition-all placeholder:text-muted-foreground/50"
                />
              </div>

              <div className="p-4 bg-muted/10 border border-border/50 rounded-lg">
                <p className="font-mono text-xs text-muted-foreground">
                  ⚡ A verification code will be transmitted to this endpoint for 
                  secondary authentication. Standard carrier rates may apply.
                </p>
              </div>
            </div>
          )}

          {/* Step 3: Purpose */}
          {currentStep === 3 && (
            <div className="space-y-6 animate-fade-in">
              <div className="text-center mb-6">
                <h2 className="font-orbitron text-lg font-semibold text-primary mb-2">
                  ACCESS JUSTIFICATION
                </h2>
                <p className="font-mono text-xs text-muted-foreground">
                  STATE YOUR OPERATIONAL REQUIREMENT
                </p>
              </div>

              <div>
                <label className="font-mono text-xs text-muted-foreground uppercase tracking-wider block mb-2">
                  Mission Briefing
                </label>
                <textarea
                  value={formData.reason}
                  onChange={(e) => handleInputChange('reason', e.target.value)}
                  placeholder="Describe your intended use of SITA intelligence systems..."
                  rows={5}
                  className="w-full p-3 bg-muted/30 border border-border rounded-lg font-mono text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary/50 transition-all resize-none placeholder:text-muted-foreground/50"
                />
                <div className="flex justify-between mt-2">
                  <span className="font-mono text-xs text-muted-foreground">
                    Minimum 20 characters required
                  </span>
                  <span className={cn(
                    'font-mono text-xs',
                    formData.reason.length >= 20 ? 'text-success' : 'text-muted-foreground'
                  )}>
                    {formData.reason.length}/20
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Step 4: Ethics */}
          {currentStep === 4 && (
            <div className="space-y-6 animate-fade-in">
              <div className="text-center mb-6">
                <h2 className="font-orbitron text-lg font-semibold text-primary mb-2">
                  ETHICS CHECK
                </h2>
                <p className="font-mono text-xs text-muted-foreground">
                  ACKNOWLEDGE RESPONSIBLE USE PROTOCOL
                </p>
              </div>

              <div className="p-4 bg-destructive/5 border border-destructive/20 rounded-lg">
                <h3 className="font-orbitron text-sm font-semibold text-destructive mb-3">
                  ⚠ BINDING AGREEMENT
                </h3>
                <div className="font-mono text-xs text-muted-foreground space-y-2">
                  <p>By accessing SITA, I acknowledge and agree that:</p>
                  <ul className="list-disc list-inside space-y-1 ml-2">
                    <li>All data accessed is classified and confidential</li>
                    <li>My session activity will be monitored and logged</li>
                    <li>Unauthorized disclosure is a violation of law</li>
                    <li>Access may be revoked at any time without notice</li>
                    <li>I will not use the system for malicious purposes</li>
                  </ul>
                </div>
              </div>

              <label className="flex items-start gap-3 cursor-pointer group">
                <div 
                  className={cn(
                    'w-5 h-5 rounded border flex-shrink-0 flex items-center justify-center transition-all mt-0.5',
                    formData.pledgeAccepted 
                      ? 'bg-primary border-primary' 
                      : 'border-border group-hover:border-primary/50'
                  )}
                  onClick={() => handleInputChange('pledgeAccepted', !formData.pledgeAccepted)}
                >
                  {formData.pledgeAccepted && <Check className="w-3 h-3 text-primary-foreground" />}
                </div>
                <span className="font-mono text-sm text-foreground">
                  I have read, understood, and accept the SITA Responsible Use Protocol 
                  and understand my obligations as an authorized agent.
                </span>
              </label>
            </div>
          )}

          {/* Navigation */}
          <div className="flex items-center justify-between mt-8 pt-6 border-t border-border/50">
            <button
              onClick={handleBack}
              className="flex items-center gap-2 font-mono text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Back</span>
            </button>

            <NeonButton
              onClick={handleNext}
              disabled={!isStepValid()}
              size="md"
            >
              {currentStep === 4 ? (
                <>
                  <span>Submit</span>
                  <Shield className="w-4 h-4 ml-2" />
                </>
              ) : (
                <>
                  <span>Continue</span>
                  <ArrowRight className="w-4 h-4 ml-2" />
                </>
              )}
            </NeonButton>
          </div>
        </GlassPanel>

        {/* Footer */}
        <div className="text-center mt-6">
          <p className="font-mono text-xs text-muted-foreground">
            ENCRYPTED CONNECTION // ALL DATA PROTECTED
          </p>
        </div>
      </div>
    </div>
  );
};

export default AccessGate;
