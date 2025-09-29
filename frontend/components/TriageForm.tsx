import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface TriageFormData {
  patient_name: string;
  patient_cpf: string;
  patient_phone: string;
  patient_age: number;
  upa_id: string;
  main_complaint: string;
  pain_level?: number;
  temperature?: number;
  blood_pressure?: string;
  heart_rate?: number;
  oxygen_saturation?: number;
  symptoms_ids: number[];
}

export function TriageForm({ upas, onSubmit }: {
  upas: Array<{id: string; name: string}>;
  onSubmit: (data: TriageFormData) => Promise<void>
}) {
  const [formData, setFormData] = useState<TriageFormData>({
    patient_name: '',
    patient_cpf: '',
    patient_phone: '',
    patient_age: 0,
    upa_id: '',
    main_complaint: '',
    symptoms_ids: []
  });

  const [loading, setLoading] = useState(false);
  const [priorityResult, setPriorityResult] = useState<string | null>(null);

  const priorityColors = {
    RED: 'bg-red-500 text-white',
    ORANGE: 'bg-orange-500 text-white',
    YELLOW: 'bg-yellow-500 text-black',
    GREEN: 'bg-green-500 text-white',
    BLUE: 'bg-blue-500 text-white'
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await fetch('/api/triages/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });

      const data = await response.json();
      setPriorityResult(data.priority);

      await onSubmit(formData);
    } catch (error) {
      console.error('Erro na triagem:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle>Triagem Digital - Protocolo Manchester</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>Nome Completo</Label>
              <Input
                required
                value={formData.patient_name}
                onChange={e => setFormData({...formData, patient_name: e.target.value})}
              />
            </div>

            <div>
              <Label>CPF</Label>
              <Input
                required
                placeholder="000.000.000-00"
                value={formData.patient_cpf}
                onChange={e => setFormData({...formData, patient_cpf: e.target.value})}
              />
            </div>

            <div>
              <Label>Telefone</Label>
              <Input
                required
                value={formData.patient_phone}
                onChange={e => setFormData({...formData, patient_phone: e.target.value})}
              />
            </div>

            <div>
              <Label>Idade</Label>
              <Input
                type="number"
                required
                value={formData.patient_age}
                onChange={e => setFormData({...formData, patient_age: parseInt(e.target.value)})}
              />
            </div>
          </div>

          <div>
            <Label>UPA</Label>
            <Select
              value={formData.upa_id}
              onValueChange={v => setFormData({...formData, upa_id: v})}
            >
              <SelectTrigger>
                <SelectValue placeholder="Selecione a UPA" />
              </SelectTrigger>
              <SelectContent>
                {upas.map(upa => (
                  <SelectItem key={upa.id} value={upa.id}>
                    {upa.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label>Queixa Principal</Label>
            <Textarea
              required
              rows={3}
              placeholder="Descreva os sintomas principais..."
              value={formData.main_complaint}
              onChange={e => setFormData({...formData, main_complaint: e.target.value})}
            />
          </div>

          <div className="border-t pt-4">
            <h3 className="font-semibold mb-3">Sinais Vitais (opcional)</h3>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <Label>Nível de Dor (0-10)</Label>
                <Input
                  type="number"
                  min="0"
                  max="10"
                  value={formData.pain_level || ''}
                  onChange={e => setFormData({...formData, pain_level: parseInt(e.target.value)})}
                />
              </div>

              <div>
                <Label>Temperatura (°C)</Label>
                <Input
                  type="number"
                  step="0.1"
                  value={formData.temperature || ''}
                  onChange={e => setFormData({...formData, temperature: parseFloat(e.target.value)})}
                />
              </div>

              <div>
                <Label>Pressão Arterial</Label>
                <Input
                  placeholder="120/80"
                  value={formData.blood_pressure || ''}
                  onChange={e => setFormData({...formData, blood_pressure: e.target.value})}
                />
              </div>

              <div>
                <Label>Freq. Cardíaca (bpm)</Label>
                <Input
                  type="number"
                  value={formData.heart_rate || ''}
                  onChange={e => setFormData({...formData, heart_rate: parseInt(e.target.value)})}
                />
              </div>

              <div>
                <Label>Saturação O₂ (%)</Label>
                <Input
                  type="number"
                  min="0"
                  max="100"
                  value={formData.oxygen_saturation || ''}
                  onChange={e => setFormData({...formData, oxygen_saturation: parseInt(e.target.value)})}
                />
              </div>
            </div>
          </div>

          {priorityResult && (
            <Alert className={priorityColors[priorityResult as keyof typeof priorityColors]}>
              <AlertDescription>
                Classificação de Risco: {priorityResult}
                <br />
                Dirija-se à recepção da UPA com este protocolo.
              </AlertDescription>
            </Alert>
          )}

          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? 'Processando...' : 'Realizar Triagem'}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}