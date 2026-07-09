import { useState, useEffect, useRef } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, BarChart, Bar, Cell as RechartsCell,
} from 'recharts'
import './App.css'

const MAX_HISTORY = 60

const THERMAL_META = {
  normal: { label: 'NORMAL', color: '#3fb950' },
  warning: { label: 'UYARI', color: '#d29922' },
  critical: { label: 'KRİTİK', color: '#db6d28' },
  shutdown: { label: 'KAPATMA', color: '#f85149' },
}

function App() {
  const [connected, setConnected] = useState(false)
  const [latest, setLatest] = useState(null)
  const [history, setHistory] = useState([])
  const [drivingStyle, setDrivingStyle] = useState(null)
  const [drivingStyleError, setDrivingStyleError] = useState(null)
  const [analyzing, setAnalyzing] = useState(false)

  useEffect(() => {
    const wsUrl = `ws://${window.location.host}/ws/telemetry`
    const ws = new WebSocket(wsUrl)

    ws.onopen = () => setConnected(true)
    ws.onclose = () => setConnected(false)
    ws.onerror = () => setConnected(false)

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      setLatest(data)
      setHistory((prev) => {
        const point = {
          time: new Date(data.timestamp).toLocaleTimeString('tr-TR'),
          voltage: data.pack_voltage,
          soc: Math.round(data.pack_soc * 1000) / 10,
          temp: data.max_temperature_c,
        }
        const next = [...prev, point]
        return next.length > MAX_HISTORY ? next.slice(next.length - MAX_HISTORY) : next
      })
    }

    return () => ws.close()
  }, [])

  const fetchDrivingStyle = async () => {
    setAnalyzing(true)
    setDrivingStyleError(null)
    try {
      const res = await fetch('/ml/driving-style?pack_id=PACK-1')
      const data = await res.json()
      if (!res.ok) {
        setDrivingStyleError(data.detail || 'Bilinmeyen hata')
      } else {
        setDrivingStyle(data)
      }
    } catch {
      setDrivingStyleError('API\'ye ulaşılamadı')
    } finally {
      setAnalyzing(false)
    }
  }

  if (!latest) {
    return (
      <div className="app">
        <div className="boot-screen">
          <span className="boot-label">BATARYA TELEMETRİ SİSTEMİ</span>
          <span className="boot-status">{connected ? 'Bağlandı — veri bekleniyor' : 'Sunucuya bağlanılıyor...'}</span>
        </div>
      </div>
    )
  }

  const thermal = THERMAL_META[latest.thermal_state] || { label: latest.thermal_state, color: '#8b949e' }

  return (
    <div className="app">
      <header className="topbar">
        <div className="topbar-title">
          <span className="eyebrow">İKA / EV BATARYA İZLEME</span>
          <h1>{latest.pack_id}</h1>
        </div>
        <div className={`conn-indicator ${connected ? 'on' : 'off'}`}>
          <span className="dot" />
          {connected ? 'CANLI' : 'BAĞLANTI YOK'}
        </div>
      </header>

      <section className="kpi-grid">
        <div className="kpi">
          <span className="kpi-label">Pack Voltaj</span>
          <span className="kpi-value">{latest.pack_voltage.toFixed(2)}<small>V</small></span>
        </div>
        <div className="kpi">
          <span className="kpi-label">Şarj Durumu</span>
          <span className="kpi-value">{(latest.pack_soc * 100).toFixed(1)}<small>%</small></span>
        </div>
        <div className="kpi">
          <span className="kpi-label">Max Sıcaklık</span>
          <span className="kpi-value">{latest.max_temperature_c.toFixed(1)}<small>°C</small></span>
        </div>
        <div className="kpi">
          <span className="kpi-label">SoH (Sağlık)</span>
          <span className="kpi-value">{latest.soh_percent.toFixed(3)}<small>%</small></span>
        </div>
        <div className="kpi">
          <span className="kpi-label">Hücre Farkı</span>
          <span className="kpi-value">{latest.cell_voltage_delta.toFixed(3)}<small>V</small></span>
        </div>
        <div className="kpi">
          <span className="kpi-label">Termal Durum</span>
          <span className="thermal-badge" style={{ '--tc': thermal.color }}>{thermal.label}</span>
        </div>
      </section>

      <section className="charts-grid">
        <div className="panel">
          <h2>Voltaj &amp; Şarj Durumu</h2>
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={history}>
              <CartesianGrid strokeDasharray="3 3" stroke="#21262d" />
              <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#8b949e' }} />
              <YAxis yAxisId="left" tick={{ fontSize: 10, fill: '#8b949e' }} />
              <YAxis yAxisId="right" orientation="right" domain={[0, 100]} tick={{ fontSize: 10, fill: '#8b949e' }} />
              <Tooltip contentStyle={{ background: '#161b22', border: '1px solid #30363d', fontSize: 12 }} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Line yAxisId="left" type="monotone" dataKey="voltage" stroke="#58a6ff" name="Voltaj (V)" dot={false} strokeWidth={2} />
              <Line yAxisId="right" type="monotone" dataKey="soc" stroke="#56d4a0" name="SoC (%)" dot={false} strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="panel">
          <h2>Sıcaklık</h2>
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={history}>
              <CartesianGrid strokeDasharray="3 3" stroke="#21262d" />
              <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#8b949e' }} />
              <YAxis tick={{ fontSize: 10, fill: '#8b949e' }} />
              <Tooltip contentStyle={{ background: '#161b22', border: '1px solid #30363d', fontSize: 12 }} />
              <Line type="monotone" dataKey="temp" stroke="#db6d28" name="Sıcaklık (°C)" dot={false} strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="panel wide">
          <h2>Hücre Voltajları</h2>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={latest.cells.map((c) => ({
              name: c.cell_id.split('-').pop(),
              voltage: c.voltage,
              balancing: c.balancing_active,
            }))}>
              <CartesianGrid strokeDasharray="3 3" stroke="#21262d" />
              <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#8b949e' }} />
              <YAxis domain={['auto', 'auto']} tick={{ fontSize: 10, fill: '#8b949e' }} />
              <Tooltip contentStyle={{ background: '#161b22', border: '1px solid #30363d', fontSize: 12 }} />
              <Bar dataKey="voltage">
                {latest.cells.map((c, i) => (
                  <RechartsCell key={i} fill={c.balancing_active ? '#d29922' : '#a371f7'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <p className="hint">Turuncu hücre = pasif dengeleme aktif</p>
        </div>
      </section>

      <section className="panel ml-panel">
        <h2>Sürüş Karakteri Analizi</h2>
        <button className="analyze-btn" onClick={fetchDrivingStyle} disabled={analyzing}>
          {analyzing ? 'Analiz ediliyor...' : 'Oturumu Analiz Et'}
        </button>
        {drivingStyleError && <p className="ml-error">{drivingStyleError}</p>}
        {drivingStyle && (
          <div className="ml-result">
            <span className="style-tag">{drivingStyle.driving_style.toUpperCase()}</span>
            <p>{drivingStyle.recommendation}</p>
          </div>
        )}
      </section>
    </div>
  )
}

export default App