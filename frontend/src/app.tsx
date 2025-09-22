import React, { useState, useEffect, useCallback, useRef } from 'react';
import { AlertCircle, Activity, Clock, Users, Phone, MapPin, ChevronRight, Bell, Heart, Thermometer, Wind } from 'lucide-react';

/**
 * Sistema OndeAtende - Interface de Triagem Médica
 * Implementa protocolo Manchester com acessibilidade WCAG AAA
 * Suporta operação 24/7 em ambientes hospitalares
 */

// Hook customizado para WebSocket com reconexão automática
const useWebSocket = (facilityId) => {
  const [connected, setConnected] = useState(false);
  const [queueData, setQueueData] = useState(null);
  const ws = useRef(null);
  const reconnectTimeout = useRef(null);
  
  const connect = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) return;
    
    const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/triage/${facilityId}/`;
    ws.current = new WebSocket(wsUrl);
    
    ws.current.onopen = () => {
      setConnected(true);
      console.log('WebSocket conectado');
      // Solicita estado inicial
      ws.current.send(JSON.stringify({ command: 'get_queue' }));
    };
    
    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'queue_state' || data.type === 'triage_updated') {
        setQueueData(data.data);
      }
    };
    
    ws.current.onclose = () => {
      setConnected(false);
      // Reconecta automaticamente após 3 segundos
      reconnectTimeout.current = setTimeout(connect, 3000);
    };
  }, [facilityId]);
  
  useEffect(() => {
    connect();
    return () => {
      clearTimeout(reconnectTimeout.current);
      ws.current?.close();
    };
  }, [connect]);
  
  return { connected, queueData, ws: ws.current };
};

// Componente de Card de Prioridade Manchester
const PriorityCard = ({ color, count, label, waitTime, isEmergency }) => {
  const colorClasses = {
    RED: 'bg-red-500 border-red-600',
    ORANGE: 'bg-orange-500 border-orange-600',
    YELLOW: 'bg-yellow-500 border-yellow-600',
    GREEN: 'bg-green-500 border-green-600',
    BLUE: 'bg-blue-500 border-blue-600',
  };
  
  const textColorClasses = {
    RED: 'text-red-900',
    ORANGE: 'text-orange-900',
    YELLOW: 'text-yellow-900',
    GREEN: 'text-green-900',
    BLUE: 'text-blue-900',
  };
  
  return (
    <div
      className={`${colorClasses[color]} border-4 rounded-xl p-6 text-white shadow-2xl transform transition-all hover:scale-105 ${
        isEmergency ? 'animate-pulse' : ''
      }`}
      role="region"
      aria-label={`Prioridade ${label}: ${count} pacientes`}
      aria-live={isEmergency ? 'assertive' : 'polite'}
    >
      <div className="flex justify-between items-start mb-4">
        <h3 className="text-2xl font-bold">{label}</h3>
        {isEmergency && (
          <AlertCircle className="w-8 h-8 animate-bounce" aria-label="Emergência" />
        )}
      </div>
      
      <div className="text-5xl font-black mb-4 text-center" aria-label={`${count} pacientes`}>
        {count}
      </div>
      
      <div className="flex items-center justify-center text-sm opacity-90">
        <Clock className="w-4 h-4 mr-1" aria-hidden="true" />
        <span>Espera: {waitTime} min</span>
      </div>
    </div>
  );
};

// Componente de Formulário de Triagem
const TriageForm = ({ onSubmit }) => {
  const [formData, setFormData] = useState({
    patientName: '',
    complaint: '',
    painScale: 0,
    vitalSigns: {
      bloodPressure: '',
      heartRate: '',
      temperature: '',
      spo2: '',
      respiratoryRate: '',
    },
    discriminators: {},
  });
  
  const [currentFlowchart, setCurrentFlowchart] = useState(null);
  
  // Fluxogramas Manchester disponíveis
  const flowcharts = {
    chest_pain: {
      name: 'Dor Torácica',
      discriminators: [
        { id: 'cardiac_pain', text: 'Dor em aperto/opressão no peito?', priority: 'ORANGE' },
        { id: 'irradiation', text: 'Dor irradia para braço/mandíbula?', priority: 'ORANGE' },
        { id: 'sweating', text: 'Sudorese fria associada?', priority: 'ORANGE' },
        { id: 'pleuritic', text: 'Dor piora com respiração?', priority: 'YELLOW' },
      ]
    },
    shortness_breath: {
      name: 'Falta de Ar',
      discriminators: [
        { id: 'stridor', text: 'Ruído agudo ao respirar (estridor)?', priority: 'RED' },
        { id: 'cyanosis', text: 'Lábios ou extremidades azulados?', priority: 'RED' },
        { id: 'wheeze', text: 'Chiado no peito?', priority: 'YELLOW' },
        { id: 'cough', text: 'Tosse associada?', priority: 'GREEN' },
      ]
    },
    fever_child: {
      name: 'Criança Febril',
      discriminators: [
        { id: 'meningism', text: 'Rigidez de nuca ou manchas na pele?', priority: 'RED' },
        { id: 'lethargy', text: 'Criança muito sonolenta/difícil acordar?', priority: 'ORANGE' },
        { id: 'high_fever', text: 'Temperatura maior que 39°C?', priority: 'YELLOW' },
        { id: 'dehydration', text: 'Sinais de desidratação?', priority: 'YELLOW' },
      ]
    },
    trauma: {
      name: 'Trauma',
      discriminators: [
        { id: 'major_bleeding', text: 'Sangramento importante?', priority: 'RED' },
        { id: 'unconscious', text: 'Perda de consciência?', priority: 'RED' },
        { id: 'deformity', text: 'Deformidade óbvia?', priority: 'ORANGE' },
        { id: 'severe_pain', text: 'Dor intensa (8-10)?', priority: 'ORANGE' },
      ]
    },
  };
  
  const handleComplaintSelect = (complaint) => {
    setCurrentFlowchart(flowcharts[complaint]);
    setFormData(prev => ({ ...prev, complaint }));
  };
  
  const handleDiscriminatorChange = (id, value) => {
    setFormData(prev => ({
      ...prev,
      discriminators: { ...prev.discriminators, [id]: value }
    }));
  };
  
  const calculatePriority = () => {
    if (!currentFlowchart) return 'BLUE';
    
    const priorities = ['RED', 'ORANGE', 'YELLOW', 'GREEN', 'BLUE'];
    let highestPriority = 'BLUE';
    
    for (const discriminator of currentFlowchart.discriminators) {
      if (formData.discriminators[discriminator.id]) {
        const index = priorities.indexOf(discriminator.priority);
        const currentIndex = priorities.indexOf(highestPriority);
        if (index < currentIndex) {
          highestPriority = discriminator.priority;
        }
      }
    }
    
    return highestPriority;
  };
  
  return (
    <form 
      onSubmit={(e) => {
        e.preventDefault();
        const priority = calculatePriority();
        onSubmit({ ...formData, priority });
      }}
      className="space-y-6 bg-white p-8 rounded-xl shadow-lg"
      aria-label="Formulário de Triagem Manchester"
    >
      <h2 className="text-3xl font-bold text-gray-800 mb-6">Nova Triagem</h2>
      
      {/* Identificação do Paciente */}
      <div className="space-y-4">
        <label htmlFor="patientName" className="block text-lg font-semibold text-gray-700">
          Nome do Paciente *
        </label>
        <input
          id="patientName"
          type="text"
          required
          className="w-full p-4 text-lg border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:ring-4 focus:ring-blue-200"
          value={formData.patientName}
          onChange={(e) => setFormData(prev => ({ ...prev, patientName: e.target.value }))}
          aria-required="true"
        />
      </div>
      
      {/* Seleção de Queixa Principal */}
      <fieldset className="space-y-4">
        <legend className="text-lg font-semibold text-gray-700">Queixa Principal *</legend>
        <div className="grid grid-cols-2 gap-4">
          {Object.entries(flowcharts).map(([key, value]) => (
            <button
              key={key}
              type="button"
              onClick={() => handleComplaintSelect(key)}
              className={`p-4 rounded-lg border-2 text-left transition-all ${
                formData.complaint === key 
                  ? 'border-blue-500 bg-blue-50' 
                  : 'border-gray-300 hover:border-gray-400'
              }`}
              aria-pressed={formData.complaint === key}
            >
              <span className="text-lg font-medium">{value.name}</span>
            </button>
          ))}
        </div>
      </fieldset>
      
      {/* Discriminadores Manchester */}
      {currentFlowchart && (
        <fieldset className="space-y-4">
          <legend className="text-lg font-semibold text-gray-700">
            Discriminadores - {currentFlowchart.name}
          </legend>
          <div className="space-y-3">
            {currentFlowchart.discriminators.map((discriminator) => (
              <div key={discriminator.id} className="flex items-center space-x-4 p-3 bg-gray-50 rounded-lg">
                <input
                  type="checkbox"
                  id={discriminator.id}
                  className="w-6 h-6"
                  checked={formData.discriminators[discriminator.id] || false}
                  onChange={(e) => handleDiscriminatorChange(discriminator.id, e.target.checked)}
                />
                <label htmlFor={discriminator.id} className="flex-1 text-lg cursor-pointer">
                  {discriminator.text}
                </label>
                <span className={`px-3 py-1 rounded-full text-sm font-bold text-white ${
                  discriminator.priority === 'RED' ? 'bg-red-500' :
                  discriminator.priority === 'ORANGE' ? 'bg-orange-500' :
                  discriminator.priority === 'YELLOW' ? 'bg-yellow-500' :
                  'bg-green-500'
                }`}>
                  {discriminator.priority}
                </span>
              </div>
            ))}
          </div>
        </fieldset>
      )}
      
      {/* Sinais Vitais */}
      <fieldset className="space-y-4">
        <legend className="text-lg font-semibold text-gray-700">Sinais Vitais</legend>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label htmlFor="bloodPressure" className="block text-sm font-medium text-gray-600 mb-1">
              <Heart className="inline w-4 h-4 mr-1" />
              Pressão Arterial
            </label>
            <input
              id="bloodPressure"
              type="text"
              placeholder="120/80"
              className="w-full p-3 border-2 rounded-lg"
              value={formData.vitalSigns.bloodPressure}
              onChange={(e) => setFormData(prev => ({
                ...prev,
                vitalSigns: { ...prev.vitalSigns, bloodPressure: e.target.value }
              }))}
            />
          </div>
          
          <div>
            <label htmlFor="heartRate" className="block text-sm font-medium text-gray-600 mb-1">
              <Activity className="inline w-4 h-4 mr-1" />
              Frequência Cardíaca
            </label>
            <input
              id="heartRate"
              type="number"
              placeholder="80"
              className="w-full p-3 border-2 rounded-lg"
              value={formData.vitalSigns.heartRate}
              onChange={(e) => setFormData(prev => ({
                ...prev,
                vitalSigns: { ...prev.vitalSigns, heartRate: e.target.value }
              }))}
            />
          </div>
          
          <div>
            <label htmlFor="temperature" className="block text-sm font-medium text-gray-600 mb-1">
              <Thermometer className="inline w-4 h-4 mr-1" />
              Temperatura (°C)
            </label>
            <input
              id="temperature"
              type="number"
              step="0.1"
              placeholder="36.5"
              className="w-full p-3 border-2 rounded-lg"
              value={formData.vitalSigns.temperature}
              onChange={(e) => setFormData(prev => ({
                ...prev,
                vitalSigns: { ...prev.vitalSigns, temperature: e.target.value }
              }))}
            />
          </div>
          
          <div>
            <label htmlFor="spo2" className="block text-sm font-medium text-gray-600 mb-1">
              <Wind className="inline w-4 h-4 mr-1" />
              SpO2 (%)
            </label>
            <input
              id="spo2"
              type="number"
              placeholder="98"
              className="w-full p-3 border-2 rounded-lg"
              value={formData.vitalSigns.spo2}
              onChange={(e) => setFormData(prev => ({
                ...prev,
                vitalSigns: { ...prev.vitalSigns, spo2: e.target.value }
              }))}
            />
          </div>
        </div>
      </fieldset>
      
      {/* Escala de Dor */}
      <fieldset className="space-y-4">
        <legend className="text-lg font-semibold text-gray-700">Escala de Dor (0-10)</legend>
        <div className="flex items-center space-x-2">
          {[0,1,2,3,4,5,6,7,8,9,10].map(num => (
            <button
              key={num}
              type="button"
              onClick={() => setFormData(prev => ({ ...prev, painScale: num }))}
              className={`w-12 h-12 rounded-lg font-bold transition-all ${
                formData.painScale === num 
                  ? num <= 3 ? 'bg-green-500 text-white' :
                    num <= 7 ? 'bg-yellow-500 text-white' :
                    'bg-red-500 text-white'
                  : 'bg-gray-200 hover:bg-gray-300'
              }`}
              aria-label={`Dor nível ${num}`}
              aria-pressed={formData.painScale === num}
            >
              {num}
            </button>
          ))}
        </div>
      </fieldset>
      
      {/* Botão de Submit com Prioridade Calculada */}
      <button
        type="submit"
        disabled={!formData.patientName || !formData.complaint}
        className={`w-full py-4 px-6 text-xl font-bold rounded-lg transition-all transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed ${
          !formData.complaint ? 'bg-gray-400' :
          calculatePriority() === 'RED' ? 'bg-red-500 text-white animate-pulse' :
          calculatePriority() === 'ORANGE' ? 'bg-orange-500 text-white' :
          calculatePriority() === 'YELLOW' ? 'bg-yellow-500 text-black' :
          calculatePriority() === 'GREEN' ? 'bg-green-500 text-white' :
          'bg-blue-500 text-white'
        }`}
      >
        Realizar Triagem - Prioridade {calculatePriority()}
      </button>
    </form>
  );
};

// Componente Principal - Dashboard de Triagem
export default function OndeAtendeApp() {
  const [selectedFacility] = useState('facility-001');
  const { connected, queueData } = useWebSocket(selectedFacility);
  const [showTriageForm, setShowTriageForm] = useState(false);
  
  // Notificação sonora para emergências
  useEffect(() => {
    if (queueData?.queues?.RED?.length > 0) {
      // Toca som de alerta para emergências
      const audio = new Audio('/emergency-alert.mp3');
      audio.play().catch(e => console.log('Erro ao tocar alerta:', e));
    }
  }, [queueData?.queues?.RED?.length]);
  
  const handleTriageSubmit = (data) => {
    console.log('Nova triagem:', data);
    // Enviaria para o WebSocket/API
    setShowTriageForm(false);
  };
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-teal-50">
      {/* Header com Status de Conexão */}
      <header className="bg-white shadow-lg border-b-4 border-teal-600">
        <div className="container mx-auto px-6 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-4">
              <Activity className="w-10 h-10 text-teal-600" />
              <h1 className="text-3xl font-bold text-gray-800">
                OndeAtende - Sistema de Triagem
              </h1>
            </div>
            
            <div className="flex items-center space-x-6">
              {/* Indicador de Conexão */}
              <div className="flex items-center space-x-2">
                <div className={`w-3 h-3 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'} animate-pulse`} />
                <span className="text-sm font-medium">
                  {connected ? 'Conectado' : 'Reconectando...'}
                </span>
              </div>
              
              {/* Botão de Nova Triagem */}
              <button
                onClick={() => setShowTriageForm(true)}
                className="px-6 py-3 bg-teal-600 text-white rounded-lg font-semibold hover:bg-teal-700 transition-all flex items-center space-x-2"
                aria-label="Iniciar nova triagem"
              >
                <span>Nova Triagem</span>
                <ChevronRight className="w-5 h-5" />
              </button>
              
              {/* Botão de Emergência */}
              <button
                className="px-6 py-3 bg-red-600 text-white rounded-lg font-semibold hover:bg-red-700 transition-all flex items-center space-x-2 animate-pulse"
                aria-label="Acionar código de emergência"
              >
                <AlertCircle className="w-5 h-5" />
                <span>Código Vermelho</span>
              </button>
            </div>
          </div>
        </div>
      </header>
      
      {/* Main Content */}
      <main className="container mx-auto px-6 py-8">
        {showTriageForm ? (
          <div className="max-w-4xl mx-auto">
            <button
              onClick={() => setShowTriageForm(false)}
              className="mb-4 text-gray-600 hover:text-gray-800 flex items-center"
            >
              ← Voltar ao Dashboard
            </button>
            <TriageForm onSubmit={handleTriageSubmit} />
          </div>
        ) : (
          <>
            {/* Cards de Prioridade Manchester */}
            <section aria-label="Filas por prioridade">
              <h2 className="text-2xl font-bold text-gray-800 mb-6">
                Filas de Atendimento - Protocolo Manchester
              </h2>
              
              <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-6 mb-8">
                <PriorityCard
                  color="RED"
                  count={queueData?.queues?.RED?.length || 0}
                  label="EMERGÊNCIA"
                  waitTime="0"
                  isEmergency={true}
                />
                <PriorityCard
                  color="ORANGE"
                  count={queueData?.queues?.ORANGE?.length || 0}
                  label="MUITO URGENTE"
                  waitTime="10"
                  isEmergency={true}
                />
                <PriorityCard
                  color="YELLOW"
                  count={queueData?.queues?.YELLOW?.length || 0}
                  label="URGENTE"
                  waitTime="60"
                  isEmergency={false}
                />
                <PriorityCard
                  color="GREEN"
                  count={queueData?.queues?.GREEN?.length || 0}
                  label="POUCO URGENTE"
                  waitTime="120"
                  isEmergency={false}
                />
                <PriorityCard
                  color="BLUE"
                  count={queueData?.queues?.BLUE?.length || 0}
                  label="NÃO URGENTE"
                  waitTime="240"
                  isEmergency={false}
                />
              </div>
            </section>
            
            {/* Estatísticas Resumidas */}
            <section className="bg-white rounded-xl shadow-lg p-6" aria-label="Estatísticas">
              <h2 className="text-xl font-bold text-gray-800 mb-4">Estatísticas do Dia</h2>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                <div className="text-center">
                  <div className="text-3xl font-bold text-gray-800">
                    {queueData?.summary?.total_waiting || 0}
                  </div>
                  <div className="text-sm text-gray-600">Total Aguardando</div>
                </div>
                
                <div className="text-center">
                  <div className="text-3xl font-bold text-red-600">
                    {queueData?.summary?.critical || 0}
                  </div>
                  <div className="text-sm text-gray-600">Casos Críticos</div>
                </div>
                
                <div className="text-center">
                  <div className="text-3xl font-bold text-blue-600">
                    {queueData?.summary?.average_wait || 0} min
                  </div>
                  <div className="text-sm text-gray-600">Tempo Médio</div>
                </div>
                
                <div className="text-center">
                  <div className="text-3xl font-bold text-green-600">
                    {queueData?.facility?.occupancy || 0}%
                  </div>
                  <div className="text-sm text-gray-600">Ocupação</div>
                </div>
              </div>
            </section>
          </>
        )}
      </main>
    </div>
  );
}