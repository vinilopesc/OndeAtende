import React, { useState, useEffect } from 'react';
import { 
  Search, MapPin, Clock, Phone, Calendar, Users, 
  AlertCircle, ChevronRight, Activity, Heart, 
  Thermometer, Wind, Star, Navigation
} from 'lucide-react';

// Componente de Busca de Especialidades
const SpecialtySearch = ({ onStartTriage }) => {
  const [specialties, setSpecialties] = useState([]);
  const [facilities, setFacilities] = useState([]);
  const [selectedSpecialty, setSelectedSpecialty] = useState('');
  const [userLocation, setUserLocation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [searchResults, setSearchResults] = useState([]);

  // Especialidades disponíveis
  const availableSpecialties = [
    { code: 'CLINICA_GERAL', name: 'Clínica Geral', icon: '🏥' },
    { code: 'CARDIOLOGIA', name: 'Cardiologia', icon: '❤️' },
    { code: 'ORTOPEDIA', name: 'Ortopedia', icon: '🦴' },
    { code: 'PEDIATRIA', name: 'Pediatria', icon: '👶' },
    { code: 'GINECOLOGIA', name: 'Ginecologia', icon: '👩' },
    { code: 'NEUROLOGIA', name: 'Neurologia', icon: '🧠' },
    { code: 'EMERGENCIA', name: 'Emergência', icon: '🚨' },
    { code: 'DERMATOLOGIA', name: 'Dermatologia', icon: '🔬' },
    { code: 'OFTALMOLOGIA', name: 'Oftalmologia', icon: '👁️' },
    { code: 'PSIQUIATRIA', name: 'Psiquiatria', icon: '🧘' },
  ];

  useEffect(() => {
    // Obter localização do usuário
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setUserLocation({
            lat: position.coords.latitude,
            lng: position.coords.longitude
          });
        },
        (error) => {
          console.log('Erro ao obter localização:', error);
          // Usar localização padrão de Montes Claros
          setUserLocation({
            lat: -16.7215,
            lng: -43.8766
          });
        }
      );
    }
  }, []);

  const handleSearch = async () => {
    if (!selectedSpecialty) return;
    
    setLoading(true);
    
    // Simular busca de unidades com a especialidade
    setTimeout(() => {
      const mockResults = [
        {
          id: 1,
          name: 'Hospital Santa Casa',
          type: 'HOSPITAL',
          address: 'Praça Honorato Alves, 22 - Centro',
          distance: 2.3,
          waitTime: 45,
          occupancy: 65,
          hasSpecialty: true,
          shifts: [
            { doctor: 'Dr. Carlos Silva', start: '07:00', end: '19:00' },
            { doctor: 'Dra. Maria Santos', start: '19:00', end: '07:00' }
          ],
          phone: '(38) 3229-2000',
          isOpen: true,
          rating: 4.5
        },
        {
          id: 2,
          name: 'UPA Major Prates',
          type: 'UPA',
          address: 'Av. Dep. Esteves Rodrigues, 852',
          distance: 5.1,
          waitTime: 30,
          occupancy: 45,
          hasSpecialty: true,
          shifts: [
            { doctor: 'Dr. João Oliveira', start: '07:00', end: '19:00' }
          ],
          phone: '(38) 3213-7000',
          isOpen: true,
          rating: 4.2
        },
        {
          id: 3,
          name: 'Hospital Universitário',
          type: 'HOSPITAL',
          address: 'Av. Cula Mangabeira, 562',
          distance: 3.8,
          waitTime: 60,
          occupancy: 78,
          hasSpecialty: true,
          shifts: [
            { doctor: 'Dra. Ana Costa', start: '08:00', end: '17:00' }
          ],
          phone: '(38) 3224-8000',
          isOpen: true,
          rating: 4.3
        }
      ];
      
      setSearchResults(mockResults);
      setLoading(false);
    }, 1500);
  };

  const openMaps = (facility) => {
    if (!userLocation) return;
    const url = `https://www.google.com/maps/dir/${userLocation.lat},${userLocation.lng}/${facility.address}`;
    window.open(url, '_blank');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header */}
      <header className="bg-white shadow-lg border-b-2 border-blue-500">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Activity className="w-10 h-10 text-blue-600" />
              <div>
                <h1 className="text-3xl font-bold text-gray-800">OndeAtende</h1>
                <p className="text-sm text-gray-600">Encontre o atendimento médico ideal</p>
              </div>
            </div>
            
            <button
              onClick={onStartTriage}
              className="px-6 py-3 bg-red-600 text-white rounded-xl font-semibold hover:bg-red-700 transition-all flex items-center space-x-2 shadow-lg hover:shadow-xl transform hover:scale-105"
            >
              <AlertCircle className="w-5 h-5" />
              <span>Triagem de Emergência</span>
            </button>
          </div>
        </div>
      </header>

      {/* Search Section */}
      <section className="container mx-auto px-4 py-8">
        <div className="bg-white rounded-2xl shadow-xl p-8 mb-8">
          <h2 className="text-2xl font-bold text-gray-800 mb-6">
            Buscar por Especialidade Médica
          </h2>
          
          {/* Specialty Grid */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4 mb-6">
            {availableSpecialties.map((specialty) => (
              <button
                key={specialty.code}
                onClick={() => setSelectedSpecialty(specialty.code)}
                className={`p-4 rounded-xl border-2 transition-all transform hover:scale-105 ${
                  selectedSpecialty === specialty.code
                    ? 'border-blue-500 bg-blue-50 shadow-lg'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="text-3xl mb-2">{specialty.icon}</div>
                <div className="text-sm font-medium">{specialty.name}</div>
              </button>
            ))}
          </div>

          {/* Location Info */}
          {userLocation && (
            <div className="flex items-center space-x-2 text-sm text-gray-600 mb-4">
              <MapPin className="w-4 h-4" />
              <span>Buscando próximo a sua localização</span>
            </div>
          )}

          {/* Search Button */}
          <button
            onClick={handleSearch}
            disabled={!selectedSpecialty || loading}
            className={`w-full py-4 rounded-xl font-semibold text-lg transition-all flex items-center justify-center space-x-2 ${
              selectedSpecialty && !loading
                ? 'bg-blue-600 text-white hover:bg-blue-700 shadow-lg hover:shadow-xl'
                : 'bg-gray-300 text-gray-500 cursor-not-allowed'
            }`}
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent" />
                <span>Buscando...</span>
              </>
            ) : (
              <>
                <Search className="w-5 h-5" />
                <span>Buscar Unidades</span>
              </>
            )}
          </button>
        </div>

        {/* Search Results */}
        {searchResults.length > 0 && (
          <div className="space-y-4">
            <h3 className="text-xl font-bold text-gray-800 mb-4">
              {searchResults.length} unidades encontradas com {
                availableSpecialties.find(s => s.code === selectedSpecialty)?.name
              }
            </h3>
            
            {searchResults.map((facility) => (
              <div
                key={facility.id}
                className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-all"
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <h4 className="text-lg font-bold text-gray-800">{facility.name}</h4>
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        facility.type === 'HOSPITAL' 
                          ? 'bg-red-100 text-red-600'
                          : facility.type === 'UPA'
                          ? 'bg-blue-100 text-blue-600'
                          : 'bg-green-100 text-green-600'
                      }`}>
                        {facility.type}
                      </span>
                      {facility.isOpen && (
                        <span className="px-2 py-1 text-xs bg-green-100 text-green-600 rounded-full">
                          Aberto
                        </span>
                      )}
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm text-gray-600 mb-4">
                      <div className="flex items-center space-x-2">
                        <MapPin className="w-4 h-4" />
                        <span>{facility.address}</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Navigation className="w-4 h-4" />
                        <span>{facility.distance} km</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Clock className="w-4 h-4" />
                        <span>Espera: ~{facility.waitTime} min</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Users className="w-4 h-4" />
                        <span>Ocupação: {facility.occupancy}%</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Phone className="w-4 h-4" />
                        <span>{facility.phone}</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Star className="w-4 h-4 text-yellow-500" />
                        <span>{facility.rating}/5.0</span>
                      </div>
                    </div>
                    
                    {/* Plantões */}
                    <div className="border-t pt-3">
                      <p className="text-sm font-semibold text-gray-700 mb-2">
                        Médicos de Plantão:
                      </p>
                      <div className="space-y-1">
                        {facility.shifts.map((shift, idx) => (
                          <div key={idx} className="text-sm text-gray-600">
                            • {shift.doctor} ({shift.start} - {shift.end})
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex flex-col space-y-2 ml-4">
                    <button
                      onClick={() => openMaps(facility)}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all flex items-center space-x-2"
                    >
                      <Navigation className="w-4 h-4" />
                      <span>Rota</span>
                    </button>
                    <button
                      className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-all flex items-center space-x-2"
                    >
                      <Phone className="w-4 h-4" />
                      <span>Ligar</span>
                    </button>
                  </div>
                </div>
                
                {/* Recomendação baseada na ocupação */}
                {facility.occupancy > 80 && (
                  <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <p className="text-sm text-yellow-800">
                      ⚠️ Alta ocupação - considere outras unidades se não for urgente
                    </p>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Info Cards */}
      {searchResults.length === 0 && (
        <section className="container mx-auto px-4 pb-8">
          <div className="grid md:grid-cols-3 gap-6">
            <div className="bg-white rounded-xl shadow-lg p-6">
              <div className="flex items-center space-x-3 mb-4">
                <div className="p-3 bg-blue-100 rounded-full">
                  <Search className="w-6 h-6 text-blue-600" />
                </div>
                <h3 className="text-lg font-semibold">Busca Inteligente</h3>
              </div>
              <p className="text-gray-600">
                Encontre unidades de saúde com a especialidade que você precisa, 
                considerando distância e tempo de espera.
              </p>
            </div>
            
            <div className="bg-white rounded-xl shadow-lg p-6">
              <div className="flex items-center space-x-3 mb-4">
                <div className="p-3 bg-green-100 rounded-full">
                  <Clock className="w-6 h-6 text-green-600" />
                </div>
                <h3 className="text-lg font-semibold">Plantões em Tempo Real</h3>
              </div>
              <p className="text-gray-600">
                Veja quais médicos estão de plantão agora e evite deslocamentos desnecessários.
              </p>
            </div>
            
            <div className="bg-white rounded-xl shadow-lg p-6">
              <div className="flex items-center space-x-3 mb-4">
                <div className="p-3 bg-red-100 rounded-full">
                  <AlertCircle className="w-6 h-6 text-red-600" />
                </div>
                <h3 className="text-lg font-semibold">Triagem Manchester</h3>
              </div>
              <p className="text-gray-600">
                Em caso de emergência, use nossa triagem online para receber orientações 
                e direcionamento prioritário.
              </p>
            </div>
          </div>
        </section>
      )}
    </div>
  );
};

// Componente de Triagem (já existente, mas melhorado)
const TriageForm = ({ onComplete, onBack }) => {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    age: '',
    complaint: '',
    discriminators: {},
    vitalSigns: {},
    painScale: 0,
  });
  const [triageResult, setTriageResult] = useState(null);
  
  const flowcharts = {
    chest_pain: {
      name: 'Dor Torácica',
      icon: '❤️',
      discriminators: [
        { id: 'cardiac_pain', text: 'Dor em aperto/opressão no peito?', priority: 'ORANGE' },
        { id: 'irradiation', text: 'Dor irradia para braço/mandíbula?', priority: 'ORANGE' },
        { id: 'sweating', text: 'Sudorese fria associada?', priority: 'ORANGE' },
        { id: 'pleuritic', text: 'Dor piora com respiração?', priority: 'YELLOW' },
      ]
    },
    shortness_breath: {
      name: 'Falta de Ar',
      icon: '🫁',
      discriminators: [
        { id: 'stridor', text: 'Ruído agudo ao respirar?', priority: 'RED' },
        { id: 'cyanosis', text: 'Lábios ou extremidades azulados?', priority: 'RED' },
        { id: 'wheeze', text: 'Chiado no peito?', priority: 'YELLOW' },
        { id: 'cough', text: 'Tosse associada?', priority: 'GREEN' },
      ]
    },
    fever_child: {
      name: 'Criança com Febre',
      icon: '🌡️',
      discriminators: [
        { id: 'meningism', text: 'Rigidez de nuca ou manchas na pele?', priority: 'RED' },
        { id: 'lethargy', text: 'Criança muito sonolenta?', priority: 'ORANGE' },
        { id: 'high_fever', text: 'Temperatura maior que 39°C?', priority: 'YELLOW' },
        { id: 'dehydration', text: 'Sinais de desidratação?', priority: 'YELLOW' },
      ]
    },
    abdominal_pain: {
      name: 'Dor Abdominal',
      icon: '🤕',
      discriminators: [
        { id: 'peritonitis', text: 'Abdome rígido/defesa muscular?', priority: 'ORANGE' },
        { id: 'vomiting_blood', text: 'Vômito com sangue?', priority: 'ORANGE' },
        { id: 'persistent_vomiting', text: 'Vômitos persistentes?', priority: 'YELLOW' },
        { id: 'mild_pain', text: 'Dor leve a moderada?', priority: 'GREEN' },
      ]
    },
    trauma: {
      name: 'Trauma/Acidente',
      icon: '🚑',
      discriminators: [
        { id: 'major_bleeding', text: 'Sangramento importante?', priority: 'RED' },
        { id: 'unconscious', text: 'Perda de consciência?', priority: 'RED' },
        { id: 'deformity', text: 'Deformidade óbvia?', priority: 'ORANGE' },
        { id: 'severe_pain', text: 'Dor intensa?', priority: 'ORANGE' },
      ]
    },
  };

  const calculatePriority = () => {
    const priorities = ['RED', 'ORANGE', 'YELLOW', 'GREEN', 'BLUE'];
    let highestPriority = 'BLUE';
    
    const flowchart = flowcharts[formData.complaint];
    if (!flowchart) return 'BLUE';
    
    for (const discriminator of flowchart.discriminators) {
      if (formData.discriminators[discriminator.id]) {
        const index = priorities.indexOf(discriminator.priority);
        const currentIndex = priorities.indexOf(highestPriority);
        if (index < currentIndex) {
          highestPriority = discriminator.priority;
        }
      }
    }
    
    // Ajuste por idade
    if (formData.age && (parseInt(formData.age) < 2 || parseInt(formData.age) > 65)) {
      const index = Math.max(0, priorities.indexOf(highestPriority) - 1);
      highestPriority = priorities[index];
    }
    
    return highestPriority;
  };

  const handleSubmit = () => {
    const priority = calculatePriority();
    const priorityInfo = {
      RED: { label: 'EMERGÊNCIA', wait: '0', message: 'Procure atendimento IMEDIATAMENTE!' },
      ORANGE: { label: 'MUITO URGENTE', wait: '10', message: 'Procure atendimento em até 10 minutos' },
      YELLOW: { label: 'URGENTE', wait: '60', message: 'Procure atendimento em até 1 hora' },
      GREEN: { label: 'POUCO URGENTE', wait: '120', message: 'Procure atendimento em até 2 horas' },
      BLUE: { label: 'NÃO URGENTE', wait: '240', message: 'Pode aguardar ou procurar UBS' },
    };
    
    setTriageResult({
      priority,
      ...priorityInfo[priority],
      timestamp: new Date().toISOString()
    });
    
    onComplete({
      ...formData,
      priority,
      result: priorityInfo[priority]
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-red-50 via-white to-orange-50">
      {/* Header */}
      <header className="bg-white shadow-lg border-b-2 border-red-500">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <button
              onClick={onBack}
              className="text-gray-600 hover:text-gray-800 flex items-center space-x-2"
            >
              <ChevronRight className="w-5 h-5 rotate-180" />
              <span>Voltar</span>
            </button>
            <div className="text-center">
              <h1 className="text-2xl font-bold text-gray-800">Triagem Manchester</h1>
              <p className="text-sm text-gray-600">Avaliação de urgência médica</p>
            </div>
            <div className="text-sm text-gray-500">
              Passo {step} de 3
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8 max-w-4xl">
        {!triageResult ? (
          <div className="bg-white rounded-2xl shadow-xl p-8">
            {/* Step 1: Idade e Queixa */}
            {step === 1 && (
              <div className="space-y-6">
                <h2 className="text-xl font-bold text-gray-800 mb-4">
                  Informações Básicas
                </h2>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Idade do paciente
                  </label>
                  <input
                    type="number"
                    className="w-full p-3 border-2 border-gray-300 rounded-lg focus:border-blue-500"
                    value={formData.age}
                    onChange={(e) => setFormData({...formData, age: e.target.value})}
                    placeholder="Digite a idade"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Qual o problema principal?
                  </label>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    {Object.entries(flowcharts).map(([key, value]) => (
                      <button
                        key={key}
                        onClick={() => setFormData({...formData, complaint: key})}
                        className={`p-4 rounded-lg border-2 transition-all ${
                          formData.complaint === key
                            ? 'border-red-500 bg-red-50'
                            : 'border-gray-300 hover:border-gray-400'
                        }`}
                      >
                        <div className="text-3xl mb-2">{value.icon}</div>
                        <div className="text-sm font-medium">{value.name}</div>
                      </button>
                    ))}
                  </div>
                </div>
                
                <button
                  onClick={() => setStep(2)}
                  disabled={!formData.age || !formData.complaint}
                  className={`w-full py-4 rounded-lg font-semibold ${
                    formData.age && formData.complaint
                      ? 'bg-red-600 text-white hover:bg-red-700'
                      : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  }`}
                >
                  Continuar
                </button>
              </div>
            )}

            {/* Step 2: Discriminadores */}
            {step === 2 && formData.complaint && (
              <div className="space-y-6">
                <h2 className="text-xl font-bold text-gray-800 mb-4">
                  Responda as perguntas sobre {flowcharts[formData.complaint].name}
                </h2>
                
                <div className="space-y-3">
                  {flowcharts[formData.complaint].discriminators.map((disc) => (
                    <div
                      key={disc.id}
                      className="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
                    >
                      <label className="flex-1 cursor-pointer" htmlFor={disc.id}>
                        {disc.text}
                      </label>
                      <div className="flex items-center space-x-4">
                        <span className={`px-2 py-1 text-xs rounded-full font-semibold ${
                          disc.priority === 'RED' ? 'bg-red-100 text-red-600' :
                          disc.priority === 'ORANGE' ? 'bg-orange-100 text-orange-600' :
                          disc.priority === 'YELLOW' ? 'bg-yellow-100 text-yellow-600' :
                          'bg-green-100 text-green-600'
                        }`}>
                          {disc.priority}
                        </span>
                        <input
                          type="checkbox"
                          id={disc.id}
                          className="w-6 h-6"
                          checked={formData.discriminators[disc.id] || false}
                          onChange={(e) => setFormData({
                            ...formData,
                            discriminators: {
                              ...formData.discriminators,
                              [disc.id]: e.target.checked
                            }
                          })}
                        />
                      </div>
                    </div>
                  ))}
                </div>
                
                <div className="flex space-x-4">
                  <button
                    onClick={() => setStep(1)}
                    className="flex-1 py-4 rounded-lg border-2 border-gray-300 text-gray-700 hover:bg-gray-50"
                  >
                    Voltar
                  </button>
                  <button
                    onClick={() => setStep(3)}
                    className="flex-1 py-4 rounded-lg bg-red-600 text-white hover:bg-red-700 font-semibold"
                  >
                    Continuar
                  </button>
                </div>
              </div>
            )}

            {/* Step 3: Escala de Dor */}
            {step === 3 && (
              <div className="space-y-6">
                <h2 className="text-xl font-bold text-gray-800 mb-4">
                  Escala de Dor
                </h2>
                
                <p className="text-gray-600">
                  Em uma escala de 0 a 10, qual a intensidade da dor?
                </p>
                
                <div className="flex justify-between items-center space-x-2">
                  {[0,1,2,3,4,5,6,7,8,9,10].map(num => (
                    <button
                      key={num}
                      onClick={() => setFormData({...formData, painScale: num})}
                      className={`w-12 h-12 rounded-lg font-bold transition-all ${
                        formData.painScale === num
                          ? num <= 3 ? 'bg-green-500 text-white' :
                            num <= 7 ? 'bg-yellow-500 text-white' :
                            'bg-red-500 text-white'
                          : 'bg-gray-200 hover:bg-gray-300'
                      }`}
                    >
                      {num}
                    </button>
                  ))}
                </div>
                
                <div className="text-center text-sm text-gray-600">
                  {formData.painScale <= 3 && 'Dor leve'}
                  {formData.painScale > 3 && formData.painScale <= 7 && 'Dor moderada'}
                  {formData.painScale > 7 && 'Dor intensa'}
                </div>
                
                <div className="flex space-x-4">
                  <button
                    onClick={() => setStep(2)}
                    className="flex-1 py-4 rounded-lg border-2 border-gray-300 text-gray-700 hover:bg-gray-50"
                  >
                    Voltar
                  </button>
                  <button
                    onClick={handleSubmit}
                    className="flex-1 py-4 rounded-lg bg-red-600 text-white hover:bg-red-700 font-semibold"
                  >
                    Finalizar Triagem
                  </button>
                </div>
              </div>
            )}
          </div>
        ) : (
          /* Resultado da Triagem */
          <div className="bg-white rounded-2xl shadow-xl p-8">
            <div className={`text-center mb-8 p-6 rounded-xl ${
              triageResult.priority === 'RED' ? 'bg-red-100' :
              triageResult.priority === 'ORANGE' ? 'bg-orange-100' :
              triageResult.priority === 'YELLOW' ? 'bg-yellow-100' :
              triageResult.priority === 'GREEN' ? 'bg-green-100' :
              'bg-blue-100'
            }`}>
              <div className={`text-6xl font-black mb-4 ${
                triageResult.priority === 'RED' ? 'text-red-600' :
                triageResult.priority === 'ORANGE' ? 'text-orange-600' :
                triageResult.priority === 'YELLOW' ? 'text-yellow-600' :
                triageResult.priority === 'GREEN' ? 'text-green-600' :
                'text-blue-600'
              }`}>
                {triageResult.label}
              </div>
              <p className="text-xl font-semibold text-gray-800">
                {triageResult.message}
              </p>
              <p className="text-gray-600 mt-2">
                Tempo estimado de espera: {triageResult.wait} minutos
              </p>
            </div>
            
            {triageResult.priority === 'RED' && (
              <div className="bg-red-50 border-2 border-red-300 rounded-lg p-4 mb-6">
                <p className="text-red-800 font-semibold flex items-center">
                  <AlertCircle className="w-5 h-5 mr-2" />
                  Ligue 192 IMEDIATAMENTE ou vá ao hospital mais próximo!
                </p>
              </div>
            )}
            
            <div className="grid grid-cols-2 gap-4">
              <button
                onClick={onBack}
                className="py-4 rounded-lg border-2 border-gray-300 text-gray-700 hover:bg-gray-50 font-semibold"
              >
                Nova Busca
              </button>
              <button
                className="py-4 rounded-lg bg-blue-600 text-white hover:bg-blue-700 font-semibold"
              >
                Ver Unidades Próximas
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// App Principal
export default function OndeAtendeApp() {
  const [currentView, setCurrentView] = useState('search'); // 'search' ou 'triage'
  const [triageData, setTriageData] = useState(null);

  const handleTriageComplete = (data) => {
    setTriageData(data);
    // Aqui você poderia redirecionar para unidades recomendadas baseado na triagem
    console.log('Triagem completa:', data);
  };

  return (
    <>
      {currentView === 'search' ? (
        <SpecialtySearch onStartTriage={() => setCurrentView('triage')} />
      ) : (
        <TriageForm 
          onComplete={handleTriageComplete}
          onBack={() => setCurrentView('search')}
        />
      )}
    </>
  );
}