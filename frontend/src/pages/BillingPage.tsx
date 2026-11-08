import React, { useState } from 'react';
import {
  CreditCard,
  Check,
  Zap,
  ShieldCheck,
  Sparkles,
  ArrowRight
} from 'lucide-react';
import { Plan } from '../types';

export const BillingPage: React.FC = () => {
  const [selectedPlanCode, setSelectedPlanCode] = useState('pro');
  const [selectedProvider, setSelectedProvider] = useState<'payme' | 'click' | 'stripe'>('payme');
  const [processing, setProcessing] = useState(false);

  const plans = [
    {
      code: 'starter',
      name: 'Starter Rejasi',
      priceUSD: '$19',
      priceUZS: '250,000 so\'m',
      period: 'oyiga',
      description: 'Instagram biznesini endi boshlayotganlar uchun',
      features: [
        '1 ta Instagram biznes akkaunt',
        '1,000 ta Direct xabarlar limiti',
        '3 ta faol Visual Flow (DAG)',
        'Private Reply (7 kunlik cheklov bilan)',
        'Standart qo\'llab-quvvatlash'
      ]
    },
    {
      code: 'pro',
      name: 'Pro Rejasi (Ommabop)',
      priceUSD: '$49',
      priceUZS: '650,000 so\'m',
      period: 'oyiga',
      popular: true,
      description: "O'rta biznes va faol sotuvchi do'konlar uchun",
      features: [
        '3 ta Instagram biznes akkaunt',
        '10,000 ta Direct xabarlar limiti',
        'Cheksiz Visual Flowlar (DAG)',
        'OpenRouter Llama 3.3 70B AI Agent',
        'RAG Bilimlar bazasi va Lead Capture',
        'Inson operatoriga uzatish (Handoff)'
      ]
    },
    {
      code: 'enterprise',
      name: 'Enterprise Rejasi',
      priceUSD: '$149',
      priceUZS: '1,950,000 so\'m',
      period: 'oyiga',
      description: 'Katta agentliklar va yirik kompaniyalar uchun',
      features: [
        'Cheksiz Instagram akkauntlar',
        '50,000 ta Direct xabarlar limiti',
        'Cheksiz AI tokenlar va RAG hujjatlar',
        'Prioritetli 24/7 texnik yordam',
        'Shaxsiy server va ajratilgan DB'
      ]
    }
  ];

  const handleCheckout = () => {
    setProcessing(true);
    setTimeout(() => {
      setProcessing(false);
      alert(`To'lov tizimi (${selectedProvider.toUpperCase()}) integratsiyasi orqali ${selectedPlanCode.toUpperCase()} obunasi faollashtirildi! ✅`);
    }, 1000);
  };

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      <div className="text-center max-w-xl mx-auto">
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-purple-950/60 text-purple-300 border border-purple-800/40 mb-3">
          <Zap className="w-3.5 h-3.5 text-purple-400" />
          Shaffof Tariflar va Avtomatizatsiya
        </span>
        <h2 className="text-2xl font-bold text-slate-100">Biznesingizga mos tarifni tanlang</h2>
        <p className="text-xs text-slate-400 mt-2">
          Payme, Click yoki Stripe orqali to'lov qiling. Istalgan vaqtda tarifni o'zgartirish yoki bekor qilish mumkin.
        </p>
      </div>

      {/* Plans Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {plans.map((plan) => {
          const isSelected = selectedPlanCode === plan.code;
          return (
            <div
              key={plan.code}
              onClick={() => setSelectedPlanCode(plan.code)}
              className={`bg-slate-900 border rounded-2xl p-6 relative flex flex-col justify-between cursor-pointer transition-all ${
                isSelected
                  ? 'border-purple-500 ring-2 ring-purple-500/30 shadow-xl'
                  : 'border-slate-800 hover:border-slate-700'
              }`}
            >
              {plan.popular && (
                <span className="absolute -top-3 left-1/2 -translate-x-1/2 bg-gradient-to-r from-pink-500 to-purple-600 text-white text-[10px] font-bold px-3 py-0.5 rounded-full uppercase tracking-wider shadow">
                  Eng Ommabop
                </span>
              )}

              <div>
                <h3 className="text-base font-bold text-slate-100">{plan.name}</h3>
                <p className="text-xs text-slate-400 mt-1 mb-4">{plan.description}</p>
                <div className="mb-6">
                  <div className="flex items-baseline gap-1">
                    <span className="text-3xl font-extrabold text-white">{plan.priceUSD}</span>
                    <span className="text-xs text-slate-400">/ {plan.period}</span>
                  </div>
                  <span className="text-xs text-purple-400 font-medium">({plan.priceUZS})</span>
                </div>

                <div className="space-y-2.5 pt-4 border-t border-slate-800 text-xs text-slate-300">
                  {plan.features.map((feat, i) => (
                    <div key={i} className="flex items-start gap-2">
                      <Check className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                      <span>{feat}</span>
                    </div>
                  ))}
                </div>
              </div>

              <button
                className={`w-full mt-6 py-2.5 rounded-xl text-xs font-semibold transition ${
                  isSelected
                    ? 'bg-purple-600 text-white shadow-lg shadow-purple-600/30'
                    : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                }`}
              >
                {isSelected ? 'Tanlangan Reja' : 'Tanlash'}
              </button>
            </div>
          );
        })}
      </div>

      {/* Payment Provider Selection */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 max-w-xl mx-auto space-y-4">
        <h4 className="text-sm font-bold text-slate-200 text-center">To'lov Usulini Tanlang</h4>
        <div className="grid grid-cols-3 gap-3">
          <button
            onClick={() => setSelectedProvider('payme')}
            className={`p-3 rounded-xl border text-center font-bold text-xs transition ${
              selectedProvider === 'payme'
                ? 'bg-teal-950/50 border-teal-500 text-teal-300 shadow'
                : 'bg-slate-800 border-slate-700 text-slate-300 hover:bg-slate-700'
            }`}
          >
            Payme (UZS)
          </button>
          <button
            onClick={() => setSelectedProvider('click')}
            className={`p-3 rounded-xl border text-center font-bold text-xs transition ${
              selectedProvider === 'click'
                ? 'bg-blue-950/50 border-blue-500 text-blue-300 shadow'
                : 'bg-slate-800 border-slate-700 text-slate-300 hover:bg-slate-700'
            }`}
          >
            Click (UZS)
          </button>
          <button
            onClick={() => setSelectedProvider('stripe')}
            className={`p-3 rounded-xl border text-center font-bold text-xs transition ${
              selectedProvider === 'stripe'
                ? 'bg-purple-950/50 border-purple-500 text-purple-300 shadow'
                : 'bg-slate-800 border-slate-700 text-slate-300 hover:bg-slate-700'
            }`}
          >
            Stripe (USD)
          </button>
        </div>

        <button
          onClick={handleCheckout}
          disabled={processing}
          className="w-full py-3 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-semibold rounded-xl text-sm flex items-center justify-center gap-2 shadow-lg shadow-purple-600/30 transition disabled:opacity-50"
        >
          {processing ? 'To\'lov amalga oshirilmoqda...' : 'Obunani Faollashtirish'}
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
